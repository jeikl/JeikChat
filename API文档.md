# AI 智能客服系统 - API 接口文档

## 目录

- [基础配置 API (Config)](#基础配置-api-config)
- [聊天服务 API (Chat)](#聊天服务-api-chat)
- [知识库服务 API (Knowledge)](#知识库服务-api-knowledge)
- [工具服务 API (Tools)](#工具服务-api-tools)

---

## 基础配置 API (Config)

### 1. 获取所有模型配置列表

| 项目 | 内容 |
|------|------|
| 请求方式 | `GET /api/config/list` |
| 触发位置 | [pages/SettingsPage.tsx](file:///f:/code/aichat/frontend/src/pages/SettingsPage.tsx) - 页面加载时 |
| 按钮/操作 | 页面加载自动触发 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": [
    {
      "id": "config_1",
      "name": "GPT-4",
      "provider": "openai",
      "model": "gpt-4",
      "apiKey": "sk-xxx",
      "temperature": 0.7,
      "maxTokens": 4096,
      "topP": 1,
      "enabled": true
    }
  ],
  "msg": "获取成功"
}
```

---

### 2. 创建新的模型配置

| 项目 | 内容 |
|------|------|
| 请求方式 | `POST /api/config/create` |
| 触发位置 | [pages/SettingsPage.tsx](file:///f:/code/aichat/frontend/src/pages/SettingsPage.tsx) - handleAddConfig() |
| 按钮/操作 | 点击"添加模型配置"按钮 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": {
    "id": "config_new_123",
    "name": "GPT-4",
    "provider": "openai",
    "model": "gpt-4",
    "apiKey": "sk-xxx",
    "temperature": 0.7,
    "maxTokens": 4096,
    "enabled": true
  },
  "msg": "创建成功"
}
```

---

### 3. 更新模型配置

| 项目 | 内容 |
|------|------|
| 请求方式 | `PUT /api/config/{id}` |
| 触发位置 | [stores/settingsStore.ts](file:///f:/code/aichat/frontend/src/stores/settingsStore.ts) - updateConfig() |
| 按钮/操作 | 点击模型卡片编辑按钮 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": {
    "id": "config_1",
    "name": "GPT-4-Updated",
    "temperature": 0.8
  },
  "msg": "更新成功"
}
```

---

### 4. 删除模型配置

| 项目 | 内容 |
|------|------|
| 请求方式 | `DELETE /api/config/{id}` |
| 触发位置 | [stores/settingsStore.ts](file:///f:/code/aichat/frontend/src/stores/settingsStore.ts) - removeConfig() |
| 按钮/操作 | 点击模型卡片删除按钮 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": null,
  "msg": "删除成功"
}
```

---

### 5. 获取当前激活的配置ID

| 项目 | 内容 |
|------|------|
| 请求方式 | `GET /api/config/active` |
| 触发位置 | [stores/settingsStore.ts](file:///f:/code/aichat/frontend/src/stores/settingsStore.ts) - activeConfigId 持久化 |
| 按钮/操作 | 页面加载自动触发 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": "config_1",
  "msg": "获取成功"
}
```

---

### 6. 设置激活的配置

| 项目 | 内容 |
|------|------|
| 请求方式 | `POST /api/config/active` |
| 触发位置 | [pages/SettingsPage.tsx](file:///f:/code/aichat/frontend/src/pages/SettingsPage.tsx) - setActiveConfig() |
| 按钮/操作 | 点击模型卡片的选择按钮 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": null,
  "msg": "设置成功"
}
```

---

## 聊天服务 API (Chat)

### 1. 发送消息（非流式）

| 项目 | 内容 |
|------|------|
| 请求方式 | `POST /api/chat/send` (stream: false) |
| 触发位置 | [stores/chatStore.ts](file:///f:/code/aichat/frontend/src/stores/chatStore.ts) - sendMessage() |
| 按钮/操作 | 输入框输入文字 → 点击发送按钮 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": {
    "sessionId": "session_123",
    "message": {
      "id": "msg_456",
      "role": "assistant",
      "content": "创建数据库的步骤如下：...",
      "timestamp": 1700000000000,
      "references": [
        {
          "knowledgeId": "kb_1",
          "knowledgeName": "产品文档",
          "content": "数据库创建指南...",
          "similarity": 0.95
        }
      ]
    }
  },
  "msg": "发送成功"
}
```

---

### 2. 发送消息（流式）⭐重要

| 项目 | 内容 |
|------|------|
| 请求方式 | `POST /api/chat/send` (stream: true) |
| 触发位置 | [stores/chatStore.ts](file:///f:/code/aichat/frontend/src/stores/chatStore.ts) - sendMessage() |
| 按钮/操作 | 输入框输入文字 → 点击发送按钮 |

**返回示例** ⚠️ SSE流式返回（保持原样，为兼容AI输出）

```
data: {"sessionId": "session_123", "content": "AI"}
data: {"content": "是"}
data: {"content": "人工智能"}
data: {"content": "（"}
data: {"content": "Artificial"}
data: {"content": " Intelligence"}
data: {"content": "）"}
data: {"content": "的"}
data: {"content": "缩写，"}
data: {"content": "它是..."}
data: {"references": [{"knowledgeId": "kb_1", "knowledgeName": "AI入门", "content": "AI是...", "similarity": 0.92}]}
data: [DONE]
```

> **说明**：SSE流式返回是AI对话的特殊需求，需要逐字返回内容实现打字机效果，不适合包装RESTful格式。

**前端处理流程**

```
用户点击发送 → 添加用户消息 → 创建AI消息占位 → 流式接收 → 逐字更新UI → 收到[DONE] → 完成
```

---

### 3. 获取指定会话的历史记录

| 项目 | 内容 |
|------|------|
| 请求方式 | `GET /api/chat/history/{sessionId}` |
| 触发位置 | [components/Common/Sidebar.tsx](file:///f:/code/aichat/frontend/src/components/Common/Sidebar.tsx) - handleSessionClick() |
| 按钮/操作 | 点击侧边栏的历史对话记录 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": {
    "id": "session_123",
    "title": "如何创建数据库？",
    "messages": [
      { "id": "msg_1", "role": "user", "content": "如何创建数据库？", "timestamp": 1700000000000 },
      { "id": "msg_2", "role": "assistant", "content": "创建数据库的步骤如下：...", "timestamp": 1700000001000 }
    ],
    "createdAt": 1700000000000,
    "updatedAt": 1700000001000
  },
  "msg": "获取成功"
}
```

---

### 4. 获取所有会话列表

| 项目 | 内容 |
|------|------|
| 请求方式 | `GET /api/chat/history` |
| 触发位置 | [stores/chatStore.ts](file:///f:/code/aichat/frontend/src/stores/chatStore.ts) - sessions 持久化 |
| 按钮/操作 | 页面加载自动触发 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": {
    "sessions": [
      { "id": "session_1", "title": "如何创建数据库？", "messages": [], "createdAt": 1700000000000, "updatedAt": 1700000001000 },
      { "id": "session_2", "title": "Python入门", "messages": [], "createdAt": 1699900000000, "updatedAt": 1699900100000 }
    ]
  },
  "msg": "获取成功"
}
```

---

### 5. 删除指定会话

| 项目 | 内容 |
|------|------|
| 请求方式 | `DELETE /api/chat/history/{sessionId}` |
| 触发位置 | [components/Common/Sidebar.tsx](file:///f:/code/aichat/frontend/src/components/Common/Sidebar.tsx) - handleDeleteSession() |
| 按钮/操作 | 鼠标悬停 → 显示删除按钮 → 点击删除 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": null,
  "msg": "删除成功"
}
```

