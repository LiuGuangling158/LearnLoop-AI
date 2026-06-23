"""
学习规划 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ...core.orchestrator import orchestrator

router = APIRouter(prefix="/schedule", tags=["学习规划"])


class ReviewRequest(BaseModel):
    knowledge_point: str
    score: int = Field(..., ge=0, le=5, description="自评分数 0-5")


@router.get("/daily")
async def daily_tasks(user_id: str = "default"):
    """
    获取今日学习任务
    """
    agent = orchestrator.get_agent("scheduler_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Scheduler Agent 未注册")

    # TODO: 从数据库读取 sm2_states 和 error_logs
    result = await agent.execute(
        context=orchestrator._context,
        action="daily",
        sm2_states=[],
        error_logs=[],
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "data": result.data,
    }


@router.post("/review")
async def record_review(request: ReviewRequest):
    """
    记录复习评分，更新 SM-2 状态
    """
    agent = orchestrator.get_agent("scheduler_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Scheduler Agent 未注册")

    # TODO: 从数据库获取当前 SM-2 状态
    result = await agent.execute(
        context=orchestrator._context,
        action="review",
        review_score=request.score,
        ef=2.5,
        interval=1,
        repetitions=0,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "data": result.data,
    }


@router.get("/stats")
async def learning_stats(user_id: str = "default"):
    """
    学习统计
    """
    return {
        "success": True,
        "data": {
            "streak_days": 0,
            "total_quizzes": 0,
            "total_errors": 0,
            "mastery_rate": 0.0,
        },
    }
