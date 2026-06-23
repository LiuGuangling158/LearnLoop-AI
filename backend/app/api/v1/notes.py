"""
笔记相关 API 路由
"""
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ...core.orchestrator import orchestrator
from ...agents.note_agent import NoteAgent
from ...utils.schemas import NoteGenerateRequest, NoteResponse

router = APIRouter(prefix="/notes", tags=["笔记"])


@router.post("/generate")
async def generate_note(request: NoteGenerateRequest):
    """
    生成结构化笔记
    支持流式 SSE 或非流式返回
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
    note_data["id"] = f"note_{uuid.uuid4().hex[:12]}"

    return {
        "success": True,
        "data": note_data,
        "metadata": result.metadata,
    }


@router.get("")
async def list_notes(user_id: str = "default", limit: int = 20, offset: int = 0):
    """
    获取笔记列表（TODO: 从 SQL 数据库读取）
    """
    # MVP 阶段返回空列表，后续接入数据库
    return {
        "success": True,
        "data": [],
        "pagination": {"limit": limit, "offset": offset, "total": 0},
    }


@router.get("/{note_id}")
async def get_note(note_id: str):
    """
    获取单篇笔记（TODO: 从数据库读取）
    """
    raise HTTPException(status_code=404, detail=f"笔记 {note_id} 暂未实现数据库查询")
