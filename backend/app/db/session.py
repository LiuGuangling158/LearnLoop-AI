"""
Database Session Manager (global singleton)
与项目现有 vector_store / llm_router 模式保持一致
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from ..core.config import settings


class DatabaseManager:
    """SQLAlchemy 数据库会话管理器（全局单例）"""

    def __init__(self):
        self.engine = None
        self._SessionLocal = None

    def init(self):
        """初始化数据库引擎和 Session 工厂"""
        settings.ensure_data_dirs()
        self.engine = create_engine(
            f"sqlite:///{settings.sqlite_path}",
            connect_args={"check_same_thread": False},
            echo=settings.debug,
        )
        # 启用 WAL 模式提升并发写入性能
        from sqlalchemy import event
        @event.listens_for(self.engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.close()

        self._SessionLocal = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,  # commit 后对象属性仍可访问
        )
        return self.engine, self._SessionLocal

    def get_session(self) -> Session:
        """获取一个新的数据库会话"""
        if not self._SessionLocal:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._SessionLocal()


# 全局单例
db_manager = DatabaseManager()
