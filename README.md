# JeikChat 全能AI助手 无缝集成各种生态 MCP API Tools 多语言混合调用


<p align="center">
  <img src="frontend/public/logo.png" alt="JeikChat Logo" width="120">
</p>

<p align="center">
  <strong>基于大语言模型的全能拓展BOT解决方案</strong>
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#技术架构">技术架构</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#部署指南">部署指南</a> •
  <a href="#api文档">API文档</a>
</p>

---

## 项目简介

JeikChat 是一个基于langchain和langgraph开发的功能完善的全能AI助手，采用现代化的前后端分离架构设计，支持多模型切换、RAG知识库检索、MCP工具扩展等核心功能。UI设计参考主流AI产品（豆包、ChatGPT、通义千问等），完美适配电脑和手机端。


# !!!注意 MCP集成功能 需要较新的模型才能使用 推荐用2025年中旬以后发布的模型 即可使用 快速集成构建你的智能助手!!!

# Python开发 由于Python是解释性语言 所以模型加载和工具的第一次初始化会比较慢 但第一次以后平台会带缓存机制 几乎所有功能都带缓存机制

# 本项目全程采用Langchain+langgraph+python+vue开发 UI美观大气上档次 任何模型 都可以集成 openai形API的大模型和MCP服务更是可以一秒无缝集成!

**作者**: jeikliu@outlook.com

---

## 开发计划

- ✅️ 基础聊天功能
- ✅️ 数据库记忆
- ✅️ 多模型支持
- [x] RAG知识库
- ✅️  MCP工具系统
- [ ] 语音对话
- [ ] 用户认证系统
- [ ] 对话历史持久化
- ✅️ 多语言支持

---


## 功能特性

### 核心功能

- **多模型支持**: 支持 OpenAI、Anthropic、Google、阿里云、字节跳动、Moonshot 等主流大模型
- **流式对话**: 支持 SSE 流式输出，打字机效果，实时响应
- **RAG知识库**: 基于向量检索的增强生成，支持 PDF、Excel、Word、Markdown 等多种文档格式
- **MCP工具扩展**: 支持通过 MCP 协议集成外部工具（搜索、GitHub、12306等）
- **响应式设计**: 完美适配桌面端和移动端

### 智能对话

- [x] 多模型即时切换
- [x] 流式输出 (Server-Sent Events)
- [x] Markdown 渲染与代码高亮
- [x] 消息复制与重新生成
- [x] 打字机效果
- [x] 对话历史管理

### RAG知识库

- [x] 多格式文档支持: PDF, Excel, CSV, Word, TXT, Markdown
- [x] 向量存储与相似度检索 (ChromaDB)
- [x] 多知识库并行管理
- [x] 知识库开关控制
- [x] 自定义 System Prompt

### Agent工具系统 (MCP)

- [x] MCP 协议支持
- [x] 工具自动发现与配置
- [x] 支持多种传输方式: HTTP Streamable、SSE、STDIO
- [x] 内置工具: Bing搜索、GitHub操作、12306查询、智谱搜索等
- [x] 工具权限管理

---

## 技术架构

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.2+ | UI框架 |
| TypeScript | 5.3+ | 类型安全 |
| Vite | 5.0+ | 构建工具 |
| Zustand | 4.5+ | 状态管理 |
| React Router | 6.21+ | 路由管理 |
| TailwindCSS | 3.4+ | 样式框架 |
| @tanstack/react-query | 5.17+ | 数据请求 |
| Lucide React | 0.312+ | 图标库 |
| date-fns | 3.2+ | 时间处理 |

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 运行环境 |
| FastAPI | 0.109+ | Web框架 |
| SQLAlchemy | 2.x | ORM |
| Pydantic | 2.x | 数据验证 |
| LangChain | 1.2 最新版本 | LLM框架 |
| LangGraph | 最新 | 工作流编排 |
| ChromaDB | 0.4.x | 向量数据库 |
| sentence-transformers | 2.x | 文本向量 |

### 支持的大模型

- **OpenAI**: GPT-4, GPT-3.5 Turbo, GPT-4o
- **Anthropic**: Claude 3 Opus, Claude 3 Sonnet, Claude 3.5
- **Google**: Gemini Pro, Gemini Ultra
- **阿里云**: 通义千问 (Qwen) 系列
- **字节跳动**: 豆包 (Doubao)
- **Moonshot**: 月之暗面 (Kimi)
- **DeepSeek**: DeepSeek Chat
- **Hunyuan**: 腾讯混元
- **本地部署**: Ollama (LLaMA2, Qwen, Mistral等)

### 支持的向量数据库(开发中)

- **ChromaDB** (默认, 轻量级)
- **Milvus** (企业级)
- **Pinecone** (云服务)
- **Qdrant** (开源)

---

## 项目结构

