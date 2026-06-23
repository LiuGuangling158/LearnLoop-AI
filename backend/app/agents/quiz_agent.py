"""
Quiz Agent - 出题系统
根据知识点自动生成多种题型、多难度的题目
"""
import json
from ..core.agent_base import BaseAgent, AgentResult, AgentContext

QUIZ_SYSTEM_PROMPT = """你是一位专业的软件测试出题老师，精通 ISTQB 考试大纲和各种题型设计。

## 支持的题型
- choice: 单选题（4个选项，1个正确答案）
- short_answer: 简答题
- dictation: 英文术语默写题
- true_false: 判断题

## 难度控制
- easy: 基础概念回忆
- medium: 概念理解和应用
- hard: 综合分析和对比

## 输出格式
{
  "quiz_id": "自动生成",
  "topic": "题目主题",
  "questions": [
    {
      "id": "q_001",
      "type": "choice",
      "difficulty": "medium",
      "question": "题目描述",
      "options": [{"key": "A", "text": "选项内容"}, ...],
      "answer": "A",
      "explanation": "解析"
    }
  ]
}

请严格输出 JSON 格式。"""


class QuizAgent(BaseAgent):
    name = "quiz_agent"
    description = "出题 Agent - 自动生成多种题型和难度的练习题"

    def get_system_prompt(self, context: AgentContext = None) -> str:
        return QUIZ_SYSTEM_PROMPT

    async def execute(
        self,
        context: AgentContext = None,
        user_input: str = "",
        topic: str = "",
        types: list = None,
        difficulty: str = "medium",
        count: int = 5,
        **kwargs,
    ) -> AgentResult:
        """
        生成题目
        """
        types = types or ["choice"]
        topic = topic or kwargs.get("raw_input", user_input)

        prompt = f"""请生成 {count} 道题目的测验：

- 主题：{topic}
- 题型：{', '.join(types)}
- 难度：{difficulty}

请输出 JSON。"""

        try:
            response = await self.call_llm(
                prompt=prompt,
                system_prompt=self.get_system_prompt(context),
                temperature=0.7,
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
                    data = {"topic": topic, "questions": [], "raw": response.content}

            return AgentResult(
                success=True,
                data=data,
                raw_content=response.content,
                metadata={
                    "usage": response.usage,
                    "model": response.model,
                    "question_count": len(data.get("questions", [])),
                },
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"题目生成失败: {str(e)}",
            )
