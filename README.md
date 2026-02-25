# AI智能客服系统 (AI Customer Service)

## 项目概述

**功能还在开发中 !!!**

**预计3月中旬开发完毕**!



本项目是一个功能完善的AI智能客服系统，采用现代化的微前端架构设计，支持实时语音对话、RAG知识库检索、多模型切换等核心功能。UI设计参考主流AI产品（豆包、ChatGPT、通义千问等），适配电脑和手机端。

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
| python-multipart | 0.0.x | 文件上传 |

### 支持的大模型

- **OpenAI**: GPT-4, GPT-3.5 Turbo
- ** Anthropic**: Claude 3 Opus, Claude 3 Sonnet
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
│   │   │   ├── Chat/           # 聊天相关组件
│   │   │   │   ├── ChatContainer.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageItem.tsx
│   │   │   │   ├── InputArea.tsx
│   │   │   │   └── VoiceControl.tsx
│   │   │   ├── KnowledgeBase/  # 知识库组件
│   │   │   │   ├── KnowledgeList.tsx
│   │   │   │   ├── FileUploader.tsx
│   │   │   │   └── VectorConfig.tsx
│   │   │   ├── Settings/       # 设置组件
│   │   │   │   ├── ModelConfig.tsx
│   │   │   │   └── SystemPrompt.tsx
│   │   │   └── Common/         # 通用组件
│   │   │       ├── Sidebar.tsx
│   │   │       ├── Header.tsx
│   │   │       └── Modal.tsx
│   │   ├── pages/              # 页面
│   │   │   ├── ChatPage.tsx
│   │   │   ├── KnowledgePage.tsx
│   │   │   └── SettingsPage.tsx
│   │   ├── hooks/              # 自定义Hooks
│   │   │   ├── useChat.ts
│   │   │   ├── useKnowledge.ts
│   │   │   └── useVoice.ts
│   │   ├── services/           # API服务
│   │   │   ├── api.ts
│   │   │   ├── chat.ts
│   │   │   ├── knowledge.ts
│   │   │   └── tts.ts
│   │   ├── stores/             # 状态管理
│   │   │   ├── chatStore.ts
│   │   │   ├── knowledgeStore.ts
│   │   │   └── settingsStore.ts
│   │   ├── types/              # TypeScript类型
│   │   │   ├── chat.ts
│   │   │   ├── knowledge.ts
│   │   │   └── config.ts
│   │   ├── utils/              # 工具函数
│   │   │   ├── format.ts
│   │   │   └── storage.ts
│   │   └── assets/styles/      # 样式文件
│   │       └── globals.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── backend/                     # 后端项目
│   ├── api/                    # API路由
│   │   ├── chat.py            # 聊天API
│   │   ├── knowledge.py       # 知识库API
│   │   ├── model.py           # 模型配置API
│   │   └── voice.py           # 语音API
│   ├── models/                 # 数据模型
│   │   ├── database.py        # 数据库连接
│   │   ├── knowledge.py       # 知识库模型
│   │   └── chat.py            # 聊天记录模型
│   ├── services/               # 业务逻辑
│   │   ├── chat_service.py    # 聊天服务
│   │   ├── llm_service.py      # 大模型服务
│   │   ├── asr_service.py      # 语音识别服务
│   │   └── tts_service.py      # 语音合成服务
│   ├── rag/                    # RAG核心
│   │   ├── loader.py           # 文档加载器
│   │   ├── splitter.py        # 文本分割器
│   │   ├── embeddings.py      # 向量化
│   │   └── retriever.py        # 检索器
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 配置文件
│   │   └── security.py         # 安全配置
│   ├── uploads/                # 上传文件目录
│   ├── vector_store/           # 向量存储目录
│   ├── main.py                # 应用入口
│   └── requirements.txt        # 依赖
│
└── README.md
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

### 3. 语音功能 (1.0版本预留)

- [ ] ASR语音识别
- [ ] TTS语音合成
- [ ] 实时语音对话 (WebRTC)

### 4. 高级功能

- [x] 对话历史管理
- [x] 知识库引用展示
- [x] 模型参数配置 (Temperature, TopP)
- [x] API Key管理
- [x] 响应速度优化

## 快速开始

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问: http://localhost:5173

### 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API文档: http://localhost:8000/docs

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
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

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

## 版本更新

### v3.0 (当前版本)

- 新增RAG知识库系统
- 支持PDF/Excel/CSV/Word文件上传
- 多知识库管理
- 自定义System Prompt
- 微信聊天数据清洗与模型训练

### v2.0

- 多模型支持
- 现代化UI设计
- 响应式布局

### v1.0

- 基础聊天功能
- 语音对话预留

## 许可证

MIT License
