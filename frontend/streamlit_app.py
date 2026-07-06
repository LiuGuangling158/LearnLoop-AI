"""
AI Study Agent - Streamlit MVP 前端 v0.4
纯 Python 写的学习界面，9 页面
"""
import sys
import io
from pathlib import Path

# 添加 backend 到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import streamlit as st
import requests
import json

# ========== 页面配置 ==========
st.set_page_config(
    page_title="LearnLoop-AI",
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
if "notes_search_query" not in st.session_state:
    st.session_state.notes_search_query = ""
if "notes_source_filter" not in st.session_state:
    st.session_state.notes_source_filter = "全部"
if "kb_page_offset" not in st.session_state:
    st.session_state.kb_page_offset = 0
if "error_page_offset" not in st.session_state:
    st.session_state.error_page_offset = 0
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None

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
    .stat-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
    }
    .stat-card.green {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
    .stat-card.orange {
        background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
    }
    .error-item {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #fecaca;
        background: #fef2f2;
        margin-bottom: 0.6rem;
    }
    .error-item.resolved {
        border-color: #bbf7d0;
        background: #f0fdf4;
    }
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: #9ca3af;
    }
    .empty-state .icon { font-size: 3rem; }
</style>
""", unsafe_allow_html=True)


# ========== 工具函数 ==========
def check_backend():
    """检查后端连接状态"""
    try:
        resp = requests.get("http://127.0.0.1:8000/health", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def api_get(path: str, params: dict = None, timeout: int = 10):
    """封装 GET 请求，统一错误处理"""
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=timeout)
        return resp
    except requests.exceptions.ConnectionError:
        st.error("❌ 无法连接到后端，请先启动 FastAPI 服务（`cd backend && python -m app.main`）")
        return None


def api_post(path: str, json_data: dict = None, files: dict = None, timeout: int = 120):
    """封装 POST 请求，统一错误处理"""
    try:
        if files:
            resp = requests.post(f"{API_BASE}{path}", files=files, data=json_data, timeout=timeout)
        else:
            resp = requests.post(f"{API_BASE}{path}", json=json_data, timeout=timeout)
        return resp
    except requests.exceptions.ConnectionError:
        st.error("❌ 无法连接到后端，请先启动 FastAPI 服务（`cd backend && python -m app.main`）")
        return None


def api_put(path: str, json_data: dict = None, timeout: int = 10):
    """封装 PUT 请求，统一错误处理"""
    try:
        resp = requests.put(f"{API_BASE}{path}", json=json_data, timeout=timeout)
        return resp
    except requests.exceptions.ConnectionError:
        st.error("❌ 无法连接到后端，请先启动 FastAPI 服务（`cd backend && python -m app.main`）")
        return None


# ========== 侧边栏 ==========
with st.sidebar:
    st.markdown("## 🧠 LearnLoop-AI")
    st.markdown("v0.4.0 — 学→练→测→记→复")
    st.markdown("---")

    # 后端状态
    backend = check_backend()
    if backend:
        st.success(f"✅ 后端已连接 ({backend.get('agents', 0)} Agents)")
    else:
        st.error("❌ 后端未启动\n\n请先运行:\n```bash\ncd backend\npython -m app.main\n```")

    st.markdown("---")

    # 导航
    page = st.radio(
        "选择功能",
        [
            "📊 学习仪表盘",
            "📝 生成笔记",
            "📚 我的笔记",
            "📁 知识库管理",
            "🎯 出题练习",
            "🔍 知识问答",
            "📅 复习计划",
            "📋 错题本",
            "⚙️ 系统信息",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### 💡 提示")
    st.info("在 .env 中配置 DEEPSEEK_API_KEY 后才能使用 AI 功能")


# ========== 主区域标题 ==========
st.markdown('<p class="main-title">🧠 LearnLoop-AI</p>', unsafe_allow_html=True)
st.markdown("*AI 驱动的个性化学习助手 — Multi-Agent 系统 v0.4*")


# ===================================================================
# 📊 学习仪表盘（NEW in v0.4）
# ===================================================================
if page == "📊 学习仪表盘":
    st.header("📊 学习仪表盘")
    st.markdown("学习概览、待复习任务、SM-2 遗忘曲线进度")

    # 加载统计数据
    stats_resp = api_get("/schedule/stats")
    daily_resp = api_get("/schedule/daily")

    stats = {}
    daily_data = {}
    if stats_resp and stats_resp.status_code == 200:
        stats = stats_resp.json().get("data", {})
    if daily_resp and daily_resp.status_code == 200:
        daily_data = daily_resp.json().get("data", {})

    # --- 统计卡片 ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        streak = stats.get("streak_days", 0)
        st.metric("🔥 连续学习", f"{streak} 天")
    with col2:
        due = stats.get("due_count", 0)
        st.metric("📅 待复习", f"{due} 项", delta=f"{stats.get('overdue_count', 0)} 逾期" if stats.get("overdue_count", 0) > 0 else None)
    with col3:
        total_q = stats.get("total_quizzes", 0)
        st.metric("📝 总做题", f"{total_q} 次")
    with col4:
        mastery = stats.get("mastery_rate", 0)
        st.metric("📈 掌握率", f"{mastery}%")

    st.markdown("---")

    # --- 今日待复习 ---
    col_title, col_action = st.columns([3, 1])
    with col_title:
        st.subheader("📅 今日待复习任务")
    with col_action:
        if st.button("🔄 去复习页面", type="primary", use_container_width=True, key="goto_review_from_dash"):
            st.rerun()

    daily_tasks = daily_data.get("daily_tasks", [])
    if not daily_tasks:
        st.success("🎉 今天没有到期的复习任务！")
        if stats.get("total_kps", 0) == 0:
            st.info("💡 去生成一篇笔记或做一套题，系统会自动为你创建复习计划。")
            col_empty, _ = st.columns([1, 3])
            with col_empty:
                if st.button("🚀 去生成笔记", type="primary", use_container_width=True, key="goto_note_from_dash"):
                    st.rerun()
    else:
        for task in daily_tasks[:8]:
            priority = task.get("priority", "low")
            emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
            with st.container():
                st.markdown(
                    f"**{emoji} {task.get('knowledge_point', '未知')}** | "
                    f"⏱ {task.get('suggested_duration_min', 10)} 分钟 | "
                    f"{task.get('reason', '')}",
                )

        total_time = daily_data.get("total_estimated_time_min", 0)
        st.caption(f"预计总复习时间: {total_time} 分钟")
        enc = daily_data.get("encouragement", "")
        if enc:
            st.info(f"💬 {enc}")

    st.markdown("---")

    # --- SM-2 知识点进度 ---
    st.subheader("📊 知识点掌握分布")

    sm2_states_resp = api_get("/schedule/states")
    if sm2_states_resp and sm2_states_resp.status_code == 200:
        states = sm2_states_resp.json().get("data", [])
        if states:
            for s in states[:10]:
                kp = s.get("knowledge_point", "未知")
                ef = s.get("ef", 2.5)
                reps = s.get("repetitions", 0)
                interval = s.get("interval_days", 1)
                err_count = s.get("error_count", 0)
                next_review = (s.get("next_review_at") or "")[:10]

                # EF 值映射到进度条 (1.3 ~ 3.0 → 0% ~ 100%)
                progress = min(1.0, max(0.0, (ef - 1.3) / 1.7))

                col_bar, col_info = st.columns([3, 1])
                with col_bar:
                    st.progress(progress, text=f"{kp}")
                with col_info:
                    st.caption(f"EF:{ef:.1f} | 间隔:{interval}d | 错{err_count}次")
        else:
            st.info("📭 暂无 SM-2 知识点数据。生成笔记或做题后会自动创建。")

    # --- 快捷入口 ---
    st.markdown("---")
    st.subheader("⚡ 快捷操作")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📝 生成笔记", use_container_width=True, key="quick_note"):
            st.rerun()
    with col2:
        if st.button("🎯 出题练习", use_container_width=True, key="quick_quiz"):
            st.rerun()
    with col3:
        if st.button("📋 查看错题", use_container_width=True, key="quick_errors"):
            st.rerun()
    with col4:
        if st.button("🔍 知识问答", use_container_width=True, key="quick_rag"):
            st.rerun()


# ===================================================================
# 📝 生成笔记
# ===================================================================
elif page == "📝 生成笔记":
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
            resp = api_post("/notes/generate", {
                "topic": topic,
                "source_text": source_text,
                "style": style,
            })
            if resp and resp.status_code == 200:
                data = resp.json()
                note = data.get("data", {})

                # 入库状态提示
                if note.get("_persisted"):
                    st.success("✅ 笔记已保存到知识库")
                elif note.get("_save_error"):
                    st.warning(f"⚠️ 笔记已生成，但保存失败: {note['_save_error']}")

                st.markdown("---")
                st.markdown(f"## 📄 {note.get('title', topic)}")

                with st.container():
                    st.markdown(note.get("content_md", "无内容"))

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

                if note.get("summary"):
                    with st.expander("📝 一句话总结"):
                        st.info(note["summary"])

            elif resp:
                st.error(f"请求失败: {resp.status_code} - {resp.text}")


# ===================================================================
# 📚 我的笔记（增强：搜索 + 过滤）
# ===================================================================
elif page == "📚 我的笔记":

    # --- 笔记详情视图 ---
    if st.session_state.notes_page_view == "detail" and st.session_state.selected_note_id:
        note_id = st.session_state.selected_note_id

        if st.button("← 返回笔记列表"):
            st.session_state.notes_page_view = "list"
            st.session_state.selected_note_id = None
            st.rerun()

        resp = api_get(f"/notes/{note_id}")
        if resp and resp.status_code == 200:
            note = resp.json().get("data", {})

            st.header(f"📄 {note.get('title', '无标题')}")

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
            st.markdown(note.get("content_md", "无内容"))

            if note.get("summary"):
                st.markdown("---")
                with st.expander("📝 一句话总结"):
                    st.info(note["summary"])

            st.markdown("---")
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("🗑️ 删除此笔记", type="secondary"):
                    st.session_state.confirm_delete = note_id
                    st.rerun()

            if st.session_state.get("confirm_delete") == note_id:
                st.warning("确定要删除这篇笔记吗？此操作不可撤消。")
                col_yes, col_no = st.columns([1, 5])
                with col_yes:
                    if st.button("✅ 确认删除", type="primary"):
                        del_resp = api_get(f"/notes/{note_id}", timeout=10)  # won't work, need DELETE
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

        elif resp:
            st.error(f"笔记不存在 (HTTP {resp.status_code})")
            if st.button("← 返回列表"):
                st.session_state.notes_page_view = "list"
                st.session_state.selected_note_id = None
                st.rerun()

    # --- 笔记列表视图 ---
    else:
        st.header("📚 我的笔记")
        st.markdown("已保存的学习笔记，支持搜索和过滤")

        # 搜索 + 过滤栏
        col_search, col_filter, col_clear = st.columns([4, 2, 1])
        with col_search:
            search_query = st.text_input(
                "🔍 搜索笔记",
                value=st.session_state.notes_search_query,
                placeholder="输入关键词搜索标题和内容...",
                label_visibility="collapsed",
            )
            st.session_state.notes_search_query = search_query
        with col_filter:
            source_filter = st.selectbox(
                "来源",
                ["全部", "AI生成", "上传的"],
                index=["全部", "AI生成", "上传的"].index(st.session_state.notes_source_filter)
                if st.session_state.notes_source_filter in ["全部", "AI生成", "上传的"]
                else 0,
                label_visibility="collapsed",
            )
            st.session_state.notes_source_filter = source_filter
        with col_clear:
            if st.button("🔄 重置"):
                st.session_state.notes_search_query = ""
                st.session_state.notes_source_filter = "全部"
                st.session_state.notes_page_offset = 0
                st.rerun()

        # 构建 API 参数
        source_type_map = {"全部": None, "AI生成": "generated", "上传的": "uploaded"}
        api_source_type = source_type_map.get(source_filter)

        offset = st.session_state.notes_page_offset
        if search_query or api_source_type:
            resp = api_get("/notes/search", {
                "query": search_query,
                "source_type": api_source_type,
                "limit": 20,
                "offset": offset,
            })
        else:
            resp = api_get("/notes", {"limit": 20, "offset": offset})

        if resp and resp.status_code == 200:
            data = resp.json()
            notes = data.get("data", [])
            pagination = data.get("pagination", {})
            total = pagination.get("total", 0)

            st.caption(f"共 {total} 篇笔记" + (f"（搜索: {search_query}）" if search_query else ""))

            if not notes:
                st.markdown("---")
                if search_query or api_source_type:
                    st.info(f"📭 没有找到匹配的笔记")
                else:
                    st.info("📭 还没有笔记，去生成第一篇吧！")
                    col_empty, _ = st.columns([1, 3])
                    with col_empty:
                        if st.button("🚀 去生成笔记", type="primary", use_container_width=True):
                            st.rerun()

            for note in notes:
                with st.container():
                    st.markdown("---")
                    col_main, col_action = st.columns([8, 1])
                    with col_main:
                        note_title = note.get("title", "无标题")
                        note_summary = note.get("summary", "")
                        note_tags = note.get("tags", [])
                        note_date = (note.get("created_at") or "")[:10]
                        note_words = note.get("word_count", 0)
                        note_source = note.get("source_type", "")
                        source_label = "🤖 AI生成" if note_source == "generated" else "📤 上传"

                        st.markdown(f"### {note_title}")
                        if note_summary:
                            st.markdown(note_summary[:150] + ("..." if len(note_summary) > 150 else ""))

                        tag_html = " ".join([f'<span class="tag-badge">{t}</span>' for t in note_tags])
                        st.markdown(
                            f'{tag_html} <span class="meta-text">| {source_label} | 📅 {note_date} | 📝 {note_words} 字</span>',
                            unsafe_allow_html=True,
                        )

                    with col_action:
                        if st.button("📖 查看", key=f"view_{note['id']}"):
                            st.session_state.notes_page_view = "detail"
                            st.session_state.selected_note_id = note["id"]
                            st.rerun()

            # 分页
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


# ===================================================================
# 📁 知识库管理（NEW）
# ===================================================================
elif page == "📁 知识库管理":
    st.header("📁 知识库管理")
    st.markdown("上传学习文档到知识库，自动建立向量索引供 RAG 检索")

    # 统计卡片
    stats_resp = api_get("/rag/stats")
    if stats_resp and stats_resp.status_code == 200:
        stats = stats_resp.json().get("data", {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 总文档", stats.get("total_notes", 0))
        with col2:
            st.metric("🤖 AI生成", stats.get("generated_notes", 0))
        with col3:
            st.metric("📤 上传文档", stats.get("uploaded_notes", 0))
        with col4:
            st.metric("🧩 向量块", stats.get("total_chunks", 0))

    st.markdown("---")

    # 上传区域
    st.subheader("📤 上传文档")
    st.caption("支持 PDF、Markdown (.md)、纯文本 (.txt) 文件")

    col_upload, col_title = st.columns([2, 1])
    with col_upload:
        uploaded_file = st.file_uploader(
            "选择文件",
            type=["pdf", "md", "txt"],
            label_visibility="collapsed",
            key="kb_file_uploader",
        )
    with col_title:
        custom_title = st.text_input(
            "自定义标题（可选）",
            placeholder="留空则使用文件名",
            label_visibility="collapsed",
            key="kb_custom_title",
        )

    if uploaded_file:
        col_info, col_action = st.columns([3, 1])
        with col_info:
            st.markdown(f"**已选择:** {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        with col_action:
            if st.button("🚀 上传并入库", type="primary", use_container_width=True):
                with st.spinner("正在解析文件并建立索引..."):
                    try:
                        files_data = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        form_data = {}
                        if custom_title:
                            form_data["title"] = custom_title

                        resp = api_post("/rag/upload", json_data=form_data, files=files_data)
                        if resp and resp.status_code == 200:
                            result = resp.json().get("data", {})
                            st.success(f"✅ 文档 '{result.get('title', '')}' 已入库（{result.get('word_count', 0)} 字）")
                            st.cache_data.clear()
                            st.rerun()
                        elif resp:
                            st.error(f"上传失败: {resp.json().get('detail', resp.text)}")
                    except Exception as e:
                        st.error(f"上传异常: {str(e)}")

    st.markdown("---")

    # 已上传文档列表
    st.subheader("📋 已上传文档")

    offset = st.session_state.kb_page_offset
    resp = api_get("/rag/sources", {"limit": 20, "offset": offset})
    if resp and resp.status_code == 200:
        data = resp.json()
        sources = data.get("data", [])
        pagination = data.get("pagination", {})
        total = pagination.get("total", 0)

        if not sources:
            st.info("📭 还没有上传文档，上传你的第一个学习资料吧！")

        for source in sources:
            with st.container():
                st.markdown("---")
                col_main, col_actions = st.columns([7, 2])
                with col_main:
                    st.markdown(f"#### 📄 {source.get('title', '无标题')}")
                    src_date = (source.get("created_at") or "")[:10]
                    st.caption(f"📝 {source.get('word_count', 0)} 字 | 📅 {src_date}")
                with col_actions:
                    col_view, col_del = st.columns(2)
                    with col_view:
                        if st.button("📖 查看", key=f"kb_view_{source['id']}"):
                            st.session_state.notes_page_view = "detail"
                            st.session_state.selected_note_id = source["id"]
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ 删除", key=f"kb_del_{source['id']}"):
                            try:
                                del_resp = requests.delete(f"{API_BASE}/rag/sources/{source['id']}", timeout=10)
                                if del_resp.status_code == 200:
                                    st.success("已删除")
                                    st.rerun()
                                else:
                                    st.error(f"删除失败: {del_resp.status_code}")
                            except Exception as e:
                                st.error(f"删除失败: {str(e)}")

        # 分页
        if total > 20:
            st.markdown("---")
            col_prev, _, col_next = st.columns([1, 3, 1])
            with col_prev:
                if offset > 0:
                    if st.button("← 上一页", key="kb_prev"):
                        st.session_state.kb_page_offset = max(0, offset - 20)
                        st.rerun()
            with col_next:
                if offset + 20 < total:
                    if st.button("下一页 →", key="kb_next"):
                        st.session_state.kb_page_offset = offset + 20
                        st.rerun()


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
            resp = api_post("/quiz/generate", {
                "topic": quiz_topic,
                "types": types,
                "difficulty": difficulty,
                "count": count,
            })
            if resp and resp.status_code == 200:
                data = resp.json()
                quiz = data.get("data", {})
                questions = quiz.get("questions", [])

                st.markdown("---")
                st.markdown(f"## 🎯 {quiz.get('topic', quiz_topic)}")
                st.caption(f"Quiz ID: {quiz.get('quiz_id', '')}")

                for i, q in enumerate(questions):
                    with st.container():
                        st.markdown(f"### 第 {i+1} 题")
                        st.markdown(f"**{q.get('question', '')}**")
                        st.caption(f"类型: {q.get('type')} | 难度: {q.get('difficulty')}")

                        if q.get("type") == "choice" and q.get("options"):
                            st.radio(
                                f"q_{q['id']}",
                                [f"{o['key']}. {o['text']}" for o in q["options"]],
                                key=f"answer_{q['id']}",
                                index=None,
                            )
                            with st.expander("查看答案"):
                                st.success(f"正确答案: **{q.get('answer')}**")
                                if q.get("explanation"):
                                    st.info(q["explanation"])

                        st.markdown("---")
            elif resp:
                st.error(f"请求失败: {resp.status_code}")


# ===================================================================
# 🔍 知识问答
# ===================================================================
elif page == "🔍 知识问答":
    st.header("🔍 知识问答")
    st.markdown("向你的知识库提问，AI 会基于你的笔记来回答（支持 Multi-Query + Rerank）")

    query = st.text_input("你的问题", placeholder="例如：Verification 和 Validation 的区别是什么？")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        top_k = st.slider("检索数量", 1, 20, 5)
    with col3:
        st.caption("Multi-Query + Rerank 自动启用")

    if st.button("🔍 提问", type="primary", disabled=not query):
        with st.spinner("正在检索知识库..."):
            resp = api_post("/rag/ask", {"query": query, "top_k": top_k})
            if resp and resp.status_code == 200:
                data = resp.json()
                rag_data = data.get("data", {})
                meta = data.get("metadata", {})

                st.markdown("---")
                st.markdown("### 📖 回答")
                st.markdown(rag_data.get("answer", "无法获取回答"))

                # 检索增强信息
                expansions = meta.get("query_expansions", 0)
                reranked = meta.get("reranked", False)
                if expansions or reranked:
                    enhancements = []
                    if expansions:
                        enhancements.append(f"🔀 查询扩展: +{expansions} 变体")
                    if reranked:
                        enhancements.append("📊 Rerank 已启用")
                    st.caption(" | ".join(enhancements))

                sources = rag_data.get("sources", [])
                if sources:
                    with st.expander(f"📚 参考来源 ({len(sources)} 条)"):
                        for s in sources:
                            st.markdown(f"**{s.get('title', '未知')}** (相关度: {s.get('score', 0):.2f})")
                            st.markdown(f"> {s.get('excerpt', '')[:200]}...")
                            st.markdown("---")

                st.caption(
                    f"检索到 {meta.get('retrieved_chunks', 0)} 个文档块 | "
                    f"置信度: {rag_data.get('confidence', 0)}"
                )
            elif resp:
                st.error(f"请求失败: {resp.status_code}")


# ===================================================================
# 📅 复习计划（NEW in v0.4）
# ===================================================================
elif page == "📅 复习计划":
    st.header("📅 复习计划")
    st.markdown("基于 SM-2 遗忘曲线的智能复习，对知识点评分后系统自动计算下次复习时间")

    # 加载 SM-2 状态
    states_resp = api_get("/schedule/states")
    if states_resp and states_resp.status_code == 200:
        all_states = states_resp.json().get("data", [])
    else:
        all_states = []

    # 加载每日任务
    daily_resp = api_get("/schedule/daily")
    if daily_resp and daily_resp.status_code == 200:
        daily_data = daily_resp.json().get("data", {})
    else:
        daily_data = {}

    # 分离到期和未到期的
    due_states = [s for s in all_states if s.get("error_count", 0) > 0 or s.get("repetitions", 0) == 0]
    not_due = [s for s in all_states if s not in due_states]

    # --- session state 管理 ---
    if "review_scores" not in st.session_state:
        st.session_state.review_scores = {}  # {kp: score}
    if "review_submitted" not in st.session_state:
        st.session_state.review_submitted = {}  # {kp: result}

    # --- 今日待复习 ---
    st.subheader("📌 待复习知识点")
    daily_tasks = daily_data.get("daily_tasks", [])

    if not all_states:
        st.info("📭 暂无知识点数据。去生成笔记或做题，系统会自动创建复习计划！")
        col_empty, _ = st.columns([1, 3])
        with col_empty:
            if st.button("🚀 去生成笔记", type="primary", use_container_width=True, key="goto_note_from_review"):
                st.rerun()
    else:
        # 优先展示有错题的知识点
        error_kps = [s for s in all_states if s.get("error_count", 0) > 0]
        fresh_kps = [s for s in all_states if s.get("error_count", 0) == 0]

        tab1, tab2, tab3 = st.tabs(["🔴 需重点复习", "🟢 正常复习", "📋 全部知识点"])

        with tab1:
            if not error_kps:
                st.success("🎉 没有需要重点复习的知识点！")
            for s in error_kps:
                kp = s.get("knowledge_point", "未知")
                ef = s.get("ef", 2.5)
                interval = s.get("interval_days", 1)
                reps = s.get("repetitions", 0)
                err_count = s.get("error_count", 0)
                next_review = (s.get("next_review_at") or "")[:10]

                with st.container():
                    st.markdown("---")
                    st.markdown(f"### 🔴 {kp}")
                    col_info, col_score = st.columns([2, 1])
                    with col_info:
                        st.markdown(f"EF: **{ef:.2f}** | 间隔: **{interval}** 天 | 已复习: **{reps}** 次 | 错题: **{err_count}** 次")
                        st.caption(f"下次复习: {next_review}")
                    with col_score:
                        current_score = st.session_state.review_scores.get(kp)
                        score_label = f"当前评分: {current_score}" if current_score is not None else "选择评分"
                        score = st.select_slider(
                            score_label,
                            options=[0, 1, 2, 3, 4, 5],
                            value=current_score,
                            format_func=lambda x: {0: "0-完全忘记", 1: "1-几乎忘记", 2: "2-勉强回忆", 3: "3-正确回忆", 4: "4-较轻松", 5: "5-非常完美"}[x],
                            key=f"score_{kp}",
                        )
                        st.session_state.review_scores[kp] = score

                    # 评分按钮
                    if st.button(f"✅ 提交评分: {kp}", type="primary", key=f"submit_review_{kp}"):
                        score_val = st.session_state.review_scores.get(kp, 3)
                        review_resp = api_post("/schedule/review", {
                            "knowledge_point": kp,
                            "score": score_val,
                            "user_id": "default",
                        })
                        if review_resp and review_resp.status_code == 200:
                            result_data = review_resp.json().get("data", {})
                            st.session_state.review_submitted[kp] = result_data
                            st.rerun()
                        else:
                            st.error("评分提交失败，请检查后端连接")

                    # 显示评分结果
                    submitted = st.session_state.review_submitted.get(kp)
                    if submitted:
                        sm2_result = submitted.get("sm2_result", {})
                        st.success(
                            f"✅ 评分 {submitted.get('last_score', '?')} → "
                            f"下次复习: **{submitted.get('next_review_at', '?')[:10]}** "
                            f"(间隔 {submitted.get('interval_days', '?')} 天, EF={submitted.get('ef', '?')})"
                        )
                        if sm2_result:
                            old_ef = s.get("ef", 2.5)
                            new_ef = sm2_result.get("ef", old_ef)
                            ef_delta = new_ef - old_ef
                            if ef_delta > 0:
                                st.caption(f"📈 EF 提升: {old_ef:.2f} → {new_ef:.2f} (+{ef_delta:.2f})")
                            elif ef_delta < 0:
                                st.caption(f"📉 EF 下降: {old_ef:.2f} → {new_ef:.2f} ({ef_delta:.2f})")

        with tab2:
            if not fresh_kps:
                st.info("暂无正常复习的知识点")
            for s in fresh_kps[:10]:
                kp = s.get("knowledge_point", "未知")
                ef = s.get("ef", 2.5)
                interval = s.get("interval_days", 1)
                reps = s.get("repetitions", 0)
                next_review = (s.get("next_review_at") or "")[:10]

                with st.container():
                    st.markdown("---")
                    st.markdown(f"### 🟢 {kp}")
                    col_info, col_score = st.columns([2, 1])
                    with col_info:
                        st.markdown(f"EF: **{ef:.2f}** | 间隔: **{interval}** 天 | 已复习: **{reps}** 次")
                        st.caption(f"下次复习: {next_review}")
                    with col_score:
                        score = st.select_slider(
                            "回忆程度",
                            options=[0, 1, 2, 3, 4, 5],
                            format_func=lambda x: {0: "0-完全忘记", 1: "1-几乎忘记", 2: "2-勉强回忆", 3: "3-正确回忆", 4: "4-较轻松", 5: "5-非常完美"}[x],
                            key=f"score_fresh_{kp}",
                        )
                        st.session_state.review_scores[kp] = score

                    if st.button(f"✅ 提交评分", type="primary", key=f"submit_fresh_{kp}"):
                        score_val = st.session_state.review_scores.get(kp, 3)
                        review_resp = api_post("/schedule/review", {
                            "knowledge_point": kp,
                            "score": score_val,
                            "user_id": "default",
                        })
                        if review_resp and review_resp.status_code == 200:
                            result_data = review_resp.json().get("data", {})
                            st.session_state.review_submitted[kp] = result_data
                            st.rerun()
                        else:
                            st.error("评分提交失败")

                    submitted = st.session_state.review_submitted.get(kp)
                    if submitted:
                        st.success(
                            f"✅ 下次复习: **{submitted.get('next_review_at', '?')[:10]}** "
                            f"(间隔 {submitted.get('interval_days', '?')} 天)"
                        )

        with tab3:
            if not all_states:
                st.info("暂无知识点")
            else:
                # 表格展示所有知识点
                st.caption(f"共 {len(all_states)} 个知识点")
                for s in all_states:
                    kp = s.get("knowledge_point", "未知")
                    ef = s.get("ef", 2.5)
                    reps = s.get("repetitions", 0)
                    interval = s.get("interval_days", 1)
                    err = s.get("error_count", 0)
                    nr = (s.get("next_review_at") or "")[:10]
                    progress = min(1.0, max(0.0, (ef - 1.3) / 1.7))

                    st.markdown("---")
                    col_name, col_bar, col_val = st.columns([2, 3, 1])
                    with col_name:
                        st.markdown(f"**{kp}**")
                    with col_bar:
                        st.progress(progress)
                    with col_val:
                        st.caption(f"EF:{ef:.1f} | 错{err}")


# ===================================================================
# 📋 错题本（NEW）
# ===================================================================
elif page == "📋 错题本":
    st.header("📋 错题本")
    st.markdown("追踪错题，发现薄弱点，针对性复习")

    # 加载错题数据
    resp = api_get("/quiz/errors/list", {"limit": 100})
    if resp and resp.status_code == 200:
        data = resp.json()
        errors = data.get("data", [])
        stats = data.get("stats", {})
        total = stats.get("total", 0)
        resolved = stats.get("resolved", 0)
        unresolved = stats.get("unresolved", 0)

        # 统计卡片
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 总错题", total)
        with col2:
            st.metric("❌ 未解决", unresolved)
        with col3:
            st.metric("✅ 已掌握", resolved)

        if not errors:
            st.markdown("---")
            st.success("🎉 做得很棒！目前没有错题记录。")
            st.markdown("去 [🎯 出题练习] 页面做题，错题会自动收录到这里。")

        else:
            # 按知识点分组
            from collections import defaultdict
            by_kp = defaultdict(list)
            for e in errors:
                kp = e.get("knowledge_point", "未分类")
                by_kp[kp].append(e)

            st.markdown("---")

            # 过滤选项
            show_filter = st.radio(
                "显示",
                ["全部", "未解决", "已掌握"],
                horizontal=True,
                key="error_filter",
            )

            for kp, items in by_kp.items():
                filtered = items
                if show_filter == "未解决":
                    filtered = [e for e in items if not e.get("is_resolved")]
                elif show_filter == "已掌握":
                    filtered = [e for e in items if e.get("is_resolved")]

                if not filtered:
                    continue

                unresolved_count = sum(1 for e in items if not e.get("is_resolved"))
                with st.expander(
                    f"📌 {kp}（{len(items)} 题，{unresolved_count} 未解决）",
                    expanded=(unresolved_count > 0),
                ):
                    for e in filtered:
                        is_resolved = e.get("is_resolved", False)
                        error_class = "error-item resolved" if is_resolved else "error-item"
                        status_badge = "✅ 已掌握" if is_resolved else "❌ 待复习"

                        st.markdown(f"""
                        <div class="{error_class}">
                            <strong>{status_badge}</strong> | 类型: {e.get('error_type', '未知')} | 复习: {e.get('reviewed_count', 0)} 次<br/>
                            <span style="color:#ef4444;">✗ 你的答案: {e.get('user_answer', '')}</span><br/>
                            <span style="color:#22c55e;">✓ 正确答案: {e.get('correct_answer', '')}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        if not is_resolved:
                            if st.button("✅ 我已掌握", key=f"resolve_{e['id']}"):
                                try:
                                    put_resp = requests.put(
                                        f"{API_BASE}/quiz/errors/{e['id']}/resolve",
                                        json={"is_resolved": True},
                                        timeout=10,
                                    )
                                    if put_resp.status_code == 200:
                                        st.success("已标记为掌握！")
                                        st.rerun()
                                except Exception as ex:
                                    st.error(f"操作失败: {ex}")


