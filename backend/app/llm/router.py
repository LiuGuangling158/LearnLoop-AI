"""
LLM Provider 路由
按任务复杂度选择合适的模型
"""
from .base import LLMProvider, LLMConfig, LLMResponse
from .deepseek import DeepSeekProvider
from .openai import OpenAIProvider
from ..core.config import settings


class LLMRouter:
    """
    模型路由器
    职责：
    1. 管理所有 LLM Provider 实例
    2. 根据任务复杂度路由到合适的模型
    3. 提供统一的调用接口
    """

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}

        # 初始化可用的 Provider
        if settings.deepseek_api_key:
            self._providers["deepseek"] = DeepSeekProvider()
        if settings.openai_api_key:
            self._providers["openai"] = OpenAIProvider()

        if not self._providers:
            print("[WARN] 警告: 没有配置任何 LLM API Key！请在 .env 中设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")

    @property
    def available_providers(self) -> list[str]:
        """返回可用的 Provider 列表"""
        return list(self._providers.keys())

    def get_provider(self, name: str = None) -> LLMProvider:
        """
        获取指定 Provider
        如果指定的不可用，fallback 到默认的
        """
        name = name or settings.default_llm_provider
        if name in self._providers:
            return self._providers[name]

        # Fallback 到第一个可用的
        if self._providers:
            fallback = list(self._providers.keys())[0]
            print(f"[WARN] {name} 不可用，fallback 到 {fallback}")
            return self._providers[fallback]

        raise RuntimeError("没有可用的 LLM Provider！请配置 API Key")

    def get_for_task(self, complexity: str = "simple") -> LLMProvider:
        """
        按任务复杂度路由模型
        complexity: 'simple' | 'medium' | 'complex'
        """
        model_name = settings.get_model_for_task(complexity)
        return self.get_provider(model_name)

    async def generate(
        self,
        prompt: str,
        provider: str = None,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        统一的非流式生成接口
        """
        llm = self.get_provider(provider)
        config = LLMConfig(
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
        return await llm.generate(prompt, config)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        统一的 Embedding 接口，三级 Fallback：
        1. OpenAI text-embedding-3-small（最优质量）
        2. 本地 sentence-transformers 模型（无需 API Key）
        3. 抛出异常（由调用方决定降级策略）
        """
        # Tier 1: OpenAI
        if "openai" in self._providers:
            try:
                return await self._providers["openai"].embed(texts)
            except Exception as e:
                print(f"[WARN] OpenAI embedding 失败: {e}，尝试本地 fallback...")

        # Tier 2: 本地 sentence-transformers
        try:
            return await self._embed_local(texts)
        except Exception as e:
            print(f"[WARN] 本地 embedding 失败: {e}")

        # Tier 3: 完全不可用
        raise RuntimeError(
            "没有可用的 Embedding Provider！\n"
            "  - 配置 OPENAI_API_KEY 使用 OpenAI Embedding\n"
            "  - 或安装 sentence-transformers 使用本地模型: pip install sentence-transformers"
        )

    async def _embed_local(self, texts: list[str]) -> list[list[float]]:
        """使用本地 sentence-transformers 模型生成 Embedding（无需 API Key）"""
        from sentence_transformers import SentenceTransformer

        # 懒加载 + 缓存模型
        if not hasattr(self, "_local_embed_model"):
            model_name = settings.local_embedding_model
            print(f"[INFO] 正在加载本地 Embedding 模型: {model_name} ...")
            self._local_embed_model = SentenceTransformer(model_name)
            print(f"[OK] 本地 Embedding 模型已加载 (维度: {settings.local_embedding_dim})")

        embeddings = self._local_embed_model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()


# 全局单例
llm_router = LLMRouter()
