"""
VectorDB 封装 (ChromaDB)
负责文档 Embedding 存储和语义检索
"""
import uuid
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from ..core.config import settings


class VectorStore:
    """
    ChromaDB 向量存储封装

    两个 Collection:
    - knowledge_chunks: 笔记文档块
    - question_embeddings: 题目向量（可选）
    """

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.knowledge_collection = self.client.get_or_create_collection(
            name="knowledge_chunks",
            metadata={"description": "笔记文档块的 Embedding 存储"},
        )

    # ========== 写入 ==========

    async def add_chunks(
        self,
        chunks: list[dict],
        embeddings: list[list[float]],
        note_id: str = "",
        note_title: str = "",
    ) -> list[str]:
        """
        批量添加文档块

        chunks: [{"content": "...", "chunk_index": 0, "section_path": "H1 > H2"}, ...]
        embeddings: [[0.1, 0.2, ...], ...]
        """
        if not chunks:
            return []

        ids = [f"chunk_{uuid.uuid4().hex[:12]}" for _ in chunks]
        documents = [c["content"] for c in chunks]
        metadatas = [
            {
                "note_id": note_id,
                "title": note_title,
                "section_path": c.get("section_path", ""),
                "chunk_index": c.get("chunk_index", i),
                "token_count": c.get("token_count", 0),
            }
            for i, c in enumerate(chunks)
        ]

        self.knowledge_collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return ids

    # ========== 检索 ==========

    async def search(
        self,
        query: str,
        top_k: int = None,
        query_embedding: list[float] = None,
    ) -> list[dict]:
        """
        语义检索

        query: 查询文本
        top_k: 返回结果数
        query_embedding: 可选，提供查询的 Embedding（避免重复生成）

        返回: [{"id": "chunk_xxx", "content": "...", "title": "...", "score": 0.92}, ...]
        """
        top_k = top_k or settings.retrieval_top_k

        if query_embedding:
            results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )
        else:
            results = self.knowledge_collection.query(
                query_texts=[query],
                n_results=top_k,
            )

        # 格式化结果
        formatted = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                formatted.append({
                    "id": chunk_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "title": metadata.get("title", ""),
                    "section_path": metadata.get("section_path", ""),
                    "score": results["distances"][0][i] if results["distances"] else 0.0,
                })

        return formatted

    async def delete_by_note(self, note_id: str):
        """删除某篇笔记的所有文档块"""
        results = self.knowledge_collection.get(
            where={"note_id": note_id}
        )
        if results["ids"]:
            self.knowledge_collection.delete(ids=results["ids"])

    # ========== 统计 ==========

    def collection_stats(self) -> dict:
        """获取 Collection 统计信息"""
        count = self.knowledge_collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.knowledge_collection.name,
        }


# 全局单例
vector_store = VectorStore()
