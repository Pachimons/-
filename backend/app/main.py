"""FastAPI 主入口 — AI 别墅设计助手后端"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import chat, plan, upload, knowledge

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="AI 别墅设计助手",
    description="通过 AI 对话帮助用户设计梦想别墅",
    version="0.1.0",
)

# 配置跨域（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)
app.include_router(plan.router)
app.include_router(upload.router)
app.include_router(knowledge.router)


@app.on_event("startup")
def startup():
    """应用启动时初始化数据库和上传目录"""
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")

    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"上传目录: {os.path.abspath(settings.UPLOAD_DIR)}")

    # 检查 API Key 配置
    if not settings.AI_API_KEY:
        logger.warning("⚠️  未配置 AI_API_KEY，AI 对话将使用模拟模式")
    else:
        logger.info(f"✅ AI 对话已配置: model={settings.AI_MODEL}")

    if not settings.IMAGE_API_KEY or settings.IMAGE_API_KEY == "your_bltcy_api_key_here":
        logger.warning("⚠️  未配置 IMAGE_API_KEY，图像生成功能将不可用")
    else:
        logger.info("✅ 图像生成 API Key 已配置")

    # 初始化 RAG 知识库（导入时自动建立索引）
    from app.services.rag_service import rag_service
    logger.info(f"✅ 知识库已加载，共 {rag_service.collection.count()} 个文档片段")


@app.get("/api/health")
def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "ai_available": bool(settings.AI_API_KEY),
        "image_available": bool(settings.IMAGE_API_KEY),
    }
