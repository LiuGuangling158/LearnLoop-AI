# 🧠 LearnLoop-AI
> AI 驱动的个性化学习助手 — Multi-Agent 协作系统  
> "学 → 练 → 测 → 记 → 复" 五步闭环

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.41-red.svg)](https://streamlit.io)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5+-orange.svg)](https://www.trychroma.com)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

---

## 📋 目录

- [项目简介](#项目简介)
- [系统架构](#系统架构)
- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API 接口](#api-接口)
- [MVP 阶段说明](#mvp-阶段说明)
- [路线图](#路线图)

---

## 项目简介

解决学习场景中的 5 大痛点：

| 痛点 | 描述 | 解决方案 |
|------|------|----------|
| 📝 笔记碎片化 | 资料散落在各处，难以统一检索 | RAG 知识库统一索引 |
| ❓ 缺乏自测 | 学完不知道掌握程度 | Quiz Agent 自动出题 |
| 🔁 错题无追踪 | 同类错误反复出现 | Memory Agent + 遗忘曲线 |
| 📅 复习无计划 | 不知道该复习什么 | SM-2 算法自动规划 |
| 🔀 多模型切换难 | 不同任务适合不同模型 | LLM Layer 按任务路由 |

**目标用户：** 软件测试/QA 学习者、技术面试备考者、自学群体。

---

## 系统架构

```
┌────────────────────────────────────────────────┐
│                   Streamlit 前端                  │
│             http://localhost:8501                │
└────────────────────┬───────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼───────────────────────────┐
│               FastAPI 后端 (:8000)               │
│  ┌──────────────────────────────────────────┐  │
│  │         Agent Orchestrator（编排器）       │  │
│  │   TaskRouter → 意图识别 → Agent 分发       │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ NoteAgent │ │QuizAgent │ │RetrievalAgent│  │
│  │ 笔记生成   │ │ 出题练习  │ │  RAG 检索    │  │
│  └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │Grading   │ │ Memory   │ │ Scheduler    │  │
│  │ Agent    │ │ Agent    │ │ Agent        │  │
│  │ 批改评分  │ │ 记忆追踪  │ │ 学习计划      │  │
│  └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │            LLM Router（模型路由）           │  │
│  │   DeepSeek │ OpenAI │ Ollama（本地）       │  │
│  └──────────────────────────────────────────┘  │
└───────┬─────────────────────┬──────────────────┘
        │                     │
┌───────▼──────┐    ┌─────────▼────────┐
│   SQLite     │    │    ChromaDB       │
│  结构化数据   │    │   向量检索 (RAG)   │
└──────────────┘    └──────────────────┘
```

---

## 核心功能

### 已实现（MVP）

| 功能 | 说明 |
|------|------|
| 📝 **笔记生成** | 输入主题 + 补充材料 → AI 生成结构化 Markdown 笔记 |
| 🎯 **出题练习** | 选择题/简答题/判断题/默写题，支持 3 档难度 |
| 🔍 **知识问答 (RAG)** | 基于向量检索的语义搜索 + LLM 带引用回答 |
| 🔀 **多模型路由** | DeepSeek / OpenAI / Ollama 可切换，按任务复杂度选模型 |
| 📊 **系统信息** | 查看 Agent 状态、LLM Provider 可用性 |

### 待实现

| 功能 | 状态 |
|------|------|
| 笔记持久化存储（SQL + VectorDB） | ⚠️ 生成链路待打通 |
| 文件上传入库（PDF/MD/TXT） | ❌ 代码标记 TODO |
| 错题本 + 遗忘曲线追踪 | ❌ 模型已定义，Agent 待完善 |
| SM-2 学习计划调度 | ❌ 待实现 |
| 易混概念对检测 | ❌ 待实现 |

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **后端框架** | FastAPI + Uvicorn | REST API 服务 |
| **前端** | Streamlit | 纯 Python 前端界面 |
| **LLM** | DeepSeek / OpenAI / Ollama | 多模型可切换 |
| **Agent 框架** | 自研（BaseAgent + Orchestrator） | Multi-Agent 协作 |
| **向量数据库** | ChromaDB | 文档 Embedding 语义检索 |
| **关系数据库** | SQLite + SQLAlchemy | 结构化数据存储 |
| **文本切块** | 自研 Markdown Splitter | 按标题层级智能分块 |
| **配置管理** | pydantic-settings + .env | 环境变量管理 |

---

## 快速开始

### 前置条件

- Python 3.10+
- DeepSeek API Key（[免费注册获取](https://platform.deepseek.com)）

### 1. 克隆项目

```bash
git clone <repo-url>
cd 自动化学习agent
```

### 2. 创建虚拟环境

**Windows CMD:**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Windows Git Bash / Linux / macOS:**
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Linux/macOS
```

### 3. 安装依赖

```cmd
pip install chromadb==0.6.3          # 新版有预编译轮子，避免 MSVC 编译问题
pip install -r backend\requirements.txt
```

> ⚠️ 如果 `chroma-hnswlib` 编译报错（缺少 MSVC），先装 `chromadb==0.6.3` 再用 `--no-deps` 安装其余依赖。

### 4. 配置 API Key

```cmd
copy .env.example .env
```

编辑 `.env`，填入你的 DeepSeek API Key：

```env
DEEPSEEK_API_KEY=sk-your-real-key-here
DEFAULT_LLM_PROVIDER=deepseek
```

### 5. 启动后端

```cmd
cd backend
python -m app.main
```

访问 http://localhost:8000/docs 查看 API 文档。

### 6. 启动前端（新终端）

```cmd
cd frontend
..\venv\Scripts\activate.bat
streamlit run streamlit_app.py
```

访问 http://localhost:8501 使用前端界面。

---

## 项目结构

```
自动化学习agent/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口，应用生命周期
│   │   ├── core/
│   │   │   ├── config.py           # 配置管理（pydantic-settings）
│   │   │   ├── agent_base.py       # Agent 基类 + AgentResult
│   │   │   ├── orchestrator.py     # Agent 编排器（任务路由+分发执行）
│   │   │   └── task_router.py      # 意图识别 + Agent 路由
│   │   ├── agents/
│   │   │   ├── note_agent.py       # 笔记生成 Agent
│   │   │   ├── quiz_agent.py       # 出题 Agent
│   │   │   ├── grading_agent.py    # 批改评分 Agent
│   │   │   ├── memory_agent.py     # 记忆追踪 Agent
│   │   │   ├── retrieval_agent.py  # RAG 检索 Agent
│   │   │   └── scheduler_agent.py  # 学习计划 Agent
│   │   ├── llm/
│   │   │   ├── base.py             # LLM 抽象基类
│   │   │   ├── deepseek.py         # DeepSeek Provider
│   │   │   ├── openai.py           # OpenAI Provider
│   │   │   └── router.py           # LLM 路由器（按任务选模型）
│   │   ├── db/
│   │   │   ├── models.py           # SQLAlchemy 数据模型
│   │   │   └── vector_store.py     # ChromaDB 向量存储封装
│   │   ├── api/v1/
│   │   │   ├── notes.py            # 笔记 API
│   │   │   ├── quiz.py             # 题目 API
│   │   │   ├── rag.py              # 知识检索 API
│   │   │   └── schedule.py         # 学习计划 API
│   │   └── utils/
│   │       ├── chunking.py         # Markdown 文本切块工具
│   │       └── schemas.py          # Pydantic 请求/响应模型
│   ├── tests/                      # 测试目录
│   └── requirements.txt            # Python 依赖
├── frontend/
│   └── streamlit_app.py            # Streamlit 前端页面
├── data/                           # 数据目录（自动生成）
│   ├── study_agent.db              # SQLite 数据库
│   └── chroma_db/                  # ChromaDB 持久化目录
├── .env.example                    # 环境变量模板
├── 需求分析.md                      # 详细需求文档
├── 知识讲解.md                      # 技术讲解文档
└── README.md                       # 本文件
```

---

## API 接口

### 笔记

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/notes/generate` | 生成结构化笔记 |
| GET | `/api/v1/notes` | 笔记列表 |

### 题目

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/quiz/generate` | 生成练习题 |
| POST | `/api/v1/quiz/grade` | 批改答案 |

### 知识检索

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/rag/ask` | 知识库问答 |
| POST | `/api/v1/rag/upload` | 上传文档入库（TODO） |

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 系统信息 |
| GET | `/health` | 健康检查 |
| POST | `/api/v1/orchestrator/agent` | 通用 Agent 调用 |

---

## MVP 阶段说明

当前为 **v0.1.0 MVP** 版本，核心 Agent 协作流程已跑通：

✅ 笔记生成（LLM 输出）  
✅ 出题练习（多题型 + 多难度）  
✅ RAG 语义检索（ChromaDB + LLM 回答）  
✅ LLM 多模型路由（DeepSeek / OpenAI / Ollama）  
✅ Streamlit 前端界面  

⚠️ **笔记生成→数据库入库** 的链路待打通  
❌ 文件上传解析入库  
❌ 错题追踪 + 遗忘曲线  
❌ 学习计划自动调度  

---

## 路线图

- [ ] **v0.2** — 笔记生成后自动入库（SQLite + ChromaDB）
- [ ] **v0.3** — 文件上传（PDF/MD/TXT 解析 + 入库）
- [ ] **v0.4** — 错题本 + SM-2 记忆追踪
- [ ] **v0.5** — 易混概念对自动检测
- [ ] **v1.0** — 完整的学习计划调度 + Docker 部署

---

## License

MIT © 2025