# ===================================================================
# 📊 系统信息
# ===================================================================
elif page == "⚙️ 系统信息":
    st.header("⚙️ 系统信息")

    backend = check_backend()
    if backend:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("LLM Providers", ", ".join(backend.get("llm_providers", [])) or "无")
        with col2:
            st.metric("Agents", backend.get("agents", 0))

        # 知识库统计
        stats_resp = api_get("/rag/stats")
        if stats_resp and stats_resp.status_code == 200:
            stats = stats_resp.json().get("data", {})
            st.markdown("---")
            st.subheader("📊 知识库统计")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总笔记", stats.get("total_notes", 0))
            with col2:
                st.metric("AI生成", stats.get("generated_notes", 0))
            with col3:
                st.metric("上传文档", stats.get("uploaded_notes", 0))
            with col4:
                st.metric("向量块", stats.get("total_chunks", 0))

    st.markdown("---")
    st.markdown("### 📂 项目文件结构")
    st.code("""
LearnLoop-AI/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # API 路由（notes, quiz, rag, schedule）
│   │   ├── core/           # 核心（Orchestrator, Config, Agent基类）
│   │   ├── agents/         # 6个专业Agent
│   │   ├── services/       # 业务服务层（NoteService, FileService）
│   │   ├── llm/            # LLM抽象层（DeepSeek, OpenAI）
│   │   ├── db/             # 数据库（SQLAlchemy + ChromaDB）
│   │   └── utils/          # 工具（Chunking, QueryExpansion, Reranker）
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── streamlit_app.py    # 前端 7 页面
├── data/                    # 数据目录
├── .env.example
└── README.md
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

    st.markdown("---")
    st.markdown("### 🔧 v0.4 新增功能")
    st.markdown("""
    - ✅ SM-2 遗忘曲线前端联动（自动创建初始状态 + 复习评分更新）
    - ✅ 学习仪表盘（统计卡片 + 待复习任务 + 知识点进度）
    - ✅ 复习计划页面（评分 0-5 + SM-2 间隔计算 + 下次复习日期展示）
    - ✅ 易混概念对自动检测（错题知识点两两组合创建混淆对）
    - ✅ Memory API（薄弱点分析 + 混淆对列表 + 学习报告）
    - ✅ Schedule API 接入真实数据库（每日任务 / 复习评分 / 统计数据）
    - ✅ SM-2 状态自动创建（笔记生成 + 错题入库时联动）
    """)
    st.markdown("### 🔧 v0.3 新增功能")
    st.markdown("""
    - ✅ 文件上传入库（PDF/MD/TXT 解析 → Chunk → Embed → ChromaDB）
    - ✅ Multi-Query 查询扩展（自动生成多个检索角度）
    - ✅ Rerank 重排序（LLM 相关性打分精排）
    - ✅ 知识库管理页面（上传 + 列表 + 删除）
    - ✅ 错题本页面（按知识点分组 + 已掌握标记）
    - ✅ 笔记搜索/过滤（标题内容模糊搜索 + 来源过滤）
    - ✅ Quiz 自动入库 + 错题自动记录
    """)
