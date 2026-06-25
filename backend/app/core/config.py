"""
应用配置管理
使用 pydantic-settings 从 .env 文件和环境变量加载配置
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    """应用全局配置"""

    # --- 应用 ---
    app_name: str = "AI Study Agent"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # --- DeepSeek ---
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"

    # --- Ollama ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # --- 数据库 ---
    sqlite_path: str = "./data/study_agent.db"
    chroma_persist_dir: str = "./data/chroma_db"

    # --- 默认 Provider ---
    default_llm_provider: str = "deepseek"

    # --- Embedding ---
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536  # text-embedding-3-small: 1536, deepseek: 1536
    # 本地 Embedding fallback（无需 API Key）
    local_embedding_model: str = "all-MiniLM-L6-v2"
    local_embedding_dim: int = 384

    # --- RAG ---
    chunk_size: int = 1000
    chunk_overlap: int = 100
    retrieval_top_k: int = 10
    rerank_top_k: int = 5

    # --- 模型路由规则 ---
    # 简单任务用便宜的模型，复杂任务用强模型
    simple_task_model: str = "deepseek"
    medium_task_model: str = "deepseek"
    complex_task_model: str = "deepseek"  # 如果 openai_api_key 有值则改为 "openai"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "allow"}

    def get_model_for_task(self, complexity: str) -> str:
        """
        按任务复杂度选择模型
        complexity: 'simple' | 'medium' | 'complex'
        """
        mapping = {
            "simple": self.simple_task_model,
            "medium": self.medium_task_model,
            "complex": self.complex_task_model,
        }
        return mapping.get(complexity, self.default_llm_provider)

    def ensure_data_dirs(self):
        """确保数据目录存在"""
        data_dir = Path(self.sqlite_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)
        Path(self.chroma_persist_dir).mkdir(parents=True, exist_ok=True)


# 全局单例
settings = Settings()
