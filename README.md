<div align="center">

<img src="frontend/public/logo.png" alt="JeikChat Logo" width="120" style="margin: 20px 0;">

# 🚀 JeikChat 智能体助手

**基于 LangGraph/LangChain 的 Agent 框架 · MCP协议扩展 · RAG知识库 · 多模型混合调用 · 拖拽上传 · 推理可视化**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=white)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-1C3C3C?style=flat-square)](https://langchain.com)
[![MCP](https://img.shields.io/badge/MCP-Protocol-green?style=flat-square)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

<p align="center">
  <strong>基于大语言模型的前后端分离AI助手解决方案</strong>
</p>

<p align="center">
  <a href="#-项目简介">项目简介</a> •
  <a href="#-核心特性">核心特性</a> •
  <a href="#-功能展示">功能展示</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-部署指南">部署指南</a> •
  <a href="#-cli命令">CLI命令</a> •
  <a href="#-api文档">API文档</a>
</p>

<p align="center">
  <strong>👨‍💻 Author: <a href="mailto:jeikliu@outlook.com">jeikliu@outlook.com</a></strong>
</p>

</div>

---

## ✅ 已实现功能

| 功能 | 状态 | 说明 |
|:---:|:---:|:---|
| 🎨 **多模态对话** | ✅ 已实现 | 支持图片理解、视频分析、音频处理、PDF 解析 |
| 🛠️ **Agent 工具** | ✅ 已实现 | MCP Tools 全面支持 (HTTP/SSE/STDIO)，可视化配置管理 |
| 📚 **RAG 知识库** | ✅ 已实现 | 基于 Qdrant 向量数据库，支持多格式文档解析 |
| 🧠 **推理可视化** | ✅ 已实现 | 思考过程展示，支持展开/收起查看模型推理链 |
| 💾 **长期记忆** | ✅ 已实现 | PostgreSQL Checkpoint 持久化对话状态 |
| 📎 **文件上传** | ✅ 已实现 | 拖拽上传 + 粘贴上传，支持多种文件格式 |
| 🌊 **流式输出** | ✅ 已实现 | SSE 实时流式响应，打字机效果 |
| 🔄 **多模型切换** | ✅ 已实现 | 支持 OpenAI、DeepSeek、Google、魔塔等主流模型 |
| ⚙️ **提示词管理** | ✅ 已实现 | 可视化 Prompt 配置，支持自定义系统提示词 |
| 🔧 **MCP 配置** | ✅ 已实现 | 弹窗式服务管理，敏感信息自动脱敏 |
| 🎯 **Skills** | 📝 待定 | 技能系统（开发中）|

---

## 📖 项目简介

**JeikChat** 是一个基于 **LangGraph** 和 **LangChain** 构建的智能体（Agent）系统，采用现代化的前后端分离架构设计。后端基于 **Python** 生态（`FastAPI` + `LangChain` + `LangGraph`），前端基于 **React** 生态（`Vite` + `TailwindCSS` + `Zustand`）。

项目深度集成了**多模型自由切换**、**RAG知识库高级检索**（支持多种文档格式解析与向量存储）、**MCP (Model Context Protocol) 工具动态扩展**、**拖拽文件上传**、**推理过程可视化**，以及带**持久化记忆 (PostgreSQL Checkpoint)** 的智能体对话编排能力。

### 🏗️ 架构全面性

本项目不仅是一个聊天应用，更是一套**通用的 AI Agent 开发框架**，包含大量可迁移的解决方案：

| 模块 | 技术方案 | 可迁移场景 |
|:---:|:---|:---|
| 🤖 **Agent 核心** | LangGraph 状态机 + 节点编排 | 任意复杂工作流编排、多步骤任务处理 |
| 🔌 **工具系统** | MCP 协议适配器 | 跨语言工具调用（Python/Node.js/Go 等）、第三方服务集成 |
| 🧠 **记忆系统** | PostgreSQL Checkpoint | 长对话持久化、跨会话状态保持 |
| 📚 **RAG 检索** | Qdrant + Embedding | 企业知识库、文档问答系统 |
| 🌊 **流式处理** | SSE + 异步生成器 | 实时数据推送、打字机效果输出 |
| ⚙️ **配置管理** | YAML + 热重载 | 动态配置更新、无需重启服务 |

### 💡 扩展能力示例

**跨语言 Skills 调用**：
```python
# 通过 MCP 协议集成其他语言实现的 Skills
# 例如：用 Go 编写高性能计算 Skill，通过 STDIO/SSE 方式接入
mcpServers:
  go-calculator:
    command: ./skills/go-calculator  # Go 编译的可执行文件
    env:
      API_KEY: ${GO_SKILL_KEY}
```

**自定义 Agent 工作流**：
```python
# 基于 LangGraph 快速构建自定义工作流
from langgraph.graph import StateGraph

workflow = StateGraph(AgentState)
workflow.add_node("planner", plan_node)
workflow.add_node("executor", execute_node)
workflow.add_node("validator", validate_node)
# 任意编排你的业务逻辑...
```

### 🎯 设计理念

- **模块化架构**：各功能模块独立设计，易于扩展和维护
- **多模型支持**：无缝切换国内外主流大模型
- **知识增强**：RAG技术让AI具备领域专业知识
- **工具生态**：MCP协议支持无限扩展AI能力边界
- **流式体验**：基于SSE的实时流式输出，打字机效果
- **用户友好**：拖拽上传、可视化推理、智能配置管理

---

## ✨ 核心特性

### 🤖 智能对话与多模型支持

| 特性 | 说明 |
|------|------|
| **主流大模型全覆盖** | 原生支持 OpenAI、Anthropic、Google GenAI、DeepSeek、智谱AI、魔塔、豆包等 |
| **极致的流式体验** | 基于 Server-Sent Events (SSE) 的流式输出与打字机效果 |
| **长期记忆** | 引入 `langgraph-checkpoint-postgres` 提供图状态的持久化 |
| **富文本交互** | 完美支持 Markdown 渲染、代码高亮、消息复制与重新生成 |
| **推理可视化** | 支持思考过程展示，可展开/收起查看模型推理链 |

### 📚 RAG 知识库增强检索

| 特性 | 说明 |
|------|------|
| **全格式文档解析** | 支持 PDF, Excel, Word, CSV, Markdown, TXT 等多格式解析 |
| **灵活的向量存储** | 基于 **Qdrant** 的高性能向量数据库引擎 |
| **高级检索能力** | 支持文档的分块、Embedding 模型切换、多知识库并行挂载 |
| **可视化选择** | 聊天界面快速切换知识库，实时同步状态 |

### 🛠️ Agent 工具系统 (MCP)

| 特性 | 说明 |
|------|------|
| **协议原生支持** | 基于 `langchain-mcp-adapters`，标准支持 MCP 协议 |
| **多传输通道** | 支持 HTTP Streamable、SSE、STDIO 等传输层 |
| **可视化配置** | 弹窗式 MCP 服务管理，支持增删改查与实时热重载 |
| **敏感信息保护** | API Key、Token 等敏感字段自动脱敏显示 |
| **工具生态** | 内置工具发现、缓存与热重载 |

### 📎 多模态与文件处理

| 特性 | 说明 |
|------|------|
| **拖拽上传** | 支持拖拽文件到输入框上传，支持图片、视频、音频、PDF 等 |
| **粘贴上传** | 支持截图直接粘贴上传 |
| **多模态对话** | 支持图片理解、视频分析等多模态交互 |

---

## 🖼️ 功能展示

### 多模态对话支持

<div align="center">

| 图片理解 | 视频分析 | 其他文件 |
|:--------:|:--------:|:--------:|
| ![图片对话](frontend/public/testimg/多模态-图片.png) | ![视频对话](frontend/public/testimg/多模态-视频.png) | ![其他文件](frontend/public/testimg/多模态-其他.png) |

</div>

### RAG 知识库 & MCP 工具选择

<div align="center">

![知识库与工具选择](frontend/public/testimg/rag%20mcp%20tools%20选择.png)

</div>

### 知识库管理

<div align="center">

![知识库管理](frontend/public/testimg/知识库选择.png)

</div>

### Agent 工具管理

<div align="center">

![工具管理](frontend/public/testimg/工具管理.png)

</div>

### 工具调用展示

<div align="center">

![工具调用](frontend/public/testimg/工具调用.png)

</div>

---

## 🚀 快速开始

### 环境要求

- **Python**: >= 3.11, < 3.14
- **Node.js**: >= 18 (前端开发需要)
- **UV**: Python 包管理工具

### 1. 安装 UV

UV 是现代化的 Python 包管理工具，比 pip 更快更高效。

**使用 pip 安装（推荐）:**
```bash
pip install uv
```

**其他安装方式:**

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**验证安装:**
```bash
uv --version
```

更多安装方式请参考 [UV 官方文档](https://docs.astral.sh/uv/getting-started/installation/)。

### 2. 克隆项目

```bash
git clone <your-repo-url>
cd aichat
```

### 3. 后端环境配置

```bash
# 进入后端目录
cd backend

# 使用 UV 安装依赖（会自动创建虚拟环境并安装所有依赖）
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置你的 API Keys
```

### 4. 前端环境配置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发模式启动
npm run dev
```

### 5. 启动服务

```bash
# 使用 CLI 启动全栈（推荐）
jeikchat all

# 或分别启动
jeikchat back    # 启动后端
jeikchat front   # 启动前端
```

访问 http://localhost:5173 即可使用。

---

## 📦 部署指南

### 目录结构

```
aichat/
├── backend/              # 后端服务
│   ├── Dockerfile        # 后端 Docker 配置
│   ├── pyproject.toml    # Python 依赖
│   ├── app/              # FastAPI 应用
│   ├── api/              # API 路由
│   ├── services/         # 业务服务
│   ├── agent/            # AI Agent 核心
│   │   ├── mcp/          # MCP 工具配置
│   │   ├── knowledges/   # 知识库数据
│   │   └── tools/        # 工具实现
│   └── config/           # 配置文件
├── frontend/             # 前端应用
│   ├── nginx.conf        # Nginx 配置
│   ├── package.json      # Node.js 依赖
│   └── src/              # React 源码
└── README.md
```

---

### 🐳 后端部署（Docker）

后端使用 **Docker** 部署，基于 `ghcr.io/astral-sh/uv:python3.11-bookworm-slim` 镜像，内置 Node.js 22.x。

#### 构建镜像

```bash
cd backend

# 构建镜像
docker build -t jeikchat-backend:latest .
```

#### 运行容器

```bash
# 基础运行
docker run -d \
  --name jeikchat-backend \
  -p 8000:8000 \
  -v $(pwd)/config:/backend/config \
  -v $(pwd)/agent/knowledges:/backend/agent/knowledges \
  -v $(pwd)/agent/mcp:/backend/agent/mcp \
  jeikchat-backend:latest

# 带环境变量的完整运行
docker run -d \
  --name jeikchat-backend \
  -p 8000:8000 \
  -v $(pwd)/config:/backend/config \
  -v $(pwd)/agent/knowledges:/backend/agent/knowledges \
  -v $(pwd)/agent/mcp:/backend/agent/mcp \
  -e OPENAI_API_KEY=your_key \
  -e DEEPSEEK_API_KEY=your_key \
  jeikchat-backend:latest
```

#### Docker Compose 部署（推荐）

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: jeikchat-backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/config:/backend/config
      - ./backend/agent/knowledges:/backend/agent/knowledges
      - ./backend/agent/mcp:/backend/agent/mcp
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - MODELSCOPE_API_KEY=${MODELSCOPE_API_KEY}
    restart: unless-stopped
    networks:
      - jeikchat-network

  # 可选：PostgreSQL 用于对话记忆持久化
  postgres:
    image: postgres:15-alpine
    container_name: jeikchat-postgres
    environment:
      - POSTGRES_USER=jeikchat
      - POSTGRES_PASSWORD=your_password
      - POSTGRES_DB=jeikchat
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - jeikchat-network

volumes:
  postgres_data:

networks:
  jeikchat-network:
    driver: bridge
```

启动：

```bash
docker-compose up -d
```

---

### 🌐 前端部署（Nginx）

前端采用 **Nginx** 部署，将构建后的 `dist` 目录放到服务器 Nginx 的站点目录。

#### 1. 构建前端

```bash
cd frontend

# 安装依赖
npm install

# 生产构建
npm run build

# 构建完成后，dist/ 目录包含所有静态文件
```

#### 2. Nginx 配置

将 `frontend/nginx.conf` 复制到服务器 Nginx 配置目录：

```bash
# 复制配置文件
sudo cp frontend/nginx.conf /etc/nginx/conf.d/jeikchat.conf

# 创建站点目录
sudo mkdir -p /var/www/jeikchat

# 复制构建文件
sudo cp -r frontend/dist/* /var/www/jeikchat/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

#### Nginx 配置说明

`nginx.conf` 关键配置：

```nginx
server {
    listen       80;
    server_name  your-domain.com;

    # 前端静态文件
    location / {
        root   /var/www/jeikchat;
        index  index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 代理到后端
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 3. 完整部署脚本

```bash
#!/bin/bash
# deploy.sh - 前端部署脚本

FRONTEND_DIR="/path/to/aichat/frontend"
NGINX_ROOT="/var/www/jeikchat"

echo "🚀 开始部署 JeikChat 前端..."

# 构建
cd $FRONTEND_DIR
npm install
npm run build

# 部署到 Nginx
sudo rm -rf $NGINX_ROOT/*
sudo cp -r dist/* $NGINX_ROOT/

# 复制配置
sudo cp nginx.conf /etc/nginx/conf.d/jeikchat.conf

# 重载 Nginx
sudo nginx -t && sudo systemctl reload nginx

echo "✅ 部署完成！"
```

---

## 🖥️ CLI 命令

JeikChat 提供便捷的 CLI 工具 `jeikchat`，支持快速启动和管理服务。

### 命令格式

```bash
jeikchat <action> [options]
```

### 可用命令

| 命令 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `back` | - | 启动后端服务 | `jeikchat back` |
| `front` | - | 启动前端服务 | `jeikchat front` |
| `all` | `a` | 启动全栈服务 | `jeikchat all` 或 `jeikchat a` |

### 选项参数

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-t, --test` | 测试模式 | false |
| `--port` | 后端端口 | 8000 |
| `--front-port` | 前端端口 | 5173 |

### 使用示例

```bash
# 启动后端（默认端口 8000）
jeikchat back

# 后端测试模式
jeikchat back -t

# 后端指定端口
jeikchat back --port 8080

# 启动前端（默认端口 5173）
jeikchat front

# 启动全栈（完整写法）
jeikchat all

# 启动全栈（简写）⭐ 推荐
jeikchat a

# 全栈自定义端口
jeikchat a --port 8080 --front-port 3000
```

---

## ⚙️ 配置说明

### 后端配置

编辑 `backend/config/models.yaml` 配置模型：

```yaml
providers:
  openai:
    name: OpenAI
    api_key: ${OPENAI_API_KEY}
    base_url: https://api.openai.com/v1
    models:
      - gpt-4o
      - gpt-4o-mini

  deepseek:
    name: DeepSeek
    api_key: ${DEEPSEEK_API_KEY}
    base_url: https://api.deepseek.com/v1
    models:
      - deepseek-chat
      - deepseek-reasoner
```

### MCP 工具配置

MCP 服务配置位于 `backend/agent/mcp/mcp.yaml`，可通过前端 **Agent 工具页面** 的"配置"按钮进行可视化编辑：

```yaml
mcpServers:
  example-server:
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "/path/to/files"
    env:
      API_KEY: your-api-key
```

### 环境变量

创建 `backend/.env`：

```env
# API Keys
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key
GOOGLE_API_KEY=your_google_key
MODELSCOPE_API_KEY=your_modelscope_key

# 数据库（可选，用于对话记忆持久化）
DATABASE_URL=postgresql://user:pass@localhost:5432/jeikchat

# 存储配置
STORAGE_TYPE=local
```

---

## 📚 API 文档

启动后端后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🛠️ 技术栈

### 后端
- **FastAPI** - 高性能 Web 框架
- **LangChain / LangGraph** - AI 应用框架
- **MCP Adapters** - Model Context Protocol 支持
- **UV** - 现代 Python 包管理器
- **Pydantic** - 数据验证
- **Qdrant** - 向量数据库
- **PostgreSQL** - 对话记忆持久化（可选）

### 前端
- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **TailwindCSS** - 样式框架
- **Zustand** - 状态管理

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证与授权

本项目采用 **自定义授权协议**：

| 使用场景 | 授权状态 | 说明 |
|:---:|:---:|:---|
| 👤 **个人使用** | ✅ 允许 | 个人学习、研究、非商业用途可免费使用 |
| 🏢 **商业使用** | ⚠️ 需授权 | 商业用途需获得作者书面授权，请联系 <a href="mailto:jeikliu@outlook.com">jeikliu@outlook.com</a> |
| 🔄 **二次开发** | ⚠️ 需授权 | 基于本项目修改、衍生作品需获得授权 |
| 📦 **再分发** | ❌ 禁止 | 禁止以任何形式重新分发本项目的代码或二进制文件 |

**联系方式**: jeikliu@outlook.com

---

<p align="center">
  Made with ❤️ by <a href="mailto:jeikliu@outlook.com">jeikliu</a>
</p>
