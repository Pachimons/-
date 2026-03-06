"""知识库路由 — 建筑规范检索 API"""
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


class SearchResult(BaseModel):
    text: str
    source: str
    section: str
    distance: float


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int


@router.get("/search", response_model=SearchResponse)
def search_knowledge(
    q: str = Query(..., description="搜索关键词"),
    n: int = Query(default=3, ge=1, le=10, description="返回结果数量"),
):
    """检索建筑规范知识库"""
    results = rag_service.search(q, n_results=n)
    return SearchResponse(
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


@router.get("/stats")
def knowledge_stats():
    """获取知识库统计信息"""
    return {
        "total_chunks": rag_service.collection.count(),
        "collection_name": rag_service.collection.name,
    }