---

### 6. 清空所有会话历史

| 项目 | 内容 |
|------|------|
| 请求方式 | `DELETE /api/chat/history` |
| 触发位置 | [stores/chatStore.ts](file:///f:/code/aichat/frontend/src/stores/chatStore.ts) - clearAllSessions() |
| 按钮/操作 | 点击"清空所有对话"按钮 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": null,
  "msg": "清空成功"
}
```

---

### 7. 重命名会话

| 项目 | 内容 |
|------|------|
| 请求方式 | `PUT /api/chat/history/{sessionId}/title` |
| 触发位置 | [components/Common/Sidebar.tsx](file:///f:/code/aichat/frontend/src/components/Common/Sidebar.tsx) - handleRenameSession() |
| 按钮/操作 | 鼠标悬停 → 显示编辑按钮 → 点击编辑 → 输入新名称 → 回车 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": null,
  "msg": "重命名成功"
}
```

---

## 知识库服务 API (Knowledge)

### 1. 获取所有知识库列表

| 项目 | 内容 |
|------|------|
| 请求方式 | `GET /api/knowledge/list` |
| 触发位置 | [pages/KnowledgePage.tsx](file:///f:/code/aichat/frontend/src/pages/KnowledgePage.tsx) - 页面加载时 |
| 按钮/操作 | 页面加载自动触发 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": [
    {
      "id": "kb_1",
      "name": "产品文档",
      "description": "产品使用文档",
      "fileCount": 10,
      "status": "ready",
      "createdAt": 1700000000000,
      "updatedAt": 1700000100000
    }
  ],
  "msg": "获取成功"
}
```

---

### 2. 创建新的知识库

| 项目 | 内容 |
|------|------|
| 请求方式 | `POST /api/knowledge/create` |
| 触发位置 | [pages/KnowledgePage.tsx](file:///f:/code/aichat/frontend/src/pages/KnowledgePage.tsx) - handleCreateKnowledge() |
| 按钮/操作 | 点击"创建知识库" → 填写表单 → 点击确认 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": {
    "id": "kb_new_456",
    "name": "新产品文档",
    "description": "新产品使用说明",
    "fileCount": 0,
    "status": "ready",
    "createdAt": 1700000000000
  },
  "msg": "创建成功"
}
```

