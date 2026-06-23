"""
Agent Orchestrator（编排器）
核心调度引擎：接收任务 → 路由分发 → Agent 执行 → 结果聚合
"""
import time
import uuid
from typing import Optional, AsyncIterator
from .agent_base import BaseAgent, AgentResult, AgentContext
from .task_router import TaskRouter, RouteResult, Intent
from ..llm.router import LLMRouter, llm_router as default_llm_router


class Orchestrator:
    """
    Agent 编排器

    工作流程:
    1. 接收用户输入
    2. TaskRouter 分析意图
    3. 分发到对应 Agent
    4. Agent 执行并返回结果
    5. 可选：多 Agent 协作（链式调用）
    """

    def __init__(self, llm_router: LLMRouter = None):
        self.llm_router = llm_router or default_llm_router
        self.task_router = TaskRouter()
        self._agents: dict[str, BaseAgent] = {}
        self._context: Optional[AgentContext] = None

    # ========== Agent 注册 ==========

    def register_agent(self, agent: BaseAgent):
        """注册一个 Agent"""
        # 注入 LLM Provider
        agent.llm = self.llm_router.get_for_task("simple")
        self._agents[agent.name] = agent
        print(f"[OK] Agent registered: {agent} -> {agent.description}")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取已注册的 Agent"""
        return self._agents.get(name)

    def list_agents(self) -> list[str]:
        """列出所有已注册的 Agent"""
        return [f"{a.name}: {a.description}" for a in self._agents.values()]

    # ========== 核心执行流程 ==========

    async def execute(
        self,
        user_input: str,
        user_id: str = "default",
        session_id: str = None,
        stream: bool = False,
    ) -> AgentResult:
        """
        处理用户输入，自动路由并执行

        参数:
            user_input: 用户输入文本
            user_id: 用户标识
            session_id: 会话标识
            stream: 是否流式返回

        返回:
            AgentResult: 执行结果
        """
        session_id = session_id or str(uuid.uuid4())[:8]
        self._context = AgentContext(
            user_id=user_id,
            session_id=session_id,
        )

        # Step 1: 意图识别 + 路由
        route_result = self.task_router.route(user_input)
        print(f">> 意图: {route_result.intent.value} → Agent: {route_result.agent_name} (置信度: {route_result.confidence:.2f})")

        # Step 2: 获取目标 Agent
        agent = self.get_agent(route_result.agent_name)
        if not agent:
            return AgentResult(
                success=False,
                error=f"未找到 Agent: {route_result.agent_name}",
                metadata={"route": route_result},
            )

        # Step 3: 按任务复杂度选择合适的 LLM
        complexity = self._estimate_complexity(route_result.intent)
        agent.llm = self.llm_router.get_for_task(complexity)

        # Step 4: 执行 Agent
        start_time = time.time()
        try:
            result = await agent.execute(
                context=self._context,
                user_input=user_input,
                **route_result.extracted_params,
            )
        except Exception as e:
            result = AgentResult(
                success=False,
                error=f"Agent [{agent.name}] 执行异常: {str(e)}",
            )

        # Step 5: 附加元数据
        result.metadata.update({
            "agent_name": agent.name,
            "intent": route_result.intent.value,
            "confidence": route_result.confidence,
            "complexity": complexity,
            "elapsed_ms": int((time.time() - start_time) * 1000),
            "session_id": session_id,
            "user_id": user_id,
        })

        return result

    async def execute_pipeline(
        self,
        user_input: str,
        agent_chain: list[str],
        context: AgentContext = None,
    ) -> list[AgentResult]:
        """
        链式执行多个 Agent（Pipeline 模式）
        每个 Agent 的输出作为下一个的输入
        """
        results = []
        current_input = user_input

        for agent_name in agent_chain:
            agent = self.get_agent(agent_name)
            if not agent:
                results.append(AgentResult(
                    success=False,
                    error=f"Agent [{agent_name}] 未注册",
                ))
                break

            agent.llm = self.llm_router.get_for_task("simple")
            result = await agent.execute(
                context=context or self._context,
                user_input=current_input,
                previous_results=results,
            )
            results.append(result)

            if not result.success:
                break

            # 将上一个 Agent 的输出作为下一个的输入
            if isinstance(result.data, dict) and "content" in result.data:
                current_input = result.data["content"]
            elif result.raw_content:
                current_input = result.raw_content

        return results

    # ========== 辅助方法 ==========

    def _estimate_complexity(self, intent: Intent) -> str:
        """根据意图估算任务复杂度"""
        complexity_map = {
            Intent.GENERATE_NOTE: "simple",
            Intent.GENERATE_QUIZ: "medium",
            Intent.GRADE_ANSWER: "complex",
            Intent.QUERY_KNOWLEDGE: "medium",
            Intent.VIEW_MEMORY: "simple",
            Intent.PLAN_STUDY: "simple",
            Intent.CHAT: "simple",
        }
        return complexity_map.get(intent, "simple")

    def new_session(self, user_id: str = "default") -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())[:8]
        self._context = AgentContext(user_id=user_id, session_id=session_id)
        return session_id


# 全局单例
orchestrator = Orchestrator()
