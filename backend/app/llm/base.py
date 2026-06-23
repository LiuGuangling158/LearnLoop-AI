"""
LLM Provider 抽象基类
所有 LLM Provider 必须实现此接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional


@dataclass
class LLMResponse:
    """LLM 返回结果"""
    content: str
    model: str = ""
    usage: dict = field(default_factory=dict)  # {"prompt_tokens": N, "completion_tokens": M}
    finish_reason: str = "stop"  # "stop" | "length" | "error"


@dataclass
class LLMConfig:
    """LLM 调用参数"""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    system_prompt: str = ""
    # JSON 模式（结构化输出）
    json_mode: bool = False
    json_schema: Optional[dict] = None


class LLMProvider(ABC):
    """LLM Provider 抽象基类"""

    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig()

    @abstractmethod
    async def generate(self, prompt: str, config: LLMConfig = None) -> LLMResponse:
        """
        非流式生成
        输入 Prompt → 等待完整响应 → 返回
        """
        ...

    @abstractmethod
    async def generate_stream(
        self, prompt: str, config: LLMConfig = None
    ) -> AsyncIterator[str]:
        """
        流式生成 (SSE)
        输入 Prompt → 逐 Token 返回
        """
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        文本转 Embedding 向量
        texts: ["文本1", "文本2"] → [[0.1, 0.2, ...], [0.3, 0.4, ...]]
        """
        ...

    def _resolve_config(self, config: LLMConfig = None) -> LLMConfig:
        """合并默认配置和请求配置"""
        if config is None:
            return self.config
        merged = LLMConfig(
            model=config.model or self.config.model,
            temperature=config.temperature or self.config.temperature,
            max_tokens=config.max_tokens or self.config.max_tokens,
            top_p=config.top_p or self.config.top_p,
            system_prompt=config.system_prompt or self.config.system_prompt,
            json_mode=config.json_mode or self.config.json_mode,
            json_schema=config.json_schema or self.config.json_schema,
        )
        return merged
