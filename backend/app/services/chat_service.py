"""对话服务 — 管理会话生命周期、消息持久化、调用 AI"""
import json
import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.requirement import Requirement
from app.services.ai_service import ai_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class ChatService:
    """对话管理核心服务"""

    def create_conversation(self, db: Session, session_id: str) -> Conversation:
        """创建新会话"""
        conv = Conversation(session_id=session_id)
        db.add(conv)
        db.flush()  # 确保 conv.id 已生成

        # 添加 AI 欢迎消息
        welcome_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content='您好！我是您的 AI 建筑设计顾问 🏡\n\n请告诉我您的**土地面积**和**所在位置**，我们就可以开始设计您的梦想别墅了！\n\n比如："我有一块 150 平米的地，在广东佛山。"',
        )
        db.add(welcome_msg)

        # 创建初始需求记录
        req = Requirement(conversation_id=conv.id, version=1)
        db.add(req)

        db.commit()
        db.refresh(conv)
        return conv

    def get_conversations(self, db: Session, session_id: str) -> list[Conversation]:
        """获取某用户的所有会话"""
        return (
            db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    def get_conversation(self, db: Session, conversation_id: str) -> Optional[Conversation]:
        """获取单个会话（含消息）"""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def delete_conversation(self, db: Session, conversation_id: str) -> bool:
        """删除会话"""
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            db.delete(conv)
            db.commit()
            return True
        return False

    async def send_message(
        self,
        db: Session,
        conversation_id: str,
        content: str,
        image_urls: list[str] = None,
    ) -> dict:
        """
        发送用户消息并获取 AI 回复（非流式）。
        
        Returns:
            {"ai_message": Message, "requirement": Requirement | None}
        """
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise ValueError(f"会话不存在: {conversation_id}")

        # 1. 保存用户消息
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )
        if image_urls:
            user_msg.image_urls = image_urls
        db.add(user_msg)
        db.commit()

        # 2. 构建对话历史
        messages = self._build_message_history(db, conversation_id)

        # 2.5 RAG：根据用户消息和已有需求检索相关建筑规范
        rag_context = self._get_rag_context(db, conversation_id, content)
        if rag_context:
            # 在消息历史最前面插入系统级的规范参考
            messages.insert(0, {
                "role": "user",
                "content": f"[系统提示 - 相关建筑规范参考，请在回复中适当引用]\n{rag_context}"
            })
            messages.insert(1, {
                "role": "assistant",
                "content": "好的，我已了解相关建筑规范，会在回复中参考。"
            })

        # 3. 调用 AI
        ai_response = await ai_service.chat(messages)

        # 4. 保存 AI 回复
        ai_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=ai_response.get("reply", ""),
        )
        db.add(ai_msg)

        # 5. 更新结构化需求
        requirement = None
        if ai_response.get("requirement"):
            requirement = self._update_requirement(db, conversation_id, ai_response["requirement"])

        # 6. 更新会话标题（如果是第一条用户消息）
        user_msgs = [m for m in conv.messages if m.role == "user"]
        if len(user_msgs) <= 1:
            conv.title = content[:50] + ("..." if len(content) > 50 else "")

        db.commit()
        db.refresh(ai_msg)

        return {"ai_message": ai_msg, "requirement": requirement}

    async def send_message_stream(
        self,
        db: Session,
        conversation_id: str,
        content: str,
        image_urls: list[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        发送用户消息并流式获取 AI 回复（SSE 用）。
        
        Yields:
            SSE 格式的文本片段
        """
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            yield f'data: {json.dumps({"error": "会话不存在"}, ensure_ascii=False)}\n\n'
            return

        # 1. 保存用户消息
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )
        if image_urls:
            user_msg.image_urls = image_urls
        db.add(user_msg)
        db.commit()

        # 2. 构建对话历史
        messages = self._build_message_history(db, conversation_id)

        # 2.5 RAG：根据用户消息和已有需求检索相关建筑规范
        rag_context = self._get_rag_context(db, conversation_id, content)
        if rag_context:
            messages.insert(0, {
                "role": "user",
                "content": f"[系统提示 - 相关建筑规范参考，请在回复中适当引用]\n{rag_context}"
            })
            messages.insert(1, {
                "role": "assistant",
                "content": "好的，我已了解相关建筑规范，会在回复中参考。"
            })

        # 3. 流式调用 AI
        full_reply = ""
        requirement_data = None
        requirement_sent = False  # 标记是否已通过流发送过需求

        async for chunk in ai_service.chat_stream(messages):
            # 检查是否包含结构化需求标记
            if "__REQUIREMENT_JSON__" in chunk:
                # 提取需求 JSON
                start = chunk.index("__REQUIREMENT_JSON__") + len("__REQUIREMENT_JSON__")
                end = chunk.index("__END_REQUIREMENT__")
                req_json = chunk[start:end]
                try:
                    requirement_data = json.loads(req_json)
                except json.JSONDecodeError:
                    pass
                # 发送需求更新事件
                if requirement_data:
                    yield f'data: {json.dumps({"type": "requirement", "data": requirement_data}, ensure_ascii=False)}\n\n'
                    requirement_sent = True
            else:
                full_reply += chunk
                yield f'data: {json.dumps({"type": "text", "content": chunk}, ensure_ascii=False)}\n\n'

        # 4. 保存完整 AI 回复
        # 尝试从完整回复中解析 JSON（如果 AI 返回的是 JSON 格式）
        parsed = ai_service._parse_response(full_reply)
        actual_reply = parsed.get("reply", full_reply)
        if parsed.get("requirement") and not requirement_data:
            requirement_data = parsed["requirement"]

        ai_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=actual_reply,
        )
        db.add(ai_msg)

        # 5. 更新需求（只在之前没通过流发送过时才发送给前端）
        if requirement_data:
            self._update_requirement(db, conversation_id, requirement_data)
            if not requirement_sent:
                yield f'data: {json.dumps({"type": "requirement", "data": requirement_data}, ensure_ascii=False)}\n\n'

        # 6. 更新会话标题
        user_msgs = [m for m in conv.messages if m.role == "user"]
        if len(user_msgs) <= 1:
            conv.title = content[:50] + ("..." if len(content) > 50 else "")

        db.commit()

        # 发送结束信号
        yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'

    def get_latest_requirement(self, db: Session, conversation_id: str) -> Optional[Requirement]:
        """获取会话最新的结构化需求"""
        return (
            db.query(Requirement)
            .filter(Requirement.conversation_id == conversation_id)
            .order_by(Requirement.version.desc())
            .first()
        )

    def _build_message_history(self, db: Session, conversation_id: str) -> list[dict]:
        """构建 AI 所需的对话历史格式"""
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.role in ("user", "assistant")
        ]

    @staticmethod
    def _clean_requirement_data(data: dict) -> dict:
        """清洗 AI 返回的需求数据，确保类型与数据库字段匹配。
        AI 可能返回 '200平米' 而数据库需要 Float，或 '3层' 而需要 Integer。
        """
        import re
        cleaned = dict(data)

        # Float 字段：提取数字部分
        for key in ("land_area", "budget"):
            val = cleaned.get(key)
            if isinstance(val, str):
                nums = re.findall(r"[\d.]+", val)
                if nums:
                    factor = 10000 if key == "budget" and "万" in val else 1
                    try:
                        cleaned[key] = float(nums[0]) * factor
                    except ValueError:
                        cleaned[key] = None
                else:
                    cleaned[key] = None

        # Integer 字段：提取数字部分
        for key in ("floors", "total_rooms", "bedrooms", "bathrooms"):
            val = cleaned.get(key)
            if isinstance(val, str):
                nums = re.findall(r"\d+", val)
                cleaned[key] = int(nums[0]) if nums else None
            elif isinstance(val, float):
                cleaned[key] = int(val)

        # Boolean 字段：字符串转布尔
        for key in ("has_elderly_room", "has_garage", "has_garden"):
            val = cleaned.get(key)
            if isinstance(val, str):
                cleaned[key] = val.lower() in ("true", "是", "yes", "1", "需要", "要")

        # completeness 确保是 float
        comp = cleaned.get("completeness")
        if isinstance(comp, str):
            nums = re.findall(r"[\d.]+", comp)
            cleaned["completeness"] = float(nums[0]) if nums else 0.0

        return cleaned

    def _update_requirement(
        self, db: Session, conversation_id: str, data: dict
    ) -> Requirement:
        """更新或创建结构化需求"""
        # 清洗数据类型
        data = self._clean_requirement_data(data)

        # 获取最新版本
        latest = self.get_latest_requirement(db, conversation_id)

        if latest:
            # 更新现有需求
            for key, value in data.items():
                if value is not None and hasattr(latest, key):
                    setattr(latest, key, value)
            latest.raw_json = data
            db.flush()
            return latest
        else:
            # 创建新需求
            req = Requirement(
                conversation_id=conversation_id,
                version=1,
                **{k: v for k, v in data.items() if v is not None and k != "completeness"},
                completeness=data.get("completeness", 0.0),
            )
            req.raw_json = data
            db.add(req)
            db.flush()
            return req

    def _get_rag_context(self, db: Session, conversation_id: str, user_content: str) -> str:
        """根据用户消息和已有需求，从知识库检索相关建筑规范"""
        try:
            # 获取已有的结构化需求
            requirement = self.get_latest_requirement(db, conversation_id)
            req_dict = requirement.raw_json if requirement else {}

            # 如果有结构化需求，用需求驱动检索
            if req_dict and any(v for k, v in req_dict.items() if k != "completeness" and v):
                return rag_service.get_context_for_requirement(req_dict)

            # 否则直接用用户消息检索
            results = rag_service.search(user_content, n_results=2)
            if results:
                parts = ["以下是相关的建筑规范参考：\n"]
                for r in results:
                    parts.append(f"---\n【{r['section']}】\n{r['text']}\n")
                return "\n".join(parts)

            return ""
        except Exception as e:
            logger.warning(f"RAG 检索失败（不影响对话）: {e}")
            return ""


# 创建全局对话服务实例
chat_service = ChatService()
