"""对话相关路由 — 会话 CRUD 和消息发送"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import (
    CreateConversationRequest,
    SendMessageRequest,
    ConversationResponse,
    ConversationDetailResponse,
    MessageResponse,
)
from app.schemas.requirement import RequirementResponse
from app.services.chat_service import chat_service

router = APIRouter(prefix="/api/conversations", tags=["对话"])


@router.post("", response_model=ConversationResponse)
def create_conversation(req: CreateConversationRequest, db: Session = Depends(get_db)):
    """创建新会话"""
    conv = chat_service.create_conversation(db, req.session_id)
    return ConversationResponse(
        id=conv.id,
        session_id=conv.session_id,
        title=conv.title,
        status=conv.status,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(conv.messages),
    )


@router.get("", response_model=list[ConversationResponse])
def list_conversations(session_id: str = Query(...), db: Session = Depends(get_db)):
    """获取某用户的所有会话"""
    convs = chat_service.get_conversations(db, session_id)
    return [
        ConversationResponse(
            id=c.id,
            session_id=c.session_id,
            title=c.title,
            status=c.status,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=len(c.messages),
        )
        for c in convs
    ]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """获取会话详情（包含所有消息）"""
    conv = chat_service.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return ConversationDetailResponse(
        id=conv.id,
        session_id=conv.session_id,
        title=conv.title,
        status=conv.status,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                image_urls=m.image_urls,
                created_at=m.created_at,
            )
            for m in conv.messages
        ],
    )


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """删除会话"""
    success = chat_service.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话已删除"}


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    req: SendMessageRequest,
    stream: bool = Query(default=True, description="是否使用流式响应"),
    db: Session = Depends(get_db),
):
    """
    发送消息。
    stream=true（默认）：返回 SSE 流式响应
    stream=false：返回完整 JSON 响应
    """
    if stream:
        # 流式响应（SSE）
        return StreamingResponse(
            chat_service.send_message_stream(
                db, conversation_id, req.content, req.image_urls
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # 非流式响应
        result = await chat_service.send_message(
            db, conversation_id, req.content, req.image_urls
        )
        ai_msg = result["ai_message"]
        return {
            "message": MessageResponse(
                id=ai_msg.id,
                conversation_id=ai_msg.conversation_id,
                role=ai_msg.role,
                content=ai_msg.content,
                image_urls=ai_msg.image_urls,
                created_at=ai_msg.created_at,
            ),
            "requirement": result.get("requirement"),
        }


@router.get("/{conversation_id}/requirement", response_model=RequirementResponse)
def get_requirement(conversation_id: str, db: Session = Depends(get_db)):
    """获取会话最新的结构化需求"""
    req = chat_service.get_latest_requirement(db, conversation_id)
    if not req:
        raise HTTPException(status_code=404, detail="暂无需求数据")
    return req
