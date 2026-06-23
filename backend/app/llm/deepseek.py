"""
DeepSeek API Provider
DeepSeek 兼容 OpenAI API 格式，所以可以用 OpenAI SDK 调用
"""
import json
from typing import AsyncIterator
from openai import AsyncOpenAI
from .base import LLMProvider, LLMConfig, LLMResponse
from ..core.config import settings


class DeepSeekProvider(LLMProvider):
    """DeepSeek API 调用封装"""

    def __init__(self, config: LLMConfig = None):
        super().__init__(config)
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        self.default_model = settings.deepseek_model

    async def generate(self, prompt: str, config: LLMConfig = None) -> LLMResponse:
        cfg = self._resolve_config(config)
        model = cfg.model or self.default_model

        messages = []
        if cfg.system_prompt:
            messages.append({"role": "system", "content": cfg.system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "top_p": cfg.top_p,
        }

        # 如果开启 JSON 模式
        if cfg.json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            return LLMResponse(
                content=choice.message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
                finish_reason=choice.finish_reason or "stop",
            )
        except Exception as e:
            return LLMResponse(
                content=f"[Error] DeepSeek API 调用失败: {str(e)}",
                model=model,
                finish_reason="error",
            )

    async def generate_stream(
        self, prompt: str, config: LLMConfig = None
    ) -> AsyncIterator[str]:
        cfg = self._resolve_config(config)
        model = cfg.model or self.default_model

        messages = []
        if cfg.system_prompt:
            messages.append({"role": "system", "content": cfg.system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "top_p": cfg.top_p,
            "stream": True,
        }

        try:
            stream = await self.client.chat.completions.create(**kwargs)
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"[Error] DeepSeek 流式调用失败: {str(e)}"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """DeepSeek 不提供 Embedding API，此方法需要 fallback 到 OpenAI"""
        raise NotImplementedError(
            "DeepSeek 不提供 Embedding API，请使用 OpenAI Embedding 或换用 text-embedding-3-small"
        )
