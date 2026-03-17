<div align="center">

# 📖 JeikChat API 接口文档

**基于 FastAPI 的高性能大语言模型后端 API**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.0-85EA2D?style=flat-square&logo=openapiinitiative&logoColor=white)](https://swagger.io/specification/)
[![SSE](https://img.shields.io/badge/SSE-Supported-blue?style=flat-square)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

<p align="center">
  <a href="#-概述">概述</a> •
  <a href="#-认证">认证</a> •
  <a href="#-聊天服务">聊天服务</a> •
  <a href="#-知识库服务">知识库服务</a> •
  <a href="#-模型配置">模型配置</a> •
  <a href="#-工具服务">工具服务</a> •
  <a href="#-文件服务">文件服务</a>
</p>

</div>

---

## 📑 目录

- [概述](#-概述)
- [认证](#-认证)
- [通用规范](#-通用规范)
- [聊天服务 API](#-聊天服务-api)
- [知识库服务 API](#-知识库服务-api)
- [模型配置 API](#-模型配置-api)
- [工具服务 API](#-工具服务-api)
- [文件服务 API](#-文件服务-api)
- [错误码说明](#-错误码说明)
- [数据模型](#-数据模型)

---

## 🌐 概述

### 基础信息

| 项目 | 说明 |
|------|------|
| **基础URL** | `http://localhost:8000/api` |
| **Swagger UI** | `http://localhost:8000/docs` |
| **ReDoc** | `http://localhost:8000/redoc` |
| **OpenAPI Schema** | `http://localhost:8000/openapi.json` |
| **数据格式** | `application/json` |
| **字符编码** | `UTF-8` |

### 支持的传输协议

| 协议 | 用途 | 说明 |
|------|------|------|
| HTTP/1.1 | 常规API调用 | 标准REST API |
| HTTP/2 | 高性能传输 | 支持多路复用 |
| SSE | 流式输出 | Server-Sent Events |
| WebSocket | 实时通信 | 预留支持 |

---

## 🔐 认证

> **注意**: 当前版本暂未实现JWT认证，所有接口公开访问。生产环境建议添加API Key或JWT认证。

### 计划中的认证方式

```http
Authorization: Bearer <your-api-key>
```

或

```http
X-API-Key: <your-api-key>
```

---

## 📋 通用规范

### 通用响应结构

#### 成功响应 (非流式)

```json
{
  "status": 1,
  "data": { ... },
  "msg": "操作成功"
}
```

#### 错误响应

```json
{
  "status": 0,
  "data": null,
  "msg": "错误描述信息"
}
```

### HTTP状态码

| 状态码 | 说明 | 场景 |
|--------|------|------|
| `200` | 成功 | 请求处理成功 |
| `201` | 已创建 | 资源创建成功 |
| `400` | 请求参数错误 | 参数校验失败 |
| `401` | 未授权 | 缺少认证信息 |
| `403` | 禁止访问 | 权限不足 |
| `404` | 资源不存在 | 请求的资源未找到 |
| `422` | 验证错误 | 请求体格式错误 |
| `500` | 服务器内部错误 | 服务端异常 |
| `503` | 服务不可用 | 依赖服务故障 |

### 分页参数

列表接口支持以下分页参数：

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `page` | integer | 页码 | 1 |
| `page_size` | integer | 每页数量 | 20 |
| `sort_by` | string | 排序字段 | created_at |
| `sort_order` | string | 排序方向 (asc/desc) | desc |

### 分页响应

```json
{
  "status": 1,
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "msg": "success"
}
```

---

## 💬 聊天服务 API

提供基于大模型的对话交互能力，支持图状态持久化与历史记忆。

### 接口概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/chat/send` | 发送消息（支持流式） |
| `GET` | `/chat/sessions` | 获取所有会话列表 |
| `GET` | `/chat/session/{session_uuid}` | 获取单个会话详情 |
| `POST` | `/chat/session/{session_uuid}/clear` | 清空会话记录 |
| `DELETE` | `/chat/session/{session_uuid}` | 删除会话 |
| `POST` | `/chat/cancel/{task_id}` | 取消进行中的任务 |

### 1. 发送消息

发送消息并获取AI回复，支持流式输出。

```http
POST /api/chat/send
Content-Type: application/json
```

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `content` | string/array | ✅ | 用户消息内容，支持文本或多模态 |
| `sessionId` | string | ❌ | 会话ID，不传则创建新会话 |
| `sessionUuid` | string | ❌ | 会话UUID，用于持久化记忆 |
| `model` | string | ❌ | 模型ID，默认使用系统配置 |
| `thinking` | string | ❌ | 思考模式 (auto/on/off)，默认auto |
| `knowledgeBaseIds` | array | ❌ | 挂载的知识库ID列表 |
| `tools` | array | ❌ | 启用的工具配置列表 |
| `stream` | boolean | ❌ | 是否流式输出，默认true |

#### 请求示例

**基础对话：**

```json
{
  "content": "你好，请介绍一下自己",
  "model": "gpt-4o",
  "thinking": "auto"
}
```

**带知识库的对话：**

```json
{
  "content": "这篇文档讲了什么？",
  "sessionUuid": "550e8400-e29b-41d4-a716-446655440000",
  "model": "qwen3.5-flash",
  "knowledgeBaseIds": ["kb-tech-docs", "kb-product-manual"],
  "thinking": "on"
}
```

**带工具调用的对话：**

```json
{
  "content": "北京今天天气怎么样？",
  "sessionUuid": "550e8400-e29b-41d4-a716-446655440000",
  "tools": [
    {
      "toolid": "get_current_weather",
      "mcp": 1,
      "name": "天气查询",
      "description": "获取指定城市的天气信息"
    }
  ]
}
```

**多模态输入：**

```json
{
  "content": [
    {
      "type": "text",
      "text": "描述这张图片"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "data:image/jpeg;base64,/9j/4AAQ..."
      }
    }
  ],
  "model": "gpt-4o-vision"
}
```

#### 响应示例

**非流式响应：**

```json
{
  "status": 1,
  "data": {
    "task_id": "task-123456",
    "session_id": "sess-abc123",
    "message": {
      "id": "msg-789",
      "role": "assistant",
      "content": "你好！我是JeikChat AI助手...",
      "reasoning": "用户询问自我介绍，我需要...",
      "timestamp": 1704067200000,
      "references": []
    }
  },
  "msg": "success"
}
```

**流式响应 (SSE)：**

```http
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

```
event: message
data: {"type": "start", "task_id": "task-123456"}

event: message
data: {"type": "reasoning", "content": "用户询问自我介绍..."}

event: message
data: {"type": "content", "content": "你好！"}

event: message
data: {"type": "content", "content": "我是"}

event: message
data: {"type": "content", "content": "JeikChat AI助手"}

event: message
data: {"type": "tool_call", "tool": "get_current_time", "input": {}}

event: message
data: {"type": "tool_result", "tool": "get_current_time", "output": "2024-01-01 12:00:00"}

event: message
data: {"type": "references", "references": [{"knowledge_id": "kb-1", "content": "...", "similarity": 0.95}]}

event: message
data: {"type": "end", "finish_reason": "stop"}
```

#### SSE事件类型

| 事件类型 | 说明 |
|----------|------|
| `start` | 开始生成 |
| `reasoning` | 推理过程（思考模式开启时） |
| `content` | 内容片段 |
| `tool_call` | 工具调用请求 |
| `tool_result` | 工具执行结果 |
| `references` | 知识库引用 |
| `error` | 错误信息 |
| `end` | 生成结束 |

### 2. 获取会话列表

获取所有聊天会话列表。

```http
GET /api/chat/sessions?page=1&page_size=20
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "items": [
      {
        "id": "sess-abc123",
        "title": "关于人工智能的讨论...",
        "message_count": 12,
        "model": "gpt-4o",
        "knowledge_base_ids": ["kb-1"],
        "created_at": 1704067200000,
        "updated_at": 1704153600000
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  },
  "msg": "success"
}
```

### 3. 获取会话详情

获取指定会话的完整聊天记录。

```http
GET /api/chat/session/{session_uuid}
```

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `session_uuid` | string | 会话UUID |

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Python编程问题",
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "Python如何实现异步编程？",
        "timestamp": 1704067200000
      },
      {
        "id": "msg-2",
        "role": "assistant",
        "content": "Python实现异步编程主要有以下几种方式...",
        "reasoning": "用户询问Python异步编程，我需要介绍asyncio...",
        "timestamp": 1704067210000,
        "references": []
      }
    ],
    "model": "gpt-4o",
    "knowledge_base_ids": ["kb-python-docs"],
    "created_at": 1704067200000,
    "updated_at": 1704067210000
  },
  "msg": "success"
}
```

### 4. 清空会话记录

清空指定会话的所有消息记录，但保留会话本身。

```http
POST /api/chat/session/{session_uuid}/clear
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "session_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "cleared_at": 1704153600000
  },
  "msg": "会话已清空"
}
```

### 5. 删除会话

删除整个会话及其所有消息记录。

```http
DELETE /api/chat/session/{session_uuid}
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "session_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "deleted_at": 1704153600000
  },
  "msg": "会话已删除"
}
```

### 6. 取消任务

取消正在进行的生成任务。

```http
POST /api/chat/cancel/{task_id}
```

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务ID |

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "task_id": "task-123456",
    "cancelled_at": 1704153600000
  },
  "msg": "任务已取消"
}
```

---

## 📚 知识库服务 API

基于 RAG（检索增强生成）技术的知识库管理接口。

### 接口概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/knowledge/list` | 获取知识库列表 |
| `POST` | `/knowledge/create` | 创建知识库 |
| `POST` | `/knowledge/create-with-files` | 创建知识库并上传文件 |
| `POST` | `/knowledge/create-async` | 异步创建知识库 |
| `GET` | `/knowledge/create-progress/{task_id}` | 查询创建进度 |
| `GET` | `/knowledge/{kb_name}` | 获取知识库详情 |
| `PUT` | `/knowledge/{kb_name}` | 更新知识库 |
| `DELETE` | `/knowledge/{kb_name}` | 删除知识库 |
| `POST` | `/knowledge/{kb_name}/upload` | 上传文件到知识库 |
| `GET` | `/knowledge/{kb_name}/files` | 获取知识库文件列表 |
| `DELETE` | `/knowledge/{kb_name}/files/{file_name}` | 删除知识库文件 |
| `POST` | `/knowledge/retrieve` | 单知识库检索 |
| `POST` | `/knowledge/batch-search` | 多知识库混合检索 |

### 1. 获取知识库列表

```http
GET /api/knowledge/list?page=1&page_size=20
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "items": [
      {
        "id": "kb-tech-docs",
        "name": "技术文档",
        "description": "公司内部技术文档库",
        "document_count": 25,
        "total_chunks": 1250,
        "embedding_model": "bge-small-zh-v1.5",
        "vector_store": "chroma",
        "created_at": 1704067200000,
        "updated_at": 1704153600000,
        "status": "ready"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
  },
  "msg": "success"
}
```

### 2. 创建知识库

```http
POST /api/knowledge/create
Content-Type: application/json
```

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 知识库名称（唯一标识） |
| `description` | string | ❌ | 知识库描述 |
| `embedding_model` | string | ❌ | Embedding模型ID |
| `chunk_size` | integer | ❌ | 分块大小，默认1000 |
| `chunk_overlap` | integer | ❌ | 分块重叠，默认200 |

#### 请求示例

```json
{
  "name": "kb-product-manual",
  "description": "产品使用手册知识库",
  "embedding_model": "bge-small-zh-v1.5",
  "chunk_size": 800,
  "chunk_overlap": 150
}
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "id": "kb-product-manual",
    "name": "kb-product-manual",
    "description": "产品使用手册知识库",
    "embedding_model": "bge-small-zh-v1.5",
    "chunk_size": 800,
    "chunk_overlap": 150,
    "status": "empty",
    "created_at": 1704153600000
  },
  "msg": "知识库创建成功"
}
```

### 3. 创建知识库并上传文件

```http
POST /api/knowledge/create-with-files
Content-Type: multipart/form-data
```

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 知识库名称 |
| `description` | string | ❌ | 知识库描述 |
| `files` | array | ✅ | 文件列表（支持多文件） |
| `embedding_model` | string | ❌ | Embedding模型 |

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "id": "kb-tech-docs",
    "name": "kb-tech-docs",
    "document_count": 3,
    "total_chunks": 150,
    "status": "ready",
    "files": [
      {
        "name": "api-doc.pdf",
        "size": 1024576,
        "chunks": 50,
        "status": "processed"
      }
    ]
  },
  "msg": "知识库创建成功"
}
```

### 4. 异步创建知识库

适用于大文件或批量文件处理。

```http
POST /api/knowledge/create-async
Content-Type: multipart/form-data
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "task_id": "task-kb-123456",
    "knowledge_base_id": "kb-large-docs",
    "status": "processing"
  },
  "msg": "知识库创建任务已提交"
}
```

### 5. 查询创建进度

```http
GET /api/knowledge/create-progress/{task_id}
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "task_id": "task-kb-123456",
    "knowledge_base_id": "kb-large-docs",
    "status": "processing",
    "progress": 65,
    "current_file": "large-document.pdf",
    "processed_files": 2,
    "total_files": 5,
    "message": "正在处理 large-document.pdf...",
    "created_at": 1704153600000,
    "updated_at": 1704153660000
  },
  "msg": "success"
}
```

**状态说明：**

| 状态 | 说明 |
|------|------|
| `pending` | 等待处理 |
| `processing` | 处理中 |
| `completed` | 已完成 |
| `failed` | 处理失败 |

### 6. 获取知识库详情

```http
GET /api/knowledge/{kb_name}
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "id": "kb-tech-docs",
    "name": "kb-tech-docs",
    "description": "技术文档知识库",
    "document_count": 25,
    "total_chunks": 1250,
    "embedding_model": "bge-small-zh-v1.5",
    "vector_store": "chroma",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "created_at": 1704067200000,
    "updated_at": 1704153600000,
    "status": "ready"
  },
  "msg": "success"
}
```

### 7. 更新知识库

```http
PUT /api/knowledge/{kb_name}
Content-Type: application/json
```

#### 请求示例

```json
{
  "description": "更新后的描述",
  "chunk_size": 1200
}
```

### 8. 删除知识库

```http
DELETE /api/knowledge/{kb_name}
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "id": "kb-tech-docs",
    "deleted_at": 1704153600000
  },
  "msg": "知识库已删除"
}
```

### 9. 上传文件到知识库

```http
POST /api/knowledge/{kb_name}/upload
Content-Type: multipart/form-data
```

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `files` | array | ✅ | 文件列表 |

#### 支持的文件格式

| 格式 | MIME类型 | 说明 |
|------|----------|------|
| PDF | `application/pdf` | 支持文本提取 |
| Word | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | .docx |
| Excel | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | .xlsx |
| PowerPoint | `application/vnd.openxmlformats-officedocument.presentationml.presentation` | .pptx |
| Markdown | `text/markdown` | .md |
| Text | `text/plain` | .txt |
| CSV | `text/csv` | .csv |
| HTML | `text/html` | .html |

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "uploaded_files": [
      {
        "name": "document.pdf",
        "size": 1048576,
        "chunks": 45,
        "status": "processed"
      }
    ],
    "failed_files": [],
    "total_chunks_added": 45
  },
  "msg": "文件上传成功"
}
```

### 10. 获取知识库文件列表

```http
GET /api/knowledge/{kb_name}/files?page=1&page_size=20
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "items": [
      {
        "name": "api-reference.pdf",
        "size": 2097152,
        "chunks": 89,
        "status": "processed",
        "uploaded_at": 1704067200000
      }
    ],
    "total": 25,
    "page": 1,
    "page_size": 20
  },
  "msg": "success"
}
```

### 11. 删除知识库文件

```http
DELETE /api/knowledge/{kb_name}/files/{file_name}
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "file_name": "api-reference.pdf",
    "deleted_at": 1704153600000
  },
  "msg": "文件已删除"
}
```

### 12. 单知识库检索

在指定知识库中进行向量检索。

```http
POST /api/knowledge/retrieve
Content-Type: application/json
```

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `knowledge_base_id` | string | ✅ | 知识库ID |
| `query` | string | ✅ | 查询文本 |
| `top_k` | integer | ❌ | 返回结果数量，默认5 |
| `score_threshold` | float | ❌ | 相似度阈值，默认0.5 |

#### 请求示例

```json
{
  "knowledge_base_id": "kb-tech-docs",
  "query": "如何配置数据库连接？",
  "top_k": 5,
  "score_threshold": 0.7
}
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "query": "如何配置数据库连接？",
    "results": [
      {
        "content": "数据库连接配置需要在config.yaml中设置...",
        "metadata": {
          "source": "deployment-guide.pdf",
          "page": 15,
          "chunk_index": 23
        },
        "score": 0.92
      }
    ],
    "total": 5
  },
  "msg": "success"
}
```

### 13. 多知识库混合检索

在多个知识库中同时进行检索并合并结果。

```http
POST /api/knowledge/batch-search
Content-Type: application/json
```

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `knowledge_base_ids` | array | ✅ | 知识库ID列表 |
| `query` | string | ✅ | 查询文本 |
| `top_k` | integer | ❌ | 每个知识库返回数量 |
| `rerank` | boolean | ❌ | 是否重排序，默认true |

#### 请求示例

```json
{
  "knowledge_base_ids": ["kb-tech-docs", "kb-product-manual"],
  "query": "安装步骤",
  "top_k": 3,
  "rerank": true
}
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "query": "安装步骤",
    "results": [
      {
        "content": "安装步骤如下：1. 下载安装包...",
        "metadata": {
          "source": "install-guide.pdf",
          "knowledge_base_id": "kb-tech-docs",
          "knowledge_base_name": "技术文档"
        },
        "score": 0.95
      }
    ],
    "sources": {
      "kb-tech-docs": 3,
      "kb-product-manual": 2
    }
  },
  "msg": "success"
}
```

---

## ⚙️ 模型配置 API

动态管理系统支持的 LLM 提供商、配置以及向量嵌入模型。

### 接口概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/models/list` | 获取所有可用模型 |
| `GET` | `/models/providers` | 获取服务商列表 |
| `GET` | `/models/provider/{provider_key}` | 获取特定服务商详情 |
| `POST` | `/models/config` | 保存/更新模型配置 |
| `GET` | `/models/config/{model_id}` | 获取指定配置 |
| `GET` | `/models/test` | 测试模型可用性 |
| `GET` | `/models/embedding/list` | 获取Embedding模型列表 |
| `GET` | `/config/app-info` | 获取系统应用信息 |

### 1. 获取所有可用模型

```http
GET /api/models/list
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "providers": [
      {
        "key": "openai",
        "name": "OpenAI",
        "display_name": "OpenAI",
        "enabled": true,
        "models": [
          {
            "id": "gpt-4o",
            "name": "GPT-4o",
            "display_name": "GPT-4o",
            "enabled": true,
            "tags": ["多模态", "旗舰"],
            "capabilities": {
              "vision": true,
              "function_calling": true,
              "streaming": true
            },
            "context_window": 128000,
            "max_output_tokens": 4096
          },
          {
            "id": "gpt-4o-mini",
            "name": "GPT-4o Mini",
            "display_name": "GPT-4o Mini",
            "enabled": true,
            "tags": ["轻量", "快速"],
            "capabilities": {
              "vision": true,
              "function_calling": true,
              "streaming": true
            },
            "context_window": 128000,
            "max_output_tokens": 4096
          }
        ]
      },
      {
        "key": "deepseek",
        "name": "DeepSeek",
        "display_name": "DeepSeek",
        "enabled": true,
        "models": [
          {
            "id": "deepseek-chat",
            "name": "DeepSeek Chat",
            "display_name": "DeepSeek-V3",
            "enabled": true,
            "tags": ["通用"],
            "capabilities": {
              "vision": false,
              "function_calling": true,
              "streaming": true
            },
            "context_window": 64000,
            "max_output_tokens": 8192
          },
          {
            "id": "deepseek-reasoner",
            "name": "DeepSeek Reasoner",
            "display_name": "DeepSeek-R1",
            "enabled": true,
            "tags": ["推理"],
            "capabilities": {
              "vision": false,
              "function_calling": true,
              "streaming": true,
              "reasoning": true
            },
            "context_window": 64000,
            "max_output_tokens": 8192
          }
        ]
      }
    ]
  },
  "msg": "success"
}
```

### 2. 获取服务商列表

```http
GET /api/models/providers
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "providers": [
      {
        "key": "openai",
        "name": "OpenAI",
        "display_name": "OpenAI",
        "enabled": true,
        "model_count": 5
      },
      {
        "key": "deepseek",
        "name": "DeepSeek",
        "display_name": "DeepSeek",
        "enabled": true,
        "model_count": 2
      }
    ]
  },
  "msg": "success"
}
```

### 3. 获取特定服务商详情

```http
GET /api/models/provider/{provider_key}
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "key": "openai",
    "name": "OpenAI",
    "display_name": "OpenAI",
    "base_url": "https://api.openai.com/v1",
    "enabled": true,
    "models": [
      {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "enabled": true,
        "tags": ["多模态"]
      }
    ]
  },
  "msg": "success"
}
```

### 4. 保存/更新模型配置

```http
POST /api/models/config
Content-Type: application/json
```

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `provider` | string | ✅ | 服务商key |
| `api_key` | string | ❌ | API密钥 |
| `base_url` | string | ❌ | 自定义Base URL |
| `models` | array | ❌ | 模型配置列表 |
| `enabled` | boolean | ❌ | 是否启用 |

#### 请求示例

```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "enabled": true,
  "models": [
    {
      "id": "gpt-4o",
      "enabled": true
    },
    {
      "id": "gpt-4o-mini",
      "enabled": true
    }
  ]
}
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "provider": "openai",
    "updated_at": 1704153600000,
    "models_updated": 2
  },
  "msg": "配置已保存"
}
```

### 5. 测试模型可用性

```http
GET /api/models/test?provider=openai&model=gpt-4o
```

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `provider` | string | ✅ | 服务商key |
| `model` | string | ✅ | 模型ID |

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "provider": "openai",
    "model": "gpt-4o",
    "available": true,
    "latency_ms": 450,
    "tested_at": 1704153600000
  },
  "msg": "模型可用"
}
```

### 6. 获取Embedding模型列表

```http
GET /api/models/embedding/list
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "default_provider": "modelscope",
    "providers": [
      {
        "key": "modelscope",
        "name": "魔塔",
        "enabled": true,
        "models": [
          {
            "id": "Qwen/Qwen3-Embedding-8B",
            "name": "Qwen3-Embedding-8B",
            "default": true,
            "dimension": 4096
          },
          {
            "id": "bge-small-zh-v1.5",
            "name": "BGE-Small-ZH",
            "default": false,
            "dimension": 512
          },
          {
            "id": "bge-base-zh-v1.5",
            "name": "BGE-Base-ZH",
            "default": false,
            "dimension": 768
          }
        ]
      },
      {
        "key": "openai",
        "name": "OpenAI",
        "enabled": true,
        "models": [
          {
            "id": "text-embedding-3-small",
            "name": "text-embedding-3-small",
            "dimension": 1536
          },
          {
            "id": "text-embedding-3-large",
            "name": "text-embedding-3-large",
            "dimension": 3072
          }
        ]
      }
    ]
  },
  "msg": "success"
}
```

### 7. 获取系统应用信息

```http
GET /api/config/app-info
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "name": "JeikChat",
    "version": "3.0.0",
    "description": "JeikChat 智能客服系统",
    "social_links": [
      {
        "name": "Github",
        "url": "https://github.com/jeikl/JeikChat",
        "icon": "Github"
      },
      {
        "name": "Gitee",
        "url": "https://gitee.com/jeikl/jeikchat",
        "icon": "Gitee"
      }
    ],
    "features": {
      "chat": true,
      "knowledge_base": true,
      "mcp_tools": true,
      "streaming": true
    }
  },
  "msg": "success"
}
```

---

## 🛠️ 工具服务 API

Model Context Protocol (MCP) 扩展工具系统，赋予 AI 使用外部工具的能力。

### 接口概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/tools` | 获取可用工具列表 |
| `POST` | `/tools/{tool_id}/enable` | 启用特定工具 |
| `POST` | `/tools/{tool_id}/disable` | 禁用特定工具 |
| `POST` | `/tools/batch-set` | 批量设置工具状态 |
| `POST` | `/tools/cache/refresh` | 刷新工具缓存 |
| `GET` | `/tools/cache/status` | 查询缓存状态 |
| `GET` | `/tools/stream` | 工具调用SSE流式日志 |