---

### 3. 更新知识库信息

| 项目 | 内容 |
|------|------|
| 请求方式 | `PUT /api/knowledge/{id}` |
| 触发位置 | [pages/KnowledgePage.tsx](file:///f:/code/aichat/frontend/src/pages/KnowledgePage.tsx) - handleUpdateKnowledge() |
| 按钮/操作 | 点击编辑按钮 → 修改信息 → 保存 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": {
    "id": "kb_1",
    "name": "更新后的名称",
    "description": "更新后的描述"
  },
  "msg": "更新成功"
}
```

---

### 4. 删除知识库

| 项目 | 内容 |
|------|------|
| 请求方式 | `DELETE /api/knowledge/{id}` |
| 触发位置 | [pages/KnowledgePage.tsx](file:///f:/code/aichat/frontend/src/pages/KnowledgePage.tsx) - handleDeleteKnowledge() |
| 按钮/操作 | 点击删除按钮 → 确认删除 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": null,
  "msg": "删除成功"
}
```

---

### 5. 获取知识库中的文件列表

| 项目 | 内容 |
|------|------|
| 请求方式 | `GET /api/knowledge/{knowledgeId}/files` |
| 触发位置 | [pages/KnowledgePage.tsx](file:///f:/code/aichat/frontend/src/pages/KnowledgePage.tsx) - 点击知识库卡片 |
| 按钮/操作 | 点击某个知识库卡片，展开查看文件 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": [
    { "id": "file_1", "name": "产品手册.pdf", "type": "pdf", "size": 1024000, "status": "ready", "createdAt": 1700000000000 },
    { "id": "file_2", "name": "常见问题.docx", "type": "docx", "size": 512000, "status": "processing", "createdAt": 1700000100000 }
  ],
  "msg": "获取成功"
}
```

---

### 6. 上传文件到知识库

| 项目 | 内容 |
|------|------|
| 请求方式 | `POST /api/knowledge/{knowledgeId}/upload` |
| 触发位置 | [pages/KnowledgePage.tsx](file:///f:/code/aichat/frontend/src/pages/KnowledgePage.tsx) - handleUploadFile() |
| 按钮/操作 | 点击"上传文件" → 选择文件 → 开始上传 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": {
    "id": "file_new_789",
    "name": "产品手册.pdf",
    "type": "pdf",
    "size": 1024000,
    "status": "processing",
    "createdAt": 1700000000000
  },
  "msg": "上传成功"
}
```

---

### 7. 删除知识库中的文件

| 项目 | 内容 |
|------|------|
| 请求方式 | `DELETE /api/knowledge/{knowledgeId}/files/{fileId}` |
| 触发位置 | [pages/KnowledgePage.tsx](file:///f:/code/aichat/frontend/src/pages/KnowledgePage.tsx) - handleDeleteFile() |
| 按钮/操作 | 点击文件删除按钮 → 确认删除 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": null,
  "msg": "删除成功"
}
```

---

### 8. 在知识库中搜索

| 项目 | 内容 |
|------|------|
| 请求方式 | `GET /api/knowledge/{knowledgeId}/search` |
| 触发位置 | [pages/KnowledgePage.tsx](file:///f:/code/aichat/frontend/src/pages/KnowledgePage.tsx) - 知识库内搜索框 |
| 按钮/操作 | 在搜索框输入关键词 → 回车搜索 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": [
    {
      "content": "创建数据库的第一步是...",
      "metadata": { "file": "产品手册.pdf", "page": 10 },
      "score": 0.95
    }
  ],
  "msg": "搜索成功"
}
```

---

### 9. 批量搜索多个知识库

