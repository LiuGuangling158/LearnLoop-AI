"""
LLM-based Chunk Reranker
用 LLM 对检索到的 chunk 进行相关性打分，实现重排序
"""
import json
from ..llm.base import LLMConfig
from ..core.config import settings


RERANK_PROMPT = """Rate the relevance of each document chunk to the user query on a scale of 0-10.

## User Query
{query}

## Document Chunks
{chunks_formatted}

## Rules
- 10 = perfectly answers the query
- 5 = somewhat related
- 0 = completely unrelated
- Consider both keyword match and semantic relevance

## Output format
Return a JSON array of objects: [{{"id": "chunk_id", "score": N}}, ...]
Order by score descending.

Output ONLY the JSON array:"""


async def rerank_chunks(
    llm_provider,
    query: str,
    chunks: list[dict],
    top_n: int = None,
) -> list[dict]:
    """
    对检索到的 chunk 列表进行 LLM 重排序

    参数:
        llm_provider: LLM Provider 实例
        query: 用户查询
        chunks: 检索结果列表，每个元素含 id, content 等字段
        top_n: 重排后保留的数量（默认使用 config.rerank_top_k）

    返回:
        按相关性分数降序排列的 chunk 列表
    """
    top_n = top_n or settings.rerank_top_k

    if not chunks or len(chunks) <= 1:
        return chunks

    # 截断参与重排的 chunk 数量，控制 token 消耗
    max_input = settings.rerank_max_input_chunks
    truncate_chars = settings.rerank_chunk_truncate_chars

    chunks_to_rank = chunks[:max_input]

    # 格式化 chunks 文本（截断每个 chunk 节省 token）
    chunks_text_parts = []
    for c in chunks_to_rank:
        content = c.get("content", "")[:truncate_chars]
        chunks_text_parts.append(f"[ID: {c.get('id', '')}]\n{content}")

    chunks_formatted = "\n\n---\n\n".join(chunks_text_parts)

    prompt = RERANK_PROMPT.format(query=query, chunks_formatted=chunks_formatted)

    try:
        response = await llm_provider.generate(
            prompt,
            LLMConfig(
                temperature=0.1,
                max_tokens=1024,
                json_mode=True,
            ),
        )

        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        scores = json.loads(content)

        if isinstance(scores, list) and len(scores) > 0:
            # 构建 id → score 映射
            score_map = {}
            for s in scores:
                if isinstance(s, dict) and "id" in s:
                    score_map[s["id"]] = s.get("score", 0)

            # 为每个 chunk 设置 rerank_score
            for c in chunks:
                c["rerank_score"] = score_map.get(c.get("id", ""), 0)

            # 按 rerank_score 降序排列
            ranked = sorted(chunks, key=lambda c: c.get("rerank_score", 0), reverse=True)
            return ranked[:top_n]

    except (json.JSONDecodeError, Exception) as e:
        print(f"[WARN] Rerank failed: {e}, fallback to original order")

    # Fallback: 保持原顺序，取 top_n
    return chunks[:top_n]
