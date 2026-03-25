# No Streamlimit 🚀

> FOF 量化投资决策平台 — 告别 Streamlit 崩溃，拥抱稳定架构

## 技术架构

```
┌──────────────┐     HTTP/WS      ┌──────────────────┐
│   Vue 3      │ ◄──────────────► │     FastAPI       │
│   + Vite     │                  │   + Uvicorn       │
│   + ECharts  │                  │   + Pydantic      │
└──────────────┘                  └────────┬──────────┘
                                           │
                                  ┌────────▼──────────┐
                                  │  Celery Worker     │
                                  │  (Redis Broker)    │
                                  │  BL·HRP·AI 计算    │
                                  └───────────────────┘
```

## 快速开始

### 后端
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 填入你的 API Keys
python -m uvicorn main:app --reload --port 8000
```
访问 http://localhost:8000/api/docs 查看 Swagger API 文档

### 前端
```bash
cd frontend
npm install
npm run dev
```
访问 http://localhost:5173 查看界面

## 项目结构

```
├── backend/           # FastAPI 后端
│   ├── main.py        # 应用入口
│   ├── api/v1/        # REST API 路由
│   ├── core/          # 配置 & 安全
│   ├── services/      # 量化引擎 (Phase 2)
│   └── tasks/         # Celery 异步任务
├── frontend/          # Vue 3 前端
│   └── src/
│       ├── views/     # 页面组件
│       ├── api/       # Axios API 封装
│       └── router/    # 路由配置
└── 20260325/          # 旧 Streamlit 项目备份
```

## 迁移进度

- [x] Phase 1: 项目骨架搭建
- [ ] Phase 2: 量化引擎迁移 (services/)
- [ ] Phase 3: 前端完善 & 生产部署
