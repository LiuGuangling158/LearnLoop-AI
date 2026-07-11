"""
记忆相关 API 路由 (v0.4)
薄弱点分析、易混概念对、学习报告
"""
from fastapi import APIRouter, HTTPException
from ...core.orchestrator import orchestrator
from ...services.sm2_service import sm2_service
from ...db.session import db_manager
from ...db.models import ErrorLog

router = APIRouter(prefix="/memory", tags=["记忆管理"])


@router.get("/weak-points")
async def weak_points(user_id: str = "default"):
    """
    薄弱知识点分析。
    从 error_log 聚合统计 + LLM 分析。
    """
    session = db_manager.get_session()
    try:
        # 按知识点聚合统计
        errors = (
            session.query(ErrorLog)
            .filter(
                ErrorLog.user_id == user_id,
                ErrorLog.is_resolved == False,
            )
            .all()
        )

        if not errors:
            return {
                "success": True,
                "data": {
                    "weak_points": [],
                    "by_knowledge_point": {},
                    "by_type": {},
                    "total_unresolved": 0,
                    "message": "暂无薄弱点，继续加油！🎉",
                },
            }

        # 按知识点分组
        by_kp = {}
        by_type = {}
        for e in errors:
            kp = e.knowledge_point or "未分类"
            et = e.error_type or "未知"

            if kp not in by_kp:
                by_kp[kp] = {"count": 0, "examples": []}
            by_kp[kp]["count"] += 1
            if len(by_kp[kp]["examples"]) < 3:
                by_kp[kp]["examples"].append({
                    "user_answer": e.user_answer,
                    "correct_answer": e.correct_answer,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                })

            if et not in by_type:
                by_type[et] = 0
            by_type[et] += 1

        # 按错误次数排序
        sorted_kps = sorted(by_kp.items(), key=lambda x: x[1]["count"], reverse=True)
        weak_points = [
            {"knowledge_point": kp, "error_count": info["count"], "examples": info["examples"]}
            for kp, info in sorted_kps
        ]

        # 尝试用 LLM 分析（可选，失败不影响返回基础数据）
        improvement_suggestions = []
        try:
            agent = orchestrator.get_agent("memory_agent")
            if agent:
                error_dicts = [e.to_dict() for e in errors[:20]]  # 最多 20 条给 LLM
                llm_result = await agent.execute(
                    context=orchestrator._context,
                    action="analyze",
                    error_logs=error_dicts,
                )
                if llm_result.success and isinstance(llm_result.data, dict):
                    improvement_suggestions = llm_result.data.get("improvement_suggestions", [])
                    # 兼容旧版 LLM 返回 improvement_plan 字段
                    if not improvement_suggestions:
                        plan = llm_result.data.get("improvement_plan", "")
                        if plan:
                            improvement_suggestions = [plan] if isinstance(plan, str) else plan
                    if isinstance(improvement_suggestions, str):
                        improvement_suggestions = [improvement_suggestions]
        except Exception as e:
            print(f"[WARN] LLM 薄弱点分析失败: {e}")

        return {
            "success": True,
            "data": {
                "weak_points": weak_points,
                "by_knowledge_point": {kp: info["count"] for kp, info in sorted_kps},
                "by_type": by_type,
                "total_unresolved": len(errors),
                "improvement_suggestions": improvement_suggestions,
            },
        }
    finally:
        session.close()


@router.get("/confusions")
async def confusion_pairs(user_id: str = "default"):
    """
    获取易混概念对列表。
    """
    try:
        pairs = sm2_service.get_confusion_pairs(user_id)
    except Exception as e:
        print(f"[WARN] 获取混淆对失败: {e}")
        pairs = []

    return {
        "success": True,
        "data": pairs,
        "total": len(pairs),
    }


@router.get("/error-log")
async def error_log_list(
    user_id: str = "default",
    limit: int = 50,
    offset: int = 0,
    is_resolved: bool = None,
):
    """
    获取错题记录（分页 + 过滤）。
    与 quiz.py 的 /quiz/errors/list 互补，这里提供更丰富的过滤。
    """
    session = db_manager.get_session()
    try:
        q = session.query(ErrorLog).filter(ErrorLog.user_id == user_id)

        if is_resolved is not None:
            q = q.filter(ErrorLog.is_resolved == is_resolved)

        total = q.count()
        errors = (
            q.order_by(ErrorLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "success": True,
            "data": [e.to_dict() for e in errors],
            "pagination": {"limit": limit, "offset": offset, "total": total},
        }
    finally:
        session.close()


@router.get("/report")
async def learning_report(user_id: str = "default"):
    """
    综合学习报告（LLM 生成）。
    整合 SM-2 统计 + 错题数据 + 混淆对，由 Memory Agent 生成报告。
    """
    agent = orchestrator.get_agent("memory_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Memory Agent 未注册")

    # 收集数据
    session = db_manager.get_session()
    try:
        errors = (
            session.query(ErrorLog)
            .filter(ErrorLog.user_id == user_id)
            .order_by(ErrorLog.created_at.desc())
            .limit(30)
            .all()
        )
        error_dicts = [e.to_dict() for e in errors]
    finally:
        session.close()

    try:
        stats = sm2_service.get_stats(user_id)
        confusions = sm2_service.get_confusion_pairs(user_id)
    except Exception as e:
        print(f"[WARN] 获取统计数据失败: {e}")
        stats = {}
        confusions = []

    # 调用 Memory Agent 生成报告
    result = await agent.execute(
        context=orchestrator._context,
        action="report",
        error_logs=error_dicts,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "data": {
            **result.data,
            "stats": stats,
            "confusion_pairs": confusions,
        },
    }
