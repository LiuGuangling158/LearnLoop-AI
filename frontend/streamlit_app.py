"""
AI Study Agent - Streamlit MVP 前端 v0.4
纯 Python 写的企业知识训练界面，10 页面
"""
import sys
from pathlib import Path
from html import escape

# 添加 backend 到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import streamlit as st
import requests

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
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None
if "kb_confirm_batch_delete" not in st.session_state:
    st.session_state.kb_confirm_batch_delete = False
if "kb_confirm_clear_all" not in st.session_state:
    st.session_state.kb_confirm_clear_all = False

# ========== 样式 ==========
st.markdown("""
<style>
    :root {
        --ink: #172033;
        --muted: #5b6475;
        --line: rgba(35, 48, 75, 0.12);
        --glass: rgba(255, 255, 255, 0.68);
        --blue: #2563eb;
        --cyan: #0891b2;
        --green: #16a34a;
        --amber: #d97706;
        --rose: #e11d48;
    }
    .stApp {
        color: var(--ink);
        background:
            radial-gradient(circle at 12% 10%, rgba(37, 99, 235, 0.14), transparent 26%),
            radial-gradient(circle at 82% 4%, rgba(8, 145, 178, 0.12), transparent 24%),
            linear-gradient(135deg, #f6f9ff 0%, #edf7f4 46%, #fff8ee 100%);
    }
    .block-container {
        padding-top: 1.5rem;
        max-width: 1320px;
    }
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(18px);
        border-right: 1px solid rgba(255, 255, 255, 0.72);
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] label {
        color: #263246;
    }
    h1, h2, h3, h4 {
        letter-spacing: 0;
    }
    div[data-testid="stMetric"] {
        background: transparent;
        border-left: 3px solid rgba(37, 99, 235, 0.55);
        padding-left: 0.85rem;
    }
    div[data-testid="stMetric"] label {
        color: var(--muted);
    }
    .hero-glass {
        padding: 1.2rem 1.35rem;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.72);
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.74), rgba(255, 255, 255, 0.42));
        box-shadow: 0 18px 42px rgba(31, 41, 55, 0.10);
        backdrop-filter: blur(18px);
        margin-bottom: 1rem;
    }
    .main-title {
        font-size: clamp(2.0rem, 4vw, 3.2rem);
        font-weight: 760;
        color: #14213d;
        line-height: 1.08;
        margin: 0 0 0.45rem 0;
    }
    .hero-copy {
        color: #435063;
        font-size: 1.02rem;
        margin: 0;
    }
    .hero-ribbon {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    .ribbon-dot {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.28rem 0.58rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.72);
        color: #31405a;
        font-size: 0.84rem;
    }
    .section-glass {
        margin: 1rem 0;
        padding: 1rem 1.1rem;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.7);
        background: rgba(255, 255, 255, 0.50);
        backdrop-filter: blur(14px);
    }
    .section-title {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin: 0 0 0.7rem 0;
        color: #1f2a44;
        font-size: 1.08rem;
        font-weight: 700;
    }
    .metric-band {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.85rem;
        padding: 0.85rem 0;
        border-top: 1px solid var(--line);
        border-bottom: 1px solid var(--line);
    }
    .metric-item {
        min-height: 78px;
        padding: 0.4rem 0.75rem;
        border-left: 4px solid var(--accent);
        background: linear-gradient(90deg, var(--wash), rgba(255, 255, 255, 0.26));
    }
    .metric-label {
        color: var(--muted);
        font-size: 0.84rem;
        margin-bottom: 0.2rem;
    }
    .metric-value {
        color: #15213a;
        font-size: 1.85rem;
        line-height: 1.05;
        font-weight: 760;
    }
    .metric-note {
        color: #64748b;
        font-size: 0.78rem;
        margin-top: 0.22rem;
    }
    .flow-strip {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 0.45rem;
        margin: 0.4rem 0 0.1rem 0;
    }
    .flow-step {
        padding: 0.72rem 0.75rem;
        border-radius: 8px;
        color: #1f2a44;
        background: linear-gradient(135deg, rgba(255,255,255,0.64), var(--wash));
        border: 1px solid rgba(255, 255, 255, 0.72);
        min-height: 74px;
    }
    .flow-step strong {
        display: block;
        font-size: 0.92rem;
    }
    .flow-step span {
        color: var(--muted);
        font-size: 0.78rem;
    }
    .scenario-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 0.7rem;
    }
    .scenario-row {
        border-left: 4px solid var(--accent);
        padding: 0.7rem 0.8rem;
        background: linear-gradient(90deg, var(--wash), rgba(255,255,255,0.28));
        border-radius: 8px;
    }
    .scenario-row strong {
        display: block;
        color: #1e293b;
        margin-bottom: 0.25rem;
    }
    .scenario-row span {
        display: block;
        color: #4b5563;
        font-size: 0.84rem;
        line-height: 1.45;
    }
    .glass-list-row {
        padding: 0.85rem 0.2rem 0.85rem 0.8rem;
        border-left: 3px solid var(--accent, #2563eb);
        border-bottom: 1px solid var(--line);
        background: linear-gradient(90deg, var(--wash, rgba(37,99,235,0.08)), rgba(255,255,255,0.18));
    }
    .tag-badge, .tag-chip {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 0.25rem;
        background: rgba(37, 99, 235, 0.10);
        color: #1d4ed8;
        font-size: 0.8rem;
        margin-right: 0.3rem;
    }
    .meta-text {
        color: #9ca3af;
        font-size: 0.85rem;
    }
    .error-row {
        padding: 0.85rem 0.9rem;
        border-left: 4px solid #e11d48;
        border-bottom: 1px solid rgba(225, 29, 72, 0.16);
        background: linear-gradient(90deg, rgba(225, 29, 72, 0.10), rgba(255, 255, 255, 0.25));
        margin-bottom: 0.55rem;
    }
    .error-row.resolved {
        border-left-color: #16a34a;
        background: linear-gradient(90deg, rgba(22, 163, 74, 0.10), rgba(255, 255, 255, 0.25));
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
    """封装 GET 请求，统一错误处理。自动过滤 None 值参数"""
    try:
        if params:
            params = {k: v for k, v in params.items() if v is not None}
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


ENTERPRISE_SCENARIOS = [
    {
        "name": "QA/测试训练",
        "desc": "测试规范、缺陷流程、ISTQB 和自动化实践转成训练题与复习任务",
        "color": "#2563eb",
        "wash": "rgba(37,99,235,0.10)",
    },
    {
        "name": "客服/售后培训",
        "desc": "FAQ、工单案例和 SOP 转成话术训练，减少政策误答和质检扣分",
        "color": "#0891b2",
        "wash": "rgba(8,145,178,0.10)",
    },
    {
        "name": "合规制度培训",
        "desc": "制度条款、审计案例和监管问答形成可追踪的掌握度记录",
        "color": "#d97706",
        "wash": "rgba(217,119,6,0.12)",
    },
    {
        "name": "研发新人入职",
        "desc": "架构文档、部署手册和事故复盘沉淀为问答、测验和辅导建议",
        "color": "#16a34a",
        "wash": "rgba(22,163,74,0.10)",
    },
    {
        "name": "销售/产品赋能",
        "desc": "产品白皮书、竞品对比和方案材料转成异议处理训练",
        "color": "#e11d48",
        "wash": "rgba(225,29,72,0.10)",
    },
]

NAV_PAGES = [
    "📊 学习仪表盘",
    "📝 生成笔记",
    "📚 我的笔记",
    "📁 知识库管理",
    "🎯 出题练习",
    "🔍 知识问答",
    "📅 复习计划",
    "📋 记忆中心",
    "🏢 企业蓝图",
    "⚙️ 系统信息",
]


def render_hero(title: str, subtitle: str, chips: list[str] = None):
    """渲染毛玻璃页头。"""
    chips = chips or []
    chip_html = "".join(
        f'<span class="ribbon-dot">{escape(chip)}</span>' for chip in chips
    )
    st.markdown(
        f"""
        <div class="hero-glass">
            <p class="main-title">{escape(title)}</p>
            <p class="hero-copy">{escape(subtitle)}</p>
            <div class="hero-ribbon">{chip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(title: str, body_html: str):
    """渲染玻璃分区，保持页面轻量通透。"""
    st.markdown(
        f"""
        <div class="section-glass">
            <div class="section-title">{escape(title)}</div>
            {body_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_band(metrics: list[dict]):
    """渲染横向指标带。"""
    colors = ["#2563eb", "#0891b2", "#16a34a", "#d97706", "#e11d48"]
    items = []
    for i, metric in enumerate(metrics):
        color = metric.get("color", colors[i % len(colors)])
        wash = metric.get("wash", f"{color}18")
        note = metric.get("note", "")
        items.append(
            f"""
            <div class="metric-item" style="--accent:{color}; --wash:{wash};">
                <div class="metric-label">{escape(str(metric.get("label", "")))}</div>
                <div class="metric-value">{escape(str(metric.get("value", "")))}</div>
                <div class="metric-note">{escape(str(note))}</div>
            </div>
            """
        )
    st.markdown(f'<div class="metric-band">{"".join(items)}</div>', unsafe_allow_html=True)


def render_learning_flow():
    steps = [
        ("资料导入", "PDF/MD/TXT"),
        ("结构化笔记", "Note Agent"),
        ("岗位训练", "Quiz Agent"),
        ("自动批改", "Grading Agent"),
        ("薄弱点沉淀", "Memory Agent"),
        ("间隔复习", "SM-2 Scheduler"),
    ]
    colors = ["#2563eb", "#0891b2", "#16a34a", "#d97706", "#e11d48", "#7c3aed"]
    html = []
    for i, (name, desc) in enumerate(steps):
        html.append(
            f"""
            <div class="flow-step" style="--wash:{colors[i]}18;">
                <strong>{escape(name)}</strong>
                <span>{escape(desc)}</span>
            </div>
            """
        )
    render_section("企业学习闭环", f'<div class="flow-strip">{"".join(html)}</div>')


def render_scenario_matrix():
    rows = []
    for item in ENTERPRISE_SCENARIOS:
        rows.append(
            f"""
            <div class="scenario-row" style="--accent:{item["color"]}; --wash:{item["wash"]};">
                <strong>{escape(item["name"])}</strong>
                <span>{escape(item["desc"])}</span>
            </div>
            """
        )
    render_section("企业级使用场景", f'<div class="scenario-grid">{"".join(rows)}</div>')


def render_list_row(title: str, meta: str = "", color: str = "#2563eb", wash: str = "rgba(37,99,235,0.08)"):
    st.markdown(
        f"""
        <div class="glass-list-row" style="--accent:{color}; --wash:{wash};">
            <strong>{escape(title)}</strong><br/>
            <span class="meta-text">{escape(meta)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def navigate_to(page_name: str):
    """在下一次 rerun 前切换侧边栏页面。"""
    if page_name in NAV_PAGES:
        st.session_state.pending_nav_page = page_name
    st.rerun()


if "nav_page" not in st.session_state:
    st.session_state.nav_page = NAV_PAGES[0]
if st.session_state.get("pending_nav_page") in NAV_PAGES:
    st.session_state.nav_page = st.session_state.pop("pending_nav_page")


# ========== 侧边栏 ==========
with st.sidebar:
    st.markdown("## 🧠 LearnLoop-AI")
    st.markdown("企业知识训练平台 · v0.4.0")
    st.caption("学 → 练 → 测 → 记 → 复")
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
        NAV_PAGES,
        key="nav_page",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### 企业场景")
    st.caption("QA 训练 · 客服培训 · 合规认证 · 研发入职 · 销售赋能")
    st.markdown("### 💡 提示")
    st.info("在 .env 中配置 DEEPSEEK_API_KEY 后才能使用 AI 功能")


# ========== 主区域标题 ==========
render_hero(
    "LearnLoop-AI",
    "AI 驱动的企业知识训练平台，用 Multi-Agent 把资料变成可问答、可练习、可追踪、可复习的能力闭环。",
    ["Multi-Agent", "RAG 知识库", "自动出题", "智能批改", "SM-2 复习"],
)


# ===================================================================
# 📊 学习仪表盘（NEW in v0.4）
# ===================================================================
if page == "📊 学习仪表盘":
    st.header("📊 企业学习运营仪表盘")
    st.markdown("围绕知识资产、岗位训练、测评反馈和复习节奏追踪组织能力。")

    # 加载统计数据
    stats_resp = api_get("/schedule/stats")
    daily_resp = api_get("/schedule/daily")

    stats = {}
    daily_data = {}
    if stats_resp and stats_resp.status_code == 200:
        stats = stats_resp.json().get("data", {})
    if daily_resp and daily_resp.status_code == 200:
        daily_data = daily_resp.json().get("data", {})

    # --- 运营指标带 ---
    streak = stats.get("streak_days", 0)
    due = stats.get("due_count", 0)
    overdue = stats.get("overdue_count", 0)
    total_q = stats.get("total_quizzes", 0)
    mastery = stats.get("mastery_rate", 0)
    total_kps = stats.get("total_kps", 0)
    render_metric_band([
        {"label": "连续学习", "value": f"{streak} 天", "note": "个人/团队活跃节奏", "color": "#2563eb", "wash": "rgba(37,99,235,0.10)"},
        {"label": "待复习知识点", "value": f"{due} 项", "note": f"{overdue} 项逾期", "color": "#d97706", "wash": "rgba(217,119,6,0.12)"},
        {"label": "测验提交", "value": f"{total_q} 次", "note": "训练闭环样本", "color": "#0891b2", "wash": "rgba(8,145,178,0.10)"},
        {"label": "掌握率", "value": f"{mastery}%", "note": "基于错题解决情况", "color": "#16a34a", "wash": "rgba(22,163,74,0.10)"},
        {"label": "知识点资产", "value": f"{total_kps} 个", "note": "SM-2 跟踪对象", "color": "#e11d48", "wash": "rgba(225,29,72,0.10)"},
    ])

    st.markdown("---")
    render_learning_flow()
    render_scenario_matrix()
    st.markdown("---")

    # --- 今日待复习 ---
    col_title, col_action = st.columns([3, 1])
    with col_title:
        st.subheader("📅 今日待复习任务")
    with col_action:
        if st.button("🔄 去复习页面", type="primary", use_container_width=True, key="goto_review_from_dash"):
            navigate_to("📅 复习计划")

    daily_tasks = daily_data.get("daily_tasks", [])
    if not daily_tasks:
        st.success("🎉 今天没有到期的复习任务！")
        if stats.get("total_kps", 0) == 0:
            st.info("💡 去生成一篇笔记或做一套题，系统会自动为你创建复习计划。")
            col_empty, _ = st.columns([1, 3])
            with col_empty:
                if st.button("🚀 去生成笔记", type="primary", use_container_width=True, key="goto_note_from_dash"):
                    navigate_to("📝 生成笔记")
    else:
        for task in daily_tasks[:8]:
            priority = task.get("priority", "low")
            color = {"high": "#e11d48", "medium": "#d97706", "low": "#16a34a"}.get(priority, "#64748b")
            wash = {"high": "rgba(225,29,72,0.10)", "medium": "rgba(217,119,6,0.12)", "low": "rgba(22,163,74,0.10)"}.get(priority, "rgba(100,116,139,0.10)")
            with st.container():
                render_list_row(
                    task.get("knowledge_point", "未知"),
                    f"优先级: {priority} | {task.get('suggested_duration_min', 10)} 分钟 | {task.get('reason', '')}",
                    color=color,
                    wash=wash,
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
            navigate_to("📝 生成笔记")
    with col2:
        if st.button("🎯 出题练习", use_container_width=True, key="quick_quiz"):
            navigate_to("🎯 出题练习")
    with col3:
        if st.button("📋 查看错题", use_container_width=True, key="quick_errors"):
            navigate_to("📋 记忆中心")
    with col4:
        if st.button("🔍 知识问答", use_container_width=True, key="quick_rag"):
            navigate_to("🔍 知识问答")


# ===================================================================
# 📝 生成笔记
# ===================================================================
elif page == "📝 生成笔记":
    st.header("📝 生成岗位知识笔记")
    st.markdown("把企业资料、培训主题或岗位 SOP 转成结构化 Markdown，并自动进入知识库和复习体系。")

    col0, col1, col2 = st.columns([1.4, 3, 1])
    with col0:
        scenario = st.selectbox(
            "企业场景",
            ["通用学习", "QA/测试训练", "客服/售后培训", "合规制度培训", "研发新人入职", "销售/产品赋能"],
        )
    with col1:
        topic = st.text_input("学习主题", placeholder="例如：软件测试方法、退款政策、代码评审规范...")
    with col2:
        style = st.selectbox("笔记风格", ["detailed", "summary", "mindmap"])

    source_text = st.text_area(
        "补充内容（可选）",
        placeholder=f"粘贴 {scenario} 相关制度、SOP、课件、FAQ 或项目复盘内容...",
        height=150,
    )

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

                tags = note.get("tags", [])
                render_metric_band([
                    {"label": "章节数", "value": note.get("sections_count", 0), "note": "结构化学习单元", "color": "#2563eb", "wash": "rgba(37,99,235,0.10)"},
                    {"label": "企业场景", "value": scenario, "note": "用于岗位化训练", "color": "#0891b2", "wash": "rgba(8,145,178,0.10)"},
                    {"label": "耗时", "value": f"{data.get('metadata', {}).get('elapsed_ms', 0)}ms", "note": "Agent 生成链路", "color": "#16a34a", "wash": "rgba(22,163,74,0.10)"},
                ])
                if tags:
                    st.markdown(f"**标签:** {' '.join(['`' + str(t) + '`' for t in tags])}")

                col4, _ = st.columns([1, 4])
                with col4:
                    if note.get("_persisted"):
                        if st.button("📚 查看我的笔记", key="goto_notes_from_gen"):
                            st.session_state.notes_page_view = "list"
                            navigate_to("📚 我的笔记")

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
                        tag_html = " ".join([f'<span class="tag-badge">{escape(str(t))}</span>' for t in tags])
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
            st.text_input(
                "🔍 搜索笔记",
                key="notes_search_query",
                placeholder="输入关键词搜索标题和内容...",
                label_visibility="collapsed",
            )
        with col_filter:
            st.selectbox(
                "来源",
                ["全部", "AI生成", "上传的"],
                key="notes_source_filter",
                label_visibility="collapsed",
            )
        with col_clear:
            if st.button("🔄 重置"):
                st.session_state.notes_search_query = ""
                st.session_state.notes_source_filter = "全部"
                st.session_state.notes_page_offset = 0
                st.rerun()

        # 构建 API 参数
        source_type_map = {"全部": None, "AI生成": "generated", "上传的": "uploaded"}
        api_source_type = source_type_map.get(
            st.session_state.notes_source_filter, None
        )

        offset = st.session_state.notes_page_offset
        search_query = st.session_state.notes_search_query
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
                            navigate_to("📝 生成笔记")

            for note in notes:
                with st.container():
                    col_main, col_action = st.columns([8, 1])
                    with col_main:
                        note_title = note.get("title", "无标题")
                        note_summary = note.get("summary", "")
                        note_tags = note.get("tags", [])
                        note_date = (note.get("created_at") or "")[:10]
                        note_words = note.get("word_count", 0)
                        note_source = note.get("source_type", "")
                        source_label = "🤖 AI生成" if note_source == "generated" else "📤 上传"

                        tag_html = " ".join([f'<span class="tag-badge">{escape(str(t))}</span>' for t in note_tags])
                        st.markdown(
                            f"""
                            <div class="glass-list-row" style="--accent:#2563eb; --wash:rgba(37,99,235,0.08);">
                                <strong>{escape(note_title)}</strong><br/>
                                <span>{escape(note_summary[:150] + ("..." if len(note_summary) > 150 else ""))}</span><br/>
                                {tag_html}
                                <span class="meta-text">| {source_label} | 📅 {note_date} | 📝 {note_words} 字</span>
                            </div>
                            """,
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

    # 知识资产指标带
    stats_resp = api_get("/rag/stats")
    if stats_resp and stats_resp.status_code == 200:
        stats = stats_resp.json().get("data", {})
        render_metric_band([
            {"label": "总文档", "value": stats.get("total_notes", 0), "note": "企业知识资产", "color": "#2563eb", "wash": "rgba(37,99,235,0.10)"},
            {"label": "AI 生成", "value": stats.get("generated_notes", 0), "note": "结构化笔记", "color": "#0891b2", "wash": "rgba(8,145,178,0.10)"},
            {"label": "上传文档", "value": stats.get("uploaded_notes", 0), "note": "制度/SOP/课件", "color": "#16a34a", "wash": "rgba(22,163,74,0.10)"},
            {"label": "向量块", "value": stats.get("total_chunks", 0), "note": "RAG 检索单元", "color": "#d97706", "wash": "rgba(217,119,6,0.12)"},
        ])

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
                col_main, col_actions = st.columns([7, 2])
                with col_main:
                    src_date = (source.get("created_at") or "")[:10]
                    render_list_row(
                        source.get("title", "无标题"),
                        f"字数: {source.get('word_count', 0)} | 创建日期: {src_date} | 来源: 企业知识库",
                        color="#0891b2",
                        wash="rgba(8,145,178,0.10)",
                    )
                with col_actions:
                    col_view, col_del = st.columns(2)
                    with col_view:
                        if st.button("📖 查看", key=f"kb_view_{source['id']}"):
                            st.session_state.notes_page_view = "detail"
                            st.session_state.selected_note_id = source["id"]
                            st.rerun()
                    with col_del:
                        confirm_key = f"kb_del_confirm_{source['id']}"
                        if st.session_state.get(confirm_key):
                            col_y, col_n = st.columns(2)
                            with col_y:
                                if st.button("✅", key=f"kb_del_yes_{source['id']}", help="确认删除"):
                                    try:
                                        del_resp = requests.delete(f"{API_BASE}/rag/sources/{source['id']}", timeout=10)
                                        if del_resp.status_code == 200:
                                            st.session_state.pop(confirm_key, None)
                                            st.success("已删除")
                                            st.rerun()
                                        else:
                                            st.error(f"删除失败: {del_resp.status_code}")
                                    except Exception as e:
                                        st.error(f"删除失败: {str(e)}")
                            with col_n:
                                if st.button("❌", key=f"kb_del_no_{source['id']}", help="取消"):
                                    st.session_state.pop(confirm_key, None)
                                    st.rerun()
                        else:
                            if st.button("🗑️", key=f"kb_del_{source['id']}", help="删除此文档"):
                                st.session_state[confirm_key] = True
                                st.rerun()

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

    # --- 批量删除操作 (v0.4.1) ---
    st.markdown("---")
    st.subheader("🗑️ 知识库清理")

    col1, col2, col3 = st.columns(3)

    with col1:
        if not st.session_state.kb_confirm_batch_delete:
            if st.button("🗑️ 清空上传文档", type="secondary", use_container_width=True,
                         disabled=(total == 0),
                         help="删除所有上传类型的文档（AI 生成的笔记不受影响）"):
                st.session_state.kb_confirm_batch_delete = True
                st.rerun()
        else:
            st.warning(f"⚠️ 将删除全部 {total} 篇上传文档，不可撤销！")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ 确认清空", type="primary", use_container_width=True, key="kb_confirm_yes"):
                    with st.spinner("正在删除..."):
                        del_resp = requests.delete(f"{API_BASE}/rag/sources", timeout=30)
                        if del_resp and del_resp.status_code == 200:
                            result = del_resp.json().get("data", {})
                            st.success(f"已删除 {result.get('deleted_count', 0)} 篇文档")
                            st.session_state.kb_confirm_batch_delete = False
                            st.session_state.kb_page_offset = 0
                            st.rerun()
                        else:
                            st.error("删除失败，请检查后端连接")
            with col_no:
                if st.button("❌ 取消", use_container_width=True, key="kb_confirm_no"):
                    st.session_state.kb_confirm_batch_delete = False
                    st.rerun()

    with col2:
        if st.button("🧹 清理孤立向量块", type="secondary", use_container_width=True,
                     help="清除 ChromaDB 中已无对应笔记的残留向量数据"):
            with st.spinner("正在扫描孤立块..."):
                clean_resp = requests.delete(f"{API_BASE}/rag/chunks/orphans", timeout=30)
                if clean_resp and clean_resp.status_code == 200:
                    result = clean_resp.json().get("data", {})
                    cleaned = result.get("cleaned", 0)
                    if cleaned > 0:
                        st.success(f"已清除 {cleaned} 个孤立向量块")
                    else:
                        st.info("没有发现孤立向量块，知识库很干净 ✨")
                else:
                    st.error("清理失败，请检查后端连接")

    with col3:
        if not st.session_state.kb_confirm_clear_all:
            if st.button("💣 重置整个知识库", type="secondary", use_container_width=True,
                         disabled=(stats.get("total_notes", 0) == 0),
                         help="删除所有笔记（含 AI 生成的）和全部向量数据"):
                st.session_state.kb_confirm_clear_all = True
                st.rerun()
        else:
            st.error("💀 将删除所有笔记和向量数据，完全不可撤销！")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ 确认重置", type="primary", use_container_width=True, key="kb_clearall_yes"):
                    with st.spinner("正在清空整个知识库..."):
                        clear_resp = requests.delete(
                            f"{API_BASE}/rag/clear-all?confirm=CONFIRM", timeout=30
                        )
                        if clear_resp and clear_resp.status_code == 200:
                            result = clear_resp.json().get("data", {})
                            st.success(f"知识库已重置（删除 {result.get('deleted_notes', 0)} 篇笔记，{result.get('deleted_chunks', 0)} 个向量块）")
                            st.session_state.kb_confirm_clear_all = False
                            st.session_state.kb_page_offset = 0
                            st.rerun()
                        else:
                            detail = clear_resp.json().get("detail", "未知错误") if clear_resp else "无响应"
                            st.error(f"重置失败: {detail}")
            with col_no:
                if st.button("❌ 取消", key="kb_clearall_no"):
                    st.session_state.kb_confirm_clear_all = False
                    st.rerun()


# ===================================================================
# 🎯 出题练习
# ===================================================================
elif page == "🎯 出题练习":
    st.header("🎯 岗位训练与测评")
    st.markdown("根据企业知识点自动生成题目，用于新人训练、岗位认证、合规测评和复训。")

    col0, col1, col2, col3 = st.columns([1.3, 2, 1, 1])
    with col0:
        quiz_scenario = st.selectbox(
            "训练场景",
            ["QA/测试训练", "客服/售后培训", "合规制度培训", "研发新人入职", "销售/产品赋能"],
        )
    with col1:
        quiz_topic = st.text_input("出题主题", placeholder="例如：边界值分析、退款条件、代码评审规范")
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
    st.header("🔍 企业知识问答")
    st.markdown("面向制度、SOP、课件和项目文档提问，回答基于知识库来源并经过 Multi-Query + Rerank 增强。")

    query = st.text_input("你的问题", placeholder="例如：Verification 和 Validation 的区别是什么？客服什么时候可以承诺退款？")

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
                navigate_to("📝 生成笔记")
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

    # --- 学习计划管理 (v0.4.1) ---
    st.markdown("---")
    st.subheader("📝 学习计划")

    # 加载现有计划
    plans_resp = api_get("/schedule/plans")
    plans = []
    if plans_resp and plans_resp.status_code == 200:
        plans = plans_resp.json().get("data", [])

    # 新建计划（折叠）
    with st.expander("➕ 创建新计划", expanded=(len(plans) == 0)):
        col_topic, col_date = st.columns([2, 1])
        with col_topic:
            plan_topic = st.text_input("学习主题", placeholder="例如：ISTQB 第一章", key="plan_topic")
        with col_date:
            plan_date = st.date_input("目标日期", value=None, key="plan_date")
        plan_goal = st.text_area("学习目标（可选）", placeholder="掌握 ISTQB 基础概念，能通过模拟测试", key="plan_goal")

        if st.button("💾 保存计划", type="primary", disabled=not plan_topic, key="save_plan"):
            req_data = {
                "topic": plan_topic,
                "goal_description": plan_goal,
                "target_date": plan_date.isoformat() if plan_date else None,
            }
            save_resp = api_post("/schedule/plan", req_data)
            if save_resp and save_resp.status_code == 200:
                st.success(f"计划 '{plan_topic}' 已创建！")
                st.rerun()
            else:
                st.error("创建失败，请检查后端连接")

    # 已有计划列表
    if plans:
        for p in plans:
            status = p.get("status", "active")
            status_emoji = {"active": "🟢", "paused": "🟡", "completed": "✅"}.get(status, "⚪")
            target = p.get("target_date", "")
            target_display = f" | 🎯 {target}" if target else ""

            col_info, col_status = st.columns([3, 1])
            with col_info:
                st.markdown(f"{status_emoji} **{p.get('topic', '无标题')}**{target_display}")
                if p.get("goal_description"):
                    st.caption(p["goal_description"][:100])
            with col_status:
                st.caption(status)
            st.markdown("---")
    else:
        st.info("还没有学习计划，点击上方创建。")


# ===================================================================
# 📋 记忆中心（v0.4.1 升级：错题本 + 薄弱点 + 易混概念）
# ===================================================================
elif page == "📋 记忆中心":
    st.header("📋 能力风险与记忆中心")
    st.markdown("沉淀错题、薄弱知识点和易混概念，帮助团队主管看到能力风险而不只是学习完成率。")

    # 加载错题数据（Tab1 用）
    resp = api_get("/quiz/errors/list", {"limit": 100})
    errors = []
    if resp and resp.status_code == 200:
        data = resp.json()
        errors = data.get("data", [])
        stats = data.get("stats", {})
        total = stats.get("total", 0)
        resolved = stats.get("resolved", 0)
        unresolved = stats.get("unresolved", 0)
    else:
        total = resolved = unresolved = 0

    # 错题与掌握指标带
    render_metric_band([
        {"label": "总错题", "value": total, "note": "历史能力风险样本", "color": "#2563eb", "wash": "rgba(37,99,235,0.10)"},
        {"label": "未解决", "value": unresolved, "note": "需要复训/复习", "color": "#e11d48", "wash": "rgba(225,29,72,0.10)"},
        {"label": "已掌握", "value": resolved, "note": "已闭环问题", "color": "#16a34a", "wash": "rgba(22,163,74,0.10)"},
    ])

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📋 错题列表", "🎯 薄弱点分析", "🔀 易混概念对"])

    # ===== Tab 1: 错题列表 =====
    with tab1:
        if not errors:
            st.success("🎉 做得很棒！目前没有错题记录。")
            st.markdown("去 [🎯 出题练习] 页面做题，错题会自动收录到这里。")
        else:
            from collections import defaultdict
            by_kp = defaultdict(list)
            for e in errors:
                kp = e.get("knowledge_point", "未分类")
                by_kp[kp].append(e)

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
                        error_class = "error-row resolved" if is_resolved else "error-row"
                        status_badge = "✅ 已掌握" if is_resolved else "❌ 待复习"

                        st.markdown(f"""
                        <div class="{error_class}">
                            <strong>{escape(status_badge)}</strong> | 类型: {escape(str(e.get('error_type', '未知')))} | 复习: {e.get('reviewed_count', 0)} 次<br/>
                            <span style="color:#be123c;">你的答案: {escape(str(e.get('user_answer', '')))}</span><br/>
                            <span style="color:#15803d;">正确答案: {escape(str(e.get('correct_answer', '')))}</span>
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

    # ===== Tab 2: 薄弱点分析 =====
    with tab2:
        wp_resp = api_get("/memory/weak-points")
        if wp_resp and wp_resp.status_code == 200:
            wp_data = wp_resp.json().get("data", {})
            weak_points = wp_data.get("weak_points", [])
            by_type = wp_data.get("by_type", {})
            suggestions = wp_data.get("improvement_suggestions", [])
            total_unresolved = wp_data.get("total_unresolved", 0)

            if not weak_points:
                st.success("🎉 没有发现薄弱点！")
            else:
                st.caption(f"基于 {total_unresolved} 条未解决错题分析")

                # 按错误类型分布
                if by_type:
                    st.subheader("📊 错误类型分布")
                    colors = ["#e11d48", "#d97706", "#2563eb", "#0891b2", "#16a34a"]
                    render_metric_band([
                        {
                            "label": etype,
                            "value": f"{count} 次",
                            "note": "未解决错题",
                            "color": colors[i % len(colors)],
                            "wash": "rgba(225,29,72,0.08)",
                        }
                        for i, (etype, count) in enumerate(by_type.items())
                    ])

                st.markdown("---")

                # 薄弱知识点排行
                st.subheader("🔴 薄弱知识点排行")
                for i, wp in enumerate(weak_points):
                    kp = wp.get("knowledge_point", "未知")
                    count = wp.get("error_count", 0)
                    examples = wp.get("examples", [])

                    with st.container():
                        st.markdown(f"**{i+1}. {kp}** — 错误 **{count}** 次")
                        if examples:
                            with st.expander(f"查看错题示例 ({len(examples)} 条)"):
                                for ex in examples:
                                    st.markdown(
                                        f"✗ `{ex.get('user_answer', '')}` → ✓ `{ex.get('correct_answer', '')}`"
                                    )
                        st.progress(min(1.0, count / max(1, weak_points[0].get('error_count', 1))))

                # LLM 改进建议
                if suggestions:
                    st.markdown("---")
                    st.subheader("💡 改进建议")
                    for s in suggestions:
                        st.info(s)
        else:
            st.info("📭 暂无薄弱点数据。做题产生错题后会自动分析。")

    # ===== Tab 3: 易混概念对 =====
    with tab3:
        conf_resp = api_get("/memory/confusions")
        if conf_resp and conf_resp.status_code == 200:
            conf_data = conf_resp.json()
            pairs = conf_data.get("data", [])
            total_pairs = conf_data.get("total", 0)

            if not pairs:
                st.success("🎉 没有检测到易混概念对！")
                st.caption("当做错的不同知识点出现在同一批题目中时，系统会自动检测并记录混淆对。")
            else:
                st.caption(f"共检测到 {total_pairs} 组易混概念")

                for p in pairs:
                    a = p.get("concept_a", "")
                    b = p.get("concept_b", "")
                    count = p.get("error_count", 0)
                    last = (p.get("last_confused_at") or "")[:10]

                    col_main, col_count = st.columns([3, 1])
                    with col_main:
                        severity_color = "#e11d48" if count >= 3 else "#d97706" if count >= 2 else "#16a34a"
                        severity_wash = "rgba(225,29,72,0.10)" if count >= 3 else "rgba(217,119,6,0.12)" if count >= 2 else "rgba(22,163,74,0.10)"
                        render_list_row(
                            f"{a} ↔ {b}",
                            f"最近混淆: {last} | 适合生成对比题和复习任务",
                            color=severity_color,
                            wash=severity_wash,
                        )
                    with col_count:
                        severity = "🔴" if count >= 3 else "🟡" if count >= 2 else "🟢"
                        st.markdown(f"**{severity} 混淆次数**")
                        st.markdown(f"## {count}")

                    st.markdown("---")
        else:
            st.info("📭 暂无易混概念数据。")


# ===================================================================
# 🏢 企业蓝图
# ===================================================================
elif page == "🏢 企业蓝图":
    st.header("🏢 企业级落地蓝图")
    st.markdown("从部门试点到集团级多租户，把学习助手扩展为企业知识运营与人才训练平台。")

    render_learning_flow()
    render_scenario_matrix()

    st.markdown("---")
    st.subheader("🎬 场景演示路径")
    selected_scene = st.selectbox(
        "选择演示场景",
        ["QA 新人训练闭环", "客服政策与话术训练", "合规制度培训", "研发新人入职", "销售与产品赋能"],
    )

    playbooks = {
        "QA 新人训练闭环": [
            ("导入资料", "上传 ISTQB、测试规范、缺陷流程和自动化实践。", "#2563eb"),
            ("生成笔记", "整理“软件测试基础与缺陷生命周期”结构化笔记。", "#0891b2"),
            ("知识问答", "提问 Verification 和 Validation 的区别，展示来源引用。", "#16a34a"),
            ("岗位测评", "生成边界值分析、缺陷生命周期等题目并提交答案。", "#d97706"),
            ("复习闭环", "查看错题、薄弱点、易混概念和 SM-2 复习任务。", "#e11d48"),
        ],
        "客服政策与话术训练": [
            ("导入资料", "上传退款政策、投诉升级 SOP、账号安全处理流程。", "#2563eb"),
            ("知识问答", "询问什么情况下可以承诺退款，验证政策边界。", "#0891b2"),
            ("场景出题", "生成退款条件、升级投诉、隐私数据处理题。", "#16a34a"),
            ("语义批改", "简答题按话术准确性、合规边界、完整性评分。", "#d97706"),
            ("主管复训", "根据薄弱点安排定向辅导，减少质检扣分。", "#e11d48"),
        ],
        "合规制度培训": [
            ("制度入库", "导入合规手册、审计案例、监管问答。", "#2563eb"),
            ("条款摘要", "生成适用范围、风险点、操作禁区。", "#0891b2"),
            ("案例测评", "生成判断题和风险识别简答题。", "#16a34a"),
            ("风险反馈", "指出遗漏的审批、留痕、权限和数据处理风险。", "#d97706"),
            ("审计记录", "保留学习、测试、错题、复习的可追溯记录。", "#e11d48"),
        ],
        "研发新人入职": [
            ("项目文档", "导入架构说明、部署流程、代码规范和事故复盘。", "#2563eb"),
            ("新人问答", "查询服务启动失败排查路径和配置要求。", "#0891b2"),
            ("训练路径", "生成后端新人 14 天上手计划。", "#16a34a"),
            ("排障题", "生成部署、日志、配置、评审规范相关题目。", "#d97706"),
            ("导师辅导", "按新人薄弱点减少重复答疑。", "#e11d48"),
        ],
        "销售与产品赋能": [
            ("产品资料", "导入白皮书、竞品对比、报价规则、行业方案。", "#2563eb"),
            ("一线查询", "快速回答客户行业场景和产品能力边界。", "#0891b2"),
            ("异议训练", "生成竞品对比、方案匹配、风险边界题。", "#16a34a"),
            ("话术评分", "检查完整性、准确性和不当承诺。", "#d97706"),
            ("赋能复盘", "统计团队薄弱产品点和常见误答。", "#e11d48"),
        ],
    }
    for title, desc, color in playbooks[selected_scene]:
        render_list_row(title, desc, color=color, wash=f"{color}18")

    st.markdown("---")
    st.subheader("📈 企业价值指标")
    render_metric_band([
        {"label": "新人达标周期", "value": "↓", "note": "入职到通过岗位测评的平均天数", "color": "#2563eb", "wash": "rgba(37,99,235,0.10)"},
        {"label": "题库维护成本", "value": "↓", "note": "由 Agent 从知识库自动生成训练题", "color": "#0891b2", "wash": "rgba(8,145,178,0.10)"},
        {"label": "高频错题率", "value": "↓", "note": "通过错题闭环与 SM-2 复习降低重复错误", "color": "#e11d48", "wash": "rgba(225,29,72,0.10)"},
        {"label": "知识命中率", "value": "↑", "note": "Multi-Query + Rerank 提升企业文档检索质量", "color": "#16a34a", "wash": "rgba(22,163,74,0.10)"},
    ])

    st.markdown("---")
    st.subheader("🧭 企业化路线")
    deployment_html = """
    <div class="flow-strip">
        <div class="flow-step" style="--wash:rgba(37,99,235,0.10);"><strong>单机试点版</strong><span>SQLite + ChromaDB，适合小团队 Demo 和 PoC</span></div>
        <div class="flow-step" style="--wash:rgba(8,145,178,0.10);"><strong>部门生产版</strong><span>PostgreSQL + 权限控制 + 部门看板</span></div>
        <div class="flow-step" style="--wash:rgba(22,163,74,0.10);"><strong>集团多租户版</strong><span>租户隔离、审计、模型网关和成本治理</span></div>
        <div class="flow-step" style="--wash:rgba(217,119,6,0.12);"><strong>生态集成版</strong><span>LMS、企业 IM、工单系统、SSO 和 Webhook</span></div>
    </div>
    """
    render_section("部署演进模式", deployment_html)

    governance_rows = [
        ("身份与组织", "JWT/OIDC、部门、岗位、角色和租户隔离", "#2563eb"),
        ("内容治理", "专家审核、版本管理、敏感信息检测和题目发布流", "#0891b2"),
        ("数据安全", "知识库权限过滤、审计日志、密钥托管和数据脱敏", "#e11d48"),
        ("可观测性", "结构化日志、健康检查、模型成本统计和备份恢复", "#16a34a"),
    ]
    st.subheader("🛡️ 治理能力清单")
    for title, desc, color in governance_rows:
        render_list_row(title, desc, color=color, wash=f"{color}18")


# ===================================================================
# 📊 系统信息
# ===================================================================
elif page == "⚙️ 系统信息":
    st.header("⚙️ 系统信息")

    backend = check_backend()
    if backend:
        render_metric_band([
            {"label": "LLM Providers", "value": ", ".join(backend.get("llm_providers", [])) or "无", "note": "模型路由可用供应商", "color": "#2563eb", "wash": "rgba(37,99,235,0.10)"},
            {"label": "Agents", "value": backend.get("agents", 0), "note": "已注册专业 Agent", "color": "#0891b2", "wash": "rgba(8,145,178,0.10)"},
        ])

        # 知识库统计
        stats_resp = api_get("/rag/stats")
        if stats_resp and stats_resp.status_code == 200:
            stats = stats_resp.json().get("data", {})
            st.markdown("---")
            st.subheader("📊 知识库统计")
            render_metric_band([
                {"label": "总笔记", "value": stats.get("total_notes", 0), "note": "结构化知识记录", "color": "#2563eb", "wash": "rgba(37,99,235,0.10)"},
                {"label": "AI 生成", "value": stats.get("generated_notes", 0), "note": "Agent 自动整理", "color": "#0891b2", "wash": "rgba(8,145,178,0.10)"},
                {"label": "上传文档", "value": stats.get("uploaded_notes", 0), "note": "企业资料入口", "color": "#16a34a", "wash": "rgba(22,163,74,0.10)"},
                {"label": "向量块", "value": stats.get("total_chunks", 0), "note": "RAG 检索资产", "color": "#d97706", "wash": "rgba(217,119,6,0.12)"},
            ])

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
│   └── streamlit_app.py    # 前端 10 页面
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
    - ✅ 学习仪表盘（运营指标带 + 待复习任务 + 知识点进度）
    - ✅ 复习计划页面（评分 0-5 + SM-2 间隔计算 + 下次复习日期展示）
    - ✅ 易混概念对自动检测（错题知识点两两组合创建混淆对）
    - ✅ Memory API（薄弱点分析 + 混淆对列表 + 学习报告）
    - ✅ Schedule API 接入真实数据库（每日任务 / 复习评分 / 统计数据）
    - ✅ SM-2 状态自动创建（笔记生成 + 错题入库时联动）
    - ✅ 企业蓝图页面（场景演示路径 + 企业价值指标 + 治理路线）
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
