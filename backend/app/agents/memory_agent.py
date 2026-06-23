"""
Memory Agent - 错题本系统
记录错题、分析薄弱点、检测易混概念
"""
import json
from ..core.agent_base import BaseAgent, AgentResult, AgentContext

MEMORY_SYSTEM_PROMPT = """你是一位学习记忆分析专家，擅长分析学习者的错误模式并给出强化建议。

## 你的能力
1. 分析错题记录，找出薄弱知识点
2. 检测易混概念对
3. 给出针对性强化建议

## 输出格式
{
  "weak_points": ["薄弱点1", "薄弱点2"],
  "confusion_pairs": [{"concept_a": "A", "concept_b": "B", "reason": "混淆原因"}],
  "improvement_plan": "学习建议"
}

请严格输出 JSON 格式。"""


class MemoryAgent(BaseAgent):
    name = "memory_agent"
    description = "记忆 Agent - 错题管理、薄弱点分析、易混概念检测"

    def get_system_prompt(self, context: AgentContext = None) -> str:
        return MEMORY_SYSTEM_PROMPT

    async def execute(
        self,
        context: AgentContext = None,
        user_input: str = "",
        error_logs: list = None,
        grading_result: dict = None,
        action: str = "analyze",  # analyze | record | report
        **kwargs,
    ) -> AgentResult:
        """
        analyze: 分析薄弱点（从错题记录中）
        record: 记录新的错题
        report: 生成学习报告
        """
        if action == "record" and grading_result:
            # 从批改结果中提取错题，记录到数据库
            return await self._record_errors(grading_result)

        if action == "analyze":
            return await self._analyze_weak_points(error_logs or [])

        if action == "report":
            return await self._generate_report(error_logs or [])

        # 默认：对话式查询
        return AgentResult(
            success=True,
            data={"message": f"Memory Agent 收到: {user_input}", "action": action},
            raw_content="",
        )

    async def _record_errors(self, grading_result: dict) -> AgentResult:
        """记录错题"""
        errors = []
        for r in grading_result.get("results", []):
            if not r.get("is_correct", False):
                errors.append({
                    "question_id": r.get("question_id"),
                    "user_answer": r.get("user_answer"),
                    "correct_answer": r.get("correct_answer"),
                    "error_type": r.get("error_type", "未分类"),
                    "feedback": r.get("feedback", ""),
                })

        return AgentResult(
            success=True,
            data={
                "recorded_errors": len(errors),
                "errors": errors,
            },
            metadata={"action": "record"},
        )

    async def _analyze_weak_points(self, error_logs: list) -> AgentResult:
        """分析薄弱知识点"""
        if not error_logs:
            return AgentResult(
                success=True,
                data={"message": "暂无错题记录", "weak_points": [], "confusion_pairs": []},
            )

        prompt = f"""请分析以下错题记录，找出薄弱知识点和易混概念：

{json.dumps(error_logs, ensure_ascii=False, indent=2)}

请输出 JSON。"""

        try:
            response = await self.call_llm(
                prompt=prompt,
                system_prompt=self.get_system_prompt(),
                temperature=0.5,
                max_tokens=2048,
                json_mode=True,
            )
            data = json.loads(response.content)
            return AgentResult(success=True, data=data, raw_content=response.content)
        except Exception as e:
            return AgentResult(success=False, error=str(e))

    async def _generate_report(self, error_logs: list) -> AgentResult:
        """生成学习报告"""
        if not error_logs:
            return AgentResult(
                success=True,
                data={"message": "暂无数据，无法生成报告"},
            )

        prompt = f"""请根据以下错题记录生成一份学习报告：

{json.dumps(error_logs, ensure_ascii=False, indent=2)}

报告应包含：总体统计、薄弱知识点排名、改进建议。输出 JSON。"""

        try:
            response = await self.call_llm(
                prompt=prompt,
                system_prompt=self.get_system_prompt(),
                temperature=0.5,
                max_tokens=2048,
                json_mode=True,
            )
            data = json.loads(response.content)
            return AgentResult(success=True, data=data, raw_content=response.content)
        except Exception as e:
            return AgentResult(success=False, error=str(e))
