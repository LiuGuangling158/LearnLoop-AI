"""
SM-2 Service: 间隔重复状态管理服务
管理 SM2State / ConfusionPair 的 CRUD，编排 SM-2 算法计算和持久化

仿 note_service.py 的单例模式
"""
import uuid
from datetime import datetime, timedelta
from ..db.session import db_manager
from ..db.models import SM2State, ConfusionPair, ErrorLog
from ..agents.scheduler_agent import SM2Calculator


class SM2Service:
    """SM-2 状态管理服务（全局单例）"""

    # ========== SM-2 状态 ==========

    def get_or_create_state(
        self,
        knowledge_point: str,
        user_id: str = "default",
    ) -> dict:
        """
        获取或创建 SM-2 状态。
        如果 knowledge_point 不存在，创建初始状态（ef=2.5, interval=1, repetitions=0）。

        返回: dict with keys: id, knowledge_point, ef, interval_days, repetitions,
              next_review_at, last_score, created_at, updated_at, is_new
        """
        session = db_manager.get_session()
        try:
            existing = (
                session.query(SM2State)
                .filter(
                    SM2State.user_id == user_id,
                    SM2State.knowledge_point == knowledge_point,
                )
                .first()
            )

            if existing:
                return {
                    "id": existing.id,
                    "user_id": existing.user_id,
                    "knowledge_point": existing.knowledge_point,
                    "ef": existing.ef,
                    "interval_days": existing.interval_days,
                    "repetitions": existing.repetitions,
                    "next_review_at": existing.next_review_at.isoformat() if existing.next_review_at else None,
                    "last_score": existing.last_score,
                    "created_at": existing.created_at.isoformat() if existing.created_at else None,
                    "updated_at": existing.updated_at.isoformat() if existing.updated_at else None,
                    "is_new": False,
                }

            # 创建初始状态
            now = datetime.utcnow()
            state = SM2State(
                id=f"sm2_{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                knowledge_point=knowledge_point,
                ef=2.5,
                interval_days=1,
                repetitions=0,
                next_review_at=now,  # 初始状态当天就可以复习
                last_score=0,
            )
            session.add(state)
            session.commit()

            return {
                "id": state.id,
                "user_id": state.user_id,
                "knowledge_point": state.knowledge_point,
                "ef": state.ef,
                "interval_days": state.interval_days,
                "repetitions": state.repetitions,
                "next_review_at": state.next_review_at.isoformat() if state.next_review_at else None,
                "last_score": state.last_score,
                "created_at": state.created_at.isoformat() if state.created_at else None,
                "updated_at": state.updated_at.isoformat() if state.updated_at else None,
                "is_new": True,
            }
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"SM-2 状态操作失败: {e}")
        finally:
            session.close()

    def update_review(
        self,
        knowledge_point: str,
        score: int,
        user_id: str = "default",
    ) -> dict:
        """
        记录复习评分，应用 SM-2 算法计算新的复习间隔。

        score: 0-5 评分
        返回: 更新后的 SM-2 状态 dict
        """
        if not (0 <= score <= 5):
            raise ValueError(f"评分必须在 0-5 之间，收到: {score}")

        session = db_manager.get_session()
        try:
            state = (
                session.query(SM2State)
                .filter(
                    SM2State.user_id == user_id,
                    SM2State.knowledge_point == knowledge_point,
                )
                .first()
            )

            if not state:
                # 如果状态不存在，先创建再评分
                session.close()
                self.get_or_create_state(knowledge_point, user_id)
                session = db_manager.get_session()
                state = (
                    session.query(SM2State)
                    .filter(
                        SM2State.user_id == user_id,
                        SM2State.knowledge_point == knowledge_point,
                    )
                    .first()
                )
                if not state:
                    raise RuntimeError(f"无法创建 SM-2 状态: {knowledge_point}")

            # 应用 SM-2 算法
            calc = SM2Calculator()
            result = calc.calculate(
                ef=state.ef,
                interval=state.interval_days,
                repetitions=state.repetitions,
                score=score,
            )

            # 更新状态
            state.ef = result["ef"]
            state.interval_days = result["interval"]
            state.repetitions = result["repetitions"]
            state.next_review_at = datetime.strptime(result["next_review_date"], "%Y-%m-%d")
            state.last_score = score
            state.updated_at = datetime.utcnow()

            session.commit()

            return {
                "id": state.id,
                "user_id": state.user_id,
                "knowledge_point": state.knowledge_point,
                "ef": state.ef,
                "interval_days": state.interval_days,
                "repetitions": state.repetitions,
                "next_review_at": state.next_review_at.isoformat() if state.next_review_at else None,
                "last_score": state.last_score,
                "created_at": state.created_at.isoformat() if state.created_at else None,
                "updated_at": state.updated_at.isoformat() if state.updated_at else None,
                "sm2_result": result,
                "is_new": False,
            }
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"SM-2 复习更新失败: {e}")
        finally:
            session.close()

    def get_due_items(self, user_id: str = "default") -> list[dict]:
        """
        获取今日到期的待复习知识点。
        返回: SM-2 状态列表，按 overdue 天数 + error_count 排序
        """
        session = db_manager.get_session()
        try:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            due_states = (
                session.query(SM2State)
                .filter(
                    SM2State.user_id == user_id,
                    SM2State.next_review_at <= today,
                )
                .all()
            )

            # 为每个知识点聚合错误次数
            results = []
            for s in due_states:
                error_count = (
                    session.query(ErrorLog)
                    .filter(
                        ErrorLog.user_id == user_id,
                        ErrorLog.knowledge_point == s.knowledge_point,
                        ErrorLog.is_resolved == False,
                    )
                    .count()
                )

                # 计算逾期天数
                overdue_days = 0
                if s.next_review_at:
                    overdue_days = (today - s.next_review_at.replace(hour=0, minute=0, second=0, microsecond=0)).days

                results.append({
                    "id": s.id,
                    "knowledge_point": s.knowledge_point,
                    "ef": s.ef,
                    "interval_days": s.interval_days,
                    "repetitions": s.repetitions,
                    "next_review_at": s.next_review_at.isoformat() if s.next_review_at else None,
                    "last_score": s.last_score,
                    "error_count": error_count,
                    "overdue_days": max(0, overdue_days),
                    "priority": (
                        "high" if error_count > 3 or overdue_days > 2
                        else "medium" if error_count > 0 or overdue_days > 0
                        else "low"
                    ),
                })

            # 排序：高优先在前，然后按逾期天数降序
            priority_order = {"high": 0, "medium": 1, "low": 2}
            results.sort(key=lambda x: (priority_order.get(x["priority"], 2), -x["overdue_days"], -x["error_count"]))

            return results
        finally:
            session.close()

    def get_all_states(self, user_id: str = "default") -> list[dict]:
        """
        获取所有 SM-2 状态，按 next_review_at 排序。
        """
        session = db_manager.get_session()
        try:
            states = (
                session.query(SM2State)
                .filter(SM2State.user_id == user_id)
                .order_by(SM2State.next_review_at.asc())
                .all()
            )

            results = []
            for s in states:
                error_count = (
                    session.query(ErrorLog)
                    .filter(
                        ErrorLog.user_id == user_id,
                        ErrorLog.knowledge_point == s.knowledge_point,
                        ErrorLog.is_resolved == False,
                    )
                    .count()
                )

                results.append({
                    "id": s.id,
                    "knowledge_point": s.knowledge_point,
                    "ef": s.ef,
                    "interval_days": s.interval_days,
                    "repetitions": s.repetitions,
                    "next_review_at": s.next_review_at.isoformat() if s.next_review_at else None,
                    "last_score": s.last_score,
                    "error_count": error_count,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                })

            return results
        finally:
            session.close()

    def get_stats(self, user_id: str = "default") -> dict:
        """
        获取学习统计数据。
        返回: total_kps, due_count, overdue_count, avg_ef, streak_days,
              total_quizzes, total_errors, resolved_errors, mastery_rate
        """
        session = db_manager.get_session()
        try:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            # SM-2 统计
            all_states = (
                session.query(SM2State)
                .filter(SM2State.user_id == user_id)
                .all()
            )

            total_kps = len(all_states)
            due_count = sum(1 for s in all_states if s.next_review_at and s.next_review_at <= today)
            overdue_count = sum(
                1 for s in all_states
                if s.next_review_at and (today - s.next_review_at.replace(hour=0, minute=0, second=0, microsecond=0)).days > 0
            )
            avg_ef = round(sum(s.ef for s in all_states) / len(all_states), 2) if all_states else 2.5

            # 连续学习天数（基于 sm2_states.updated_at 的连续活跃天数）
            streak_days = self._calculate_streak(user_id, session)

            # 错题统计
            total_errors = (
                session.query(ErrorLog)
                .filter(ErrorLog.user_id == user_id)
                .count()
            )
            resolved_errors = (
                session.query(ErrorLog)
                .filter(
                    ErrorLog.user_id == user_id,
                    ErrorLog.is_resolved == True,
                )
                .count()
            )

            # 总做题数（quiz_attempts）
            from ..db.models import QuizAttempt
            total_attempts = (
                session.query(QuizAttempt)
                .filter(QuizAttempt.user_id == user_id)
                .count()
            )

            # 掌握率
            mastery_rate = round(resolved_errors / total_errors * 100, 1) if total_errors > 0 else 0.0

            return {
                "total_kps": total_kps,
                "due_count": due_count,
                "overdue_count": overdue_count,
                "avg_ef": avg_ef,
                "streak_days": streak_days,
                "total_quizzes": total_attempts,
                "total_errors": total_errors,
                "resolved_errors": resolved_errors,
                "unresolved_errors": total_errors - resolved_errors,
                "mastery_rate": mastery_rate,
            }
        finally:
            session.close()

    def _calculate_streak(self, user_id: str, session) -> int:
        """
        计算连续学习天数。
        基于 sm2_states.updated_at：从今天往前数，连续每天都有更新的天数。
        """
        states = (
            session.query(SM2State)
            .filter(SM2State.user_id == user_id)
            .order_by(SM2State.updated_at.desc())
            .all()
        )

        if not states:
            return 0

        # 收集所有有更新的日期
        active_dates = set()
        for s in states:
            if s.updated_at:
                active_dates.add(s.updated_at.date())

        if not active_dates:
            return 0

        # 从今天开始往前数连续天数
        today = datetime.utcnow().date()
        streak = 0
        check_date = today

        while check_date in active_dates:
            streak += 1
            check_date = check_date - timedelta(days=1)

        # 如果今天没有活动，检查是否昨天有
        if streak == 0:
            check_date = today - timedelta(days=1)
            while check_date in active_dates:
                streak += 1
                check_date = check_date - timedelta(days=1)

        return streak

    # ========== 混淆对管理 ==========

    def get_or_create_confusion(
        self,
        concept_a: str,
        concept_b: str,
        user_id: str = "default",
    ) -> dict:
        """
        检测并创建/更新混淆对。
        概念对按字母序排序存储，避免 (A,B) 和 (B,A) 重复。

        返回: confusion pair dict
        """
        # 按字母序排序，保证唯一性
        a, b = sorted([concept_a, concept_b])

        session = db_manager.get_session()
        try:
            existing = (
                session.query(ConfusionPair)
                .filter(
                    ConfusionPair.user_id == user_id,
                    ConfusionPair.concept_a == a,
                    ConfusionPair.concept_b == b,
                )
                .first()
            )

            if existing:
                existing.error_count = (existing.error_count or 0) + 1
                existing.last_confused_at = datetime.utcnow()
                session.commit()
                return {
                    "id": existing.id,
                    "concept_a": existing.concept_a,
                    "concept_b": existing.concept_b,
                    "error_count": existing.error_count,
                    "last_confused_at": existing.last_confused_at.isoformat() if existing.last_confused_at else None,
                    "is_new": False,
                }

            # 创建新的混淆对
            pair = ConfusionPair(
                id=f"conf_{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                concept_a=a,
                concept_b=b,
                error_count=1,
                last_confused_at=datetime.utcnow(),
            )
            session.add(pair)
            session.commit()

            return {
                "id": pair.id,
                "concept_a": pair.concept_a,
                "concept_b": pair.concept_b,
                "error_count": pair.error_count,
                "last_confused_at": pair.last_confused_at.isoformat() if pair.last_confused_at else None,
                "is_new": True,
            }
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"混淆对操作失败: {e}")
        finally:
            session.close()

    def get_confusion_pairs(self, user_id: str = "default") -> list[dict]:
        """
        获取所有混淆对，按 error_count 降序。
        """
        session = db_manager.get_session()
        try:
            pairs = (
                session.query(ConfusionPair)
                .filter(ConfusionPair.user_id == user_id)
                .order_by(ConfusionPair.error_count.desc())
                .all()
            )

            return [
                {
                    "id": p.id,
                    "concept_a": p.concept_a,
                    "concept_b": p.concept_b,
                    "error_count": p.error_count,
                    "last_confused_at": p.last_confused_at.isoformat() if p.last_confused_at else None,
                }
                for p in pairs
            ]
        finally:
            session.close()

    def detect_confusions_from_errors(
        self,
        new_error_kps: list[str],
        user_id: str = "default",
    ) -> list[dict]:
        """
        从新产生的错题知识点列表中检测混淆对。
        如果同一批次中有 >=2 个不同的错题知识点，两两组合创建混淆对。

        new_error_kps: 本次错题的知识点列表（已去重）
        返回: 新创建/更新的混淆对列表
        """
        results = []
        unique_kps = list(set(kp for kp in new_error_kps if kp))

        # 两两组合
        for i in range(len(unique_kps)):
            for j in range(i + 1, len(unique_kps)):
                try:
                    result = self.get_or_create_confusion(
                        unique_kps[i],
                        unique_kps[j],
                        user_id,
                    )
                    results.append(result)
                except Exception as e:
                    print(f"[WARN] 混淆对检测失败 ({unique_kps[i]} vs {unique_kps[j]}): {e}")

        return results


# 全局单例
sm2_service = SM2Service()
