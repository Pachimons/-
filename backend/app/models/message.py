"""消息模型 — 用户和 AI 之间的每一条对话消息"""
import uuid
import json
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    # 消息唯一 ID
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # 所属会话 ID
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    # 消息角色：user（用户）/ assistant（AI）/ system（系统）
    role = Column(String, nullable=False)
    # 消息文本内容
    content = Column(Text, default="")
    # 附带的图片 URL 列表（JSON 字符串）
    _image_urls = Column("image_urls", Text, default="[]")
    # 额外元数据（JSON 字符串，如 token 用量等）
    _metadata = Column("metadata", Text, default="{}")
    # 创建时间
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关联关系
    conversation = relationship("Conversation", back_populates="messages")

    @property
    def image_urls(self) -> list:
        """获取图片 URL 列表"""
        try:
            return json.loads(self._image_urls) if self._image_urls else []
        except json.JSONDecodeError:
            return []

    @image_urls.setter
    def image_urls(self, value: list):
        """设置图片 URL 列表"""
        self._image_urls = json.dumps(value, ensure_ascii=False)

    @property
    def meta(self) -> dict:
        """获取元数据字典"""
        try:
            return json.loads(self._metadata) if self._metadata else {}
        except json.JSONDecodeError:
            return {}

    @meta.setter
    def meta(self, value: dict):
        """设置元数据字典"""
        self._metadata = json.dumps(value, ensure_ascii=False)
