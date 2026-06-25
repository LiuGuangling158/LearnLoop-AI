"""
Note Service: 笔记持久化服务层
编排完整写入链路: SQLite → Chunking → Embedding → ChromaDB
"""
import json
import uuid
from datetime import datetime
from typing import Optional

from ..db.session import db_manager
from ..db.models import Note
from ..db.vector_store import vector_store
from ..utils.chunking import split_markdown_by_headers
from ..llm.router import llm_router


class NoteService:
    """笔记持久化服务（全局单例）"""

    # ========== 写入 ==========

    async def save_note(
        self,
        title: str,
        content_md: str,
        summary: str = "",
        tags: list[str] = None,
        user_id: str = "default",
        source_type: str = "generated",
        embed: bool = True,
    ) -> dict:
        """
        完整写入链路：
        1. SQLite INSERT (notes 表)
        2. Markdown 分块（按标题层级）
        3. Embedding 向量化（多层 fallback）
        4. ChromaDB 写入（knowledge_chunks collection）

        返回: 保存后的 note dict（含 id）
        """
        note_id = f"note_{uuid.uuid4().hex[:12]}"
        tags_json = json.dumps(tags or [], ensure_ascii=False)
        word_count = len(content_md)

        session = db_manager.get_session()
        try:
            # Step 1: 写入 SQLite
            note = Note(
                id=note_id,
                user_id=user_id,
                title=title,
                content_md=content_md,
                summary=summary,
                tags=tags_json,
                source_type=source_type,
                word_count=word_count,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(note)
            session.commit()

            # Step 2: 分块
            chunks = split_markdown_by_headers(content_md)
            if not chunks:
                session.close()
                return note.to_dict()

            # Step 3: Embedding + Step 4: ChromaDB 写入
            embedding_id = ""
            if embed:
                try:
                    chunk_texts = [c["content"] for c in chunks]
                    embeddings = await llm_router.embed(chunk_texts)

                    chunk_ids = await vector_store.add_chunks(
                        chunks=chunks,
                        embeddings=embeddings,
                        note_id=note_id,
                        note_title=title,
                    )
                    embedding_id = ",".join(chunk_ids)
                except Exception as e:
                    print(f"[WARN] Embedding/ChromaDB 写入失败: {e}")
                    print(f"       笔记 '{title}' 已存入 SQLite，但未建立向量索引")

            # 更新 embedding_id
            if embedding_id:
                note.embedding_id = embedding_id
                session.commit()

            session.close()
            return note.to_dict()

        except Exception as e:
            session.rollback()
            session.close()
            raise RuntimeError(f"笔记保存失败: {e}")

    # ========== 查询 ==========

    def list_notes(
        self,
        user_id: str = "default",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """分页查询笔记列表"""
        session = db_manager.get_session()
        try:
            query = session.query(Note).filter(Note.user_id == user_id)
            total = query.count()
            notes = (
                query.order_by(Note.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [n.to_dict() for n in notes], total
        finally:
            session.close()

    def get_note(self, note_id: str) -> Optional[dict]:
        """获取单篇笔记"""
        session = db_manager.get_session()
        try:
            note = session.query(Note).filter(Note.id == note_id).first()
            if not note:
                return None
            return note.to_dict()
        finally:
            session.close()

    # ========== 删除 ==========

    def delete_note(self, note_id: str) -> bool:
        """删除笔记（SQLite + ChromaDB 同步清除）"""
        session = db_manager.get_session()
        try:
            note = session.query(Note).filter(Note.id == note_id).first()
            if not note:
                return False

            # 删除 ChromaDB 中的向量数据
            if note.embedding_id:
                try:
                    # 通过 note_id 过滤删除
                    import asyncio
                    asyncio.create_task(vector_store.delete_by_note(note_id))
                except Exception as e:
                    print(f"[WARN] ChromaDB 删除失败: {e}")

            session.delete(note)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()


# 全局单例
note_service = NoteService()
