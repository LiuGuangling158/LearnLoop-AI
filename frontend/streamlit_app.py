"""
AI Study Agent - Streamlit MVP 前端
纯 Python 写的学习界面，无需 JavaScript
"""
import sys
from pathlib import Path

# 添加 backend 到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import streamlit as st
import requests
import json

# ========== 页面配置 ==========
st.set_page_config(
    page_title="AI Study Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API 地址
API_BASE = "http://127.0.0.1:8000/api/v1"

# ========== Session State 初始化 ==========
if "notes_page_view" not in st.session_state:
    st.session_state.notes_page_view = "list"  # "list" | "detail"
if "selected_note_id" not in st.session_state:
    st.session_state.selected_note_id = None
if "notes_page_offset" not in st.session_state:
    st.session_state.notes_page_offset = 0

# ========== 样式 ==========
st.markdown("""
<style>
    .main-title { font-size: 2.5rem; font-weight: 700; color: #6366f1; }
    .agent-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        margin-bottom: 0.5rem;
    }
    .result-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        margin-top: 1rem;
    }
    .note-card {
        padding: 1.2rem;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        margin-bottom: 0.8rem;
        cursor: pointer;
        transition: all 0.2s;
        background: #ffffff;
    }
    .note-card:hover {
        border-color: #6366f1;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
    }
    .tag-badge {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 0.25rem;
        background: #eef2ff;
        color: #6366f1;
        font-size: 0.8rem;
        margin-right: 0.3rem;
    }
    .meta-text {
        color: #9ca3af;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ========== 侧边栏 ==========
with st.sidebar:
    st.markdown("## 🧠 AI Study Agent")
    st.markdown("---")

    # 检查后端连接
    try:
        resp = requests.get("http://127.0.0.1:8000/health", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            st.success(f"✅ 后端已连接 ({data.get('agents', 0)} Agents)")
        else:
            st.error("❌ 后端异常")
    except Exception:
        st.error("❌ 后端未启动\n\n请先运行:\n```bash\ncd backend\npython -m app.main\n```")

    st.markdown("---")

    # 导航
    page = st.radio(
        "选择功能",
        ["📝 生成笔记", "📚 我的笔记", "🎯 出题练习", "🔍 知识问答", "📊 系统信息"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### 💡 提示")
    st.info("在 .env 中配置 DEEPSEEK_API_KEY 后才能使用 AI 功能")

# ========== 主区域 ==========
st.markdown('<p class="main-title">🧠 AI Study Agent</p>', unsafe_allow_html=True)
st.markdown("*AI 驱动的个性化学习助手 — Multi-Agent 系统*")

# ===================================================================
# 📝 生成笔记
# ===================================================================
if page == "📝 生成笔记":
    st.header("📝 生成学习笔记")
    st.markdown("输入一个主题，AI 会帮你生成结构化的 Markdown 笔记，并自动保存到知识库")

    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("学习主题", placeholder="例如：软件测试方法、ISTQB 基础、黑盒测试...")
    with col2:
        style = st.selectbox("笔记风格", ["detailed", "summary", "mindmap"])

    source_text = st.text_area("补充内容（可选）", placeholder="粘贴你想整理的文章、课件内容...", height=150)

    if st.button("🚀 生成笔记", type="primary", disabled=not topic):
        with st.spinner("AI 正在整理笔记..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/notes/generate",
                    json={
                        "topic": topic,
                        "source_text": source_text,
                        "style": style,
                    },
                    timeout=120,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    note = data.get("data", {})

                    # 入库状态提示
                    if note.get("_persisted"):
                        st.success("✅ 笔记已保存到知识库")
                    elif note.get("_save_error"):
                        st.warning(f"⚠️ 笔记已生成，但保存失败: {note['_save_error']}")

                    st.markdown("---")
                    st.markdown(f"## 📄 {note.get('title', topic)}")

                    # 显示笔记内容
                    with st.container():
                        st.markdown(note.get("content_md", "无内容"))

                    # 底部信息
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("章节数", note.get("sections_count", 0))
                    with col2:
                        tags = note.get("tags", [])
                        st.markdown(f"**标签:** {' '.join(['`' + t + '`' for t in tags])}")
                    with col3:
                        st.metric("耗时", f"{data.get('metadata', {}).get('elapsed_ms', 0)}ms")
                    with col4:
                        if note.get("_persisted"):
                            if st.button("📚 查看我的笔记", key="goto_notes_from_gen"):
                                st.session_state.notes_page_view = "list"
                                st.rerun()

                    # 摘要
                    if note.get("summary"):
                        with st.expander("📝 一句话总结"):
                            st.info(note["summary"])

                else:
                    st.error(f"请求失败: {resp.status_code} - {resp.text}")
            except requests.exceptions.ConnectionError:
                st.error("无法连接到后端，请先启动 FastAPI 服务")
            except Exception as e:
                st.error(f"错误: {str(e)}")


# ===================================================================
# 📚 我的笔记
# ===================================================================
elif page == "📚 我的笔记":

    # --- 笔记详情视图 ---
    if st.session_state.notes_page_view == "detail" and st.session_state.selected_note_id:
        note_id = st.session_state.selected_note_id

        # 返回按钮
        if st.button("← 返回笔记列表"):
            st.session_state.notes_page_view = "list"
            st.session_state.selected_note_id = None
            st.rerun()

        # 加载笔记
        try:
            resp = requests.get(f"{API_BASE}/notes/{note_id}", timeout=10)
            if resp.status_code == 200:
                note = resp.json().get("data", {})

                st.header(f"📄 {note.get('title', '无标题')}")

                # 元信息栏
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.caption(f"📅 {note.get('created_at', '')[:10] if note.get('created_at') else '未知'}")
                with col2:
                    st.caption(f"📝 {note.get('word_count', 0)} 字")
                with col3:
                    st.caption(f"📂 {note.get('source_type', '')}")
                with col4:
                    tags = note.get("tags", [])
                    if tags:
                        tag_html = " ".join([f'<span class="tag-badge">{t}</span>' for t in tags])
                        st.markdown(tag_html, unsafe_allow_html=True)

                st.markdown("---")

                # 完整 Markdown 内容
                st.markdown(note.get("content_md", "无内容"))

                # 摘要
                if note.get("summary"):
                    st.markdown("---")
                    with st.expander("📝 一句话总结"):
                        st.info(note["summary"])

                # 操作按钮
                st.markdown("---")
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("🗑️ 删除此笔记", type="secondary"):
                        # 二次确认
                        st.session_state.confirm_delete = note_id
                        st.rerun()

                # 确认删除对话框
                if st.session_state.get("confirm_delete") == note_id:
                    st.warning("确定要删除这篇笔记吗？此操作不可撤消。")
                    col_yes, col_no = st.columns([1, 5])
                    with col_yes:
                        if st.button("✅ 确认删除", type="primary"):
                            try:
                                del_resp = requests.delete(f"{API_BASE}/notes/{note_id}", timeout=10)
                                if del_resp.status_code == 200:
                                    st.success("笔记已删除")
                                    st.session_state.notes_page_view = "list"
                                    st.session_state.selected_note_id = None
                                    st.session_state.pop("confirm_delete", None)
                                    st.rerun()
                                else:
                                    st.error(f"删除失败: {del_resp.status_code}")
                            except Exception as e:
                                st.error(f"删除失败: {str(e)}")
                    with col_no:
                        if st.button("❌ 取消"):
                            st.session_state.pop("confirm_delete", None)
                            st.rerun()

            else:
                st.error(f"笔记不存在 (HTTP {resp.status_code})")
                if st.button("← 返回列表"):
                    st.session_state.notes_page_view = "list"
                    st.session_state.selected_note_id = None
                    st.rerun()
        except requests.exceptions.ConnectionError:
            st.error("无法连接到后端，请先启动 FastAPI 服务")
        except Exception as e:
            st.error(f"加载失败: {str(e)}")

    # --- 笔记列表视图 ---
    else:
        st.header("📚 我的笔记")
        st.markdown("已保存的学习笔记，点击查看详情")

        try:
            offset = st.session_state.notes_page_offset
            resp = requests.get(
                f"{API_BASE}/notes",
                params={"limit": 20, "offset": offset},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                notes = data.get("data", [])
                pagination = data.get("pagination", {})
                total = pagination.get("total", 0)

                # 统计信息
                st.caption(f"共 {total} 篇笔记")

                if not notes:
                    # 空状态
                    st.markdown("---")
                    st.info("📭 还没有笔记，去生成第一篇吧！")
                    if st.button("🚀 生成笔记", type="primary"):
                        st.rerun()  # 用户需手动切换页面

                # 笔记卡片列表
                for note in notes:
                    with st.container():
                        st.markdown("---")
                        col_main, col_action = st.columns([8, 1])
                        with col_main:
                            # 可点击的标题
                            note_title = note.get("title", "无标题")
                            note_summary = note.get("summary", "")
                            note_tags = note.get("tags", [])
                            note_date = (note.get("created_at") or "")[:10]
                            note_words = note.get("word_count", 0)

                            st.markdown(f"### {note_title}")
                            if note_summary:
                                st.markdown(note_summary[:150] + ("..." if len(note_summary) > 150 else ""))

                            # 元信息
                            tag_html = " ".join([f'<span class="tag-badge">{t}</span>' for t in note_tags])
                            st.markdown(
                                f'{tag_html} <span class="meta-text">| 📅 {note_date} | 📝 {note_words} 字</span>',
                                unsafe_allow_html=True,
                            )

                        with col_action:
                            if st.button("📖 查看", key=f"view_{note['id']}"):
                                st.session_state.notes_page_view = "detail"
                                st.session_state.selected_note_id = note["id"]
                                st.rerun()

                # 分页控件
                if total > 20:
                    st.markdown("---")
                    col_prev, col_spacer, col_next = st.columns([1, 3, 1])
                    with col_prev:
                        if offset > 0:
                            if st.button("← 上一页"):
                                st.session_state.notes_page_offset = max(0, offset - 20)
                                st.rerun()
                    with col_next:
                        if offset + 20 < total:
                            if st.button("下一页 →"):
                                st.session_state.notes_page_offset = offset + 20
                                st.rerun()
                    total_pages = (total + 19) // 20
                    current_page = offset // 20 + 1
                    st.caption(f"第 {current_page}/{total_pages} 页")

            else:
                st.error(f"获取笔记列表失败: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("无法连接到后端，请先启动 FastAPI 服务")
        except Exception as e:
            st.error(f"加载失败: {str(e)}")


# ===================================================================
# 🎯 出题练习
# ===================================================================
elif page == "🎯 出题练习":
    st.header("🎯 出题练习")
    st.markdown("根据知识点自动生成练习题")

    col1, col2, col3 = st.columns(3)
    with col1:
        quiz_topic = st.text_input("出题主题", placeholder="例如：软件测试基础")
    with col2:
        difficulty = st.selectbox("难度", ["easy", "medium", "hard"], index=1)
    with col3:
        count = st.number_input("题目数量", min_value=1, max_value=20, value=5)

    types = st.multiselect(
        "题型",
        ["choice", "short_answer", "dictation", "true_false"],
        default=["choice"],
        format_func=lambda x: {"choice": "选择题", "short_answer": "简答题", "dictation": "默写题", "true_false": "判断题"}[x],
    )

    if st.button("🎯 生成题目", type="primary", disabled=not quiz_topic):
        with st.spinner("AI 正在出题..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/quiz/generate",
                    json={
                        "topic": quiz_topic,
                        "types": types,
                        "difficulty": difficulty,
                        "count": count,
                    },
                    timeout=120,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    quiz = data.get("data", {})
                    questions = quiz.get("questions", [])

                    st.markdown("---")
                    st.markdown(f"## 🎯 {quiz.get('topic', '')}")

                    # 显示题目
                    for i, q in enumerate(questions):
                        with st.container():
                            st.markdown(f"### 第 {i+1} 题")
                            st.markdown(f"**{q.get('question', '')}**")
                            st.caption(f"类型: {q.get('type')} | 难度: {q.get('difficulty')}")

                            if q.get("type") == "choice" and q.get("options"):
                                user_answer = st.radio(
                                    f"q_{q['id']}",
                                    [f"{o['key']}. {o['text']}" for o in q["options"]],
                                    key=f"answer_{q['id']}",
                                    index=None,
                                )
                                # 显示正确答案
                                with st.expander("查看答案"):
                                    st.success(f"正确答案: **{q.get('answer')}**")
                                    if q.get("explanation"):
                                        st.info(q["explanation"])

                            st.markdown("---")
                else:
                    st.error(f"请求失败: {resp.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("无法连接到后端，请先启动 FastAPI 服务")
            except Exception as e:
                st.error(f"错误: {str(e)}")


# ===================================================================
# 🔍 知识问答
# ===================================================================
elif page == "🔍 知识问答":
    st.header("🔍 知识问答")
    st.markdown("向你的知识库提问，AI 会基于你的笔记来回答")

    query = st.text_input("你的问题", placeholder="例如：Verification 和 Validation 的区别是什么？")

    col1, col2 = st.columns([3, 1])
    with col2:
        top_k = st.slider("检索数量", 1, 20, 5)

    if st.button("🔍 提问", type="primary", disabled=not query):
        with st.spinner("正在检索知识库..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/rag/ask",
                    json={"query": query, "top_k": top_k},
                    timeout=120,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    rag_data = data.get("data", {})

                    st.markdown("---")
                    st.markdown("### 📖 回答")
                    st.markdown(rag_data.get("answer", "无法获取回答"))

                    # 来源
                    sources = rag_data.get("sources", [])
                    if sources:
                        with st.expander(f"📚 参考来源 ({len(sources)} 条)"):
                            for s in sources:
                                st.markdown(f"**{s.get('title', '未知')}** (相关度: {s.get('relevance_score', 0):.2f})")
                                st.markdown(f"> {s.get('excerpt', '')[:200]}...")
                                st.markdown("---")

                    # 元信息
                    st.caption(f"检索到 {data.get('metadata', {}).get('retrieved_chunks', 0)} 个文档块 | 置信度: {rag_data.get('confidence', 0)}")
                else:
                    st.error(f"请求失败: {resp.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("无法连接到后端，请先启动 FastAPI 服务")
            except Exception as e:
                st.error(f"错误: {str(e)}")


# ===================================================================
# 📊 系统信息
# ===================================================================
elif page == "📊 系统信息":
    st.header("📊 系统信息")

    try:
        resp = requests.get("http://127.0.0.1:8000/", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            st.json(data)
    except Exception:
        st.warning("后端未启动，无法获取系统信息")

    st.markdown("---")
    st.markdown("### 📂 项目文件结构")
    st.code("""
ai-study-agent/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # API 路由
│   │   ├── core/           # 核心（Orchestrator, Config, Agent基类）
│   │   ├── agents/         # 6个专业Agent
│   │   ├── services/       # 业务服务层（持久化等）
│   │   ├── llm/            # LLM抽象层（DeepSeek, OpenAI）
│   │   ├── db/             # 数据库（SQL + VectorDB）
│   │   └── utils/          # 工具（Chunking, Schemas）
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── streamlit_app.py    # 前端界面
├── .env.example
├── 需求分析.md
└── 知识讲解.md
    """)

    st.markdown("---")
    st.markdown("### 🚀 启动方式")
    st.code("""
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 配置 API Key
cp ../.env.example ../.env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 3. 启动后端
python -m app.main

# 4. 启动前端（新终端）
cd frontend
streamlit run streamlit_app.py
    """)