| 项目 | 内容 |
|------|------|
| 请求方式 | `POST /api/knowledge/batch-search` |
| 触发位置 | [stores/chatStore.ts](file:///f:/code/aichat/frontend/src/stores/chatStore.ts) - sendMessage() 发送消息时 |
| 按钮/操作 | 用户发送消息时自动在选中的知识库中搜索 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": [
    {
      "content": "数据库性能优化的关键在于...",
      "metadata": { "knowledgeId": "kb_1", "knowledgeName": "产品文档", "file": "优化指南.pdf" },
      "score": 0.92
    }
  ],
  "msg": "搜索成功"
}
```

---

### 10. 获取所有可用的Agent工具列表

| 项目 | 内容 |
|------|------|
| 请求方式 | `GET /api/tools` |
| 触发位置 | [pages/AgentToolsPage.tsx](file:///f:/code/aichat/frontend/src/pages/AgentToolsPage.tsx) - 页面加载时 |
| 按钮/操作 | Agent Tools 页面加载时自动触发 |

**返回示例** ✅ 成功

```json
{
  "status": 1,
  "data": [
    { "id": "tool_1", "name": "数据库查询", "description": "可以执行SQL查询操作", "enabled": true },
    { "id": "tool_2", "name": "天气查询", "description": "查询指定城市的天气信息", "enabled": false }
  ],
  "msg": "获取成功，共 2 个工具"
}
```

**返回示例** ⚠️ 无工具

```json
{
  "status": 0,
  "data": [],
  "msg": "未获取到任何 Agent Tool，请检查后台配置"
}
```

---

## 工具服务 API (Tools)

### 1. 启用指定工具

| 项目 | 内容 |
|------|------|
| 请求方式 | `POST /api/tools/{toolId}/enable` |
| 触发位置 | [pages/AgentToolsPage.tsx](file:///f:/code/aichat/frontend/src/pages/AgentToolsPage.tsx) - handleToggleTool() |
| 按钮/操作 | 点击未启用的工具卡片 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": null,
  "msg": "启用成功"
}
```

---

### 2. 批量设置工具状态

| 项目 | 内容 |
|------|------|
| 请求方式 | `POST /api/tools/batch-set` |
| 触发位置 | [pages/AgentToolsPage.tsx](file:///f:/code/aichat/frontend/src/pages/AgentToolsPage.tsx) - handleBatchSet() |
| 按钮/操作 | 点击"全选"或"取消全选"按钮 |

**返回示例** ✅ RESTful

```json
{
  "status": 1,
  "data": null,
  "msg": "设置成功"
}
```

---

## 附录

### 返回格式说明

| 类型 | 格式 | 说明 |
|------|------|------|
| RESTful | `{ status: 1, data: ..., msg: "..." }` | 普通API统一返回格式 |
| 失败 | `{ status: 0, data: null, msg: "错误信息" }` | 操作失败时返回 |
| SSE流式 | `data: {...}\ndata: [DONE]` | AI对话流式输出，保持原样 |

### 文件位置速查

| 文件 | 路径 |
|------|------|
| 聊天容器 | [components/Chat/ChatContainer.tsx](file:///f:/code/aichat/frontend/src/components/Chat/ChatContainer.tsx) |
| 输入区域 | [components/Chat/InputArea.tsx](file:///f:/code/aichat/frontend/src/components/Chat/InputArea.tsx) |
| 顶部导航 | [components/Common/Header.tsx](file:///f:/code/aichat/frontend/src/components/Common/Header.tsx) |
| 侧边栏 | [components/Common/Sidebar.tsx](file:///f:/code/aichat/frontend/src/components/Common/Sidebar.tsx) |
| 聊天页面 | [pages/ChatPage.tsx](file:///f:/code/aichat/frontend/src/pages/ChatPage.tsx) |
| 知识库页面 | [pages/KnowledgePage.tsx](file:///f:/code/aichat/frontend/src/pages/KnowledgePage.tsx) |
| 工具页面 | [pages/AgentToolsPage.tsx](file:///f:/code/aichat/frontend/src/pages/AgentToolsPage.tsx) |
| 设置页面 | [pages/SettingsPage.tsx](file:///f:/code/aichat/frontend/src/pages/SettingsPage.tsx) |
| 聊天状态 | [stores/chatStore.ts](file:///f:/code/aichat/frontend/src/stores/chatStore.ts) |
| 知识库状态 | [stores/knowledgeStore.ts](file:///f:/code/aichat/frontend/src/stores/knowledgeStore.ts) |
| 设置状态 | [stores/settingsStore.ts](file:///f:/code/aichat/frontend/src/stores/settingsStore.ts) |
| 统一API | [services/api.ts](file:///f:/code/aichat/frontend/src/services/api.ts) |
| 后端聊天API | [api/chat.py](file:///f:/code/aichat/backend/api/chat.py) |
| 后端知识库API | [api/knowledge.py](file:///f:/code/aichat/backend/api/knowledge.py) |
| 后端模型API | [api/model.py](file:///f:/code/aichat/backend/api/model.py) |

---

*文档最后更新时间: 2024-01-15*
