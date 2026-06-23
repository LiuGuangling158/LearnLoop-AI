"""
出题相关 API 路由
"""
import uuid
from fastapi import APIRouter, HTTPException
from ...core.orchestrator import orchestrator
from ...utils.schemas import QuizGenerateRequest, GradeRequest

router = APIRouter(prefix="/quiz", tags=["出题"])


@router.post("/generate")
async def generate_quiz(request: QuizGenerateRequest):
    """
    生成题目
    """
    agent = orchestrator.get_agent("quiz_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Quiz Agent 未注册")

    result = await agent.execute(
        context=orchestrator._context,
        user_input=request.topic,
        topic=request.topic,
        types=request.types,
        difficulty=request.difficulty,
        count=request.count,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    quiz_data = result.data
    quiz_data["quiz_id"] = f"quiz_{uuid.uuid4().hex[:12]}"

    # TODO: 存入数据库

    return {
        "success": True,
        "data": quiz_data,
        "metadata": result.metadata,
    }


@router.post("/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, request: GradeRequest):
    """
    提交答案 → 自动批改
    这是个简化的 Pipeline：Quiz → Grade
    """
    # Step 1: 获取题目数据（TODO: 从数据库读取）
    # MVP 阶段需要前端同时传题目数据 + 用户答案
    # 暂时直接调 Grading Agent

    agent = orchestrator.get_agent("grading_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Grading Agent 未注册")

    # 把 request.answers 转为 grading agent 需要的格式
    answers_list = [{"question_id": a.question_id, "answer": a.answer} for a in request.answers]

    result = await agent.execute(
        context=orchestrator._context,
        quiz_data={"quiz_id": quiz_id, "questions": []},  # TODO: 从 DB 读取题目
        user_answers=answers_list,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    grade_data = result.data
    grade_data["grade_id"] = f"grade_{uuid.uuid4().hex[:12]}"

    return {
        "success": True,
        "data": grade_data,
        "metadata": result.metadata,
    }


@router.get("/history")
async def quiz_history(user_id: str = "default", limit: int = 20):
    """
    做题历史（TODO: 从数据库读取）
    """
    return {
        "success": True,
        "data": [],
        "pagination": {"limit": limit, "total": 0},
    }