### 1. 获取可用工具列表

```http
GET /api/tools
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "builtin_tools": [
      {
        "id": "get_current_time",
        "name": "获取当前时间",
        "description": "获取当前系统时间",
        "type": "builtin",
        "enabled": true,
        "parameters": {
          "type": "object",
          "properties": {},
          "required": []
        }
      },
      {
        "id": "calculate",
        "name": "计算器",
        "description": "执行数学计算",
        "type": "builtin",
        "enabled": true,
        "parameters": {
          "type": "object",
          "properties": {
            "expression": {
              "type": "string",
              "description": "数学表达式"
            }
          },
          "required": ["expression"]
        }
      }
    ],
    "mcp_tools": [
      {
        "id": "zhipu-web-search-sse_webSearchPro",
        "name": "webSearchPro",
        "description": "智谱AI网络搜索工具",
        "type": "mcp",
        "server": "zhipu-web-search-sse",
        "enabled": true,
        "parameters": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "搜索关键词"
            }
          },
          "required": ["query"]
        }
      },
      {
        "id": "github_github_fork_repository",
        "name": "github_fork_repository",
        "description": "Fork一个GitHub仓库",
        "type": "mcp",
        "server": "github",
        "enabled": false,
        "parameters": {
          "type": "object",
          "properties": {
            "owner": {
              "type": "string",
              "description": "仓库所有者"
            },
            "repo": {
              "type": "string",
              "description": "仓库名称"
            }
          },
          "required": ["owner", "repo"]
        }
      }
    ]
  },
  "msg": "success"
}
```

