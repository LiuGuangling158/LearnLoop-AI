"""
Retrieval Agent - RAG 知识检索
基于向量数据库检索相关笔记，结合 LLM 生成带引用的回答
v0.3: 集成 Multi-Query 扩展召回 + Rerank 重排序
"""
import json
from ..core.agent_base import BaseAgent, AgentResult, AgentContext
from ..core.config import settings
from ..utils.query_expansion import expand_queries
from ..utils.reranker import rerank_chunks


def _enrich_sources(llm_sources: list[dict], retrieved_chunks: list[dict]) -> list[dict]:
    """
    将检索到的 score 注入 LLM 生成的 sources，按 title 匹配。
    如果 LLM 没有返回 sources，直接用检索结果作为 sources。
    """
    # 构建 title → chunk 的映射
    chunk_map = {}
    for c in retrieved_chunks:
        title = c.get("title", "")
        if title not in chunk_map:
            chunk_map[title] = c

    enriched = []
    for s in llm_sources:
        title = s.get("title", "")
        matched = chunk_map.get(title)
        if matched:
            s["score"] = matched.get("score", 0)
            s["chunk_id"] = matched.get("id", "")
        else:
            # 模糊匹配：title 互相包含
            for ct, chunk in chunk_map.items():
                if title and (title in ct or ct in title):
                    s["score"] = chunk.get("score", 0)
                    s["chunk_id"] = chunk.get("id", "")
                    break
            else:
                s["score"] = 0.0
                s["chunk_id"] = ""
        enriched.append(s)

    # 如果 LLM 没有返回 sources，直接用检索结果
    if not enriched and retrieved_chunks:
        enriched = [
            {
                "title": c.get("title", "未知"),
                "excerpt": c.get("content", "")[:200],
                "score": c.get("score", 0),
                "chunk_id": c.get("id", ""),
            }
            for c in retrieved_chunks[:5]
        ]

    return enriched


def _merge_deduplicate_chunks(all_results: list[list[dict]]) -> list[dict]:
    """合并多个检索结果列表，按 id 去重，保留最高分的"""
    seen = {}
    for results in all_results:
        for c in results:
            cid = c.get("id", "")
            if cid not in seen:
                seen[cid] = c
            else:
                # 保留 score 更高的
                if c.get("score", 0) > seen[cid].get("score", 0):
                    seen[cid] = c
    return list(seen.values())


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
        RAG 问答流程（v0.3 增强版）:
        1. Multi-Query 扩展（多个角度检索）
        2. 合并去重检索结果
        3. Rerank 重排序
        4. LLM 生成带引用的回答
        """
        query = query or user_input

        # Step 1: 向量检索（支持 Multi-Query 扩展）
        retrieved_chunks = []
        expand_count = 0

        if self.vector_store:
            try:
                if settings.query_expansion_enabled and self.llm:
                    # Multi-Query 扩展
                    queries = await expand_queries(
                        self.llm,
                        query,
                        n=settings.query_expansion_count,
                    )
                    expand_count = len(queries) - 1  # 减去原始 query
                    print(f"[RAG] Query expanded: {len(queries)} queries (original + {expand_count} variants)")

                    # 并行检索（ChromaDB query 支持 query_texts 批量查询，但不同 query 可能返回不同结果）
                    # 逐个检索以保证质量
                    all_results = []
                    for q in queries:
                        chunks = await self.vector_store.search(q, top_k=max(top_k, 10))
                        all_results.append(chunks)

                    # 合并去重
                    retrieved_chunks = _merge_deduplicate_chunks(all_results)
                else:
                    retrieved_chunks = await self.vector_store.search(query, top_k=max(top_k, 10))
            except Exception as e:
                print(f"[WARN] 向量检索失败: {e}（将继续无检索回答）")

        # Step 2: Rerank 重排序
        reranked = False
        if settings.rerank_enabled and len(retrieved_chunks) > top_k and self.llm:
            try:
                before_count = len(retrieved_chunks)
                retrieved_chunks = await rerank_chunks(
                    self.llm,
                    query,
                    retrieved_chunks,
                    top_n=top_k,
                )
                reranked = True
                print(f"[RAG] Reranked: {before_count} → {len(retrieved_chunks)} chunks")
            except Exception as e:
                print(f"[WARN] Rerank 失败: {e}（保持原始检索顺序）")
                retrieved_chunks = retrieved_chunks[:top_k]
        else:
            retrieved_chunks = retrieved_chunks[:top_k]

        # Step 3: 构建 Prompt
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

        # Step 4: LLM 生成
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

            # 将检索 score 注入 LLM 返回的 sources，同时过滤无意义的 source
            enriched_sources = _enrich_sources(
                llm_sources=data.get("sources", []),
                retrieved_chunks=retrieved_chunks,
            )
            data["sources"] = enriched_sources

            return AgentResult(
                success=True,
                data=data,
                raw_content=response.content,
                metadata={
                    "retrieved_chunks": len(retrieved_chunks),
                    "query_expansions": expand_count,
                    "reranked": reranked,
                    "usage": response.usage,
                },
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"RAG 问答失败: {str(e)}",
            )
