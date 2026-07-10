"""
RAG 知识检索 API 路由
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from ...core.orchestrator import orchestrator
from ...services.note_service import note_service
from ...services.file_service import file_service
from ...db.session import db_manager
from ...db.models import Note
from ...db.vector_store import vector_store
from ...utils.schemas import RAGAskRequest

router = APIRouter(prefix="/rag", tags=["知识检索"])


@router.post("/ask")
async def ask_knowledge(request: RAGAskRequest):
    """
    知识库问答
    """
    agent = orchestrator.get_agent("retrieval_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Retrieval Agent 未注册")

    result = await agent.execute(
        context=orchestrator._context,
        user_input=request.query,
        query=request.query,
        top_k=request.top_k,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "data": result.data,
        "metadata": result.metadata,
    }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
):
    """
    上传文档到知识库
    支持 .pdf / .md / .txt 文件
    完整链路: 解析 → Chunk → Embed → ChromaDB + SQLite
    """
    # 校验文件扩展名
    allowed = {".pdf", ".md", ".txt"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}（支持: {', '.join(sorted(allowed))}）",
        )

    # 读取文件内容
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件读取失败: {e}")

    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空")

    # 处理上传（解析 + 入库）
    try:
        result = await file_service.process_upload(
            file_content=content,
            filename=file.filename,
            title=title or None,
        )
        return {
            "success": True,
            "data": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {e}")


@router.get("/sources")
async def list_sources(
    user_id: str = "default",
    limit: int = 50,
    offset: int = 0,
):
    """
    知识库文档列表（上传的文档）
    """
    session = db_manager.get_session()
    try:
        query = session.query(Note).filter(
            Note.user_id == user_id,
            Note.source_type == "uploaded",
        )
        total = query.count()
        notes = (
            query.order_by(Note.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {
            "success": True,
            "data": [n.to_dict() for n in notes],
            "pagination": {"limit": limit, "offset": offset, "total": total},
        }
    finally:
        session.close()


@router.delete("/sources/{note_id}")
async def delete_source(note_id: str):
    """
    删除知识库文档（SQLite + ChromaDB 同步清除）
    """
    deleted = await note_service.delete_note(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"文档 {note_id} 不存在")
    return {
        "success": True,
        "data": {"deleted_id": note_id},
    }


@router.get("/stats")
async def get_stats():
    """
    知识库统计信息
    """
    # ChromaDB 统计
    chroma_stats = vector_store.collection_stats()

    # SQLite 统计
    session = db_manager.get_session()
    try:
        total_notes = session.query(Note).count()
        uploaded_notes = session.query(Note).filter(Note.source_type == "uploaded").count()
        generated_notes = session.query(Note).filter(Note.source_type == "generated").count()
    finally:
        session.close()

    return {
        "success": True,
        "data": {
            "total_notes": total_notes,
            "uploaded_notes": uploaded_notes,
            "generated_notes": generated_notes,
            "total_chunks": chroma_stats.get("total_chunks", 0),
            "collection_name": chroma_stats.get("collection_name", ""),
        },
    }


# ========== v0.4.1 知识库清空 ==========

@router.delete("/sources")
async def delete_sources_batch(
    note_ids: str = Query("", description="逗号分隔的文档 ID 列表，为空则清空全部上传文档"),
):
    """
    批量删除知识库文档。
    - 传 note_ids 参数：删除指定文档（逗号分隔）
    - 不传参数：清空所有上传类型的文档

    每条文档同步清除 SQLite + ChromaDB。
    """
    if note_ids:
        ids = [nid.strip() for nid in note_ids.split(",") if nid.strip()]
    else:
        # 查询所有上传文档
        session = db_manager.get_session()
        try:
            notes = (
                session.query(Note)
                .filter(Note.user_id == "default", Note.source_type == "uploaded")
                .all()
            )
            ids = [n.id for n in notes]
        finally:
            session.close()

    if not ids:
        return {
            "success": True,
            "data": {"deleted_count": 0, "deleted_ids": [], "message": "没有需要删除的文档"},
        }

    deleted_ids = []
    failed_ids = []
    for nid in ids:
        try:
            ok = await note_service.delete_note(nid)
            if ok:
                deleted_ids.append(nid)
            else:
                failed_ids.append(nid)
        except Exception as e:
            print(f"[WARN] 删除文档 {nid} 失败: {e}")
            failed_ids.append(nid)

    return {
        "success": True,
        "data": {
            "deleted_count": len(deleted_ids),
            "deleted_ids": deleted_ids,
            "failed_ids": failed_ids,
            "message": f"成功删除 {len(deleted_ids)} 篇文档" + (f"，{len(failed_ids)} 篇失败" if failed_ids else ""),
        },
    }


@router.delete("/chunks/orphans")
async def clean_orphan_chunks():
    """
    清除 ChromaDB 中的孤立向量块（对应 SQLite 中已删除的笔记）。
    """
    session = db_manager.get_session()
    try:
        existing_note_ids = set(
            row[0] for row in session.query(Note.id).all()
        )
    finally:
        session.close()

    # 获取 ChromaDB 中所有 chunk 的 note_id
    all_data = vector_store.knowledge_collection.get()
    if not all_data["ids"]:
        return {"success": True, "data": {"cleaned": 0, "message": "知识库为空，无需清理"}}

    orphan_ids = []
    for i, chunk_id in enumerate(all_data["ids"]):
        metadata = all_data["metadatas"][i] if all_data["metadatas"] else {}
        note_id = metadata.get("note_id", "")
        if note_id and note_id not in existing_note_ids:
            orphan_ids.append(chunk_id)

    if orphan_ids:
        vector_store.knowledge_collection.delete(ids=orphan_ids)
        print(f"[OK] 清除 {len(orphan_ids)} 个孤立向量块")

    return {
        "success": True,
        "data": {
            "cleaned": len(orphan_ids),
            "message": f"已清除 {len(orphan_ids)} 个孤立向量块" if orphan_ids else "没有发现孤立向量块",
        },
    }


@router.delete("/clear-all")
async def clear_all_knowledge(
    confirm: str = Query("", description="安全确认，必须传 'CONFIRM' 才执行"),
):
    """
    清空整个知识库（所有笔记 + 所有 ChromaDB 向量块）。
    需要传 confirm=CONFIRM 作为安全确认。
    危险操作，不可撤销。
    """
    if confirm != "CONFIRM":
        raise HTTPException(
            status_code=400,
            detail="清空知识库是危险操作，请传 confirm=CONFIRM 确认。例如: /rag/clear-all?confirm=CONFIRM",
        )

    # 1. 删除所有笔记（SQLite）
    session = db_manager.get_session()
    try:
        all_notes = session.query(Note).all()
        note_count = len(all_notes)
        for note in all_notes:
            session.delete(note)
        session.commit()
        print(f"[OK] SQLite: 删除 {note_count} 篇笔记")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"SQLite 清除失败: {e}")
    finally:
        session.close()

    # 2. 清空 ChromaDB
    try:
        chunk_count = await vector_store.delete_all()
        print(f"[OK] ChromaDB: 删除 {chunk_count} 个向量块")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ChromaDB 清除失败: {e}")

    return {
        "success": True,
        "data": {
            "deleted_notes": note_count,
            "deleted_chunks": chunk_count,
            "message": f"知识库已清空（{note_count} 篇笔记，{chunk_count} 个向量块）",
        },
    }
