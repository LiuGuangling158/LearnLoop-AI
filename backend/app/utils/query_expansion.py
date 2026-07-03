"""
Multi-Query 查询扩展
使用 LLM 生成多个变体查询，从不同角度检索知识库，提升召回率
"""
import json
from ..llm.base import LLMConfig


QUERY_EXPANSION_PROMPT = """You are a search query optimizer. Given a user question, generate {n} alternative search queries that could retrieve relevant information from a knowledge base.

## Rules
1. Each query should use different keywords or phrasing from the original
2. Include both broad and narrow formulations
3. Prioritize queries likely to match the knowledge base structure
4. Keep queries concise (under 30 words each)

## User question
{question}

## Output format
Return ONLY a JSON array of strings, like: ["query1", "query2", "query3"]

Generate exactly {n} queries:"""


async def expand_queries(
    llm_provider,
    question: str,
    n: int = 3,
) -> list[str]:
    """
    为给定的问题生成 N 个变体查询

    参数:
        llm_provider: LLM Provider 实例
        question: 原始用户问题
        n: 生成的变体数量

    返回:
        包含原始问题在内的查询列表（去重）
    """
    if n <= 0:
        return [question]

    prompt = QUERY_EXPANSION_PROMPT.format(n=n, question=question)

    try:
        response = await llm_provider.generate(
            prompt,
            LLMConfig(
                temperature=0.7,
                max_tokens=512,
                json_mode=True,
            ),
        )

        # 解析 JSON 数组
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        queries = json.loads(content)
        if isinstance(queries, list) and len(queries) > 0:
            # 去重并保留原始问题
            seen = {question.lower()}
            result = [question]
            for q in queries:
                if isinstance(q, str) and q.lower() not in seen and len(q) > 0:
                    seen.add(q.lower())
                    result.append(q)
            return result[: n + 1]  # 原始 + n 个变体

    except (json.JSONDecodeError, Exception) as e:
        print(f"[WARN] Query expansion failed: {e}, fallback to original query")

    return [question]
