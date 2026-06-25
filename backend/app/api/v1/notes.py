"""
笔记相关 API 路由
"""
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ...core.orchestrator import orchestrator
from ...agents.note_agent import NoteAgent
from ...services.note_service import note_service
from ...utils.schemas import NoteGenerateRequest, NoteResponse

router = APIRouter(prefix="/notes", tags=["笔记"])


@router.post("/generate")
async def generate_note(request: NoteGenerateRequest):
    """
    生成结构化笔记 + 自动入库（SQLite + ChromaDB）
    """
    agent = orchestrator.get_agent("note_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Note Agent 未注册")

    result = await agent.execute(
        context=orchestrator._context,
        user_input=request.topic,
        topic=request.topic,
        source_text=request.source_text,
        style=request.style,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    note_data = result.data

    # --- 持久化入库 ---
    try:
        saved_note = await note_service.save_note(
            title=note_data.get("title", request.topic),
            content_md=note_data.get("content_md", ""),
            summary=note_data.get("summary", ""),
            tags=note_data.get("tags", []),
            user_id="default",  # TODO: v1.0 接入用户认证
            source_type="generated",
            embed=True,
        )
        note_data["id"] = saved_note["id"]
        note_data["_persisted"] = True
    except Exception as e:
        # 优雅降级：持久化失败仍返回笔记内容
        print(f"[ERROR] 笔记入库失败: {e}")
        note_data["id"] = f"note_{uuid.uuid4().hex[:12]}"
        note_data["_save_error"] = str(e)
    # ---

    return {
        "success": True,
        "data": note_data,
        "metadata": result.metadata,
    }


@router.get("")
async def list_notes(user_id: str = "default", limit: int = 20, offset: int = 0):
    """
    获取笔记列表（分页）
    """
    notes, total = note_service.list_notes(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return {
        "success": True,
        "data": notes,
        "pagination": {"limit": limit, "offset": offset, "total": total},
    }


@router.get("/{note_id}")
async def get_note(note_id: str):
    """
    获取单篇笔记详情
    """
    note = note_service.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"笔记 {note_id} 不存在")
    return {
        "success": True,
        "data": note,
    }


@router.delete("/{note_id}")
async def delete_note(note_id: str):
    """
    删除笔记（SQLite + ChromaDB 同步清除）
    """
    deleted = note_service.delete_note(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"笔记 {note_id} 不存在或删除失败")
    return {
        "success": True,
        "data": {"deleted_id": note_id},
    }
