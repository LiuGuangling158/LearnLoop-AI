"""
Retrieval Agent - RAG 知识检索
基于向量数据库检索相关笔记，结合 LLM 生成带引用的回答
"""
import json
from ..core.agent_base import BaseAgent, AgentResult, AgentContext

RETRIEVAL_SYSTEM_PROMPT = """你是一个知识库问答助手，回答基于提供的参考资料。

## 规则
1. 优先使用参考资料中的内容回答
2. 如果资料中包含答案，直接引用并标注来源
3. 如果资料不包含答案，明确告知用户"知识库中暂无相关信息"
4. 不要编造参考资料中没有的信息

## 输出格式
{
  "query": "用户的问题",
  "answer": "回答",
  "sources": [{"title": "来源笔记标题", "excerpt": "相关片段"}],
  "confidence": 0.9
}

请严格输出 JSON 格式。"""


class RetrievalAgent(BaseAgent):
    name = "retrieval_agent"
    description = "检索 Agent - RAG 知识库问答"

    def __init__(self, llm_provider=None, vector_store=None):
        super().__init__(llm_provider)
        self.vector_store = vector_store  # VectorDB 实例，由 Orchestrator 注入

    def get_system_prompt(self, context: AgentContext = None) -> str:
        return RETRIEVAL_SYSTEM_PROMPT

    async def execute(
        self,
        context: AgentContext = None,
        user_input: str = "",
        query: str = "",
        top_k: int = 5,
        **kwargs,
    ) -> AgentResult:
        """
        RAG 问答流程:
        1. 向量检索相关文档块
        2. 拼接上下文
        3. LLM 生成带引用的回答
        """
        query = query or user_input

        # Step 1: 向量检索
        retrieved_chunks = []
        if self.vector_store:
            try:
                retrieved_chunks = await self.vector_store.search(query, top_k=top_k)
            except Exception as e:
                print(f"[WARN] 向量检索失败: {e}（将继续无检索回答）")

        # Step 2: 构建 Prompt
        if retrieved_chunks:
            context_text = "\n\n---\n\n".join([
                f"[来源: {c.get('title', '未知')}]\n{c.get('content', '')}"
                for c in retrieved_chunks
            ])
            prompt = f"""请根据以下参考资料回答用户问题。

## 参考资料
{context_text}

## 用户问题
{query}

请输出 JSON。"""
        else:
            prompt = f"""知识库中暂无相关资料，请如实告知用户。

## 用户问题
{query}

请输出 JSON。"""

        # Step 3: LLM 生成
        try:
            response = await self.call_llm(
                prompt=prompt,
                system_prompt=self.get_system_prompt(context),
                temperature=0.5,
                max_tokens=2048,
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
                    data = {"query": query, "answer": response.content, "sources": [], "confidence": 0.5}

            return AgentResult(
                success=True,
                data=data,
                raw_content=response.content,
                metadata={
                    "retrieved_chunks": len(retrieved_chunks),
                    "usage": response.usage,
                },
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"RAG 问答失败: {str(e)}",
            )