### 2. 启用特定工具

```http
POST /api/tools/{tool_id}/enable
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "tool_id": "github_github_fork_repository",
    "enabled": true,
    "updated_at": 1704153600000
  },
  "msg": "工具已启用"
}
```

### 3. 禁用特定工具

```http
POST /api/tools/{tool_id}/disable
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "tool_id": "github_github_fork_repository",
    "enabled": false,
    "updated_at": 1704153600000
  },
  "msg": "工具已禁用"
}
```

### 4. 批量设置工具状态

```http
POST /api/tools/batch-set
Content-Type: application/json
```

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tools` | array | ✅ | 工具配置列表 |

#### 请求示例

```json
{
  "tools": [
    {
      "tool_id": "get_current_time",
      "enabled": true
    },
    {
      "tool_id": "zhipu-web-search-sse_webSearchPro",
      "enabled": true
    },
    {
      "tool_id": "github_github_fork_repository",
      "enabled": false
    }
  ]
}
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "updated": 3,
    "enabled": 2,
    "disabled": 1
  },
  "msg": "工具状态已更新"
}
```

### 5. 刷新工具缓存

```http
POST /api/tools/cache/refresh
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "refreshed_at": 1704153600000,
    "tools_count": 15,
    "mcp_servers": 4
  },
  "msg": "工具缓存已刷新"
}
```

### 6. 查询缓存状态

```http
GET /api/tools/cache/status
```

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "last_updated": 1704153600000,
    "tools_count": 15,
    "builtin_count": 3,
    "mcp_count": 12,
    "mcp_servers": [
      {
        "name": "zhipu-web-search-sse",
        "transport": "sse",
        "status": "connected",
        "tools_count": 2
      },
      {
        "name": "github",
        "transport": "streamable_http",
        "status": "connected",
        "tools_count": 8
      }
    ]
  },
  "msg": "success"
}
```

