"""文件上传路由 — 处理图片上传"""
import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter(prefix="/api/upload", tags=["上传"])

# 允许的图片类型
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
# 最大文件大小 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片文件。
    返回本地可访问的图片 URL。
    """
    # 验证文件类型
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}。支持: jpg, png, gif, webp",
        )

    # 读取文件内容
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

    # 生成唯一文件名
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"

    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    # 保存文件
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    # 返回可访问的 URL
    return {
        "url": f"/api/upload/files/{filename}",
        "filename": filename,
        "size": len(content),
        "content_type": file.content_type,
    }


@router.get("/files/{filename}")
async def get_file(filename: str):
    """获取已上传的文件"""
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath)
