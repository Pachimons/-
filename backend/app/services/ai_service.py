"""AI 服务 — 通过 OpenAI 兼容接口调用 Gemini 3.1 Pro，处理对话和结构化需求提取"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# 系统提示词：建筑设计顾问角色
SYSTEM_PROMPT = """你是一位专业的别墅建筑设计顾问，拥有 20 年设计经验。你的任务是通过友好的对话，逐步收集用户的建房需求。

## 你的工作方式：
1. 每次只问 1-2 个问题，不要一次问太多
2. 用通俗易懂的语言，避免专业术语
3. 给出专业建议，帮助用户做决定
4. 当收集到足够信息后，总结需求并确认

## 需要收集的关键信息（按优先级）：
1. **土地面积**和**所在位置**（省市区）
2. **楼层数**
3. **建筑风格**（现代简约/中式/欧式/地中海/日式等）
4. **房间需求**（卧室数、卫生间数、总房间数）
5. **特殊需求**（老人房、车库、花园、阳台等）
6. **预算范围**

## 回复格式要求（严格遵守）：
你的回复必须分为两部分，用分隔符 <<<REQUIREMENT>>> 隔开：

**第一部分**：你对用户说的话（使用 Markdown 格式），友好、简洁、有引导性。
**第二部分**：在 <<<REQUIREMENT>>> 之后，输出一个 JSON 对象，记录当前已收集的需求。

示例回复格式：
您好！很高兴为您服务 🏡

请告诉我您的**土地面积**和**所在位置**，我们就可以开始设计了！

<<<REQUIREMENT>>>
{"land_area": null, "land_location": null, "floors": null, "style": null, "total_rooms": null, "bedrooms": null, "bathrooms": null, "has_elderly_room": null, "has_garage": null, "has_garden": null, "budget": null, "special_notes": null, "completeness": 0.0}

## 重要规则：
- 第一部分是自然语言回复，直接写内容，不要加任何 JSON 包裹
- <<<REQUIREMENT>>> 是固定分隔符，必须独占一行
- 第二部分是紧凑的单行 JSON 对象
- requirement 中已知的需求参数填入实际值，未知的保持 null
- completeness 字段：0~1 的浮点数，表示需求收集的完整度
  - 收集到面积和位置 = 0.2
  - 加上楼层和风格 = 0.4
  - 加上房间需求 = 0.6
  - 加上特殊需求 = 0.8
  - 全部信息确认 = 1.0
