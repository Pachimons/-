"""会话模型 — 每次用户开启新的设计咨询就是一个会话"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    # 会话唯一 ID
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # 匿名用户标识（浏览器生成的 UUID）
    session_id = Column(String, index=True, nullable=False)
    # 会话标题（根据第一条消息自动生成）
    title = Column(String, default="新的设计咨询")
    # 状态：active（进行中）/ archived（已归档）
    status = Column(String, default="active")
    # 创建和更新时间
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # 关联关系
    messages = relationship("Message", back_populates="conversation",
                            cascade="all, delete-orphan", order_by="Message.created_at")
    requirements = relationship("Requirement", back_populates="conversation",
                                cascade="all, delete-orphan", order_by="Requirement.version")
    plans = relationship("Plan", back_populates="conversation",
                         cascade="all, delete-orphan")
