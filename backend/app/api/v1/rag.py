"""
RAG 知识检索 API 路由
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
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
    import asyncio

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
