import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  BookOpen,
  Brain,
  Building2,
  CalendarCheck,
  CheckCircle2,
  FileQuestion,
  Gauge,
  GraduationCap,
  Library,
  ListChecks,
  Loader2,
  MessageSquareText,
  RefreshCcw,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
  Upload,
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api/v1";
const ROOT_BASE = API_BASE.replace(/\/api\/v1\/?$/, "");

const navItems = [
  { id: "dashboard", label: "学习仪表盘", icon: BarChart3 },
  { id: "notes-generate", label: "生成笔记", icon: Sparkles },
  { id: "notes", label: "我的笔记", icon: BookOpen },
  { id: "knowledge", label: "知识库管理", icon: Library },
  { id: "quiz", label: "出题练习", icon: FileQuestion },
  { id: "rag", label: "知识问答", icon: MessageSquareText },
  { id: "review", label: "复习计划", icon: CalendarCheck },
  { id: "memory", label: "记忆中心", icon: Brain },
  { id: "blueprint", label: "企业蓝图", icon: Building2 },
  { id: "system", label: "系统信息", icon: Settings },
];

const scenarios = [
  {
    name: "QA/测试训练",
    desc: "测试规范、缺陷流程、ISTQB 和自动化实践转成训练题与复习任务",
    color: "#2563eb",
  },
  {
    name: "客服/售后培训",
    desc: "FAQ、工单案例和 SOP 转成话术训练，减少政策误答和质检扣分",
    color: "#0891b2",
  },
  {
    name: "合规制度培训",
    desc: "制度条款、审计案例和监管问答形成可追踪的掌握度记录",
    color: "#d97706",
  },
  {
    name: "研发新人入职",
    desc: "架构文档、部署手册和事故复盘沉淀为问答、测验和辅导建议",
    color: "#16a34a",
  },
  {
    name: "销售/产品赋能",
    desc: "产品白皮书、竞品对比和方案材料转成异议处理训练",
    color: "#e11d48",
  },
];

