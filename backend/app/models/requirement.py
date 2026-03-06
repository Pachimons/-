"""结构化建房需求模型 — AI 从对话中提取的建房参数"""
import uuid
import json
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Requirement(Base):
    __tablename__ = "requirements"

    # 需求唯一 ID
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # 所属会话 ID
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)

    # ====== 建房核心参数 ======
    # 土地面积（平方米）
    land_area = Column(Float, nullable=True)
    # 土地所在地（省市区）
    land_location = Column(String, nullable=True)
    # 楼层数
    floors = Column(Integer, nullable=True)
    # 建筑风格（现代/中式/欧式/地中海等）
    style = Column(String, nullable=True)
    # 总房间数
    total_rooms = Column(Integer, nullable=True)
    # 卧室数
    bedrooms = Column(Integer, nullable=True)
    # 卫生间数
    bathrooms = Column(Integer, nullable=True)
    # 是否需要老人房
    has_elderly_room = Column(Boolean, nullable=True)
    # 是否需要车库
    has_garage = Column(Boolean, nullable=True)
    # 是否需要花园
    has_garden = Column(Boolean, nullable=True)
    # 预算（元）
    budget = Column(Float, nullable=True)
    # 特殊备注
    special_notes = Column(Text, nullable=True)

    # ====== 元信息 ======
    # 需求完整度（0~1，AI 评估所有必要参数是否收集齐了）
    completeness = Column(Float, default=0.0)
    # AI 输出的原始 JSON（保留完整数据）
    _raw_json = Column("raw_json", Text, default="{}")
    # 版本号（每次对话更新需求时 +1）
    version = Column(Integer, default=1)
    # 创建和更新时间
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # 关联关系
    conversation = relationship("Conversation", back_populates="requirements")
    plans = relationship("Plan", back_populates="requirement")

    @property
    def raw_json(self) -> dict:
        try:
            return json.loads(self._raw_json) if self._raw_json else {}
        except json.JSONDecodeError:
            return {}

    @raw_json.setter
    def raw_json(self, value: dict):
        self._raw_json = json.dumps(value, ensure_ascii=False)
