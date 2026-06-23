"""
Note Agent - 笔记整理
输入话题/原始文本 → 输出结构化 Markdown 笔记
"""
import json
from ..core.agent_base import BaseAgent, AgentResult, AgentContext


NOTE_SYSTEM_PROMPT = """你是一位专业的软件测试知识整理专家，拥有 ISTQB 认证和 10 年教学经验。

## 你的任务
将用户提供的知识内容整理成结构化、易读的 Markdown 笔记。

## 输出要求
1. 使用清晰的标题层级 (## → ### → ####)
2. 关键概念用 **粗体** 标记
3. 对比内容用表格展示
4. 每个章节末尾添加 >> 关键要点总结
5. 整体末尾添加 >> 一句话总结

## 输出格式 (JSON)
{
  "title": "笔记标题",
  "content_md": "完整的 Markdown 内容",
  "summary": "一句话总结",
  "tags": ["标签1", "标签2"],
  "sections_count": 3
}

请严格输出 JSON 格式。"""


class NoteAgent(BaseAgent):
    name = "note_agent"
    description = "笔记整理 Agent - 将知识内容转化为结构化 Markdown 笔记"

    def get_system_prompt(self, context: AgentContext = None) -> str:
        return NOTE_SYSTEM_PROMPT

    async def execute(
        self,
        context: AgentContext = None,
        user_input: str = "",
        topic: str = "",
        source_text: str = "",
        **kwargs,
    ) -> AgentResult:
        """
        执行笔记生成
        """
        # 构建 Prompt
        topic = topic or user_input.replace("帮我整理", "").replace("生成笔记", "").replace("归纳", "").strip()
        source = source_text or user_input

        prompt = f"""请为以下知识内容生成结构化笔记：

## 主题
{topic}

## 原始内容
{source}

请输出 JSON。"""

        try:
            response = await self.call_llm(
                prompt=prompt,
                system_prompt=self.get_system_prompt(context),
                temperature=0.5,
                max_tokens=4096,
                json_mode=True,
            )

            # 解析 JSON 输出
            try:
                data = json.loads(response.content)
            except json.JSONDecodeError:
                # 如果 LLM 返回的不是纯 JSON，尝试提取
                content = response.content
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                    data = json.loads(json_str)
                else:
                    # Fallback: 把整个 response 当 content_md
                    data = {
                        "title": topic,
                        "content_md": response.content,
                        "summary": "",
                        "tags": [],
                        "sections_count": 0,
                    }

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
                error=f"笔记生成失败: {str(e)}",
            )
