"""设计方案模型 — AI 基于结构化需求生成的别墅设计方案"""
import uuid
import json
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Plan(Base):
    __tablename__ = "plans"

    # 方案唯一 ID
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # 所属会话 ID
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    # 基于的需求版本 ID
    requirement_id = Column(String, ForeignKey("requirements.id"), nullable=True)

    # 方案文字描述
    description = Column(Text, default="")
    # 平面图结构化数据（JSON）
    _floor_plan_data = Column("floor_plan_data", Text, default="{}")
    # 效果图 URL 列表（JSON）
    _rendering_urls = Column("rendering_urls", Text, default="[]")
    # AI 的设计建议
    ai_suggestions = Column(Text, default="")
    # 方案状态：generating（生成中）/ completed（完成）/ failed（失败）
    status = Column(String, default="generating")
    # 创建时间
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关联关系
    conversation = relationship("Conversation", back_populates="plans")
    requirement = relationship("Requirement", back_populates="plans")

    @property
    def floor_plan_data(self) -> dict:
        try:
            return json.loads(self._floor_plan_data) if self._floor_plan_data else {}
        except json.JSONDecodeError:
            return {}

    @floor_plan_data.setter
    def floor_plan_data(self, value: dict):
        self._floor_plan_data = json.dumps(value, ensure_ascii=False)

    @property
    def rendering_urls(self) -> list:
        try:
            return json.loads(self._rendering_urls) if self._rendering_urls else []
        except json.JSONDecodeError:
            return []

    @rendering_urls.setter
    def rendering_urls(self, value: list):
        self._rendering_urls = json.dumps(value, ensure_ascii=False)
