"""
AI Study Agent - FastAPI 服务入口
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 确保 backend 在 path 中
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.orchestrator import orchestrator
from app.llm.router import llm_router
from app.agents.note_agent import NoteAgent
from app.agents.quiz_agent import QuizAgent
from app.agents.grading_agent import GradingAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.scheduler_agent import SchedulerAgent
from app.db.models import init_db
from app.db.vector_store import vector_store
from app.api.v1 import notes, quiz, rag, schedule


# ========== 应用生命周期 ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的操作"""
    # 启动时
    print("=" * 60)
    print(f">> {settings.app_name} v{settings.app_version} 启动中...")
    print("=" * 60)

    # 初始化数据库
    try:
        engine, Session = init_db()
        print(f"[OK] SQLite database initialized: {settings.sqlite_path}")
    except Exception as e:
        print(f"[WARN] Database init failed: {e}")

    # 检查 LLM Provider
    providers = llm_router.available_providers
    if providers:
        print(f"[OK] LLM Providers available: {', '.join(providers)}")
    else:
        print("[ERROR] No LLM Provider configured! Set DEEPSEEK_API_KEY in .env")
        print("   Copy .env.example -> .env and fill in DEEPSEEK_API_KEY")

    # 注册所有 Agent
    try:
        orchestrator.register_agent(NoteAgent())
        orchestrator.register_agent(QuizAgent())
        orchestrator.register_agent(GradingAgent())
        orchestrator.register_agent(MemoryAgent())
        # RetrievalAgent 需要 VectorStore 注入
        retrieval_agent = RetrievalAgent(vector_store=vector_store)
        orchestrator.register_agent(retrieval_agent)
        orchestrator.register_agent(SchedulerAgent())
        print(f"[OK] Registered {len(orchestrator._agents)} Agents")
    except Exception as e:
        print(f"[WARN] Agent registration error: {e}")

    print("=" * 60)
    print(f"API Docs: http://{settings.app_host}:{settings.app_port}/docs")
    print(f"Frontend: http://{settings.app_host}:8501 (run Streamlit separately)")
    print("=" * 60)

    yield  # 应用运行中

    # 关闭时
    print(">> Application shutting down...")


# ========== 创建 FastAPI 应用 ==========

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered Personalized Learning Agent System - Multi-Agent 学习系统",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 注册路由 ==========

app.include_router(notes.router, prefix="/api/v1")
app.include_router(quiz.router, prefix="/api/v1")
app.include_router(rag.router, prefix="/api/v1")
app.include_router(schedule.router, prefix="/api/v1")


# ========== 根路由 ==========

@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "agents": orchestrator.list_agents(),
        "llm_providers": llm_router.available_providers,
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "llm_providers": llm_router.available_providers,
        "agents": len(orchestrator._agents),
    }


# ========== 通用 Agent 调用接口 ==========

@app.post("/api/v1/orchestrator/agent")
async def execute_agent(request: dict):
    """
    通用 Agent 执行接口
    自动路由用户输入到合适的 Agent
    """
    user_input = request.get("user_input", "")
    if not user_input:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "缺少 user_input"},
        )

    result = await orchestrator.execute(
        user_input=user_input,
        user_id=request.get("user_id", "default"),
        session_id=request.get("session_id"),
        stream=request.get("stream", False),
    )

    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "metadata": result.metadata,
    }


# ========== 直接启动 ==========
if __name__ == "__main__":
    import uvicorn
    settings.ensure_data_dirs()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