const flowSteps = [
  ["资料导入", "PDF/MD/TXT", "#2563eb"],
  ["结构化笔记", "Note Agent", "#0891b2"],
  ["岗位训练", "Quiz Agent", "#16a34a"],
  ["自动批改", "Grading Agent", "#d97706"],
  ["薄弱点沉淀", "Memory Agent", "#e11d48"],
  ["间隔复习", "SM-2 Scheduler", "#7c3aed"],
];

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(payload.detail || payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

function useAsync(load, deps = []) {
  const [state, setState] = useState({ loading: true, data: null, error: "" });

  useEffect(() => {
    let active = true;
    setState((prev) => ({ ...prev, loading: true, error: "" }));
    load()
      .then((data) => active && setState({ loading: false, data, error: "" }))
      .catch((error) => active && setState({ loading: false, data: null, error: error.message }));
    return () => {
      active = false;
    };
  }, deps);

  return state;
}

function Shell({ page, setPage, children, health }) {
  return (
    <div className="app-shell">
      <aside className="sidebar glass">
        <div className="brand">
          <div className="brand-mark"><Brain size={24} /></div>
          <div>
            <strong>LearnLoop-AI</strong>
            <span>企业知识训练平台</span>
          </div>
        </div>
        <div className={health?.status === "healthy" ? "status online" : "status offline"}>
          <span />
          {health?.status === "healthy" ? `后端已连接 · ${health.agents || 0} Agents` : "后端未连接"}
        </div>
        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={page === item.id ? "nav-button active" : "nav-button"}
                onClick={() => setPage(item.id)}
                type="button"
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="sidebar-foot">
          <strong>企业场景</strong>
          <span>QA 训练 · 客服培训 · 合规认证 · 研发入职 · 销售赋能</span>
        </div>
      </aside>
      <main className="main-area">
        <Hero />
        {children}
      </main>
    </div>
  );
}

function Hero() {
  return (
    <section className="hero glass">
      <div>
        <p className="eyebrow">Agentic Learning Platform</p>
        <h1>LearnLoop-AI</h1>
        <p>用 Multi-Agent 把企业资料变成可问答、可练习、可批改、可追踪、可复习的能力闭环。</p>
      </div>
      <div className="hero-tags">
        {["Multi-Agent", "RAG 知识库", "自动出题", "智能批改", "SM-2 复习"].map((tag) => (
          <span key={tag}>{tag}</span>
        ))}
      </div>
    </section>
  );
}

function Section({ title, action, children }) {
  return (
    <section className="glass section">
      <div className="section-title">
        <h2>{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

function MetricBand({ metrics }) {
  return (
    <div className="metric-band">
      {metrics.map((metric) => (
        <div className="metric-item" style={{ "--accent": metric.color }} key={metric.label}>
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
          <em>{metric.note}</em>
        </div>
      ))}
    </div>
  );
}

function FlowStrip() {
  return (
    <div className="flow-strip">
      {flowSteps.map(([title, desc, color]) => (
        <div className="flow-step" style={{ "--accent": color }} key={title}>
          <strong>{title}</strong>
          <span>{desc}</span>
        </div>
      ))}
    </div>
  );
}

function ScenarioGrid() {
  return (
    <div className="scenario-grid">
      {scenarios.map((scenario) => (
        <div className="line-row" style={{ "--accent": scenario.color }} key={scenario.name}>
          <strong>{scenario.name}</strong>
          <span>{scenario.desc}</span>
        </div>
      ))}
    </div>
  );
}

function LoadingLine({ label = "正在加载" }) {
  return (
    <div className="loading-line">
      <Loader2 size={16} className="spin" />
      {label}
    </div>
  );
}

function Empty({ children }) {
  return <div className="empty">{children}</div>;
}

function ErrorNotice({ error }) {
  if (!error) return null;
  return <div className="notice danger">{error}</div>;
}

function Dashboard({ setPage }) {
  const stats = useAsync(() => request("/schedule/stats").then((r) => r.data || {}), []);
  const daily = useAsync(() => request("/schedule/daily").then((r) => r.data || {}), []);
  const states = useAsync(() => request("/schedule/states").then((r) => r.data || []), []);

  const metrics = useMemo(() => {
    const s = stats.data || {};
    return [
      { label: "连续学习", value: `${s.streak_days || 0} 天`, note: "个人/团队活跃节奏", color: "#2563eb" },
      { label: "待复习知识点", value: `${s.due_count || 0} 项`, note: `${s.overdue_count || 0} 项逾期`, color: "#d97706" },
      { label: "测验提交", value: `${s.total_quizzes || 0} 次`, note: "训练闭环样本", color: "#0891b2" },
      { label: "掌握率", value: `${s.mastery_rate || 0}%`, note: "基于错题解决情况", color: "#16a34a" },
      { label: "知识点资产", value: `${s.total_kps || 0} 个`, note: "SM-2 跟踪对象", color: "#e11d48" },
    ];
  }, [stats.data]);

  const dailyTasks = daily.data?.daily_tasks || [];
  const sm2States = states.data || [];

  return (
    <>
      <header className="page-head">
        <h1>企业学习运营仪表盘</h1>
        <p>围绕知识资产、岗位训练、测评反馈和复习节奏追踪组织能力。</p>
      </header>
      <MetricBand metrics={metrics} />
      <Section title="企业学习闭环">
        <FlowStrip />
      </Section>
      <Section title="企业级使用场景">
        <ScenarioGrid />
      </Section>
      <Section
        title="今日待复习任务"
        action={<button className="ghost-button" type="button" onClick={() => setPage("review")}><RefreshCcw size={16} /> 去复习</button>}
      >
        {daily.loading ? <LoadingLine /> : <ErrorNotice error={daily.error} />}
        {!daily.loading && !daily.error && dailyTasks.length === 0 && (
          <Empty>
            暂无到期任务。生成笔记或做一套题后，系统会自动创建复习计划。
            <button type="button" onClick={() => setPage("notes-generate")}>生成笔记</button>
          </Empty>
        )}
        <div className="list-stack">
          {dailyTasks.slice(0, 8).map((task) => (
            <div className="line-row" style={{ "--accent": priorityColor(task.priority) }} key={`${task.knowledge_point}-${task.reason}`}>
              <strong>{task.knowledge_point || "未知知识点"}</strong>
              <span>{task.priority || "low"} · {task.suggested_duration_min || 10} 分钟 · {task.reason}</span>
            </div>
          ))}
        </div>
      </Section>
      <Section title="知识点掌握分布">
        {states.loading ? <LoadingLine /> : <ErrorNotice error={states.error} />}
        <div className="progress-list">
          {sm2States.slice(0, 10).map((state) => {
            const progress = Math.min(100, Math.max(0, (((state.ef || 2.5) - 1.3) / 1.7) * 100));
            return (
              <div className="progress-row" key={state.id || state.knowledge_point}>
                <div>
                  <strong>{state.knowledge_point}</strong>
                  <span>EF {Number(state.ef || 2.5).toFixed(1)} · 间隔 {state.interval_days || 1}d · 错 {state.error_count || 0} 次</span>
                </div>
                <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
              </div>
            );
          })}
        </div>
      </Section>
      <div className="quick-actions">
        <button type="button" onClick={() => setPage("notes-generate")}><Sparkles size={17} />生成笔记</button>
        <button type="button" onClick={() => setPage("quiz")}><FileQuestion size={17} />出题练习</button>
        <button type="button" onClick={() => setPage("memory")}><Brain size={17} />查看错题</button>
        <button type="button" onClick={() => setPage("rag")}><Search size={17} />知识问答</button>
      </div>
    </>
  );
}

function priorityColor(priority) {
  if (priority === "high") return "#e11d48";
  if (priority === "medium") return "#d97706";
  return "#16a34a";
}

function GenerateNote({ setPage }) {
  const [scenario, setScenario] = useState("通用学习");
  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState("detailed");
  const [sourceText, setSourceText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const payload = await request("/notes/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, source_text: sourceText, style }),
      });
      setResult(payload.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <header className="page-head">
        <h1>生成岗位知识笔记</h1>
        <p>把企业资料、培训主题或岗位 SOP 转成结构化 Markdown，并自动进入知识库和复习体系。</p>
      </header>
      <Section title="生成配置">
        <div className="form-grid">
          <label>企业场景<select value={scenario} onChange={(e) => setScenario(e.target.value)}>{["通用学习", ...scenarios.map((s) => s.name)].map((x) => <option key={x}>{x}</option>)}</select></label>
          <label>学习主题<input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="例如：软件测试方法、退款政策、代码评审规范" /></label>
          <label>笔记风格<select value={style} onChange={(e) => setStyle(e.target.value)}><option value="detailed">detailed</option><option value="summary">summary</option><option value="mindmap">mindmap</option></select></label>
        </div>
        <label className="wide-field">补充内容<textarea value={sourceText} onChange={(e) => setSourceText(e.target.value)} placeholder={`粘贴 ${scenario} 相关制度、SOP、课件、FAQ 或项目复盘内容`} /></label>
        <button className="primary-button" disabled={!topic || loading} type="button" onClick={submit}>{loading ? <Loader2 className="spin" size={18} /> : <Sparkles size={18} />}生成笔记</button>
      </Section>
      <ErrorNotice error={error} />
      {result && (
        <Section title={result.title || topic} action={result._persisted && <button className="ghost-button" onClick={() => setPage("notes")} type="button"><BookOpen size={16} />查看我的笔记</button>}>
          <MetricBand metrics={[
            { label: "章节数", value: result.sections_count || 0, note: "结构化学习单元", color: "#2563eb" },
            { label: "企业场景", value: scenario, note: "用于岗位化训练", color: "#0891b2" },
            { label: "入库状态", value: result._persisted ? "已入库" : "未入库", note: result._save_error || "SQLite + ChromaDB", color: result._persisted ? "#16a34a" : "#d97706" },
          ]} />
          <div className="tag-line">{(result.tags || []).map((tag) => <span key={tag}>{tag}</span>)}</div>
          <article className="markdown-output">{result.content_md || "无内容"}</article>
        </Section>
      )}
    </>
  );
}

function NotesPage() {
  const [query, setQuery] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [selected, setSelected] = useState(null);
  const notes = useAsync(() => {
    const params = new URLSearchParams({ limit: "50", offset: "0" });
    if (query || sourceType) {
      if (query) params.set("query", query);
      if (sourceType) params.set("source_type", sourceType);
      return request(`/notes/search?${params}`).then((r) => r.data || []);
    }
    return request(`/notes?${params}`).then((r) => r.data || []);
  }, [query, sourceType, refresh]);

  async function remove(noteId) {
    await request(`/notes/${noteId}`, { method: "DELETE" });
    setSelected(null);
    setRefresh((x) => x + 1);
  }

  return (
    <>
      <header className="page-head">
        <h1>我的笔记</h1>
        <p>已保存的结构化知识笔记，支持按关键词和来源过滤。</p>
      </header>
      <Section title="搜索过滤">
        <div className="toolbar">
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="搜索标题或内容" />
          <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}><option value="">全部来源</option><option value="generated">AI 生成</option><option value="uploaded">上传文档</option></select>
          <button type="button" onClick={() => { setQuery(""); setSourceType(""); }}>重置</button>
        </div>
      </Section>
      <ErrorNotice error={notes.error} />
      {notes.loading ? <LoadingLine /> : (
        <div className="two-pane">
          <Section title={`笔记列表 · ${notes.data?.length || 0} 篇`}>
            <div className="list-stack">
              {(notes.data || []).map((note) => (
                <button className="line-row clickable" style={{ "--accent": note.source_type === "uploaded" ? "#0891b2" : "#2563eb" }} key={note.id} type="button" onClick={() => setSelected(note)}>
                  <strong>{note.title}</strong>
                  <span>{note.summary || "暂无摘要"} · {note.source_type || "generated"} · {(note.created_at || "").slice(0, 10)}</span>
                </button>
              ))}
            </div>
          </Section>
          <Section title={selected ? selected.title : "笔记详情"}>
            {!selected ? <Empty>选择左侧笔记查看内容。</Empty> : (
              <>
                <div className="tag-line">{(selected.tags || []).map((tag) => <span key={tag}>{tag}</span>)}</div>
                <article className="markdown-output">{selected.content_md}</article>
                <button className="danger-button" type="button" onClick={() => remove(selected.id)}>删除笔记</button>
              </>
            )}
          </Section>
        </div>
      )}
    </>
  );
}

function KnowledgePage() {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [message, setMessage] = useState("");
  const stats = useAsync(() => request("/rag/stats").then((r) => r.data || {}), [refresh]);
  const sources = useAsync(() => request("/rag/sources?limit=50&offset=0").then((r) => r.data || []), [refresh]);

  async function upload() {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    setMessage("");
    const payload = await request("/rag/upload", { method: "POST", body: form });
    setMessage(`文档「${payload.data?.title || file.name}」已入库`);
    setFile(null);
    setTitle("");
    setRefresh((x) => x + 1);
  }

  async function remove(id) {
    await request(`/rag/sources/${id}`, { method: "DELETE" });
    setRefresh((x) => x + 1);
  }

  const s = stats.data || {};
  return (
    <>
      <header className="page-head">
        <h1>知识库管理</h1>
        <p>上传企业制度、SOP、课件和复盘文档，建立 RAG 可检索知识资产。</p>
      </header>
      <MetricBand metrics={[
        { label: "总文档", value: s.total_notes || 0, note: "企业知识资产", color: "#2563eb" },
        { label: "AI 生成", value: s.generated_notes || 0, note: "结构化笔记", color: "#0891b2" },
        { label: "上传文档", value: s.uploaded_notes || 0, note: "制度/SOP/课件", color: "#16a34a" },
        { label: "向量块", value: s.total_chunks || 0, note: "RAG 检索单元", color: "#d97706" },
      ]} />
      <Section title="上传文档">
        <div className="toolbar">
          <input type="file" accept=".pdf,.md,.txt" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="自定义标题，可选" />
          <button className="primary-button" disabled={!file} type="button" onClick={upload}><Upload size={17} />上传并入库</button>
        </div>
        {message && <div className="notice success">{message}</div>}
      </Section>
      <Section title="已上传文档">
        {sources.loading ? <LoadingLine /> : <ErrorNotice error={sources.error} />}
        <div className="list-stack">
          {(sources.data || []).map((source) => (
            <div className="line-row split" style={{ "--accent": "#0891b2" }} key={source.id}>
              <div>
                <strong>{source.title}</strong>
                <span>{source.word_count || 0} 字 · {(source.created_at || "").slice(0, 10)}</span>
              </div>
              <button type="button" onClick={() => remove(source.id)}>删除</button>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}

function QuizPage() {
  const [scenario, setScenario] = useState(scenarios[0].name);
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [count, setCount] = useState(5);
  const [types, setTypes] = useState(["choice"]);
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function toggleType(type) {
    setTypes((prev) => prev.includes(type) ? prev.filter((x) => x !== type) : [...prev, type]);
  }

  async function generate() {
    setLoading(true);
    setError("");
    try {
      const payload = await request("/quiz/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, difficulty, count: Number(count), types }),
      });
      setQuiz(payload.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <header className="page-head">
        <h1>岗位训练与测评</h1>
        <p>根据企业知识点自动生成题目，用于新人训练、岗位认证、合规测评和复训。</p>
      </header>
      <Section title="出题配置">
        <div className="form-grid">
          <label>训练场景<select value={scenario} onChange={(e) => setScenario(e.target.value)}>{scenarios.map((x) => <option key={x.name}>{x.name}</option>)}</select></label>
          <label>出题主题<input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="例如：边界值分析、退款条件、代码评审规范" /></label>
          <label>难度<select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}><option value="easy">easy</option><option value="medium">medium</option><option value="hard">hard</option></select></label>
          <label>题目数量<input type="number" min="1" max="20" value={count} onChange={(e) => setCount(e.target.value)} /></label>
        </div>
        <div className="segmented">
          {["choice", "short_answer", "dictation", "true_false"].map((type) => (
            <button className={types.includes(type) ? "active" : ""} type="button" key={type} onClick={() => toggleType(type)}>{type}</button>
          ))}
        </div>
        <button className="primary-button" disabled={!topic || !types.length || loading} type="button" onClick={generate}>{loading ? <Loader2 className="spin" size={18} /> : <Target size={18} />}生成题目</button>
      </Section>
      <ErrorNotice error={error} />
      {quiz && (
        <Section title={quiz.topic || topic}>
          <div className="list-stack">
            {(quiz.questions || []).map((q, index) => (
              <details className="question-row" key={q.id || index}>
                <summary>第 {index + 1} 题 · {q.type} · {q.difficulty}</summary>
                <p>{q.question}</p>
                {q.options?.map((option) => <div className="option-line" key={option.key}>{option.key}. {option.text}</div>)}
                <div className="answer-line">答案：{q.answer}</div>
                {q.explanation && <div className="notice info">{q.explanation}</div>}
              </details>
            ))}
          </div>
        </Section>
      )}
    </>
  );
}

function RagPage() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function ask() {
    setLoading(true);
    setError("");
    setAnswer(null);
    try {
      const payload = await request("/rag/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: Number(topK) }),
      });
      setAnswer(payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const data = answer?.data || {};
  const meta = answer?.metadata || {};
  return (
    <>
      <header className="page-head">
        <h1>企业知识问答</h1>
        <p>面向制度、SOP、课件和项目文档提问，回答基于知识库来源并经过 Multi-Query + Rerank 增强。</p>
      </header>
      <Section title="提问">
        <div className="toolbar">
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="例如：Verification 和 Validation 的区别是什么？客服什么时候可以承诺退款？" />
          <label className="inline-range">检索数量<input type="range" min="1" max="20" value={topK} onChange={(e) => setTopK(e.target.value)} /><span>{topK}</span></label>
          <button className="primary-button" disabled={!query || loading} type="button" onClick={ask}>{loading ? <Loader2 className="spin" size={17} /> : <Search size={17} />}提问</button>
        </div>
      </Section>
      <ErrorNotice error={error} />
      {data.answer && (
        <Section title="回答">
          <article className="markdown-output">{data.answer}</article>
          <div className="tag-line">
            <span>检索块 {meta.retrieved_chunks || 0}</span>
            <span>查询扩展 +{meta.query_expansions || 0}</span>
            <span>{meta.reranked ? "Rerank 已启用" : "Rerank 未启用"}</span>
            <span>置信度 {data.confidence || 0}</span>
          </div>
          <div className="list-stack">
            {(data.sources || []).map((source, index) => (
              <div className="line-row" style={{ "--accent": "#0891b2" }} key={`${source.title}-${index}`}>
                <strong>{source.title || "未知来源"}</strong>
                <span>{source.excerpt || ""}</span>
              </div>
            ))}
          </div>
        </Section>
      )}
    </>
  );
}

function ReviewPage({ setPage }) {
  const [refresh, setRefresh] = useState(0);
  const [scores, setScores] = useState({});
  const states = useAsync(() => request("/schedule/states").then((r) => r.data || []), [refresh]);

  async function submit(point) {
    await request("/schedule/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ knowledge_point: point, score: Number(scores[point] ?? 3), user_id: "default" }),
    });
    setRefresh((x) => x + 1);
  }

  const allStates = states.data || [];
  const errorKps = allStates.filter((s) => (s.error_count || 0) > 0 || (s.repetitions || 0) === 0);

  return (
    <>
      <header className="page-head">
        <h1>复习计划</h1>
        <p>基于 SM-2 遗忘曲线，对知识点评分后自动计算下次复习时间。</p>
      </header>
      <ErrorNotice error={states.error} />
      {states.loading ? <LoadingLine /> : allStates.length === 0 ? (
        <Empty>暂无知识点数据。<button type="button" onClick={() => setPage("notes-generate")}>生成笔记</button></Empty>
      ) : (
        <Section title="重点复习知识点">
          <div className="list-stack">
            {errorKps.map((state) => (
              <div className="line-row split" style={{ "--accent": priorityColor(state.priority) }} key={state.id || state.knowledge_point}>
                <div>
                  <strong>{state.knowledge_point}</strong>
                  <span>EF {Number(state.ef || 2.5).toFixed(2)} · 间隔 {state.interval_days || 1} 天 · 错 {state.error_count || 0} 次 · 下次 {(state.next_review_at || "").slice(0, 10)}</span>
                </div>
                <div className="review-action">
                  <select value={scores[state.knowledge_point] ?? 3} onChange={(e) => setScores((prev) => ({ ...prev, [state.knowledge_point]: e.target.value }))}>
                    {[0, 1, 2, 3, 4, 5].map((score) => <option key={score} value={score}>{score}</option>)}
                  </select>
                  <button type="button" onClick={() => submit(state.knowledge_point)}>提交评分</button>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </>
  );
}

function MemoryPage() {
  const errors = useAsync(() => request("/quiz/errors/list?limit=100").then((r) => ({ rows: r.data || [], stats: r.stats || {} })), []);
  const weak = useAsync(() => request("/memory/weak-points").then((r) => r.data || {}), []);
  const confusions = useAsync(() => request("/memory/confusions").then((r) => r.data || []), []);
  const stat = errors.data?.stats || {};

  return (
    <>
      <header className="page-head">
        <h1>能力风险与记忆中心</h1>
        <p>沉淀错题、薄弱知识点和易混概念，帮助团队主管看到能力风险而不只是学习完成率。</p>
      </header>
      <MetricBand metrics={[
        { label: "总错题", value: stat.total || 0, note: "历史能力风险样本", color: "#2563eb" },
        { label: "未解决", value: stat.unresolved || 0, note: "需要复训/复习", color: "#e11d48" },
        { label: "已掌握", value: stat.resolved || 0, note: "已闭环问题", color: "#16a34a" },
      ]} />
      <div className="three-pane">
        <Section title="错题列表">
          {errors.loading ? <LoadingLine /> : <ErrorNotice error={errors.error} />}
          <div className="list-stack">
            {(errors.data?.rows || []).map((item) => (
              <div className="line-row" style={{ "--accent": item.is_resolved ? "#16a34a" : "#e11d48" }} key={item.id}>
                <strong>{item.knowledge_point || "未分类"} · {item.is_resolved ? "已掌握" : "待复习"}</strong>
                <span>你的答案：{item.user_answer} · 正确答案：{item.correct_answer}</span>
              </div>
            ))}
          </div>
        </Section>
        <Section title="薄弱点">
          <div className="list-stack">
            {(weak.data?.weak_points || []).map((item) => (
              <div className="line-row" style={{ "--accent": "#d97706" }} key={item.knowledge_point}>
                <strong>{item.knowledge_point}</strong>
                <span>错误 {item.error_count || 0} 次</span>
              </div>
            ))}
          </div>
        </Section>
        <Section title="易混概念">
          <div className="list-stack">
            {(confusions.data || []).map((item) => (
              <div className="line-row" style={{ "--accent": item.error_count >= 3 ? "#e11d48" : "#0891b2" }} key={item.id}>
                <strong>{item.concept_a} ↔ {item.concept_b}</strong>
                <span>混淆 {item.error_count || 1} 次 · 最近 {(item.last_confused_at || "").slice(0, 10)}</span>
              </div>
            ))}
          </div>
        </Section>
      </div>
    </>
  );
}

function BlueprintPage() {
  const [scene, setScene] = useState("QA 新人训练闭环");
  const playbooks = {
    "QA 新人训练闭环": [
      ["导入资料", "上传 ISTQB、测试规范、缺陷流程和自动化实践。", "#2563eb"],
      ["生成笔记", "整理“软件测试基础与缺陷生命周期”结构化笔记。", "#0891b2"],
      ["知识问答", "提问 Verification 和 Validation 的区别，展示来源引用。", "#16a34a"],
      ["岗位测评", "生成边界值分析、缺陷生命周期等题目并提交答案。", "#d97706"],
      ["复习闭环", "查看错题、薄弱点、易混概念和 SM-2 复习任务。", "#e11d48"],
    ],
    "客服政策与话术训练": [
      ["导入资料", "上传退款政策、投诉升级 SOP、账号安全处理流程。", "#2563eb"],
      ["知识问答", "询问什么情况下可以承诺退款，验证政策边界。", "#0891b2"],
      ["场景出题", "生成退款条件、升级投诉、隐私数据处理题。", "#16a34a"],
      ["语义批改", "简答题按话术准确性、合规边界、完整性评分。", "#d97706"],
      ["主管复训", "根据薄弱点安排定向辅导，减少质检扣分。", "#e11d48"],
    ],
    "合规制度培训": [
      ["制度入库", "导入合规手册、审计案例、监管问答。", "#2563eb"],
      ["条款摘要", "生成适用范围、风险点、操作禁区。", "#0891b2"],
      ["案例测评", "生成判断题和风险识别简答题。", "#16a34a"],
      ["风险反馈", "指出遗漏的审批、留痕、权限和数据处理风险。", "#d97706"],
      ["审计记录", "保留学习、测试、错题、复习的可追溯记录。", "#e11d48"],
    ],
  };
  return (
    <>
      <header className="page-head">
        <h1>企业级落地蓝图</h1>
        <p>从部门试点到集团级多租户，把学习助手扩展为企业知识运营与人才训练平台。</p>
      </header>
      <Section title="企业学习闭环"><FlowStrip /></Section>
      <Section title="企业级使用场景"><ScenarioGrid /></Section>
      <Section title="场景演示路径">
        <select className="scene-select" value={scene} onChange={(e) => setScene(e.target.value)}>
          {Object.keys(playbooks).map((key) => <option key={key}>{key}</option>)}
        </select>
        <div className="list-stack">
          {playbooks[scene].map(([title, desc, color]) => (
            <div className="line-row" style={{ "--accent": color }} key={title}><strong>{title}</strong><span>{desc}</span></div>
          ))}
        </div>
      </Section>
      <Section title="企业价值指标">
        <MetricBand metrics={[
          { label: "新人达标周期", value: "↓", note: "入职到通过岗位测评的平均天数", color: "#2563eb" },
          { label: "题库维护成本", value: "↓", note: "由 Agent 从知识库自动生成训练题", color: "#0891b2" },
          { label: "高频错题率", value: "↓", note: "错题闭环与 SM-2 复习降低重复错误", color: "#e11d48" },
          { label: "知识命中率", value: "↑", note: "Multi-Query + Rerank 提升检索质量", color: "#16a34a" },
        ]} />
      </Section>
      <Section title="治理能力清单">
        <div className="scenario-grid">
          {[
            ["身份与组织", "JWT/OIDC、部门、岗位、角色和租户隔离", "#2563eb"],
            ["内容治理", "专家审核、版本管理、敏感信息检测和题目发布流", "#0891b2"],
            ["数据安全", "知识库权限过滤、审计日志、密钥托管和数据脱敏", "#e11d48"],
            ["可观测性", "结构化日志、健康检查、模型成本统计和备份恢复", "#16a34a"],
          ].map(([title, desc, color]) => (
            <div className="line-row" style={{ "--accent": color }} key={title}><strong>{title}</strong><span>{desc}</span></div>
          ))}
        </div>
      </Section>
    </>
  );
}

function SystemPage({ health }) {
  const stats = useAsync(() => request("/rag/stats").then((r) => r.data || {}), []);
  const s = stats.data || {};
  return (
    <>
      <header className="page-head">
        <h1>系统信息</h1>
        <p>查看后端连接、模型供应商、Agent 注册和知识库资产状态。</p>
      </header>
      <MetricBand metrics={[
        { label: "LLM Providers", value: health?.llm_providers?.join(", ") || "无", note: "模型路由可用供应商", color: "#2563eb" },
        { label: "Agents", value: health?.agents || 0, note: "已注册专业 Agent", color: "#0891b2" },
        { label: "总笔记", value: s.total_notes || 0, note: "结构化知识记录", color: "#16a34a" },
        { label: "向量块", value: s.total_chunks || 0, note: "RAG 检索资产", color: "#d97706" },
      ]} />
      <Section title="启动方式">
        <pre>{`# 后端
cd backend
python -m app.main

# React 前端
cd frontend
npm install
npm run dev`}</pre>
      </Section>
    </>
  );
}

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [health, setHealth] = useState(null);

  useEffect(() => {
    let active = true;

    async function checkHealth() {
      try {
        const response = await fetch(`${ROOT_BASE}/health`);
        const data = response.ok ? await response.json() : null;
        if (active) setHealth(data);
      } catch {
        if (active) setHealth(null);
      }
    }

    checkHealth();
    const timer = window.setInterval(checkHealth, 5000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const pageView = {
    dashboard: <Dashboard setPage={setPage} />,
    "notes-generate": <GenerateNote setPage={setPage} />,
    notes: <NotesPage />,
    knowledge: <KnowledgePage />,
    quiz: <QuizPage />,
    rag: <RagPage />,
    review: <ReviewPage setPage={setPage} />,
    memory: <MemoryPage />,
    blueprint: <BlueprintPage />,
    system: <SystemPage health={health} />,
  }[page];

  return (
    <Shell page={page} setPage={setPage} health={health}>
      {pageView}
    </Shell>
  );
}
