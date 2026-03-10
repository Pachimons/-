# AI 别墅设计助手

通过 AI 对话帮助用户设计梦想别墅的 Web 应用。支持智能对话收集建房需求、自动提取结构化参数、AI 生成别墅效果图。

---

## 功能特性

- **智能对话** — Gemini 3.1 Pro 驱动的建筑设计顾问，通过友好对话逐步收集需求
- **结构化需求提取** — AI 自动从对话中提取土地面积、楼层、风格、房间数等参数，实时显示在右侧面板
- **效果图生成** — 集成 nano-banana-2 图像生成 API，根据需求生成别墅效果图（持久化存储）
- **RAG 知识库** — 内置中国农村自建房建筑规范，对话中自动检索相关法规注入 AI 上下文
- **流式响应** — SSE 实时流式显示 AI 回复，体验流畅
- **图片上传** — 支持上传参考图片，AI 多模态理解
- **匿名使用** — 无需注册，基于 session_id 的匿名模式
- **三栏布局** — 左栏会话列表 | 中栏对话区（可滚动）| 右栏需求进度面板（固定）

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 16 + React 19 + Tailwind CSS v4 + shadcn/ui + Zustand |
| 后端 | Python FastAPI + SQLAlchemy + Pydantic |
| AI 对话 | Gemini 3.1 Pro Preview（通过 bltcy.ai OpenAI 兼容接口） |
| 图像生成 | nano-banana-2（通过 bltcy.ai，兼容 OpenAI DALL-E 格式） |
| 向量数据库 | ChromaDB（RAG 知识库语义检索） |
| 数据库 | SQLite |
| 部署 | Vercel（前端）+ Render（后端） |

---

## 项目结构

```
别墅/
├── frontend/                        # Next.js 16 前端
│   └── src/
│       ├── app/                     # 页面路由 (page.tsx = 三栏主页面)
│       ├── components/chat/         # 对话组件
│       │   ├── ChatArea.tsx         # 中栏：消息列表 + 输入栏
│       │   ├── Sidebar.tsx          # 左栏：历史会话列表
│       │   ├── RequirementPanel.tsx # 右栏：需求进度 + 效果图
│       │   ├── InputBar.tsx         # 消息输入框
│       │   ├── MessageBubble.tsx    # 单条消息气泡
│       │   └── StreamingBubble.tsx  # 流式回复气泡
│       ├── components/ui/           # shadcn/ui 基础组件
│       └── lib/
│           ├── api.ts               # 后端 API 请求封装（含 SSE 流式）
│           ├── store.ts             # Zustand 全局状态管理
│           └── utils.ts             # 工具函数
├── backend/                         # FastAPI 后端
│   ├── app/
│   │   ├── config.py                # 环境变量配置（load_dotenv override=True）
│   │   ├── database.py              # SQLAlchemy 数据库连接
│   │   ├── main.py                  # FastAPI 入口 + CORS + 路由注册
│   │   ├── models/                  # ORM 模型
│   │   │   ├── conversation.py      # 会话
│   │   │   ├── message.py           # 消息
│   │   │   ├── requirement.py       # 结构化需求
│   │   │   └── plan.py              # 设计方案 + 效果图
│   │   ├── routers/                 # API 路由
│   │   │   ├── chat.py              # 会话 + 消息（含 SSE 流式）
│   │   │   ├── plan.py              # 效果图生成 + 查询
│   │   │   ├── upload.py            # 图片上传
│   │   │   └── knowledge.py         # 知识库搜索
│   │   ├── schemas/                 # Pydantic 请求/响应模型
│   │   └── services/                # 核心业务逻辑
│   │       ├── ai_service.py        # AI 对话（httpx 调 OpenAI 兼容接口）
│   │       ├── chat_service.py      # 会话管理 + 需求提取 + 数据清洗
│   │       ├── image_service.py     # 效果图生成
│   │       └── rag_service.py       # RAG 知识库（ChromaDB）
│   ├── knowledge_base/              # 建筑规范 Markdown 文档
│   ├── requirements.txt             # Python 依赖
│   └── .env.example                 # 环境变量模板
├── render.yaml                      # Render 部署配置
├── .gitignore
└── README.md                        # 本文件
```

---

## 核心架构说明

### AI 对话流程

```
用户输入 → 前端 SSE 请求 → 后端 chat_service
  → 注入 RAG 知识库上下文（Top-3 相关规范片段）
  → 调用 ai_service（httpx → bltcy.ai OpenAI 兼容接口）
  → 流式返回自然语言文本（前端实时显示）
  → 流结束后解析 <<<REQUIREMENT>>> 分隔符
  → 提取结构化需求 JSON → 数据清洗 → 存入 SQLite
  → 前端右栏面板自动更新
```

