"""
Grading Agent - 自动批改
评判用户答案，给出分数和反馈
"""
import json
from ..core.agent_base import BaseAgent, AgentResult, AgentContext

GRADING_SYSTEM_PROMPT = """你是一位严格的软件测试课程批改老师，擅长评估学生的答案质量。

## 评分规则
- 客观题：精确匹配 → 对/错
- 简答题：多维度评分（关键词覆盖度 40% + 语义准确度 30% + 逻辑完整性 30%）

## 输出格式
{
  "total_score": 85,
  "results": [
    {
      "question_id": "q_001",
      "is_correct": true,
      "score": 100,
      "user_answer": "...",
      "correct_answer": "...",
      "feedback": "点评",
      "error_type": "概念混淆 | 知识遗忘 | 理解偏差 | 无",
      "reinforcement_suggestion": "强化建议"
    }
  ],
  "overall_feedback": "总体评价"
}

请严格输出 JSON 格式。"""


class GradingAgent(BaseAgent):
    name = "grading_agent"
    description = "批改 Agent - 自动评分并给出学习建议"

    def get_system_prompt(self, context: AgentContext = None) -> str:
        return GRADING_SYSTEM_PROMPT

    async def execute(
        self,
        context: AgentContext = None,
        user_input: str = "",
        quiz_data: dict = None,
        user_answers: list = None,
        **kwargs,
    ) -> AgentResult:
        """
        批改答案
        quiz_data: 题目数据（含标准答案）
        user_answers: 用户的答案列表
        """
        if not quiz_data:
            return AgentResult(success=False, error="缺少题目数据 (quiz_data)")

        if not user_answers:
            # 尝试从 user_input 解析
            return AgentResult(success=False, error="缺少用户答案 (user_answers)")

        prompt = f"""请批改以下答题：

## 题目和标准答案
{json.dumps(quiz_data.get('questions', []), ensure_ascii=False, indent=2)}

## 学生答案
{json.dumps(user_answers, ensure_ascii=False, indent=2)}

请输出 JSON 格式的批改结果。"""

        try:
            response = await self.call_llm(
                prompt=prompt,
                system_prompt=self.get_system_prompt(context),
                temperature=0.3,  # 批改需要严谨，低温度
                max_tokens=4096,
                json_mode=True,
            )

            try:
                data = json.loads(response.content)
            except json.JSONDecodeError:
                content = response.content
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                    data = json.loads(json_str)
                else:
                    data = {"total_score": 0, "results": [], "overall_feedback": response.content}

            return AgentResult(
                success=True,
                data=data,
                raw_content=response.content,
                metadata={
                    "usage": response.usage,
                    "model": response.model,
                },
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"批改失败: {str(e)}",
            )
