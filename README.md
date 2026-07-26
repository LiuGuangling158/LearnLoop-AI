# 🧠 LearnLoop-AI
> AI 驱动的个性化学习助手 — Multi-Agent 协作系统  
> "学 → 练 → 测 → 记 → 复" 五步闭环

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6-646cff.svg)](https://vitejs.dev)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.6+-orange.svg)](https://www.trychroma.com)
[![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)](.)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

---

## 📋 目录

- [项目简介](#项目简介)
- [企业级定位](#企业级定位)
- [企业级使用场景](#企业级使用场景)
- [企业化演进能力](#企业化演进能力)
- [系统架构](#系统架构)
- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API 接口](#api-接口)
- [路线图](#路线图)

---

## 项目简介

LearnLoop-AI 是一个 AI 驱动的个性化学习与企业知识训练平台。当前版本以个人学习助手为 MVP 形态，已经跑通“学 → 练 → 测 → 记 → 复”的完整闭环；进一步扩展后，可作为企业内部培训、岗位认证、知识库问答和能力追踪系统。

解决学习场景中的 5 大痛点：

| 痛点 | 描述 | 解决方案 |
|------|------|----------|
| 📝 笔记碎片化 | 资料散落在各处，难以统一检索 | RAG 知识库统一索引 |
| ❓ 缺乏自测 | 学完不知道掌握程度 | Quiz Agent 自动出题 |
| 🔁 错题无追踪 | 同类错误反复出现 | Memory Agent + 错题本 |
| 📅 复习无计划 | 不知道该复习什么 | SM-2 遗忘曲线自动规划 |
| 🔀 多模型切换难 | 不同任务适合不同模型 | LLM Layer 按任务路由 |

**目标用户：** 软件测试/QA 学习者、技术面试备考者、自学群体、企业培训负责人、客服/售后团队、研发新人培养团队、合规培训团队。

---

## 企业级定位

在企业中，培训的核心难题通常不是“没有资料”，而是资料分散、学习不可验证、错题无法复盘、知识遗忘无法跟进、管理层缺少能力风险数据。LearnLoop-AI 将文档知识库、Agent 自动生成、智能测评和间隔复习连接起来，让企业知识从静态资料变成可训练、可评估、可追踪的能力资产。

### 企业学习闭环

```text
企业资料导入
  → AI 结构化笔记
  → 岗位化题库生成
  → 自动批改与反馈
  → 错题/薄弱点沉淀
  → SM-2 个性化复习
  → 团队能力看板
```

### 企业级价值

| 价值方向 | 说明 |
|------|------|
| 新人培养提效 | 将入职手册、SOP、项目文档转化为可问答、可训练、可复习的学习路径 |
| 知识一致性 | 使用统一知识库和标准答案，减少不同导师、不同团队之间的口径差异 |
| 培训可验证 | 从“看过课程”升级为“能答题、能解释、能持续复习” |
| 风险前置发现 | 通过错题、薄弱点和易混概念识别团队能力短板 |
| 专家经验沉淀 | 把项目复盘、质检案例、故障处理经验沉淀为长期训练资产 |
| 模型成本可控 | LLM Router 按任务复杂度选择 DeepSeek/OpenAI/Ollama 等模型 |

---

## 企业级使用场景

| 场景 | 典型资料 | 使用方式 | 业务收益 |
|------|------|------|------|
| QA/测试团队训练 | 测试规范、ISTQB 资料、缺陷流程、自动化测试指南 | 自动生成测试方法笔记、用例设计题、缺陷分析题，追踪 Verification/Validation 等易混点 | 缩短 QA 新人上手周期，减少用例评审返工 |
| 客服/售后培训 | FAQ、退款政策、工单案例、投诉升级 SOP | RAG 查询标准处理流程，生成话术题和场景判断题，记录政策误答 | 提升回答一致性，降低质检扣分和错误承诺 |
| 合规制度培训 | 合规手册、审计案例、监管问答、内部制度 | 生成条款摘要和案例题，按 Rubric 批改风险识别题，形成可审计记录 | 从完成率管理升级为掌握度管理 |
| 研发新人入职 | 架构文档、部署手册、代码规范、事故复盘 | 支持项目知识问答，生成排障题和规范题，沉淀新人薄弱点 | 减少导师重复答疑，加快首次独立交付 |
| 销售/产品赋能 | 产品白皮书、竞品对比、行业方案、报价规则 | 生成客户异议处理题和竞品对比题，辅助一线快速查询 | 统一销售话术，缩短新产品赋能周期 |

更完整的企业级方案见：[docs/enterprise-blueprint.md](docs/enterprise-blueprint.md)  
演示脚本见：[docs/demo-playbooks.md](docs/demo-playbooks.md)

---

## 企业化演进能力

当前项目已经具备 MVP 所需的学习闭环。面向企业生产环境，建议按以下方向增强：

| 能力域 | 当前状态 | 企业级增强 |
|------|------|------|
| 身份与组织 | 预留 `user_id`，默认单用户 | JWT/OIDC、部门、角色、租户隔离 |
| 权限治理 | 开发环境 CORS 全开放 | RBAC、知识库权限、题库审核权限 |
| 数据存储 | SQLite + ChromaDB | PostgreSQL/pgvector、对象存储、备份恢复 |
| 内容治理 | AI 生成后直接入库 | 专家审核、版本管理、敏感信息检测 |
| 管理看板 | 学习统计与错题统计 | 部门/岗位能力矩阵、认证结果、风险排行 |
| 系统集成 | REST API + React | LMS、企业 IM、知识库、工单系统、Webhook |
| 可观测性 | 控制台日志 | 结构化日志、调用链追踪、模型成本统计 |
| 安全合规 | `.env` 管理密钥 | 密钥托管、审计日志、数据脱敏、本地模型策略 |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                       React 前端 (10 页面)                    │
│             http://localhost:5173                            │
│  仪表盘 │ 生成笔记 │ 我的笔记 │ 知识库 │ 出题 │ 问答 │ 复习 │ 错题本 │ 企业蓝图 │ 系统 │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI 后端 (:8000)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Agent Orchestrator（编排器）               │  │
│  │        TaskRouter → 意图识别 → Agent 分发               │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Service Layer（服务层）                    │  │
│  │  NoteService: SQLite + Chunk + Embed + ChromaDB       │  │
│  │  SM2Service:  SM-2 状态 + 混淆对 + 统计                │  │
│  │  FileService: PDF/MD/TXT 解析 → 复用 NoteService      │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │NoteAgent │ │QuizAgent │ │GradingAg │ │RetrievalAg   │  │
│  │ 笔记生成  │ │ 出题练习  │ │ 批改评分  │ │ RAG 检索     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌──────────┐                                 │  │
│  │MemoryAg  │ │Scheduler │                                 │  │
│  │ 记忆追踪  │ │ 学习计划  │                                 │  │
│  └──────────┘ └──────────┘                                 │  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              LLM Router（模型路由）                     │  │
│  │    DeepSeek │ OpenAI │ Ollama │ 本地 Embedding         │  │
│  └───────────────────────────────────────────────────────┘  │
└───────┬─────────────────────────┬───────────────────────────┘
        │                         │
┌───────▼──────┐        ┌─────────▼────────┐
│   SQLite     │        │    ChromaDB       │
│  结构化数据   │        │   向量检索 (RAG)   │
│  7 张表      │        │   knowledge_chunks│
└──────────────┘        └──────────────────┘
```

---

## 核心功能

### 已实现（v0.4）

| 功能 | 说明 |
|------|------|
| 📝 **笔记生成** | 输入主题 → AI 生成结构化 Markdown 笔记 → 自动入库 |
| 💾 **笔记持久化** | SQLite + 按标题分块 → Embedding → ChromaDB 索引 |
| 🔀 **Embedding 三级 Fallback** | OpenAI → 本地 sentence-transformers → 跳过（优雅降级） |
| 📚 **笔记管理** | 列表分页、详情、删除、搜索过滤（关键词 + 来源类型） |
| 📤 **文件上传** | PDF/MD/TXT 解析 → 复用笔记入库链路 → 知识库可检索 |
| 🎯 **出题练习** | 4 种题型（选择/简答/默写/判断）、3 档难度、自动入库 |
| 📝 **自动批改** | 客观题精确匹配 + 简答题 LLM 语义评分（Rubric 多维度） |
| 🔍 **知识问答 (RAG)** | Multi-Query 扩展 + Rerank 重排 + LLM 带引用回答 |
| 📋 **错题本** | 自动收录错题、按知识点分组、已掌握标记 |
| 🧠 **SM-2 遗忘曲线** | 笔记/错题自动创建 SM-2 状态、复习评分后计算最佳间隔 |
| 🔄 **混淆对检测** | 错题知识点两两组合自动创建混淆对、按频次排序 |
| 📊 **学习仪表盘** | 运营指标带 + 待复习任务 + 知识点进度 + 快捷入口 |
| 📅 **复习计划** | 到期知识点列表、0-5 评分、SM-2 间隔预测、EF 变化展示 |
| 🔀 **多模型路由** | DeepSeek / OpenAI / Ollama 可切换，按任务复杂度选模型 |
| 🏢 **企业蓝图页** | 场景演示路径、企业价值指标、部署演进与治理能力清单 |

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **后端框架** | FastAPI + Uvicorn | REST API 服务（27 个端点） |
| **前端** | React 19 + Vite + Lucide Icons | 企业级 SPA 前端（10 页面） |
| **LLM** | DeepSeek / OpenAI / Ollama | 多模型可切换 |
| **Embedding** | OpenAI / sentence-transformers | 三级 Fallback |
| **Agent 框架** | 自研（BaseAgent + Orchestrator + Service） | 6 Agent + 3 Service |
| **向量数据库** | ChromaDB | 文档 Embedding 语义检索 |
| **关系数据库** | SQLite + SQLAlchemy（WAL 模式） | 7 张表，结构化数据 |
| **间隔重复** | SM-2 算法（SuperMemo 2） | 遗忘曲线驱动的复习调度 |
| **文本切块** | 自研 Markdown Splitter | 按 H1-H3 标题层级分块 |
| **配置管理** | pydantic-settings + .env | 环境变量管理 |

---

## 快速开始

### 前置条件

- Python 3.10+
- Node.js 18+
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
pip install chromadb==0.6.3
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
npm install
npm run dev
```

访问 http://localhost:5173 使用 React 前端界面。

> 旧版 Streamlit 前端仍保留在 `frontend/streamlit_app.py`，可作为历史版本参考。

---

## 项目结构

```
自动化学习agent/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI 入口，应用生命周期
│   │   ├── core/
│   │   │   ├── config.py             # 配置管理（pydantic-settings）
│   │   │   ├── agent_base.py         # Agent 基类 + AgentResult
│   │   │   ├── orchestrator.py       # Agent 编排器
│   │   │   └── task_router.py        # 意图识别 + Agent 路由
│   │   ├── agents/                   # 6 个专业 Agent
│   │   │   ├── note_agent.py         # 笔记生成
│   │   │   ├── quiz_agent.py         # 出题
│   │   │   ├── grading_agent.py      # 批改评分
│   │   │   ├── retrieval_agent.py    # RAG 检索（Multi-Query + Rerank）
│   │   │   ├── memory_agent.py       # 记忆追踪、薄弱点分析
│   │   │   └── scheduler_agent.py    # SM-2 学习规划
│   │   ├── services/                 # 业务服务层
│   │   │   ├── note_service.py       # 笔记持久化（SQLite + Chunk + Embed）
│   │   │   ├── sm2_service.py        # SM-2 状态管理 + 混淆对检测
│   │   │   └── file_service.py       # 文件解析（PDF/MD/TXT）
│   │   ├── llm/
│   │   │   ├── base.py               # LLM 抽象基类
│   │   │   ├── deepseek.py           # DeepSeek Provider
│   │   │   ├── openai.py             # OpenAI Provider
│   │   │   └── router.py             # LLM 路由 + Embedding fallback
│   │   ├── db/
│   │   │   ├── session.py            # DB 会话管理器（WAL 模式）
│   │   │   ├── models.py             # SQLAlchemy 数据模型（7 张表）
│   │   │   └── vector_store.py       # ChromaDB 向量存储封装
│   │   ├── api/v1/
│   │   │   ├── notes.py              # 笔记 API（生成/列表/详情/删除/搜索）
│   │   │   ├── quiz.py               # 题目 API（生成/提交/历史/错题本）
│   │   │   ├── rag.py                # 知识检索 API（问答/上传/管理）
│   │   │   ├── schedule.py           # 学习规划 API（每日/复习/统计/计划）
│   │   │   └── memory.py             # 记忆 API（薄弱点/混淆对/报告）
│   │   └── utils/
│   │       ├── chunking.py           # Markdown 文本切块
│   │       ├── query_expansion.py    # Multi-Query 扩展
│   │       ├── reranker.py           # LLM Rerank 重排序
│   │       └── schemas.py            # Pydantic 请求/响应模型
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── package.json                  # React/Vite 前端依赖与脚本
│   ├── index.html                    # Vite HTML 入口
│   ├── vite.config.js                # Vite 配置
│   ├── src/
│   │   ├── App.jsx                   # React SPA 主应用（10 页面）
│   │   ├── main.jsx                  # React 挂载入口
│   │   └── styles.css                # 企业级毛玻璃视觉样式
│   └── streamlit_app.py              # 旧版 Streamlit 前端（legacy）
├── data/                             # 数据目录（自动生成）
│   ├── study_agent.db                # SQLite 数据库
│   └── chroma_db/                    # ChromaDB 持久化
├── .env.example
├── 需求分析.md
└── README.md
```

---

## API 接口

共 27 个端点，完整 API 文档见 http://localhost:8000/docs。

### 笔记

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/notes/generate` | 生成笔记 + 自动入库 |
| GET | `/api/v1/notes` | 笔记列表（分页） |
| GET | `/api/v1/notes/search` | 搜索笔记（标题/内容 + 来源过滤） |
| GET | `/api/v1/notes/{id}` | 笔记详情 |
| DELETE | `/api/v1/notes/{id}` | 删除笔记（SQLite + ChromaDB） |

### 题目

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/quiz/generate` | 生成题目 + 入库 |
| GET | `/api/v1/quiz/{id}` | 获取题目（不含答案） |
| POST | `/api/v1/quiz/{id}/submit` | 提交答案 → 批改 + 错题入库 + SM-2 联动 |
| GET | `/api/v1/quiz/history` | 做题历史 |
| GET | `/api/v1/quiz/errors/list` | 错题列表（分页 + 已解决过滤） |
| PUT | `/api/v1/quiz/errors/{id}/resolve` | 标记错题已掌握 |

### 知识检索

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/rag/ask` | RAG 问答（Multi-Query + Rerank） |
| POST | `/api/v1/rag/upload` | 上传文档入库（PDF/MD/TXT） |
| GET | `/api/v1/rag/sources` | 已上传文档列表 |
| DELETE | `/api/v1/rag/sources/{id}` | 删除文档 |
| GET | `/api/v1/rag/stats` | 知识库统计 |

### 学习规划

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/schedule/daily` | 今日复习任务 |
| POST | `/api/v1/schedule/review` | 记录复习评分（0-5）→ SM-2 计算 |
| GET | `/api/v1/schedule/stats` | 学习统计（连续天数、掌握率等） |
| GET | `/api/v1/schedule/states` | 全部 SM-2 状态 |
| POST | `/api/v1/schedule/plan` | 创建学习计划 |
| GET | `/api/v1/schedule/plans` | 学习计划列表 |

### 记忆管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/memory/weak-points` | 薄弱知识点分析 |
| GET | `/api/v1/memory/confusions` | 易混概念对列表 |
| GET | `/api/v1/memory/error-log` | 错题记录（分页 + 过滤） |
| GET | `/api/v1/memory/report` | 综合学习报告（LLM 生成） |

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 系统信息 |
| GET | `/health` | 健康检查 |
| POST | `/api/v1/orchestrator/agent` | 通用 Agent 调用 |

---

## 路线图

- [x] **v0.2** — 笔记生成后自动入库（SQLite + ChromaDB）、Embedding 三级 Fallback ✅
- [x] **v0.3** — 文件上传（PDF/MD/TXT）、Multi-Query + Rerank、错题本前端 ✅
- [x] **v0.4** — SM-2 遗忘曲线联动、学习仪表盘、复习计划、混淆对检测 ✅
- [x] **v0.5** — React/Vite 企业前端、企业蓝图页、毛玻璃视觉体系、基础企业 Demo 叙事
- [ ] **v0.6** — 用户认证（JWT）、前端拆分优化、Docker 容器化、基础企业 Demo 数据
- [ ] **v0.7** — 企业组织/角色模型、知识库权限、题库审核流、部门看板
- [ ] **v0.8** — PostgreSQL/pgvector 适配、结构化日志、模型成本统计、备份恢复
- [ ] **v1.0** — 综合评估指标、自动化测试、Next.js 正式前端、企业 LMS/IM 集成

---

## License

MIT © 2025
