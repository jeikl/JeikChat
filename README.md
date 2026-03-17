<div align="center">

<img src="frontend/public/logo.png" alt="JeikChat Logo" width="120" style="margin: 20px 0;">

# 🚀 JeikChat 全能智能助手

**无缝集成大语言模型生态 · MCP协议扩展 · RAG知识库 · 多模型混合调用**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=white)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-1C3C3C?style=flat-square)](https://langchain.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

<p align="center">
  <strong>基于大语言模型的前后端分离AI助手解决方案</strong>
</p>

<p align="center">
  <a href="#-项目简介">项目简介</a> •
  <a href="#-核心特性">核心特性</a> •
  <a href="#-技术架构">技术架构</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-目录结构">目录结构</a> •
  <a href="#-api文档">API文档</a> •
  <a href="#-部署指南">部署指南</a>
</p>

</div>

---

## 📖 项目简介

**JeikChat** 是一个功能完善的全能AI助手系统，采用现代化的前后端分离架构设计。后端基于 **Python** 生态（`FastAPI` + `LangChain` + `LangGraph`），前端基于 **React** 生态（`Vite` + `TailwindCSS` + `Zustand`）。

项目深度集成了**多模型自由切换**、**RAG知识库高级检索**（支持多种文档格式解析与向量存储）、**MCP (Model Context Protocol) 工具动态扩展**，以及带**持久化记忆 (PostgreSQL Checkpoint)** 的对话编排能力。UI设计参考主流AI产品，完美适配桌面端和移动端，为您提供极佳的交互体验。

### 🎯 设计理念

- **模块化架构**：各功能模块独立设计，易于扩展和维护
- **多模型支持**：无缝切换国内外主流大模型
- **知识增强**：RAG技术让AI具备领域专业知识
- **工具生态**：MCP协议支持无限扩展AI能力边界
- **流式体验**：基于SSE的实时流式输出，打字机效果

> ⚠️ **注意**：MCP 集成功能需要较新的模型（推荐使用2025年中旬以后发布的模型）才能获得最佳的 Function Calling 体验。系统自带缓存机制，初次加载后响应速度会显著提升。

**作者**: jeikliu@outlook.com

---

## ✨ 核心特性

### 🤖 智能对话与多模型支持

| 特性 | 说明 |
|------|------|
| **主流大模型全覆盖** | 原生支持 OpenAI、Anthropic、Google GenAI、阿里云 (DashScope)、字节跳动 (Doubao)、月之暗面 (Kimi)、DeepSeek、智谱AI、百度文心、讯飞星火等 |
| **极致的流式体验** | 基于 Server-Sent Events (SSE) 的流式输出与打字机效果 |
| **长期记忆** | 引入 `langgraph-checkpoint-postgres` 提供图状态的持久化，实现精准的历史对话管理和长期上下文跟踪 |
| **富文本交互** | 完美支持 Markdown 渲染、代码高亮、消息复制与重新生成 |
| **思考模式** | 支持模型的推理过程展示（Thinking Mode） |

### 📚 RAG 知识库增强检索

| 特性 | 说明 |
|------|------|
| **全格式文档解析** | 基于 `unstructured` 深度集成，支持 PDF, Excel, Word, CSV, Markdown, TXT 等多格式解析 |
| **灵活的向量存储** | 支持 **ChromaDB** (本地轻量级) 和 **Qdrant** 等多种向量数据库引擎 |
| **高级检索能力** | 支持文档的分块 (Chunking)、Embedding 模型切换、并行知识库挂载以及多知识库混合检索 |
| **异步处理** | 支持大型文档的异步处理与构建进度追踪 |
| **Embedding模型** | 支持魔塔、OpenAI、HuggingFace等多种Embedding服务 |

### 🛠️ Agent 工具系统 (MCP)

| 特性 | 说明 |
|------|------|
| **协议原生支持** | 基于 `langchain-mcp-adapters`，标准支持 MCP 协议 |
| **多传输通道** | 支持 HTTP Streamable、SSE、STDIO 等传输层 |
| **工具生态** | 内置工具发现、缓存与热重载，可轻松对接 Bing搜索、GitHub操作、12306查询、文件读写等外部扩展 |
| **动态加载** | 支持运行时动态加载和卸载MCP服务 |

### 🎨 现代化前端界面

| 特性 | 说明 |
|------|------|
| **响应式设计** | 完美适配桌面端、平板和移动端 |
| **深色模式** | 支持亮色/暗色主题切换 |
| **代码高亮** | 支持多种编程语言的语法高亮 |
| **LaTeX支持** | 数学公式渲染支持 |
| **消息操作** | 支持复制、重新生成、删除等操作 |

---

## 🛠️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              JeikChat 系统架构                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         前端层 (Frontend)                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │   React 18  │  │  TypeScript │  │    Vite 5   │  │ TailwindCSS │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │   Zustand   │  │  React Query│  │ React Router│  │    Axios    │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼ HTTP/WebSocket                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         API网关层 (FastAPI)                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │   CORS      │  │   JWT Auth  │  │  Rate Limit │  │   Swagger   │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        业务服务层 (Services)                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │ Chat Service│  │  RAG Service│  │Tool Service │  │File Service │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        AI引擎层 (AI Engine)                          │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                      LangChain / LangGraph                   │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │   │   │
│  │  │  │   ChatModel │  │  Embedding  │  │   Vector Store      │  │   │   │
│  │  │  │  (多模型)    │  │   (向量化)   │  │ (Chroma/Qdrant)    │  │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    MCP 工具系统                              │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │   │   │
│  │  │  │   STDIO     │  │     SSE     │  │  HTTP Streamable    │  │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        数据持久层 (Storage)                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │  PostgreSQL │  │  ChromaDB   │  │   Qdrant    │  │     S3      │ │   │
│  │  │  (对话记忆)  │  │  (向量存储)  │  │  (向量存储)  │  │  (文件存储)  │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 后端技术栈 (Backend)

| 技术/依赖 | 版本 | 用途说明 |
| :--- | :--- | :--- |
| **Python** | >=3.11, <3.14 | 核心运行环境 |
| **FastAPI** | Latest | 高性能异步 Web 框架 |
| **Uvicorn** | [standard] | ASGI 服务器，支持 HTTP/2 和 WebSocket |
| **LangChain** | Latest | 大模型应用开发框架 |
| **LangChain-Community** | Latest | LangChain社区组件 |
| **LangChain-OpenAI** | Latest | OpenAI模型集成 |
| **LangChain-DeepSeek** | >=1.0.1 | DeepSeek模型集成 |
| **LangChain-Google-GenAI** | >=4.2.1 | Google Gemini模型集成 |
| **LangChain-Chroma** | >=1.1.0 | ChromaDB向量存储集成 |
| **LangChain-Qdrant** | >=1.1.0 | Qdrant向量存储集成 |
| **LangChain-MCP-Adapters** | >=0.2.1 | MCP协议适配器 |
| **LangChain-Unstructured** | >=1.0.1 | 文档解析集成 |
| **LangGraph** | Latest | 状态化多Agent工作流编排 |
| **LangGraph-Checkpoint-Postgres** | Latest | PostgreSQL持久化检查点 |
| **ChromaDB** | Latest | 本地轻量级向量数据库 |
| **Qdrant** | Latest | 高性能向量数据库 |
| **Unstructured** | >=0.21.5 | 非结构化数据解析（全功能版） |
| **Sentence-Transformers** | Latest | 本地Embedding模型 |
| **PyPDF** | Latest | PDF文档解析 |
| **Python-Docx** | Latest | Word文档解析 |
| **OpenPyXL** | Latest | Excel文档解析 |
| **Pandas** | Latest | 数据处理与分析 |
| **SQLAlchemy** | Latest | ORM框架 |
| **Psycopg** | [binary,pool] | PostgreSQL异步驱动 |
| **Pydantic** | Latest | 数据验证与序列化 |
| **Pydantic-Settings** | Latest | 配置管理 |
| **HTTPX** | Latest | 异步HTTP客户端 |
| **Tenacity** | Latest | 重试机制 |
| **Boto3** | >=1.42.69 | AWS S3兼容存储 |
| **DashScope** | >=1.25.14 | 阿里云灵积模型服务 |
| **Python-Magic** | Latest | 文件类型检测 |
| **AIOFiles** | Latest | 异步文件操作 |
| **Python-Jose** | [cryptography] | JWT认证 |
| **Passlib** | [bcrypt] | 密码哈希 |
| **Python-Multipart** | Latest | 表单数据解析 |
| **PyYAML** | Latest | YAML配置解析 |
| **Pytest** | >=7.0.0 | 单元测试框架 |
| **Pytest-Asyncio** | >=0.21.0 | 异步测试支持 |

### 前端技术栈 (Frontend)

| 技术/依赖 | 版本 | 用途说明 |
| :--- | :--- | :--- |
| **React** | ^18.2.0 | UI组件库 |
| **React-DOM** | ^18.2.0 | DOM渲染 |
| **TypeScript** | ^5.3.3 | 类型系统 |
| **Vite** | ^5.0.12 | 构建工具 |
| **Zustand** | ^4.5.0 | 轻量级状态管理 |
| **TanStack React Query** | ^5.17.0 | 服务端状态管理 |
| **React Router DOM** | ^6.21.3 | 路由管理 |
| **TailwindCSS** | ^3.4.1 | 原子化CSS框架 |
| **PostCSS** | ^8.4.33 | CSS处理 |
| **Autoprefixer** | ^10.4.17 | CSS前缀自动补全 |
| **Axios** | ^1.6.5 | HTTP客户端 |
| **React Markdown** | ^9.0.1 | Markdown渲染 |
| **React Syntax Highlighter** | ^15.5.0 | 代码语法高亮 |
| **Rehype-Highlight** | ^7.0.0 | 代码高亮插件 |
| **Rehype-Raw** | ^7.0.0 | 原始HTML支持 |
| **Remark-GFM** | ^4.0.0 | GitHub风格Markdown |
| **Lucide React** | ^0.312.0 | 图标库 |
| **Date-Fns** | ^3.2.0 | 日期处理 |
| **React-Hot-Toast** | ^2.4.1 | 消息提示 |
| **UUID** | ^13.0.0 | UUID生成 |
| **ESLint** | ^8.56.0 | 代码检查 |
| **@Types/*** | Latest | TypeScript类型定义 |

---

## 📁 目录结构

```
aichat/
├── 📁 backend/                    # 后端服务
│   ├── 📁 agent/                  # AI Agent核心模块
│   │   ├── 📁 adapter/            # 模型适配器
│   │   │   └── embedding.py       # Embedding模型适配
│   │   ├── 📁 demo/               # 示例代码
│   │   ├── 📁 knowledges/         # 知识库文件存储
│   │   │   └── vector_store/      # 向量存储目录
│   │   ├── 📁 mcp/                # MCP工具系统
│   │   │   ├── mcp.yaml           # MCP服务配置
│   │   │   ├── mcpToolNode.py     # MCP工具节点
│   │   │   ├── cache_manager.py   # 缓存管理
│   │   │   ├── config_loader.py   # 配置加载器
│   │   │   └── connection_manager.py # 连接管理
│   │   ├── 📁 prompt/             # 提示词模板
│   │   ├── 📁 tools/              # 内置工具
│   │   │   ├── RAG.py             # RAG检索工具
│   │   │   ├── calculate.py       # 计算工具
│   │   │   ├── getNowTime.py      # 时间工具
│   │   │   ├── werther.py         # 天气工具
│   │   │   └── retrieve_docs.py   # 文档检索
│   │   └── chatRouterStream.py    # 聊天路由(流式)
│   ├── 📁 api/                    # API接口层
│   │   ├── 📁 routes/             # 路由模块
│   │   │   ├── chat.py            # 聊天接口
│   │   │   ├── knowledge.py       # 知识库接口
│   │   │   ├── model.py           # 模型配置接口
│   │   │   ├── tools.py           # 工具管理接口
│   │   │   ├── tools_stream.py    # 工具流式接口
│   │   │   ├── file.py            # 文件接口
│   │   │   └── mock.py            # 测试模式接口
│   │   └── response.py            # 统一响应封装
│   ├── 📁 config/                 # 配置文件
│   │   ├── app_config.yaml        # 应用配置
│ │   ├── models.yaml              # 模型配置
│   │   ├── prompts.yaml           # 提示词配置
│   │   └── settings.py            # 配置管理类
│   ├── 📁 fileUntils/             # 文件工具
│   │   └── RustFs.py              # Rust文件系统
│   ├── 📁 logs/                   # 日志目录
│   ├── 📁 schemas/                # Pydantic模型
│   │   ├── chat.py                # 聊天相关模型
│   │   └── knowledge.py           # 知识库相关模型
│   ├── 📁 services/               # 业务服务层
│   │   ├── llm.py                 # LLM服务
│   │   ├── rag.py                 # RAG服务
│   │   ├── knowledge.py           # 知识库服务
│   │   ├── knowledge_mapping.py   # 知识库映射
│   │   └── stream.py              # 流式服务
│   ├── 📁 app/                    # 应用入口
│   │   └── main.py                # FastAPI主应用
│   ├── pyproject.toml             # Python项目配置
│   ├── uv.lock                    # UV锁文件
│   └── cli.py                     # CLI命令行工具
│
├── 📁 frontend/                   # 前端应用
│   ├── 📁 src/
│   │   ├── 📁 components/         # 组件目录
│   │   │   ├── 📁 Chat/           # 聊天组件
│   │   │   │   ├── ChatContainer.tsx
│   │   │   │   ├── InputArea.tsx
│   │   │   │   └── MessageItem.tsx
│   │   │   └── 📁 Common/         # 通用组件
│   │   │       ├── Header.tsx
│   │   │       └── Sidebar.tsx
│   │   ├── 📁 pages/              # 页面组件
│   │   │   ├── ChatPage.tsx       # 聊天页面
│   │   │   ├── KnowledgePage.tsx  # 知识库页面
│   │   │   ├── AgentToolsPage.tsx # 工具页面
│   │   │   └── SettingsPage.tsx   # 设置页面
│   │   ├── 📁 services/           # API服务
│   │   │   ├── api.ts             # API封装
│   │   │   ├── chat.ts            # 聊天服务
│   │   │   ├── client.ts          # HTTP客户端
│   │   │   └── knowledge.ts       # 知识库服务
│   │   ├── 📁 stores/             # 状态管理
│   │   │   ├── chatStore.ts       # 聊天状态
│   │   │   ├── knowledgeStore.ts  # 知识库状态
│   │   │   └── settingsStore.ts   # 设置状态
│   │   ├── 📁 types/              # TypeScript类型
│   │   │   ├── chat.ts            # 聊天类型
│   │   │   ├── knowledge.ts       # 知识库类型
│   │   │   └── config.ts          # 配置类型
│   │   ├── 📁 utils/              # 工具函数
│   │   │   └── toast.tsx          # 消息提示
│   │   ├── 📁 assets/             # 静态资源
│   │   │   └── styles/
│   │   │       └── globals.css    # 全局样式
│   │   ├── App.tsx                # 根组件
│   │   └── main.tsx               # 入口文件
│   ├── 📁 public/                 # 公共资源
│   │   ├── logo.png               # Logo
│   │   └── gitee.svg              # Gitee图标
│   ├── index.html                 # HTML模板
│   ├── package.json               # NPM配置
│   ├── tsconfig.json              # TypeScript配置
│   ├── vite.config.ts             # Vite配置
│   ├── tailwind.config.js         # Tailwind配置
│   └── nginx.conf                 # Nginx配置
│
├── 📄 README.md                   # 项目说明
├── 📄 API文档.md                   # API接口文档
└── 📄 .env                        # 环境变量
```

---

## 🚀 快速开始

### 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Python | >= 3.11, < 3.14 | 推荐使用 3.11 或 3.12 |
| Node.js | >= 18 | 推荐使用 LTS 版本 |
| PostgreSQL | >= 14 | 可选，用于高级记忆持久化 |
| Git | Latest | 代码版本管理 |

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd aichat
```

### 2. 环境配置

#### 后端配置

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖（推荐使用uv，更快）
pip install uv
uv pip install -e .

# 或者使用pip
pip install -e .
```

#### 前端配置

```bash
cd ../frontend

# 安装依赖
npm install

# 或者使用pnpm（更快）
pnpm install
```

#### 环境变量配置

在项目根目录创建 `.env` 文件：

```env
# ============================================================
# 应用基础配置
# ============================================================
APP_NAME="JeikChat"
APP_VERSION="3.0.0"
AICHAT_ENVIRONMENT="dev"
JEIKCHAT_DEV_MODE="true"

# ============================================================
# 服务端口配置
# ============================================================
BACKEND_HOST="0.0.0.0"
BACKEND_PORT="8000"
VITE_FRONTEND_HOST="::"
VITE_FRONTEND_PORT="5173"

# ============================================================
# CORS配置
# ============================================================
CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"

# ============================================================
# 数据库配置
# ============================================================
DB_URL="postgresql://username:password@localhost:5432/jeikchat?sslmode=disable"
# 或者使用SQLite（开发环境）
# DB_URL="sqlite:///./jeikchat.db"

# ============================================================
# 向量存储配置
# ============================================================
VECTOR_STORE_TYPE="chroma"  # 可选: chroma, qdrant

# ============================================================
# 文件上传配置
# ============================================================
MAX_FILE_SIZE="104857600"  # 100MB
CHUNK_SIZE="1000"
CHUNK_OVERLAP="200"

# ============================================================
# LLM API密钥配置
# ============================================================
# OpenAI
OPENAI_API_KEY="sk-..."
OPENAI_BASE_URL="https://api.openai.com/v1"

# DeepSeek
DEEPSEEK_API_KEY="sk-..."

# 阿里云DashScope
DASHSCOPE_API_KEY="sk-..."

# Google Gemini
GOOGLE_API_KEY="AIza..."

# 智谱AI
ZHIPU_API_KEY="..."

# 百度文心
BAIDU_API_KEY="..."
BAIDU_SECRET_KEY="..."

# 讯飞星火
XFYUN_API_KEY="..."

# ============================================================
# MCP配置
# ============================================================
MCP_CONFIG_PATH="./agent/mcp/mcp.yaml"
```

### 3. 启动服务

项目提供了便捷的 CLI 工具 `jeikchat` 用于管理服务。

#### 方式一：一键启动所有服务（推荐）

```bash
# 在激活了后端虚拟环境的终端中执行
jeikchat run all
# 或使用简写
jeikchat run a
```

#### 方式二：分别启动

```bash
# 终端1: 启动后端 API (默认 8000 端口)
cd backend
jeikchat run back

# 终端2: 启动前端页面 (默认 5173 端口)
cd frontend
npm run dev
```

#### 方式三：使用Python直接启动

```bash
# 后端
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端
cd frontend
npm run dev
```

### 4. 访问服务

- 🌍 **Web 界面**: http://localhost:5173
- 📖 **API 文档 (Swagger)**: http://localhost:8000/docs
- 🔍 **ReDoc 文档**: http://localhost:8000/redoc
- ✅ **健康检查**: http://localhost:8000/health

### 5. CLI 命令参考

```bash
# 查看帮助
jeikchat --help

# 启动后端
jeikchat run back

# 启动后端（测试模式）
jeikchat run back --test

# 启动前端
jeikchat run front

# 一键启动所有服务
jeikchat run all

# 指定端口启动
jeikchat run back --port 8080
jeikchat run front --port 3000
```

---

## 📦 部署指南

### Docker Compose 部署（推荐生产环境）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    container_name: jeikchat-postgres
    environment:
      POSTGRES_USER: jeikchat
      POSTGRES_PASSWORD: your_password
      POSTGRES_DB: jeikchat
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  # ChromaDB向量数据库
  chroma:
    image: chromadb/chroma:latest
    container_name: jeikchat-chroma
    volumes:
      - chroma_data:/chroma/chroma
    ports:
      - "8001:8000"
    restart: unless-stopped

  # 后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: jeikchat-backend
    environment:
      - DB_URL=postgresql://jeikchat:your_password@postgres:5432/jeikchat
      - VECTOR_STORE_TYPE=chroma
      - CHROMA_HOST=chroma
      - CHROMA_PORT=8000
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - chroma
    restart: unless-stopped

  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: jeikchat-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  chroma_data:
```

启动命令：

```bash
docker-compose up -d --build
```

### 传统服务器部署

#### 后端部署

```bash
cd backend

# 安装生产依赖
pip install -e .

# 使用Gunicorn + Uvicorn启动
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 或使用Uvicorn直接启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 前端部署

```bash
cd frontend

# 构建生产版本
npm run build

# 将dist目录部署到Nginx
```

#### Nginx配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/jeikchat/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # SSE支持
        proxy_buffering off;
        proxy_read_timeout 86400;
    }

    # WebSocket支持（如需要）
    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 🔧 配置详解

### 模型配置 (`backend/config/models.yaml`)

```yaml
# Embedding模型配置
embeddings:
  default_provider: modelscope
  providers:
    modelscope:
      name: "魔塔"
      api_key: "your-api-key"
      base_url: "https://api-inference.modelscope.cn/v1"
      models:
        - id: "Qwen/Qwen3-Embedding-8B"
          default: true
        - id: "bge-small-zh-v1.5"

# LLM提供商配置
providers:
  openai:
    name: "OpenAI"
    api_key: "sk-..."
    base_url: "https://api.openai.com/v1"
    display_name: "OpenAI"
    models:
      - id: "gpt-4o"
        tags: ["多模态"]
      - id: "gpt-4o-mini"
    enable: true

  deepseek:
    name: "DeepSeek"
    api_key: "sk-..."
    base_url: "https://api.deepseek.com"
    display_name: "DeepSeek"
    models:
      - id: "deepseek-chat"
      - id: "deepseek-reasoner"
        tags: ["推理"]
    enable: true
```

### MCP配置 (`backend/agent/mcp/mcp.yaml`)

```yaml
servers:
  # STDIO模式
  - name: postgres-full
    transport: stdio
    command: npx
    args: [-y, mcp-postgres-full-access, postgresql://...]

  # SSE模式
  - name: zhipu-web-search
    transport: sse
    url: https://open.bigmodel.cn/api/mcp/web_search/sse?Authorization=...

  # HTTP Streamable模式
  - name: github
    transport: streamable_http
    url: https://mcp.api-inference.modelscope.net/.../mcp

settings:
  timeout: 30
  auto_reload: true
  log_level: info

# 默认选中的工具
default_selected_tools:
  - get_current_time
  - zhipu-web-search-*
```

---

## 🧪 测试

```bash
cd backend

# 运行所有测试
pytest

# 运行异步测试
pytest -v

# 测试模式启动
jeikchat run back --test
```

---

## 📚 相关文档

- [API接口文档](./API文档.md) - 详细的API接口说明
- [LangChain文档](https://python.langchain.com/) - LangChain官方文档
- [LangGraph文档](https://langchain-ai.github.io/langgraph/) - LangGraph官方文档
- [MCP协议文档](https://modelcontextprotocol.io/) - Model Context Protocol官方文档
- [FastAPI文档](https://fastapi.tiangolo.com/) - FastAPI官方文档
- [React文档](https://react.dev/) - React官方文档

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目基于 [MIT](LICENSE) 许可证开源。

---

## 💬 联系方式

- 📧 邮箱: jeikliu@outlook.com
- 🐙 GitHub: [https://github.com/jeikl/JeikChat](https://github.com/jeikl/JeikChat)
- 🦊 Gitee: [https://gitee.com/jeikl/jeikchat](https://gitee.com/jeikl/jeikchat)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个Star! ⭐**

</div>