### 7. 工具调用SSE流式日志

实时监听工具调用过程。

```http
GET /api/tools/stream
Accept: text/event-stream
```

#### SSE事件格式

```
event: tool_start
data: {"tool_id": "get_current_time", "task_id": "task-123", "timestamp": 1704153600000}

event: tool_call
data: {"tool_id": "get_current_time", "input": {}, "timestamp": 1704153600100}

event: tool_result
data: {"tool_id": "get_current_time", "output": "2024-01-01 12:00:00", "duration_ms": 50}

event: tool_end
data: {"tool_id": "get_current_time", "task_id": "task-123", "timestamp": 1704153600150}
```

---

## 📁 文件服务 API

处理系统的通用文件上传逻辑。

### 接口概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/file/upload` | 通用文件上传 |

### 1. 通用文件上传

```http
POST /api/file/upload
Content-Type: multipart/form-data
```

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | file | ✅ | 上传的文件 |
| `path` | string | ❌ | 存储路径 |

#### 响应示例

```json
{
  "status": 1,
  "data": {
    "file_name": "document.pdf",
    "file_url": "https://storage.example.com/uploads/document.pdf",
    "file_size": 1048576,
    "mime_type": "application/pdf",
    "uploaded_at": 1704153600000
  },
  "msg": "文件上传成功"
}
```

