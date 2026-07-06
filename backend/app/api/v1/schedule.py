"""
学习规划 API 路由 (v0.4 — 接入真实 DB)
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from ...core.orchestrator import orchestrator
from ...services.sm2_service import sm2_service
from ...db.session import db_manager
from ...db.models import SM2State, ErrorLog, LearningPlan, QuizAttempt
from ...utils.schemas import ReviewRequest, PlanRequest

router = APIRouter(prefix="/schedule", tags=["学习规划"])


@router.get("/daily")
async def daily_tasks(user_id: str = "default"):
    """
    获取今日学习任务。
    从 DB 读取到期的 SM-2 状态 + 未解决的错题，传给 SchedulerAgent 生成任务。
    """
    agent = orchestrator.get_agent("scheduler_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Scheduler Agent 未注册")

    # 从 DB 读取真实数据
    try:
        due_items = sm2_service.get_due_items(user_id)
    except Exception as e:
        print(f"[WARN] 获取到期项失败: {e}")
        due_items = []

    # 获取未解决的错题（作为 error_logs 传给 Agent）
    session = db_manager.get_session()
    try:
        unresolved_errors = (
            session.query(ErrorLog)
            .filter(
                ErrorLog.user_id == user_id,
                ErrorLog.is_resolved == False,
            )
            .order_by(ErrorLog.created_at.desc())
            .limit(50)
            .all()
        )
        error_log_dicts = [e.to_dict() for e in unresolved_errors]
    finally:
        session.close()

    # 调用 SchedulerAgent 生成每日任务
    result = await agent.execute(
        context=orchestrator._context,
        action="daily",
        sm2_states=due_items,
        error_logs=error_log_dicts,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "data": result.data,
        "metadata": {
            "due_items_count": len(due_items),
            "unresolved_errors": len(error_log_dicts),
        },
    }


@router.post("/review")
async def record_review(request: ReviewRequest):
    """
    记录复习评分，应用 SM-2 算法更新下次复习日期。
    score: 0-5（0=完全忘记, 3=勉强记住, 4=正确回忆, 5=非常轻松）
    """
    try:
        result = sm2_service.update_review(
            knowledge_point=request.knowledge_point,
            score=request.score,
            user_id=request.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "success": True,
        "data": result,
        "message": (
            f"知识点 '{request.knowledge_point}' 评分 {request.score} → "
            f"下次复习: {result.get('next_review_at', '未知')} "
            f"(间隔 {result.get('interval_days', 1)} 天, EF={result.get('ef', 2.5)})"
        ),
    }


@router.get("/stats")
async def learning_stats(user_id: str = "default"):
    """
    学习统计（仪表盘数据源）。
    从 SM-2 状态 + 错题记录 + 做题记录聚合统计。
    """
    try:
        stats = sm2_service.get_stats(user_id)
    except Exception as e:
        print(f"[WARN] 获取统计失败: {e}")
        stats = {
            "total_kps": 0, "due_count": 0, "overdue_count": 0,
            "avg_ef": 2.5, "streak_days": 0,
            "total_quizzes": 0, "total_errors": 0,
            "resolved_errors": 0, "unresolved_errors": 0, "mastery_rate": 0.0,
        }

    # 补充做题正确率
    session = db_manager.get_session()
    try:
        attempts = (
            session.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id)
            .all()
        )
        total_attempts = len(attempts)
        avg_score = round(sum(a.score for a in attempts) / total_attempts, 1) if total_attempts > 0 else 0.0
    finally:
        session.close()

    return {
        "success": True,
        "data": {
            **stats,
            "avg_score": avg_score,
        },
    }


@router.post("/plan")
async def create_plan(request: PlanRequest, user_id: str = "default"):
    """
    创建学习计划。
    """
    import uuid

    session = db_manager.get_session()
    try:
        plan = LearningPlan(
            id=f"plan_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            topic=request.topic,
            goal_description=request.goal_description,
            target_date=datetime.strptime(request.target_date, "%Y-%m-%d") if request.target_date else None,
            status="active",
        )
        session.add(plan)
        session.commit()

        return {
            "success": True,
            "data": {
                "id": plan.id,
                "topic": plan.topic,
                "goal_description": plan.goal_description,
                "target_date": request.target_date,
                "status": plan.status,
                "created_at": plan.created_at.isoformat() if plan.created_at else None,
            },
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建学习计划失败: {e}")
    finally:
        session.close()


@router.get("/plans")
async def list_plans(user_id: str = "default"):
    """
    获取学习计划列表。
    """
    session = db_manager.get_session()
    try:
        plans = (
            session.query(LearningPlan)
            .filter(LearningPlan.user_id == user_id)
            .order_by(LearningPlan.created_at.desc())
            .all()
        )
        return {
            "success": True,
            "data": [
                {
                    "id": p.id,
                    "topic": p.topic,
                    "goal_description": p.goal_description,
                    "target_date": p.target_date.isoformat() if p.target_date else None,
                    "status": p.status,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in plans
            ],
        }
    finally:
        session.close()


@router.get("/states")
async def list_sm2_states(user_id: str = "default"):
    """
    获取所有 SM-2 状态（复习计划页面数据源）。
    """
    try:
        states = sm2_service.get_all_states(user_id)
    except Exception as e:
        print(f"[WARN] 获取 SM-2 状态失败: {e}")
        states = []

    return {
        "success": True,
        "data": states,
        "total": len(states),
    }