### 关键设计决策

1. **AI 接口**：不直接调用 Google Gemini SDK，而是通过 `bltcy.ai` 的 OpenAI 兼容接口（`/v1/chat/completions`），用 `httpx` 发请求。这样可以轻松切换模型。

2. **流式输出格式**：AI 系统提示词（`ai_service.py` 中的 `SYSTEM_PROMPT`）要求回复分两部分——先自然语言，再用 `<<<REQUIREMENT>>>` 分隔符后跟需求 JSON。流式模式下只推送自然语言给前端，JSON 在流结束后单独解析。

3. **数据清洗**：AI 可能返回 `"200平米"` 而数据库字段是 Float，`chat_service._clean_requirement_data()` 负责提取数字、转换单位（如 "万" → ×10000）、字符串转布尔等。

4. **RAG 知识库**：启动时自动把 `knowledge_base/*.md` 按标题分段、写入 ChromaDB。对话前检索 Top-3 相关片段注入为系统消息。

5. **前端状态管理**：Zustand store 管理所有全局状态（会话列表、消息、需求、效果图）。切换会话时并行加载消息、需求和效果图（`Promise.allSettled`）。

6. **SSE 流式处理**：前端 `api.ts` 中的 `sendMessageStream` 用 `fetch` + `TextDecoder` 解析 SSE。流结束后主动 `controller.abort()` 避免 Safari "Load failed" 报错。

---

## 快速开始（本地开发）

### 前置条件

- **Node.js** >= 18
- **Python** >= 3.11
- **npm**

### 1. 克隆项目

```bash
git clone https://github.com/Pachimons/-.git
cd -
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境并安装依赖
python3 -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key（见下方"环境变量说明"）

# 启动后端（开发模式，支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动前端（开发模式，默认连接 http://localhost:8000）
npm run dev
```

### 4. 打开浏览器

访问 http://localhost:3000 即可使用。

> **提示**：未配置 `AI_API_KEY` 时，AI 对话自动切换为**模拟模式**，返回预设回复，可用于前端调试。模拟模式支持关键词匹配（面积、楼层、风格等），模拟需求收集流程。

---

## 环境变量说明

### 后端 (`backend/.env`)

| 变量名 | 说明 | 必填 | 默认值 |
|--------|------|------|--------|
| `AI_API_KEY` | AI 对话 API Key（bltcy.ai） | 是（否则模拟模式） | — |
| `AI_API_BASE` | AI API 地址（OpenAI 兼容） | 否 | `https://api.bltcy.ai/v1` |
| `AI_MODEL` | AI 模型名 | 否 | `gemini-3.1-pro-preview` |
| `IMAGE_API_KEY` | 图像生成 API Key | 是（否则无法生成效果图） | — |
| `IMAGE_API_BASE` | 图像生成 API 地址 | 否 | `https://api.bltcy.ai/v1` |
| `IMAGE_MODEL` | 图像生成模型名 | 否 | `nano-banana-2` |
| `HTTP_PROXY` | HTTP 代理（本地需翻墙时用，云端不需要） | 否 | — |
| `DATABASE_URL` | 数据库连接字符串 | 否 | `sqlite:///./villa_ai.db` |
| `UPLOAD_DIR` | 上传文件存储目录 | 否 | `./uploads` |
| `CORS_ORIGINS` | 允许的前端域名（逗号分隔） | 否 | `*` |

### 前端 (`frontend/.env.local`)

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `NEXT_PUBLIC_API_BASE` | 后端 API 地址 | `http://localhost:8000` |

### API Key 获取

AI 对话和图像生成都通过 **bltcy.ai** 平台：
- 注册地址：https://api.bltcy.ai
- AI 对话和图像生成可使用同一个 API Key
- 当前使用模型：`gemini-3.1-pro-preview`（对话）、`nano-banana-2`（图像）

---

