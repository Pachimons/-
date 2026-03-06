"""应用配置 — 从 .env 文件加载所有配置项"""
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv(override=True)


class Settings:
    """全局配置类，集中管理所有配置项"""

    # AI 对话 API 配置（OpenAI 兼容接口）
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_API_BASE: str = os.getenv("AI_API_BASE", "https://api.bltcy.ai/v1")
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-3.1-pro-preview")

    # 图像生成 API 配置 (nano-banana-2)
    IMAGE_API_KEY: str = os.getenv("IMAGE_API_KEY", "")
    IMAGE_API_BASE: str = os.getenv("IMAGE_API_BASE", "https://api.bltcy.ai/v1")
    IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "nano-banana-2")

    # HTTP 代理（系统代理，httpx 需要显式传入）
    HTTP_PROXY: str = os.getenv("HTTP_PROXY", "")

    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./villa_ai.db")

    # 文件上传配置
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

    # CORS 允许的来源（开发模式允许所有来源）
    CORS_ORIGINS: list = ["*"]

    # 服务端口
    PORT: int = int(os.getenv("PORT", "8000"))


# 创建全局配置实例
settings = Settings()
