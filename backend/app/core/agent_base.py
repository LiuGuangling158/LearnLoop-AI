"""
Agent 抽象基类
所有专业 Agent 必须继承此类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, AsyncIterator
from ..llm.base import LLMProvider, LLMConfig, LLMResponse


@dataclass
class AgentResult:
    """Agent 执行结果"""
    success: bool
    data: Any = None           # 结构化输出 (dict/list)
    raw_content: str = ""      # LLM 原始输出
    error: str = ""
    metadata: dict = field(default_factory=dict)  # token 用量、耗时等


@dataclass
class AgentContext:
    """Agent 执行上下文 - 在 Agent 间传递共享信息"""
    user_id: str = ""
    session_id: str = ""
    # 当前相关的笔记/题目/知识点
    related_notes: list = field(default_factory=list)
    current_topic: str = ""
    # 可以继续追加更多上下文字段


class BaseAgent(ABC):
    """
    Agent 基类

    每个 Agent 有三要素：
    1. system_prompt - 定义 Agent 的角色和能力
    2. tools - Agent 可以调用的工具列表
    3. execute() - Agent 入口方法

    子类需要实现：
    - get_system_prompt() → str
    - execute(context, **kwargs) → AgentResult
    """

    # Agent 元信息（子类覆盖）
    name: str = "base"
    description: str = "Base Agent"
    version: str = "0.1.0"

    def __init__(self, llm_provider: LLMProvider = None):
        """
        llm_provider: 如果不传，由 Orchestrator 在调用时注入
        """
        self.llm = llm_provider

    @abstractmethod
    def get_system_prompt(self, context: AgentContext = None) -> str:
        """返回此 Agent 的 System Prompt（人设 + 规则）"""
        ...

    @abstractmethod
    async def execute(
        self,
        context: AgentContext = None,
        **kwargs,
    ) -> AgentResult:
        """
        Agent 执行入口
        每个 Agent 根据自己的职责实现此方法
        """
        ...

    async def call_llm(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        stream: bool = False,
    ) -> LLMResponse | AsyncIterator[str]:
        """
        便捷方法：调用 LLM
        """
        if not self.llm:
            raise RuntimeError(f"Agent [{self.name}] 没有设置 LLM Provider")

        config = LLMConfig(
            system_prompt=system_prompt or self.get_system_prompt(),
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )

        if stream:
            return self.llm.generate_stream(prompt, config)
        return await self.llm.generate(prompt, config)

    def __repr__(self) -> str:
        return f"<{self.name} v{self.version}>"
