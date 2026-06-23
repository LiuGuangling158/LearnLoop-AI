"""
Scheduler Agent - 学习规划器
基于 SM-2 算法生成每日学习任务
"""
import json
from datetime import date, datetime, timedelta
from ..core.agent_base import BaseAgent, AgentResult, AgentContext

SCHEDULER_SYSTEM_PROMPT = """你是一位学习规划师，擅长制定个性化复习计划。

## 你的依据
- SM-2 间隔重复算法
- 用户的错题记录和薄弱点
- 当前学习进度

## 输出格式
{
  "date": "日期",
  "daily_tasks": [
    {
      "type": "review | new_learn",
      "knowledge_point": "知识点",
      "reason": "原因",
      "priority": "high | medium | low",
      "suggested_duration_min": 15
    }
  ],
  "total_estimated_time_min": 45,
  "encouragement": "一句鼓励的话"
}

请严格输出 JSON 格式。"""


class SM2Calculator:
    """
    SM-2 算法实现
    根据用户对知识点的评分，计算下次复习间隔
    """

    @staticmethod
    def calculate(ef: float, interval: int, repetitions: int, score: int) -> dict:
        """
        ef: Easiness Factor (初始值 2.5)
        interval: 当前间隔天数
        repetitions: 重复次数
        score: 用户评分 0-5
              0-2: 完全忘记
              3: 勉强记住
              4: 正确回忆
              5: 非常轻松

        返回: {ef, interval, repetitions, next_review_date}
        """
        if score >= 3:
            if repetitions == 0:
                new_interval = 1
            elif repetitions == 1:
                new_interval = 6
            else:
                new_interval = max(1, round(interval * ef))

            new_repetitions = repetitions + 1
        else:
            new_interval = 1
            new_repetitions = 1

        # 更新 EF
        new_ef = ef + (0.1 - (5 - score) * (0.08 + (5 - score) * 0.02))
        new_ef = max(1.3, new_ef)  # EF 最低 1.3

        next_review = date.today() + timedelta(days=new_interval)

        return {
            "ef": round(new_ef, 2),
            "interval": new_interval,
            "repetitions": new_repetitions,
            "next_review_date": next_review.isoformat(),
        }


class SchedulerAgent(BaseAgent):
    name = "scheduler_agent"
    description = "学习规划 Agent - 基于 SM-2 生成每日学习任务"
    sm2 = SM2Calculator()

    def get_system_prompt(self, context: AgentContext = None) -> str:
        return SCHEDULER_SYSTEM_PROMPT

    async def execute(
        self,
        context: AgentContext = None,
        user_input: str = "",
        sm2_states: list = None,
        error_logs: list = None,
        action: str = "daily",  # daily | plan | review
        review_score: int = None,
        **kwargs,
    ) -> AgentResult:
        """
        daily: 生成今日学习任务
        plan: 创建学习计划
        review: 记录复习评分，更新 SM-2 状态
        """
        if action == "review" and review_score is not None:
            return await self._process_review(kwargs.get("ef", 2.5),
                                              kwargs.get("interval", 1),
                                              kwargs.get("repetitions", 0),
                                              review_score)

        if action == "daily":
            return await self._generate_daily_tasks(sm2_states or [], error_logs or [])

        if action == "plan":
            return await self._create_plan(user_input)

        return AgentResult(
            success=True,
            data={"message": f"Scheduler Agent 收到: {user_input}", "action": action},
        )

    async def _process_review(self, ef: float, interval: int, repetitions: int, score: int) -> AgentResult:
        """处理复习评分"""
        result = self.sm2.calculate(ef, interval, repetitions, score)

        return AgentResult(
            success=True,
            data={
                "sm2_result": result,
                "message": f"评分 {score} → 下次复习: {result['next_review_date']} (间隔 {result['interval']} 天)",
            },
        )

    async def _generate_daily_tasks(self, sm2_states: list, error_logs: list) -> AgentResult:
        """生成今日学习任务"""
        today = date.today().isoformat()

        # 筛选今天需要复习的知识点
        due_items = [s for s in sm2_states if s.get("next_review_at", "") <= today]
        due_items.sort(key=lambda x: x.get("error_count", 0), reverse=True)

        tasks = []
        for item in due_items[:5]:  # 最多 5 个复习任务
            error_count = item.get("error_count", 0)
            priority = "high" if error_count > 3 else "medium" if error_count > 0 else "low"
            tasks.append({
                "type": "review",
                "knowledge_point": item.get("knowledge_point", ""),
                "reason": f"间隔 {item.get('interval', 1)} 天需复习，已错 {error_count} 次",
                "priority": priority,
                "suggested_duration_min": 15 if priority == "high" else 10,
            })

        result = {
            "date": today,
            "daily_tasks": tasks,
            "total_estimated_time_min": sum(t["suggested_duration_min"] for t in tasks),
            "encouragement": "坚持复习是掌握知识的最好方法！💪",
        }

        return AgentResult(success=True, data=result)

    async def _create_plan(self, user_input: str) -> AgentResult:
        """使用 LLM 创建学习计划"""
        prompt = f"""请根据用户需求创建学习计划：

{user_input}

请输出 JSON。"""

        try:
            response = await self.call_llm(
                prompt=prompt,
                system_prompt=self.get_system_prompt(),
                temperature=0.7,
                max_tokens=2048,
                json_mode=True,
            )
            data = json.loads(response.content)
            return AgentResult(success=True, data=data, raw_content=response.content)
        except Exception as e:
            return AgentResult(success=False, error=str(e))
