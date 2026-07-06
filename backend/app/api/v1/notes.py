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

        # --- v0.4: 自动创建 SM-2 状态 ---
        try:
            from ...services.sm2_service import sm2_service

            # 收集知识点：标签 + 标题
            knowledge_points = list(note_data.get("tags", []))
            title = note_data.get("title", "")
            if title and title not in knowledge_points:
                knowledge_points.append(title)

            for kp in knowledge_points:
                if kp:
                    try:
                        sm2_service.get_or_create_state(kp, "default")
                    except Exception as e:
                        print(f"[WARN] SM-2 状态创建失败 ({kp}): {e}")

            if knowledge_points:
                print(f"[OK] 为 {len(knowledge_points)} 个知识点初始化 SM-2 状态")
        except Exception as e:
            print(f"[WARN] SM-2 批量创建失败: {e}")
        # ---

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
    deleted = await note_service.delete_note(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"笔记 {note_id} 不存在或删除失败")
    return {
        "success": True,
        "data": {"deleted_id": note_id},
    }


@router.get("/search")
async def search_notes(
    query: str = "",
    source_type: str = None,
    user_id: str = "default",
    limit: int = 20,
    offset: int = 0,
):
    """
    搜索笔记（标题/内容模糊匹配 + 来源类型过滤）
    """
    notes, total = note_service.search_notes(
        query=query,
        source_type=source_type,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return {
        "success": True,
        "data": notes,
        "pagination": {"limit": limit, "offset": offset, "total": total},
    }
