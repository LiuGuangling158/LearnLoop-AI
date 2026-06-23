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
        统一的 Embedding 接口
        DeepSeek 不支持 Embedding，所以用 OpenAI
        """
        if "openai" in self._providers:
            return await self._providers["openai"].embed(texts)
        raise RuntimeError("Embedding 需要 OpenAI API Key（DeepSeek 不支持 Embedding）")


# 全局单例
llm_router = LLMRouter()
