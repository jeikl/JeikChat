# JeikChat 智能客服系统

## 项目概述

功能还在开发中 预计2026.3.15日之前开发完毕


作者唯一email : jeiklil@outlook.com

本项目是一个功能完善的JeikChat智能客服系统，采用现代化的微前端架构设计，支持实时语音对话、RAG知识库检索、多模型切换等核心功能。UI设计参考主流AI产品（豆包、ChatGPT、通义千问等），适配电脑和手机端。

## 技术架构

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.x | UI框架 |
| TypeScript | 5.x | 类型安全 |
| Vite | 5.x | 构建工具 |
| Zustand | 4.x | 状态管理 |
| React Router | 6.x | 路由管理 |
| TailwindCSS | 3.x | 样式框架 |
| @tanstack/react-query | 5.x | 数据请求 |
| Lucide React | 最新 | 图标库 |
| date-fns | 3.x | 时间处理 |

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 运行环境 |
| FastAPI | 0.109.x | Web框架 |
| SQLAlchemy | 2.x | ORM |
| Pydantic | 2.x | 数据验证 |
| LangChain | 0.1.x | LLM框架 |
| LangChain-Community | 0.0.x | 社区组件 |
| ChromaDB | 0.4.x | 向量数据库 |
| sentence-transformers | 2.x | 文本向量 |

### 支持的大模型

- **OpenAI**: GPT-4, GPT-3.5 Turbo
- **Anthropic**: Claude 3 Opus, Claude 3 Sonnet
- **Google**: Gemini Pro
- **阿里云**: 通义千问 (Qwen)
- **字节跳动**: 豆包
- **Moonshot**: 月之暗面 (Kimi)
- **本地部署**: Ollama (LLaMA2, Qwen, Mistral等)

### 支持的向量数据库

- **ChromaDB** (默认, 轻量级)
- **Milvus** (企业级)
- **Pinecone** (云服务)
- **Qdrant** (开源)

## 项目结构

```
aichat/
├── frontend/                    # 前端项目
│   ├── src/
│   │   ├── components/          # UI组件
│   │   ├── pages/               # 页面
│   │   ├── services/            # API服务
│   │   ├── stores/              # 状态管理
│   │   └── types/               # TypeScript类型
│   ├── dist/                    # 构建产物
│   ├── nginx.conf               # Nginx配置
│   └── package.json
│
├── backend/                     # 后端项目
│   ├── api/                     # API路由
│   ├── services/                # 业务逻辑
│   ├── core/                    # 核心配置
│   ├── uploads/                 # 上传文件目录
│   ├── vector_store/            # 向量存储目录
│   ├── main.py                  # 应用入口
│   └── pyproject.toml           # Python配置
│
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
# 前端依赖
cd frontend
npm install

# 后端依赖 (会自动安装)
```

### 2. 启动开发模式

```bash
# 使用 CLI 启动前后端
jeikchat run all -t

# 或者分别启动
jeikchat run front    # 前端 http://localhost:5173
jeikchat run back     # 后端 http://localhost:8000
```

### 3. 访问系统

- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## CLI 命令详解

```bash
# 启动所有服务
jeikchat run all -t

# 启动前端
jeikchat run front

# 启动后端
jeikchat run back -t

# 指定主机和端口
jeikchat run all -t --host :: -p 9000

# 参数说明
# -t, --test    测试模式（使用模拟数据）
# -h, --host   指定监听地址（默认 127.0.0.1）
# -p, --port   指定端口
```

## 部署教学

### 方式一：开发模式部署

适合本地测试和开发：

```bash
jeikchat run all -t --host :: -p 9000
```

访问：http://localhost:9000

### 方式二：Nginx + 后端部署

适合生产环境，支持 IPv4/IPv6 双栈：

#### 1. 构建前端

```bash
cd frontend
npm run build
```

#### 2. 配置 Nginx

将以下文件复制到 Nginx 安装目录：