---

## ❌ 错误码说明

### 通用错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| `400001` | 请求参数错误 | 检查请求参数格式和必填项 |
| `400002` | JSON解析错误 | 检查请求体是否为有效JSON |
| `400003` | 参数校验失败 | 根据错误信息修正参数值 |
| `401001` | 未授权访问 | 检查API Key或登录状态 |
| `401002` | Token已过期 | 重新获取Token |
| `403001` | 权限不足 | 检查用户权限配置 |
| `404001` | 资源不存在 | 检查资源ID是否正确 |
| `404002` | 接口不存在 | 检查请求路径 |
| `422001` | 请求实体过大 | 减小请求体大小 |
| `429001` | 请求过于频繁 | 降低请求频率 |
| `500001` | 服务器内部错误 | 联系管理员 |
| `500002` | 数据库错误 | 联系管理员 |
| `500003` | 外部服务错误 | 检查外部服务状态 |
| `503001` | 服务暂时不可用 | 稍后重试 |

### 业务错误码

| 错误码 | 说明 | 场景 |
|--------|------|------|
| `CHAT001` | 模型调用失败 | LLM API返回错误 |
| `CHAT002` | 会话不存在 | 查询的会话ID无效 |
| `CHAT003` | 任务不存在 | 取消的任务ID无效 |
| `KB001` | 知识库已存在 | 创建重复名称的知识库 |
| `KB002` | 知识库不存在 | 操作的知识库ID无效 |
| `KB003` | 文件格式不支持 | 上传了不支持的文件类型 |
| `KB004` | 文件过大 | 超过最大文件大小限制 |
| `KB005` | 文档解析失败 | 文件内容无法解析 |
| `MODEL001` | 模型配置无效 | 模型配置参数错误 |
| `MODEL002` | 模型测试失败 | 模型API连接失败 |
| `TOOL001` | 工具调用失败 | MCP工具执行错误 |
| `TOOL002` | 工具不存在 | 操作的工具ID无效 |

