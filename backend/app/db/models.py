"""
SQLAlchemy 数据模型定义
使用 SQLite（MVP 阶段）/ 可平滑迁移到 PostgreSQL
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean,
    DateTime, Text, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from ..core.config import settings

Base = declarative_base()


# ========== 用户表 ==========
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== 笔记表 ==========
class Note(Base):
    __tablename__ = "notes"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), default="default")
    title = Column(String, nullable=False)
    content_md = Column(Text, nullable=False)
    summary = Column(Text, default="")
    tags = Column(Text, default="[]")         # JSON Array
    source_type = Column(String, default="generated")  # generated | uploaded | manual
    embedding_id = Column(String, default="")  # VectorDB 中对应的 ID
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ========== 题目表 ==========
class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), default="default")
    topic = Column(String, nullable=False)
    difficulty = Column(String, CheckConstraint("difficulty IN ('easy','medium','hard')"))
    questions_json = Column(Text, nullable=False)  # JSON Array
    source_note_ids = Column(Text, default="[]")
    generated_by = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== 做题记录表 ==========
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), default="default")
    quiz_id = Column(String, ForeignKey("quizzes.id"))
    answers_json = Column(Text, nullable=False)
    score = Column(Float, default=0.0)
    graded_by = Column(String, default="")
    grading_json = Column(Text, default="{}")
    completed_at = Column(DateTime, default=datetime.utcnow)


# ========== 错题记录表 ==========
class ErrorLog(Base):
    __tablename__ = "error_log"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), default="default")
    question_id = Column(String, nullable=False)
    quiz_id = Column(String, ForeignKey("quizzes.id"))
    attempt_id = Column(String, ForeignKey("quiz_attempts.id"))
    user_answer = Column(Text, default="")
    correct_answer = Column(Text, default="")
    error_type = Column(String, default="")    # 概念混淆 | 知识遗忘 | 理解偏差
    knowledge_point = Column(String, default="")
    reviewed_count = Column(Integer, default=0)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== 学习计划表 ==========
class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), default="default")
    topic = Column(String, nullable=False)
    goal_description = Column(Text, default="")
    target_date = Column(DateTime, nullable=True)
    status = Column(
        String,
        CheckConstraint("status IN ('active','paused','completed')"),
        default="active",
    )
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== SM-2 记忆状态表 ==========
class SM2State(Base):
    __tablename__ = "sm2_states"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), default="default")
    knowledge_point = Column(String, nullable=False)
    ef = Column(Float, default=2.5)          # Easiness Factor
    interval_days = Column(Integer, default=1)
    repetitions = Column(Integer, default=0)
    next_review_at = Column(DateTime, nullable=True)
    last_score = Column(Integer, default=0)  # 0-5
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ========== 易混概念对表 ==========
class ConfusionPair(Base):
    __tablename__ = "confusion_pairs"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), default="default")
    concept_a = Column(String, nullable=False)
    concept_b = Column(String, nullable=False)
    error_count = Column(Integer, default=1)
    last_confused_at = Column(DateTime, default=datetime.utcnow)


# ========== 数据库初始化 ==========
def init_db():
    """初始化 SQL 数据库"""
    engine = create_engine(
        f"sqlite:///{settings.sqlite_path}",
        connect_args={"check_same_thread": False},  # SQLite 多线程支持
        echo=settings.debug,
    )
    settings.ensure_data_dirs()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session