```
nginx/
├── conf/
│   └── nginx.conf      # 复制 frontend/nginx.conf
├── html/
│   └── dist/           # 复制 frontend/dist 整个文件夹
└── nginx.exe
```

#### 3. 启动服务

```bash
# 启动后端
jeikchat run back -t

# 启动 Nginx
cd nginx目录
nginx.exe
```

#### 4. 访问方式

- IPv4: http://你的IP
- IPv6: http://[你的IPv6地址]

### 方式三：Docker 部署

#### 1. 创建 Dockerfile (后端)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 创建 docker-compose.yml

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
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
```

#### 3. 启动

```bash
docker-compose up -d
```

### 方式四：公网部署注意事项

1. **防火墙开放端口**：80, 8000
2. **域名解析**：配置 A 记录和 AAAA 记录
3. **HTTPS**：建议使用 Let's Encrypt 或 Cloudflare
4. **安全组**：云服务器需开放对应端口

## 环境变量配置

### 后端 (.env)

```env
# 数据库
DATABASE_URL=sqlite:///./aichat.db

# 默认LLM配置
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# 可选: 其他模型
ANTHROPIC_API_KEY=your-anthropic-key
QWEN_API_KEY=your-qwen-key
DOUBAO_API_KEY=your-doubao-key

# 向量数据库
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_STORE_TYPE=chroma

# 文件上传
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=100MB

# CORS
CORS_ORIGINS=*
```

## 核心功能

### 1. 智能对话

- [x] 多模型支持切换
- [x] 流式输出 (SSE)
- [x] Markdown渲染
- [x] 代码高亮
- [x] 复制功能
- [x] 打字机效果

### 2. RAG知识库

- [x] 支持文件类型: PDF, Excel, CSV, Word, TXT, Markdown
- [x] 向量存储 (ChromaDB)
- [x] 相似度检索
- [x] 多知识库管理
- [x] 自定义System Prompt
- [x] 知识库命名/重命名

### 3. Agent Tools

- [x] 工具扩展系统
- [x] 动态启用/禁用工具
- [x] 知识库查询集成

### 4. 系统设置

- [x] 模型参数配置 (Temperature, TopP)
- [x] API Key管理
- [x] 多模型切换

## API接口文档

### 聊天API

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/chat/send | 发送消息 |
| GET | /api/chat/history/{session_id} | 获取历史 |
| DELETE | /api/chat/history/{session_id} | 删除会话 |

### 知识库API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/knowledge/list | 获取知识库列表 |
| POST | /api/knowledge/create | 创建知识库 |
| POST | /api/knowledge/upload | 上传文件 |
| DELETE | /api/knowledge/{id} | 删除知识库 |
| GET | /api/knowledge/{id}/search | 检索知识 |

### 模型配置API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/models/list | 获取可用模型 |
| POST | /api/models/config | 配置模型参数 |
| GET | /api/models/test | 测试连接 |

### Agent Tools API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /tools/ | 获取可用工具 |
| POST | /tools/enable | 启用工具 |
| POST | /tools/disable | 禁用工具 |

## 版本更新

### v3.0 (当前版本)

- 新增RAG知识库系统
- 支持PDF/Excel/CSV/Word文件上传
- 多知识库管理
- 自定义System Prompt
- Agent Tools 扩展系统
- Nginx 部署配置
- IPv4/IPv6 双栈支持

### v2.0

- 多模型支持
- 现代化UI设计
- 响应式布局

### v1.0

- 基础聊天功能
- 语音对话预留

## 常见问题

### Q: 前端加载慢怎么办？

1. 使用 Nginx 部署并开启 Gzip 压缩
2. 配置静态资源缓存
3. 使用 CDN 加速

### Q: 模型调用失败？

1. 检查 API Key 是否正确
2. 检查网络是否能访问目标 API
3. 查看后端日志

### Q: 知识库检索不到内容？

1. 检查文件是否上传成功
2. 确认向量是否生成成功
3. 调整相似度阈值

## 许可证

MIT License