- 当 completeness >= 0.8 时，在回复中提醒用户可以生成设计方案了
"""


class AIService:
    """AI 能力封装，通过 OpenAI 兼容接口调用 Gemini"""

    def __init__(self):
        """初始化 API 客户端"""
        self.api_key = settings.AI_API_KEY
        self.api_base = settings.AI_API_BASE.rstrip("/")
        self.model = settings.AI_MODEL
        self.chat_url = f"{self.api_base}/chat/completions"
        # 代理配置（系统代理，httpx 需要显式传入）
        self.proxy = settings.HTTP_PROXY or None

        if self.api_key:
            proxy_info = f", proxy={self.proxy}" if self.proxy else ""
            logger.info(f"AI 服务已配置: model={self.model}, base={self.api_base}{proxy_info}")
        else:
            logger.warning("未配置 AI_API_KEY，AI 对话功能将使用模拟模式")

    def _build_api_messages(self, messages: list[dict]) -> list[dict]:
        """构建 OpenAI 格式的消息列表，含系统提示词"""
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in messages:
            role = msg["role"] if msg["role"] in ("user", "assistant", "system") else "user"
            api_messages.append({"role": role, "content": msg["content"]})
        return api_messages

    async def chat(
        self,
        messages: list[dict],
        image_data: Optional[bytes] = None,
    ) -> dict:
        """
        发送消息给 AI，返回回复和结构化需求（非流式）。
        
        Args:
            messages: 对话历史，格式 [{"role": "user"/"assistant", "content": "..."}]
            image_data: 可选的图片数据（多模态）
            
        Returns:
            {"reply": "AI的回复文本", "requirement": {...结构化需求...}}
        """
        if not self.api_key:
            return self._mock_response(messages)

        try:
            api_messages = self._build_api_messages(messages)

            async with httpx.AsyncClient(timeout=60.0, proxy=self.proxy) as client:
                resp = await client.post(
                    self.chat_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": api_messages,
                        "temperature": 0.7,
                        "max_tokens": 2048,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            # 提取 AI 回复文本
            reply_text = data["choices"][0]["message"]["content"]
            return self._parse_response(reply_text)

        except httpx.HTTPStatusError as e:
            logger.error(f"AI API HTTP 错误 {e.response.status_code}: {e.response.text}")
            return {
                "reply": f"AI 服务暂时不可用（HTTP {e.response.status_code}），请稍后重试。",
                "requirement": None,
            }
        except Exception as e:
            logger.error(f"AI API 调用失败: {e}")
            return {
                "reply": "抱歉，我暂时无法处理您的请求，请稍后重试。",
                "requirement": None,
            }

    async def chat_stream(
        self,
        messages: list[dict],
        image_data: Optional[bytes] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话（SSE 用），逐步返回文本。
        注意：流式模式下结构化需求在最后一次性解析。
        
        Yields:
            每次生成的文本片段
        """
        if not self.api_key:
            mock = self._mock_response(messages)
            # 模拟流式：先逐段发送回复文本
            reply = mock.get("reply", "")
            # 模拟打字效果，按句子分段发送
            sentences = reply.replace("\n", "\n|").split("|")
            for sentence in sentences:
                if sentence:
                    yield sentence
                    await asyncio.sleep(0.05)
            # 最后发送结构化需求
            if mock.get("requirement"):
                yield f"\n__REQUIREMENT_JSON__{json.dumps(mock['requirement'], ensure_ascii=False)}__END_REQUIREMENT__"
            return

        try:
            api_messages = self._build_api_messages(messages)

            # 使用 httpx 流式请求
            async with httpx.AsyncClient(timeout=120.0, proxy=self.proxy) as client:
                async with client.stream(
                    "POST",
                    self.chat_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": api_messages,
                        "temperature": 0.7,
                        "max_tokens": 2048,
                        "stream": True,
                    },
                ) as resp:
                    resp.raise_for_status()
                    full_text = ""
                    # 标记是否进入了需求 JSON 区域（<<<REQUIREMENT>>> 之后）
                    in_requirement_section = False
                    requirement_buffer = ""

                    async for line in resp.aiter_lines():
                        # OpenAI SSE 格式：data: {...}
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if payload.strip() == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(payload)
                            delta = chunk_data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if not content:
                                continue

                            full_text += content

                            if in_requirement_section:
                                # 已进入需求区域，累积但不推送给前端
                                requirement_buffer += content
                            elif "<<<REQUIREMENT>>>" in (full_text if "<<<" in content else content):
                                # 检测到分隔符，切割当前 chunk
                                # 分隔符可能跨多个 chunk，用 full_text 检测
                                before, _, after = full_text.partition("<<<REQUIREMENT>>>")
                                # 只推送分隔符之前的新内容（如果有）
                                already_sent = full_text[:len(full_text) - len(content)]
                                unsent_reply = before[len(already_sent):] if len(before) > len(already_sent) else ""
                                if unsent_reply:
                                    yield unsent_reply
                                in_requirement_section = True
                                requirement_buffer = after
                            else:
                                # 正常回复文本，直接推送给前端
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            logger.debug(f"跳过无法解析的 SSE 片段: {line[:100]}")

            # 流结束后，解析需求 JSON
            if requirement_buffer:
                try:
                    req_json = requirement_buffer.strip()
                    # 去除可能的 markdown 代码块包裹
                    if req_json.startswith("```"): req_json = req_json.split("\n", 1)[-1]
                    if req_json.endswith("```"): req_json = req_json[:-3].strip()
                    req_data = json.loads(req_json)
                    yield f"\n__REQUIREMENT_JSON__{json.dumps(req_data, ensure_ascii=False)}__END_REQUIREMENT__"
                except json.JSONDecodeError:
                    logger.warning(f"无法解析需求 JSON: {requirement_buffer[:200]}")
            else:
                # 回退：AI 没有输出分隔符，尝试从完整文本解析
                parsed = self._parse_response(full_text)
                if parsed.get("requirement"):
                    yield f"\n__REQUIREMENT_JSON__{json.dumps(parsed['requirement'], ensure_ascii=False)}__END_REQUIREMENT__"

        except httpx.HTTPStatusError as e:
            logger.error(f"AI 流式 HTTP 错误 {e.response.status_code}: {e.response.text}")
            yield f"AI 服务暂时不可用（HTTP {e.response.status_code}），请稍后重试。"
        except Exception as e:
            import traceback
            logger.error(f"AI 流式调用失败: type={type(e).__name__}, msg={e}\n{traceback.format_exc()}")
            yield "抱歉，我暂时无法处理您的请求，请稍后重试。"

    def _parse_response(self, text: str) -> dict:
        """解析 AI 返回的响应（支持分隔符格式和纯 JSON 格式）"""
        # 先尝试分隔符格式
        if "<<<REQUIREMENT>>>" in text:
            reply_part, _, req_part = text.partition("<<<REQUIREMENT>>>")
            requirement = None
            try:
                req_json = req_part.strip()
                if req_json.startswith("```"): req_json = req_json.split("\n", 1)[-1]
                if req_json.endswith("```"): req_json = req_json[:-3].strip()
                requirement = json.loads(req_json)
            except json.JSONDecodeError:
                logger.warning(f"无法解析需求 JSON: {req_part[:200]}")
            return {"reply": reply_part.strip(), "requirement": requirement}

        # 回退：尝试纯 JSON 格式（旧版提示词兼容）
        try:
            cleaned = text.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:]
            if cleaned.startswith("```"): cleaned = cleaned[3:]
            if cleaned.endswith("```"): cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)
            return {
                "reply": data.get("reply", text),
                "requirement": data.get("requirement", None)
            }
        except json.JSONDecodeError:
            logger.warning("AI 返回非 JSON 格式，原文返回")
            return {"reply": text, "requirement": None}

    def _mock_response(self, messages: list[dict]) -> dict:
        """模拟模式（无 API Key 时使用，方便前端开发调试）"""
        user_msg = messages[-1]["content"] if messages else ""
        
        # 简单的关键词匹配，模拟 AI 回复
        if not messages or len(messages) <= 1:
            return {
                "reply": '您好！我是您的 AI 建筑设计顾问 🏡\n\n请告诉我您的**土地面积**和**所在位置**，我们就可以开始设计您的梦想别墅了！\n\n比如："我有一块 150 平米的地，在广东佛山。"',
                "requirement": {
                    "completeness": 0.0
                }
            }
        
        if any(kw in user_msg for kw in ["平米", "亩", "面积", "地"]):
            return {
                "reply": "好的，了解了您的土地信息！\n\n接下来想问问您：\n1. 想建**几层**呢？\n2. 有没有喜欢的**建筑风格**？（现代简约、中式、欧式等）",
                "requirement": {
                    "land_area": 150.0,
                    "land_location": "广东",
                    "completeness": 0.2
                }
            }
        
        if any(kw in user_msg for kw in ["层", "楼", "风格"]):
            return {
                "reply": "很好的选择！\n\n现在聊聊房间需求：\n- 您需要几间**卧室**？\n- 需要几个**卫生间**？\n- 家里有**老人**需要住在一楼吗？",
                "requirement": {
                    "land_area": 150.0,
                    "land_location": "广东",
                    "floors": 3,
                    "style": "现代简约",
                    "completeness": 0.4
                }
            }
        
        return {
            "reply": f"收到您的信息：{user_msg}\n\n让我为您分析一下，请稍等...\n\n您还有什么其他需求吗？",
            "requirement": {
                "completeness": 0.3
            }
        }


# 创建全局 AI 服务实例
ai_service = AIService()