---

## 📊 数据模型

### Message (消息)

```typescript
interface Message {
  id: string;                    // 消息唯一标识
  role: 'user' | 'assistant' | 'system';  // 消息角色
  content: string;               // 消息内容
  reasoning?: string;            // 推理过程（思考模式）
  timestamp: number;             // 时间戳（毫秒）
  references?: KnowledgeReference[];  // 知识库引用
  isStreaming?: boolean;         // 是否正在流式输出
  thinking?: boolean;            // 是否显示思考过程
  isCancelled?: boolean;         // 是否已取消
  hasReasoning?: boolean;        // 是否有推理内容
  reasoningExpanded?: boolean;   // 推理内容是否展开
  internalContent?: string;      // 内部处理内容（工具调用等）
}
```

### ChatSession (聊天会话)

```typescript
interface ChatSession {
  id: string;                    // 会话唯一标识
  title: string;                 // 会话标题
  messages: Message[];           // 消息列表
  createdAt: number;             // 创建时间
  updatedAt: number;             // 更新时间
  modelId?: string;              // 使用的模型ID
  knowledgeBaseIds?: string[];   // 挂载的知识库ID列表
  isDefault?: boolean;           // 是否默认会话
}
```

### KnowledgeBase (知识库)

```typescript
interface KnowledgeBase {
  id: string;                    // 知识库唯一标识
  name: string;                  // 知识库名称
  description?: string;          // 知识库描述
  documentCount: number;         // 文档数量
  totalChunks: number;           // 总块数
  embeddingModel: string;        // Embedding模型
  vectorStore: string;           // 向量存储类型
  chunkSize: number;             // 分块大小
  chunkOverlap: number;          // 分块重叠
  createdAt: number;             // 创建时间
  updatedAt: number;             // 更新时间
  status: 'empty' | 'processing' | 'ready' | 'error';  // 状态
}
```