## API 接口文档

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/conversations` | 创建新会话 |
| GET | `/api/conversations?session_id=xxx` | 获取会话列表 |
| GET | `/api/conversations/:id` | 获取会话详情（含消息） |
| DELETE | `/api/conversations/:id` | 删除会话 |
| POST | `/api/conversations/:id/messages?stream=true` | 发送消息（SSE 流式） |
| GET | `/api/conversations/:id/requirement` | 获取结构化需求 |
| GET | `/api/conversations/:id/plans` | 获取会话的所有效果图 |
| POST | `/api/conversations/:id/generate-image` | 生成效果图 |
| POST | `/api/upload/image` | 上传图片 |
| GET | `/api/upload/files/:filename` | 获取已上传文件 |
| GET | `/api/knowledge/search?q=xxx&n=3` | 检索建筑规范 |
| GET | `/api/knowledge/stats` | 知识库统计 |

---

## 部署

### 当前部署地址

| 服务 | 平台 | 地址 |
|------|------|------|
| 前端 | Vercel | https://ten-green-27.vercel.app |
| 后端 | Render（免费版） | https://villa-ai.onrender.com |

> **注意**：Render 免费版闲置 15 分钟后会休眠，首次访问需等 30-60 秒冷启动。付费版可常驻运行。

### 部署后端到 Render

1. 在 [Render](https://render.com) 创建 **Web Service**，连接 GitHub 仓库
2. 设置 **Root Directory** = `backend`
3. **Build Command** = `pip install -r requirements.txt`
4. **Start Command** = `gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
5. 添加环境变量（见上方表格），`PYTHON_VERSION` 设为 `3.11.11`
6. `CORS_ORIGINS` 设为前端域名，如 `https://ten-green-27.vercel.app,*`

### 部署前端到 Vercel

1. 在 [Vercel](https://vercel.com) 导入 GitHub 仓库
2. 设置 **Root Directory** = `frontend`
3. Framework Preset 选 `Next.js`
4. 添加环境变量：`NEXT_PUBLIC_API_BASE` = Render 后端地址（如 `https://villa-ai.onrender.com`）
5. 点击 Deploy

### 代码更新后自动部署

```bash
git add -A
git commit -m "描述你的改动"
git push origin main
# Vercel 和 Render 都会自动重新部署
```

---

## RAG 知识库

内置中国农村自建房建筑规范，基于 ChromaDB 向量数据库实现语义检索。

- **知识库目录**: `backend/knowledge_base/` — Markdown 格式规范文档
- **自动索引**: 首次启动时自动读取文档、按标题分段、写入 ChromaDB（存于 `backend/chroma_db/`）
- **对话注入**: AI 回复前自动检索 Top-3 相关规范片段，注入为系统消息
- **已包含规范**: 用地规划、结构安全、功能布局、给排水、电气、节能保温、消防安全、常见户型建议

**添加新规范**：将 `.md` 文件放入 `backend/knowledge_base/`，删除 `backend/chroma_db/` 目录并重启后端即可重建索引。

---

## 已知问题和注意事项

### 已修复的问题
- AI 返回 `"200平米"` 等中文字符串导致数据库写入失败 → 已添加 `_clean_requirement_data` 数据清洗
- Safari/WebKit 上 SSE 流结束后报 "Load failed" → 已在前端主动 abort + 忽略完成后的错误
- 切换历史会话时右栏需求和效果图不更新 → 已在 `selectConversation` 中并行加载
- 首次进入页面不显示历史会话 → 已在 `initSession` 后立即调用 `loadConversations`
- 消息过多后无法滚动 → 已用原生 `overflow-y-auto` 替代 ScrollArea 组件

### 待注意
- Render 免费版冷启动慢（30-60 秒），可考虑升级或换平台
- Render 免费版有 512MB 内存限制，ChromaDB 占用较大
- 本地开发如需代理访问 bltcy.ai，需在 `.env` 中配置 `HTTP_PROXY`（如 `http://127.0.0.1:7890`），云端部署不需要
- 前端使用 Tailwind CSS v4 新语法（`@theme`、`@custom-variant`），IDE 可能报 lint 警告，可忽略
- `config.py` 中 `load_dotenv(override=True)` 确保 `.env` 值覆盖 shell 已有环境变量

---

## 待开发功能

- [x] RAG 知识库（建筑规范自动检索）
- [x] 三栏布局（右栏固定需求面板）
- [x] 效果图持久化存储和历史加载
- [x] 公网部署（Vercel + Render）
- [ ] 公网部署稳定性优化（冷启动、错误重试机制）
- [ ] 用户登录注册系统
- [ ] 方案对比和历史版本管理
- [ ] 导出 PDF 报告
- [ ] 更多建筑规范文档入库
- [ ] 移动端适配（响应式布局）
- [ ] 效果图多角度生成

---

## GitHub 仓库

- **地址**: https://github.com/Pachimons/-
- **分支**: `main`
