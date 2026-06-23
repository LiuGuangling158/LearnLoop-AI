"""
Task Router（任务路由器）
负责意图识别和任务分发
"""
from enum import Enum
from dataclasses import dataclass


class Intent(str, Enum):
    """用户意图分类"""
    GENERATE_NOTE = "generate_note"          # 生成笔记
    GENERATE_QUIZ = "generate_quiz"          # 出题
    GRADE_ANSWER = "grade_answer"            # 批改答案
    QUERY_KNOWLEDGE = "query_knowledge"      # 知识问答 (RAG)
    VIEW_MEMORY = "view_memory"              # 查看错题/弱点
    PLAN_STUDY = "plan_study"                # 学习规划
    CHAT = "chat"                            # 普通对话


@dataclass
class RouteResult:
    """路由结果"""
    intent: Intent
    agent_name: str         # 目标 Agent 名称
    confidence: float       # 置信度 0-1
    extracted_params: dict  # 从用户输入中提取的参数


# 意图 → Agent 映射表
INTENT_AGENT_MAP = {
    Intent.GENERATE_NOTE: "note_agent",
    Intent.GENERATE_QUIZ: "quiz_agent",
    Intent.GRADE_ANSWER: "grading_agent",
    Intent.QUERY_KNOWLEDGE: "retrieval_agent",
    Intent.VIEW_MEMORY: "memory_agent",
    Intent.PLAN_STUDY: "scheduler_agent",
    Intent.CHAT: "note_agent",  # 默认用 Note Agent 处理
}

# 意图关键词匹配表（简单版，后续可升级为 LLM 意图分类）
INTENT_KEYWORDS = {
    Intent.GENERATE_NOTE: ["整理笔记", "生成笔记", "总结", "做笔记", "归纳", "整理知识"],
    Intent.GENERATE_QUIZ: ["出题", "做题", "测验", "考试", "题目", "来几道", "测试一下"],
    Intent.GRADE_ANSWER: ["批改", "评分", "改题", "对答案", "判分"],
    Intent.QUERY_KNOWLEDGE: ["什么是", "区别", "是什么", "解释", "查询", "搜索", "找一下"],
    Intent.VIEW_MEMORY: ["错题", "弱点", "易混", "错误记录", "我错了哪些", "薄弱"],
    Intent.PLAN_STUDY: ["今天学什么", "复习计划", "学习规划", "任务", "安排"],
}


class TaskRouter:
    """
    任务路由器
    职责：
    1. 分析用户输入 → 识别意图
    2. 将意图映射到对应的 Agent
    3. 提取关键参数
    """

    def __init__(self, use_llm: bool = False):
        """
        use_llm: 是否使用 LLM 做意图分类（更准确但增加延迟/成本）
                 默认 False，使用关键词匹配
        """
        self.use_llm = use_llm

    def route(self, user_input: str, context: dict = None) -> RouteResult:
        """
        分析用户输入，返回路由结果
        """
        # 关键词匹配（简单快速）
        intent, confidence = self._keyword_match(user_input)

        # 如果置信度太低或启用 LLM 模式，用 LLM 分类
        if confidence < 0.5 and self.use_llm:
            intent, confidence = self._llm_classify(user_input)

        agent_name = INTENT_AGENT_MAP.get(intent, "note_agent")
        params = self._extract_params(user_input, intent)

        return RouteResult(
            intent=intent,
            agent_name=agent_name,
            confidence=confidence,
            extracted_params=params,
        )

    def _keyword_match(self, text: str) -> tuple[Intent, float]:
        """基于关键词的意图匹配"""
        best_intent = Intent.CHAT
        best_score = 0.0

        for intent, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_intent = intent

        # 归一化置信度
        confidence = min(best_score / 3.0, 1.0) if best_score > 0 else 0.3
        return best_intent, confidence

    def _llm_classify(self, text: str) -> tuple[Intent, float]:
        """
        TODO: 使用 LLM 做意图分类
        向 LLM 发送用户输入 + 意图列表 → 让它返回最匹配的意图
        """
        # 目前 fallback 到关键词匹配
        return self._keyword_match(text)

    def _extract_params(self, text: str, intent: Intent) -> dict:
        """
        从用户输入中提取参数
        例如: "帮我出5道中等难度的软件测试选择题"
            → {"count": 5, "difficulty": "medium", "topic": "软件测试", "types": ["choice"]}
        """
        params = {"raw_input": text}

        # 简单提取：难度
        if "简单" in text or "容易" in text or "easy" in text.lower():
            params["difficulty"] = "easy"
        elif "难" in text or "困难" in text or "hard" in text.lower():
            params["difficulty"] = "hard"
        elif "中等" in text or "中等难度" in text or "medium" in text.lower():
            params["difficulty"] = "medium"

        # 提取数量
        import re
        count_match = re.search(r'(\d+)\s*[道题个]', text)
        if count_match:
            params["count"] = int(count_match.group(1))

        # 提取题型
        types = []
        if "选择" in text:
            types.append("choice")
        if "简答" in text or "问答" in text:
            types.append("short_answer")
        if "默写" in text or "翻译" in text:
            types.append("dictation")
        if "判断" in text:
            types.append("true_false")
        if types:
            params["types"] = types

        return params


# 全局单例
task_router = TaskRouter()