### KnowledgeReference (知识引用)

```typescript
interface KnowledgeReference {
  source: any;                   // 源信息
  knowledgeId: string;           // 知识库ID
  knowledgeName: string;         // 知识库名称
  content: string;               // 引用内容
  similarity: number;            // 相似度分数
}
```

### Tool (工具)

```typescript
interface Tool {
  id: string;                    // 工具唯一标识
  name: string;                  // 工具名称
  description: string;           // 工具描述
  type: 'builtin' | 'mcp';       // 工具类型
  server?: string;               // MCP服务器名称（MCP工具）
  enabled: boolean;              // 是否启用
  parameters: object;            // 参数Schema
}
```

### ToolConfig (工具配置)

```typescript
interface ToolConfig {
  toolid: string;                // 工具ID
  mcp: number;                   // 0=普通工具, 1=MCP工具
  name?: string;                 // 显示名称
  description?: string;          // 描述
}
```

### Model (模型)

```typescript
interface Model {
  id: string;                    // 模型唯一标识
  name: string;                  // 模型名称
  displayName: string;           // 显示名称
  enabled: boolean;              // 是否启用
  tags: string[];                // 标签列表
  capabilities: {
    vision: boolean;             // 是否支持视觉
    functionCalling: boolean;    // 是否支持函数调用
    streaming: boolean;          // 是否支持流式
    reasoning?: boolean;         // 是否支持推理
  };
  contextWindow: number;         // 上下文窗口大小
  maxOutputTokens: number;       // 最大输出token数
}
```

