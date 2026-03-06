"""方案相关路由 — 生成设计方案和效果图"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.plan import Plan
from app.schemas.plan import GeneratePlanRequest, GenerateImageRequest, PlanResponse
from app.services.chat_service import chat_service
from app.services.image_service import image_service

router = APIRouter(prefix="/api", tags=["方案"])


@router.post("/conversations/{conversation_id}/generate-image")
async def generate_image(
    conversation_id: str,
    req: GenerateImageRequest,
    db: Session = Depends(get_db),
):
    """生成别墅效果图"""
    # 获取最新需求
    requirement = chat_service.get_latest_requirement(db, conversation_id)

    if req.prompt:
        # 使用自定义 Prompt
        prompt = req.prompt
    elif requirement:
        # 根据需求自动生成 Prompt
        prompt = image_service.build_villa_prompt(requirement.raw_json)
    else:
        prompt = "A beautiful modern villa with white walls, large windows, surrounded by a garden, architectural rendering, photorealistic"

    # 调用图像生成 API
    urls = await image_service.generate_image(
        prompt=prompt,
        image_size=req.image_size,
    )

    if not urls:
        raise HTTPException(status_code=500, detail="图像生成失败，请重试")

    # 保存到方案记录
    plan = Plan(
        conversation_id=conversation_id,
        requirement_id=requirement.id if requirement else None,
        description=f"基于以下 Prompt 生成的效果图：{prompt}",
        status="completed",
    )
    plan.rendering_urls = urls
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return PlanResponse(
        id=plan.id,
        conversation_id=plan.conversation_id,
        requirement_id=plan.requirement_id,
        description=plan.description,
        rendering_urls=urls,
        status=plan.status,
        created_at=plan.created_at,
    )


@router.get("/conversations/{conversation_id}/plans", response_model=list[PlanResponse])
def get_conversation_plans(conversation_id: str, db: Session = Depends(get_db)):
    """获取会话的所有效果图方案"""
    plans = (
        db.query(Plan)
        .filter(Plan.conversation_id == conversation_id)
        .order_by(Plan.created_at.desc())
        .all()
    )
    return [
        PlanResponse(
            id=p.id,
            conversation_id=p.conversation_id,
            requirement_id=p.requirement_id,
            description=p.description,
            rendering_urls=p.rendering_urls,
            status=p.status,
            created_at=p.created_at,
        )
        for p in plans
    ]


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: str, db: Session = Depends(get_db)):
    """获取方案详情"""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="方案不存在")
    return PlanResponse(
        id=plan.id,
        conversation_id=plan.conversation_id,
        requirement_id=plan.requirement_id,
        description=plan.description,
        floor_plan_data=plan.floor_plan_data,
        rendering_urls=plan.rendering_urls,
        ai_suggestions=plan.ai_suggestions,
        status=plan.status,
        created_at=plan.created_at,
    )
