"""
Pydantic 请求/响应 Schema 定义
用于 FastAPI 的请求验证和 API 文档自动生成
"""
from typing import Optional
from pydantic import BaseModel, Field


# ========== Note Agent ==========
class NoteGenerateRequest(BaseModel):
    topic: str = Field(..., description="笔记主题", example="软件测试方法")
    source_text: Optional[str] = Field("", description="原始文本（可选）")
    style: str = Field("detailed", description="笔记风格: detailed | summary | mindmap")
    language: str = Field("zh-CN", description="输出语言")


class NoteResponse(BaseModel):
    id: str
    title: str
    content_md: str
    summary: str
    tags: list[str]
    sections_count: int


# ========== Quiz Agent ==========
class QuizGenerateRequest(BaseModel):
    topic: str = Field(..., description="出题主题", example="软件测试基础")
    types: list[str] = Field(["choice"], description="题型: choice | short_answer | dictation | true_false")
    difficulty: str = Field("medium", description="难度: easy | medium | hard")
    count: int = Field(5, ge=1, le=50, description="题目数量")


class QuestionOption(BaseModel):
    key: str
    text: str


class Question(BaseModel):
    id: str
    type: str
    difficulty: str
    question: str
    options: Optional[list[QuestionOption]] = None
    answer: str
    explanation: str = ""


class QuizResponse(BaseModel):
    quiz_id: str
    topic: str
    questions: list[Question]
    total: int


# ========== Grading Agent ==========
class UserAnswer(BaseModel):
    question_id: str
    answer: str


class GradeRequest(BaseModel):
    quiz_id: str
    answers: list[UserAnswer]


class GradeResult(BaseModel):
    question_id: str
    is_correct: bool
    score: float
    feedback: str = ""
    error_type: str = ""
    reinforcement_suggestion: str = ""


class GradeResponse(BaseModel):
    grade_id: str
    total_score: float
    results: list[GradeResult]
    overall_feedback: str = ""


# ========== RAG Agent ==========
class RAGAskRequest(BaseModel):
    query: str = Field(..., description="问题", example="Verification 和 Validation 的区别是什么？")
    top_k: int = Field(5, ge=1, le=20, description="检索数量")


class RAGSource(BaseModel):
    title: str
    excerpt: str
    relevance_score: float


class RAGResponse(BaseModel):
    query: str
    answer: str
    sources: list[RAGSource] = []
    confidence: float = 0.0


# ========== 通用 ==========
class OrchestratorRequest(BaseModel):
    user_input: str = Field(..., description="用户输入")
    user_id: str = Field("default")
    session_id: Optional[str] = None
    stream: bool = Field(False, description="是否流式返回")


class AgentInfo(BaseModel):
    name: str
    description: str
    version: str
