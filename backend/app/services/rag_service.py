"""RAG 知识库服务 — 基于 ChromaDB 的建筑规范检索"""
import os
import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)

# 知识库文档目录
KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"
# ChromaDB 持久化目录
CHROMA_DIR = Path(__file__).parent.parent.parent / "chroma_db"


class RAGService:
    """建筑规范知识库检索服务"""

    def __init__(self):
        """初始化 ChromaDB 客户端和集合"""
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name="building_standards",
            metadata={"description": "中国农村自建房建筑规范"},
        )
        # 启动时检查是否需要索引
        if self.collection.count() == 0:
            logger.info("知识库为空，开始建立索引...")
            self._index_documents()
        else:
            logger.info(f"知识库已有 {self.collection.count()} 条文档片段")

    def _index_documents(self):
        """读取知识库目录下的 Markdown 文档，分段后写入 ChromaDB"""
        if not KB_DIR.exists():
            logger.warning(f"知识库目录不存在: {KB_DIR}")
            return

        doc_count = 0
        for filepath in KB_DIR.glob("*.md"):
            logger.info(f"正在索引: {filepath.name}")
            text = filepath.read_text(encoding="utf-8")
            chunks = self._split_by_sections(text, filepath.name)

            if chunks:
                ids = [f"{filepath.stem}_{i}" for i in range(len(chunks))]
                documents = [c["text"] for c in chunks]
                metadatas = [{"source": c["source"], "section": c["section"]} for c in chunks]

                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                )
                doc_count += len(chunks)
                logger.info(f"  已索引 {len(chunks)} 个片段")

        logger.info(f"知识库索引完成，共 {doc_count} 个文档片段")

    def _split_by_sections(self, text: str, filename: str) -> list[dict]:
        """
        按 Markdown 二级标题（##）分段。
        每个片段包含标题和内容，保留上下文。
        """
        chunks = []
        current_section = ""
        current_content = []

        for line in text.split("\n"):
            if line.startswith("## "):
                # 保存上一个段落
                if current_content:
                    content = "\n".join(current_content).strip()
                    if len(content) > 50:  # 忽略太短的片段
                        chunks.append({
                            "text": content,
                            "source": filename,
                            "section": current_section,
                        })
                current_section = line.lstrip("# ").strip()
                current_content = [line]
            elif line.startswith("### "):
                # 三级标题也作为分段点，但保留在当前段落中
                if current_content and len("\n".join(current_content)) > 200:
                    content = "\n".join(current_content).strip()
                    chunks.append({
                        "text": content,
                        "source": filename,
                        "section": current_section,
                    })
                    current_content = [f"## {current_section}", line]
                else:
                    current_content.append(line)
            else:
                current_content.append(line)

        # 保存最后一个段落
        if current_content:
            content = "\n".join(current_content).strip()
            if len(content) > 50:
                chunks.append({
                    "text": content,
                    "source": filename,
                    "section": current_section,
                })

        return chunks

    def search(self, query: str, n_results: int = 3) -> list[dict]:
        """
        根据用户问题检索相关建筑规范。

        Args:
            query: 用户的问题或需求描述
            n_results: 返回结果数量

        Returns:
            [{"text": "...", "source": "...", "section": "...", "distance": 0.x}]
        """
        if self.collection.count() == 0:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, self.collection.count()),
            )

            docs = []
            for i in range(len(results["documents"][0])):
                docs.append({
                    "text": results["documents"][0][i],
                    "source": results["metadatas"][0][i].get("source", ""),
                    "section": results["metadatas"][0][i].get("section", ""),
                    "distance": results["distances"][0][i] if results.get("distances") else 0,
                })

            return docs
        except Exception as e:
            logger.error(f"知识库检索失败: {e}")
            return []

    def get_context_for_requirement(self, requirement: dict) -> str:
        """
        根据结构化需求，自动生成检索查询并返回相关规范文本。
        用于注入 AI 对话的上下文。

        Args:
            requirement: 结构化需求字典

        Returns:
            相关建筑规范的文本摘要
        """
        queries = []

        # 根据需求生成检索关键词
        if requirement.get("land_area"):
            queries.append(f"宅基地面积 {requirement['land_area']} 平米 用地规划")

        if requirement.get("floors"):
            queries.append(f"{requirement['floors']} 层别墅 建筑高度 结构要求")

        if requirement.get("bedrooms") or requirement.get("total_rooms"):
            queries.append("房间面积标准 卧室 客厅 卫生间 最小面积")

        if requirement.get("has_elderly_room"):
            queries.append("老人房 无障碍设计 一楼卧室")

        if requirement.get("has_garage"):
            queries.append("车库设计 停车位 尺寸标准")

        if requirement.get("style"):
            queries.append(f"{requirement['style']}风格 别墅设计 户型建议")

        if not queries:
            queries = ["农村自建房 基本建筑规范"]

        # 执行检索并去重
        all_results = []
        seen_sections = set()
        for q in queries[:3]:  # 最多3个查询
            results = self.search(q, n_results=2)
            for r in results:
                if r["section"] not in seen_sections:
                    seen_sections.add(r["section"])
                    all_results.append(r)

        if not all_results:
            return ""

        # 组装上下文文本
        context_parts = ["以下是相关的建筑规范参考：\n"]
        for r in all_results[:5]:  # 最多5个片段
            context_parts.append(f"---\n【{r['section']}】\n{r['text']}\n")

        return "\n".join(context_parts)


# 创建全局 RAG 服务实例
rag_service = RAGService()
