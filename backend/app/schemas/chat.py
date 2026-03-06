"""对话相关的请求和响应模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    """创建新会话的请求"""
    session_id: str = Field(..., description="匿名用户标识（浏览器生成的 UUID）")


class SendMessageRequest(BaseModel):
    """发送消息的请求"""
    content: str = Field(..., description="消息文本内容")
    image_urls: list[str] = Field(default=[], description="附带的图片 URL 列表")


class MessageResponse(BaseModel):
    """单条消息的响应"""
    id: str
    conversation_id: str
    role: str
    content: str
    image_urls: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """会话信息的响应"""
    id: str
    session_id: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    """会话详情（包含所有消息）"""
    id: str
    session_id: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}