---

## 🧪 测试示例

### cURL示例

**发送聊天消息：**

```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你好",
    "model": "gpt-4o"
  }'
```

**流式输出：**

```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你好",
    "stream": true
  }' \
  --no-buffer
```

**创建知识库：**

```bash
curl -X POST http://localhost:8000/api/knowledge/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-kb",
    "description": "我的知识库"
  }'
```

**上传文件：**

```bash
curl -X POST http://localhost:8000/api/knowledge/my-kb/upload \
  -F "files=@document.pdf"
```

### Python示例

```python
import requests

# 发送消息
response = requests.post(
    "http://localhost:8000/api/chat/send",
    json={
        "content": "你好",
        "model": "gpt-4o"
    }
)
data = response.json()
print(data)

# 流式输出
import sseclient

response = requests.post(
    "http://localhost:8000/api/chat/send",
    json={"content": "你好", "stream": True},
    stream=True
)
client = sseclient.SSEClient(response)
for event in client.events():
    print(event.data)
```

### JavaScript/TypeScript示例

```typescript
// 发送消息
const response = await fetch('http://localhost:8000/api/chat/send', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content: '你好',
    model: 'gpt-4o'
  })
});
const data = await response.json();

// 流式输出
const eventSource = new EventSource(
  'http://localhost:8000/api/chat/send',
  { method: 'POST', body: JSON.stringify({ content: '你好' }) }
);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

---

## 📚 相关资源

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [OpenAPI规范](https://swagger.io/specification/)
- [SSE规范](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [LangChain文档](https://python.langchain.com/)
- [MCP协议文档](https://modelcontextprotocol.io/)

---

<div align="center">

**文档版本**: 3.0.0 | **最后更新**: 2024-01-01

</div>
