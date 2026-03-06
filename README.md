# AI 别墅设计助手

通过 AI 对话帮助用户设计梦想别墅的 Web 应用。支持智能对话收集建房需求、自动提取结构化参数、AI 生成别墅效果图。

## 功能特性

- **智能对话** — Gemini 1.5 Pro 驱动的建筑设计顾问，通过友好对话逐步收集需求
- **结构化需求提取** — AI 自动从对话中提取土地面积、楼层、风格、房间数等参数
- **效果图生成** — 集成 nano-banana-2 图像生成 API，根据需求生成别墅效果图
- **流式响应** — SSE 实时流式显示 AI 回复，体验流畅
- **图片上传** — 支持上传参考图片，AI 多模态理解
- **匿名使用** — 无需注册，基于 session_id 的匿名模式

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 16 + React + Tailwind CSS v4 + shadcn/ui + Zustand |
| 后端 | Python FastAPI + SQLAlchemy + Pydantic |
| AI 对话 | Google Gemini 1.5 Pro API |
| 图像生成 | nano-banana-2（兼容 OpenAI DALL-E 格式） |
| 数据库 | SQLite（本地开发） |

## 项目结构

```
别墅/
├── frontend/                # Next.js 前端
│   └── src/
│       ├── app/             # 页面路由
│       ├── components/chat/ # 对话组件（ChatArea, Sidebar, InputBar 等）
│       ├── components/ui/   # shadcn/ui 基础组件
│       └── lib/             # API 封装 + Zustand Store
├── backend/                 # FastAPI 后端
│   └── app/
│       ├── config.py        # 环境变量配置
│       ├── database.py      # SQLAlchemy 数据库连接
│       ├── main.py          # FastAPI 入口
│       ├── models/          # ORM 模型（Conversation, Message, Requirement, Plan）
│       ├── routers/         # 路由（chat, plan, upload）
│       ├── schemas/         # Pydantic 数据模型
│       └── services/        # 核心服务（ai_service, chat_service, image_service）
└── temp/                    # 产品文档
```

## 快速开始

### 前置条件

- **Node.js** >= 18
- **Python** >= 3.11
- **npm**

### 1. 启动后端

```bash
# 进入后端目录
cd backend

# 创建虚拟环境并安装依赖
python3 -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt

# 配置环境变量（复制并编辑 .env）
cp .env.example .env
# 编辑 .env，填入你的 API Key

# 启动后端（开发模式，支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动前端（开发模式）
npm run dev
```

### 3. 打开浏览器

访问 http://localhost:3000 即可使用。

## 环境变量说明

### 后端 (`backend/.env`)

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `AI_API_KEY` | AI 对话 API Key（不填则模拟模式） | — |
| `AI_API_BASE` | AI 对话 API 地址（OpenAI 兼容） | `https://api.bltcy.ai/v1` |
| `AI_MODEL` | AI 对话模型名 | `gemini-3.1-pro-preview` |
| `IMAGE_API_KEY` | nano-banana-2 图像生成 API Key | — |
| `IMAGE_API_BASE` | 图像生成 API 地址 | `https://api.bltcy.ai/v1` |
| `IMAGE_MODEL` | 图像生成模型名 | `nano-banana-2` |
| `HTTP_PROXY` | HTTP 代理地址（可选） | — |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./villa_ai.db` |
| `UPLOAD_DIR` | 上传文件存储目录 | `./uploads` |

### 前端 (`frontend/.env.local`)

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `NEXT_PUBLIC_API_BASE` | 后端 API 地址 | `http://localhost:8000` |

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/conversations` | 创建新会话 |
| GET | `/api/conversations?session_id=xxx` | 获取会话列表 |
| GET | `/api/conversations/:id` | 获取会话详情（含消息） |
| DELETE | `/api/conversations/:id` | 删除会话 |
| POST | `/api/conversations/:id/messages?stream=true` | 发送消息（SSE 流式） |
| GET | `/api/conversations/:id/requirement` | 获取结构化需求 |
| POST | `/api/conversations/:id/generate-image` | 生成效果图 |
| POST | `/api/upload/image` | 上传图片 |
| GET | `/api/upload/files/:filename` | 获取已上传文件 |
| GET | `/api/knowledge/search?q=xxx&n=3` | 检索建筑规范 |
| GET | `/api/knowledge/stats` | 知识库统计 |

## RAG 知识库

内置了中国农村自建房建筑规范知识库，基于 ChromaDB 向量数据库实现语义检索。

- **知识库目录**: `backend/knowledge_base/` — 放置 Markdown 格式的规范文档
- **自动索引**: 首次启动时自动读取文档、分段、写入 ChromaDB
- **对话注入**: AI 回复前自动检索相关规范，注入为上下文参考
- **已包含规范**: 用地规划、结构安全、功能布局、给排水、电气、节能保温、消防安全、常见户型建议

要添加新的规范文档，只需将 `.md` 文件放入 `backend/knowledge_base/` 目录，然后删除 `backend/chroma_db/` 并重启后端即可重建索引。

## 开发模式说明

- 未配置 `GOOGLE_API_KEY` 时，AI 对话自动切换为**模拟模式**，返回预设回复，方便前端调试
- 模拟模式支持关键词匹配（面积、楼层、风格等），模拟需求收集流程
- 图像生成需要有效的 `IMAGE_API_KEY` 才能使用

## 待开发功能

- [x] RAG 知识库（建筑规范自动检索）
- [ ] 用户登录注册系统
- [ ] 方案对比和历史版本管理
- [ ] 导出 PDF 报告
- [ ] 生产环境部署（Vercel + Railway）
