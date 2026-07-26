# LearnLoop-AI React Frontend

这是 LearnLoop-AI 的 React/Vite 企业级前端。旧版 Streamlit 文件 `streamlit_app.py` 暂时保留为参考，新的主前端使用 `src/App.jsx` 和 `src/styles.css`。

## 启动

```cmd
cd frontend
npm install
npm run dev
```

默认访问：

- React 前端：http://localhost:5173
- FastAPI 后端：http://localhost:8000

如需修改 API 地址：

```env
VITE_API_BASE=http://127.0.0.1:8000/api/v1
```

## 页面

- 学习仪表盘
- 生成笔记
- 我的笔记
- 知识库管理
- 出题练习
- 知识问答
- 复习计划
- 记忆中心
- 企业蓝图
- 系统信息