```
aichat/
├── frontend/                    # 前端项目 (React + TypeScript + Vite)
│   ├── src/
│   │   ├── components/          # UI组件
│   │   │   ├── Chat/            # 聊天相关组件
│   │   │   └── Common/          # 通用组件
│   │   ├── pages/               # 页面
│   │   ├── services/            # API服务
│   │   ├── stores/              # 状态管理 (Zustand)
│   │   └── types/               # TypeScript类型
│   ├── dist/                    # 构建产物
│   ├── nginx.conf               # Nginx配置
│   └── package.json
│
├── backend/                     # 后端项目 (Python + FastAPI)
│   ├── agent/                   # AI Agent核心
│   │   ├── mcp/                 # MCP工具管理
│   │   ├── tools/               # 内置工具
│   │   └── prompt/              # 提示词模板
│   ├── api/                     # API路由
│   │   └── routes/              # 路由模块
│   ├── services/                # 业务逻辑
│   ├── app/                     # 应用配置
│   ├── schemas/                 # 数据模型
│   └── pyproject.toml           # Python配置
│
├── .env                         # 环境变量
├── .env.local                   # 本地环境变量
└── README.md
```

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- npm 或 yarn

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd aichat
```

### 2. 安装依赖

```bash
# 安装后端依赖
cd backend
pip install -e .

# 安装前端依赖
cd ../frontend
npm install
```

### 3. 配置环境变量

创建 `.env` 文件:

```bash
# 后端配置
cd backend
cp .env.example .env

# 编辑 .env 文件，配置你的 API Keys
```

### 4. 启动服务

**方式一：使用 CLI 工具 (推荐)**

```bash
# 启动前后端服务
jeikchat run all

# 或使用简写
jeikchat run a
```

**方式二：分别启动**

```bash
# 终端1: 启动后端
cd backend
jeikchat run back
# 或: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端2: 启动前端
cd frontend
npm run dev
```

### 5. 访问系统

- **前端**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

---

## CLI 命令详解

```bash
# 查看帮助
jeikchat --help

# 启动所有服务
jeikchat run all
jeikchat run a          # 简写

# 启动前端
jeikchat run front      # http://localhost:5173

# 启动后端
jeikchat run back       # http://localhost:8000

# 测试模式 (使用模拟数据)
jeikchat run all -t
jeikchat run back -t

# 指定主机和端口
jeikchat run all --host 0.0.0.0 --port 9000
jeikchat run all -h :: -p 9000    # IPv6

# 参数说明
# -t, --test      测试模式
# -h, --host      监听地址 (默认 127.0.0.1)
# -p, --port      服务端口
```

---

## 部署指南

### 方式一：开发模式部署

适合本地测试和开发：

```bash
jeikchat run all -t --host 0.0.0.0 --port 9000
```

访问：http://localhost:9000

### 方式二：生产环境部署 (Nginx + 后端)

#### 1. 构建前端

```bash
cd frontend
npm run build
```

#### 2. 配置 Nginx

复制配置文件到 Nginx 目录：

```bash
# nginx.conf -> nginx/conf/nginx.conf
# dist/ -> nginx/html/
```

#### 3. 启动服务

```bash
# 启动后端
jeikchat run back

# 启动 Nginx
nginx.exe
```

#### 4. 访问方式

- IPv4: http://你的IP
- IPv6: http://[你的IPv6地址]

### 方式三：Docker 部署

#### 1. 构建镜像

```bash
# 后端镜像
cd backend
docker build -t aichat-backend .

# 前端镜像
cd ../frontend
docker build -t aichat-frontend .
```

#### 2. 使用 Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./vector_store:/app/vector_store

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

```bash
docker-compose up -d
```

### 公网部署注意事项

1. **防火墙**: 开放 80, 8000 端口
2. **域名解析**: 配置 A 记录和 AAAA 记录
3. **HTTPS**: 建议使用 Let's Encrypt 或 Cloudflare
4. **安全组**: 云服务器需开放对应端口

---

## 环境变量配置

### 后端 (.env)

```env
# 应用配置
APP_NAME=JeikChat
APP_VERSION=3.0.0
APP_DESCRIPTION=JeikChat智能客服系统

# 数据库
DATABASE_URL=sqlite:///./aichat.db

# 默认LLM配置
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# 可选: 其他模型
ANTHROPIC_API_KEY=your-anthropic-key
QWEN_API_KEY=your-qwen-key
DOUBAO_API_KEY=your-doubao-key
KIMI_API_KEY=your-kimi-key
DEEPSEEK_API_KEY=your-deepseek-key
GOOGLE_API_KEY=your-google-key

# 向量数据库
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_STORE_TYPE=chroma

# 文件上传
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=100MB
MAX_UPLOAD_FILES=10

# CORS
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# MCP配置
MCP_CONFIG_PATH=./agent/mcp/mcp.yaml
MCP_TIMEOUT=30
MCP_AUTO_RELOAD=true

# 日志
LOG_LEVEL=INFO
```

---

## MCP工具配置

MCP (Model Context Protocol) 工具配置位于 `backend/agent/mcp/mcp.yaml`：

```yaml
servers:
  - name: bing-search
    transport: streamable_http
    url: https://mcp.api-inference.modelscope.net/7fcb19ec6e704b/mcp

  - name: github-mcp
    transport: stdio
    command: npx
    args: [-y, "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: your-token

settings:
  timeout: 30
  auto_reload: true
  log_level: info
```

---

## API文档

详细的 API 接口文档请参考 [API文档.md](./API文档.md)

主要接口包括：

- **模型配置 API**: `/api/config/*`
- **聊天服务 API**: `/api/chat/*`
- **知识库 API**: `/api/knowledge/*`
- **工具服务 API**: `/api/tools/*`

在线文档: http://localhost:8000/docs (启动后访问)

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

---

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 联系方式

- **作者**: jeikliu@outlook.com
- **项目主页**: [GitHub Repository](your-repo-url)

---

<p align="center">
  Made with ❤️ by JeikLiu
</p>
