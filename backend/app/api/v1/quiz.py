"""
出题相关 API 路由
"""
import json
import uuid
from fastapi import APIRouter, HTTPException
from ...core.orchestrator import orchestrator
from ...db.session import db_manager
from ...db.models import Quiz, QuizAttempt, ErrorLog
from ...utils.schemas import (
    QuizGenerateRequest,
    GradeRequest,
    ErrorResolveRequest,
)

router = APIRouter(prefix="/quiz", tags=["出题"])


@router.post("/generate")
async def generate_quiz(request: QuizGenerateRequest):
    """
    生成题目 + 自动入库
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
    quiz_id = f"quiz_{uuid.uuid4().hex[:12]}"
    quiz_data["quiz_id"] = quiz_id

    # 存入数据库
    try:
        session = db_manager.get_session()
        quiz_record = Quiz(
            id=quiz_id,
            user_id="default",
            topic=request.topic,
            difficulty=request.difficulty,
            questions_json=json.dumps(quiz_data.get("questions", []), ensure_ascii=False),
            source_note_ids=json.dumps([], ensure_ascii=False),
            generated_by=result.metadata.get("model", ""),
        )
        session.add(quiz_record)
        session.commit()
        session.close()
    except Exception as e:
        print(f"[WARN] Quiz 入库失败: {e}")

    return {
        "success": True,
        "data": quiz_data,
        "metadata": result.metadata,
    }


@router.post("/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, request: GradeRequest):
    """
    提交答案 → 自动批改 + 错题入库
    """
    agent = orchestrator.get_agent("grading_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Grading Agent 未注册")

    # 从数据库读取题目（用于批改参考）
    session = db_manager.get_session()
    try:
        quiz = session.query(Quiz).filter(Quiz.id == quiz_id).first()
        questions = json.loads(quiz.questions_json) if quiz else []
    finally:
        session.close()

    answers_list = [{"question_id": a.question_id, "answer": a.answer} for a in request.answers]

    result = await agent.execute(
        context=orchestrator._context,
        quiz_data={"quiz_id": quiz_id, "questions": questions},
        user_answers=answers_list,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    grade_data = result.data
    grade_id = f"grade_{uuid.uuid4().hex[:12]}"
    grade_data["grade_id"] = grade_id

    # 存入做题记录 + 错题记录
    try:
        session = db_manager.get_session()

        # 做题记录
        attempt = QuizAttempt(
            id=f"attempt_{uuid.uuid4().hex[:12]}",
            user_id="default",
            quiz_id=quiz_id,
            answers_json=json.dumps(answers_list, ensure_ascii=False),
            score=grade_data.get("total_score", 0),
            graded_by="grading_agent",
            grading_json=json.dumps(grade_data, ensure_ascii=False),
        )
        session.add(attempt)

        # 错题入库
        results = grade_data.get("results", [])
        for r in results:
            if not r.get("is_correct", True):
                error = ErrorLog(
                    id=f"error_{uuid.uuid4().hex[:12]}",
                    user_id="default",
                    question_id=r.get("question_id", ""),
                    quiz_id=quiz_id,
                    attempt_id=attempt.id,
                    user_answer=r.get("user_answer", ""),
                    correct_answer=r.get("correct_answer", ""),
                    error_type=r.get("error_type", ""),
                    knowledge_point=r.get("knowledge_point", ""),
                )
                session.add(error)

        session.commit()
        session.close()
    except Exception as e:
        print(f"[WARN] 做题记录入库失败: {e}")

    return {
        "success": True,
        "data": grade_data,
        "metadata": result.metadata,
    }


@router.get("/history")
async def quiz_history(user_id: str = "default", limit: int = 20):
    """
    做题历史
    """
    session = db_manager.get_session()
    try:
        quizzes = (
            session.query(Quiz)
            .filter(Quiz.user_id == user_id)
            .order_by(Quiz.created_at.desc())
            .limit(limit)
            .all()
        )
        return {
            "success": True,
            "data": [
                {
                    "id": q.id,
                    "topic": q.topic,
                    "difficulty": q.difficulty,
                    "created_at": q.created_at.isoformat() if q.created_at else None,
                    "question_count": len(json.loads(q.questions_json)) if q.questions_json else 0,
                }
                for q in quizzes
            ],
            "pagination": {"limit": limit, "total": len(quizzes)},
        }
    finally:
        session.close()


@router.get("/{quiz_id}")
async def get_quiz(quiz_id: str):
    """
    获取单套题目（不含答案，用于前端展示）
    """
    session = db_manager.get_session()
    try:
        quiz = session.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail=f"题目 {quiz_id} 不存在")

        questions = json.loads(quiz.questions_json) if quiz.questions_json else []
        # 移除答案（前端做题时不显示）
        for q in questions:
            q.pop("answer", None)
            q.pop("explanation", None)

        return {
            "success": True,
            "data": {
                "quiz_id": quiz.id,
                "topic": quiz.topic,
                "difficulty": quiz.difficulty,
                "questions": questions,
            },
        }
    finally:
        session.close()


# ========== 错题本 ==========

@router.get("/errors/list")
async def list_errors(
    user_id: str = "default",
    limit: int = 50,
    offset: int = 0,
    is_resolved: bool = None,
):
    """
    获取错题列表
    """
    session = db_manager.get_session()
    try:
        q = session.query(ErrorLog).filter(ErrorLog.user_id == user_id)

        if is_resolved is not None:
            q = q.filter(ErrorLog.is_resolved == is_resolved)

        total = q.count()
        resolved_count = session.query(ErrorLog).filter(
            ErrorLog.user_id == user_id,
            ErrorLog.is_resolved == True,
        ).count()

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
            "stats": {
                "total": total,
                "resolved": resolved_count,
                "unresolved": total - resolved_count,
            },
        }
    finally:
        session.close()


@router.put("/errors/{error_id}/resolve")
async def resolve_error(error_id: str, request: ErrorResolveRequest = None):
    """
    标记错题为已掌握/未掌握
    """
    session = db_manager.get_session()
    try:
        error = session.query(ErrorLog).filter(ErrorLog.id == error_id).first()
        if not error:
            raise HTTPException(status_code=404, detail=f"错题记录 {error_id} 不存在")

        error.is_resolved = request.is_resolved if request else True
        error.reviewed_count = (error.reviewed_count or 0) + 1
        session.commit()

        return {
            "success": True,
            "data": error.to_dict(),
        }
    finally:
        session.close()
