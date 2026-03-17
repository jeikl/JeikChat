/**
 * ============================================================
 * JeikChat 智能客服系统 - API 统一管理文件
 * ============================================================
 * 
 * 本文件整合了所有前端API接口，提供了完整的类型定义和中文注释说明
 * 所有模块都应该从这里导入API，而不是直接使用 axios
 * 
 * 模块分类：
 * - 基础配置 (Config) - LLM模型配置相关API
 * - 聊天服务 (Chat) - 对话相关API
 * - 知识库服务 (Knowledge) - 知识库管理相关API
 * - 工具服务 (Tools) - Agent工具相关API
 * 
 * 使用示例：
 *   import { chatApi, knowledgeApi, configApi } from '@/services/api';
 *   const sessions = await chatApi.getAllSessions();
 * 
 * 返回格式说明：
 * - 普通API: { status: 1, data: ..., msg: "..." }
 * - 流式API: SSE格式，保持原样不包装
 * ============================================================
 */

import apiClient from './client';
import type { Message, ChatSession, KnowledgeReference } from '@/types/chat';
import type { KnowledgeBase, KnowledgeFile, SearchResult, VectorStoreConfig } from '@/types/knowledge';
import type { LLMConfig } from '@/types/config';

// ============================================================
// 类型定义
// ============================================================

// RESTful统一响应格式
export interface ApiResponse<T> {
  status: number;
  data: T;
  msg: string;
}

// 工具配置对象（用于发送消息时传递工具信息）
export interface ToolConfig {
  toolid: string;  // 工具名
  mcp: number;     // 0=普通工具, 1=MCP工具
  name?: string;   // 显示名称（可选）
  description?: string;  // 描述（可选）
}

// 聊天相关类型
export interface SendMessageRequest {
  content: string;
  sessionId?: string;
  model?: string;
  knowledgeBaseIds?: string[];
  stream?: boolean;
  tools?: ToolConfig[];  // 改为 ToolConfig 对象列表
}

export interface SendMessageResponse {
  sessionId: string;
  message: Message;
}

export interface ChatHistoryResponse {
  sessions: ChatSession[];
}

// 知识库相关类型
export interface CreateKnowledgeRequest {
  name: string;
  description?: string;
  systemPrompt?: string;
  vectorStoreConfig?: VectorStoreConfig;
}

// 工具相关类型
export interface Tool {
  toolid: string;  // 工具唯一标识（原名）
  name: string;    // 显示名称
  description: string;
  mcp: number;     // 0=普通工具, 1=MCP工具
  enabled?: boolean;
}

// MCP 服务分组类型
export interface MCPToolService {
  id: string;
  name: string;
  description: string;
  toolCount: number;
  tools: Tool[];
  source: 'built-in' | 'mcp';
}

// ============================================================
// 基础配置 API (LLM模型配置)
// ============================================================

/**
 * 配置相关API - 用于管理LLM模型配置
 * 触发位置：设置页面 - 模型选择下拉框
 */
export const configApi = {
  /**
   * 获取所有模型配置列表
   * @请求方式 GET /api/config/list
   * @触发位置 SettingsPage.tsx - 页面加载时
   * @返回 { status: 1, data: [...], msg: "获取成功" }
   */
  getConfigs: async (): Promise<LLMConfig[]> => {
    const response = await apiClient.get<ApiResponse<LLMConfig[]>>('/config/list');
    return response.data.data || [];
  },

  /**
   * 创建新的模型配置
   * @请求方式 POST /api/config/create
   * @触发位置 SettingsPage.tsx - handleAddConfig()
   * @返回 { status: 1, data: {...}, msg: "创建成功" }
   */
  createConfig: async (config: Omit<LLMConfig, 'id'>): Promise<LLMConfig> => {
    const response = await apiClient.post<ApiResponse<LLMConfig>>('/config/create', config);
    return response.data.data;
  },

  /**
   * 更新模型配置
   * @请求方式 PUT /api/config/{id}
   * @触发位置 SettingsPage.tsx - handleUpdateConfig()
   * @返回 { status: 1, data: {...}, msg: "更新成功" }
   */
  updateConfig: async (id: string, config: Partial<LLMConfig>): Promise<LLMConfig> => {
    const response = await apiClient.put<ApiResponse<LLMConfig>>(`/config/${id}`, config);
    return response.data.data;
  },

  /**
   * 删除模型配置
   * @请求方式 DELETE /api/config/{id}
   * @触发位置 SettingsPage.tsx - handleDeleteConfig()
   * @返回 { status: 1, data: null, msg: "删除成功" }
   */
  deleteConfig: async (id: string): Promise<void> => {
    await apiClient.delete(`/config/${id}`);
  },

  /**
   * 获取当前激活的配置ID
   * @请求方式 GET /api/config/active
   * @触发位置 Header.tsx - 页面加载时
   * @返回 { status: 1, data: "config_1", msg: "获取成功" }
   */
  getActiveConfig: async (): Promise<string> => {
    const response = await apiClient.get<ApiResponse<string>>('/config/active');
    return response.data.data;
  },

  /**
   * 设置激活的配置
   * @请求方式 POST /api/config/active
   * @触发位置 SettingsPage.tsx - setActiveConfig()
   * @返回 { status: 1, data: null, msg: "设置成功" }
   */
  setActiveConfig: async (id: string): Promise<void> => {
    await apiClient.post('/config/active', { id });
  },
  /**
   * 获取应用信息（包括社交链接）
   * @请求方式 GET /api/config/app-info
   * @触发位置 Header.tsx - 页面加载时
   * @返回 { status: 1, data: {...}, msg: "获取成功" }
   */
  getAppInfo: async (): Promise<any> => {
    const response = await apiClient.get<ApiResponse<any>>('/config/app-info');
    return response.data.data || {};
  },
};

// ============================================================
// 聊天服务 API
// ============================================================

/**
 * 聊天相关API - 用于处理对话功能
 * 触发位置：ChatContainer组件、Sidebar组件
 */
export const chatApi = {
  /**
   * 发送消息（非流式）
   * @请求方式 POST /api/chat/send (stream: false)
   * @触发位置 chatStore.ts - sendMessage()
   * @返回 { status: 1, data: {...}, msg: "发送成功" }
   */
  sendMessage: async (data: SendMessageRequest): Promise<SendMessageResponse> => {
    const response = await apiClient.post<ApiResponse<SendMessageResponse>>('/chat/send', {
      ...data,
      stream: true,
    });
    return response.data.data;
  },

  /**
   * 发送消息（流式）- 用于实时显示AI回复
   * @请求方式 POST /api/chat/send (stream: true)
   * @触发位置 chatStore.ts - sendMessage()
   * @返回 SSE流式响应（保持原样不包装）
   */
  sendMessageStream: async (
    data: SendMessageRequest,
    onChunk: (content: string, references?: KnowledgeReference[]) => void
  ): Promise<SendMessageResponse> => {
    const response = await apiClient.post('/chat/send', {
      ...data,
      stream: true,
    }, {
      responseType: 'stream',
    });

    return new Promise((resolve, reject) => {
      let sessionId = '';
      let content = '';
      let references: KnowledgeReference[] = [];

      response.data.on('data', (chunk: Buffer) => {
        const lines = chunk.toString().split('\n').filter(line => line.trim());
        
        for (const line of lines) {
          const data = line.replace('data: ', '');
          
          if (data === '[DONE]') {
            resolve({
              sessionId,
              message: {
                id: Date.now().toString(),
                role: 'assistant',
                content,
                timestamp: Date.now(),
                references,
              },
            });
            return;
          }

          try {
            const parsed = JSON.parse(data);
            
            if (parsed.sessionId) sessionId = parsed.sessionId;
            if (parsed.content) {
              content += parsed.content;
              onChunk(content, references);
            }
            if (parsed.references) {
              references = parsed.references;
            }
          } catch {
            // 跳过无效JSON
          }
        }
      });

      response.data.on('error', reject);
    });
  },

  /**
   * 获取指定会话的历史记录
   * @请求方式 GET /api/chat/history/{sessionId}
   * @触发位置 Sidebar.tsx - handleSessionClick()
   * @返回 { status: 1, data: {...}, msg: "获取成功" }
   */
  getHistory: async (sessionId: string): Promise<ChatSession> => {
    const response = await apiClient.get<ApiResponse<ChatSession>>(`/chat/history/${sessionId}`);
    return response.data.data;
  },

  /**
   * 获取所有会话列表
   * @请求方式 GET /api/chat/history
   * @触发位置 chatStore.ts - sessions持久化
   * @返回 { status: 1, data: { sessions: [...] }, msg: "获取成功" }
   */
  getAllSessions: async (): Promise<ChatHistoryResponse> => {
    const response = await apiClient.get<ApiResponse<{ sessions: ChatSession[] }>>('/chat/history');
    return response.data.data || { sessions: [] };
  },

  /**
   * 删除指定会话
   * @请求方式 DELETE /api/chat/history/{sessionId}
   * @触发位置 Sidebar.tsx - handleDeleteSession()
   * @返回 { status: 1, data: null, msg: "删除成功" }
   */
  deleteSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/chat/history/${sessionId}`);
  },

  /**
   * 清空所有会话历史
   * @请求方式 DELETE /api/chat/history
   * @触发位置 chatStore.ts - clearAllSessions()
   * @返回 { status: 1, data: null, msg: "清空成功" }
   */
  clearAllSessions: async (): Promise<void> => {
    await apiClient.delete('/chat/history');
  },
};

// ============================================================
// 文件服务 API
// ============================================================

/**
 * 文件上传相关API
 * 触发位置：InputArea.tsx - handlePaste/FileSelect
 */
export const fileApi = {
  /**
   * 上传文件
   * @请求方式 POST /api/file/upload
   * @触发位置 InputArea.tsx
   * @返回 { status: 1, data: { url: "...", filename: "..." }, msg: "上传成功" }
   */
  uploadFile: async (file: File): Promise<{ url: string; filename: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<ApiResponse<{ url: string; filename: string }>>('/file/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data.data;
  },
};

// ============================================================
// 知识库服务 API
// ============================================================

/**
 * 知识库相关API - 用于管理知识库、文件和搜索
 * 触发位置：KnowledgePage组件、Header组件
 */
export const knowledgeApi = {
  /**
   * 获取所有知识库列表
   * @请求方式 GET /api/knowledge/list
   * @触发位置 KnowledgePage.tsx - 页面加载时
   * @返回 { status: 1, data: [...], msg: "获取成功" }
   *         { status: 0, data: [], msg: "未获取到知识库" }
   */
  list: async (): Promise<{ data: KnowledgeBase[]; msg: string; status: number }> => {
    const response = await apiClient.get<ApiResponse<KnowledgeBase[]>>('/knowledge/list');
    return {
      data: response.data.data || [],
      msg: response.data.msg || '',
      status: response.data.status || 1
    };
  },

  /**
   * 创建新的知识库
   * @请求方式 POST /api/knowledge/create
   * @触发位置 KnowledgePage.tsx - handleCreateKnowledge()
   * @返回 { status: 1, data: {...}, msg: "创建成功" }
   */
  create: async (data: CreateKnowledgeRequest): Promise<KnowledgeBase> => {
    const response = await apiClient.post<ApiResponse<KnowledgeBase>>('/knowledge/create', data);
    return response.data.data;
  },

  /**
   * 更新知识库信息
   * @请求方式 PUT /api/knowledge/{id}
   * @触发位置 KnowledgePage.tsx - handleUpdateKnowledge()
   * @返回 { status: 1, data: {...}, msg: "更新成功" }
   */
  update: async (id: string, data: Partial<CreateKnowledgeRequest>): Promise<KnowledgeBase> => {
    const response = await apiClient.put<ApiResponse<KnowledgeBase>>(`/knowledge/${id}`, data);
    return response.data.data;
  },

  /**
   * 删除知识库
   * @请求方式 DELETE /api/knowledge/{id}
   * @触发位置 KnowledgePage.tsx - handleDeleteKnowledge()
   * @返回 { status: 1, data: null, msg: "删除成功" }
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/knowledge/${id}`);
  },

  /**
   * 获取知识库中的文件列表
   * @请求方式 GET /api/knowledge/{knowledgeId}/files
   * @触发位置 KnowledgePage.tsx - 查看知识库文件
   * @返回 { status: 1, data: [...], msg: "获取成功" }
   */
  getFiles: async (knowledgeId: string): Promise<KnowledgeFile[]> => {
    const response = await apiClient.get<ApiResponse<KnowledgeFile[]>>(`/knowledge/${knowledgeId}/files`);
    return response.data.data || [];
  },

  /**
   * 上传文件到知识库
   * @请求方式 POST /api/knowledge/{knowledgeId}/upload
   * @触发位置 KnowledgePage.tsx - handleUploadFile()
   * @返回 { status: 1, data: {...}, msg: "上传成功" }
   */
  uploadFile: async (
    knowledgeId: string, 
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<KnowledgeFile> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<ApiResponse<KnowledgeFile>>(
      `/knowledge/${knowledgeId}/upload`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
            onProgress(progress);
          }
        },
      }
    );
    return response.data.data;
  },

  /**
   * 删除知识库中的文件
   * @请求方式 DELETE /api/knowledge/{knowledgeId}/files/{fileId}
   * @触发位置 KnowledgePage.tsx - handleDeleteFile()
   * @返回 { status: 1, data: null, msg: "删除成功" }
   */
  deleteFile: async (knowledgeId: string, fileId: string): Promise<void> => {
    await apiClient.delete(`/knowledge/${knowledgeId}/files/${fileId}`);
  },

  /**
   * 在单个知识库中搜索
   * @请求方式 GET /api/knowledge/{knowledgeId}/search
   * @触发位置 KnowledgePage.tsx - 知识库内搜索
   * @返回 { status: 1, data: [...], msg: "搜索成功" }
   */
  search: async (knowledgeId: string, query: string, topK: number = 5): Promise<SearchResult[]> => {
    const response = await apiClient.get<ApiResponse<SearchResult[]>>(`/knowledge/${knowledgeId}/search`, {
      params: { query, topK },
    });
    return response.data.data || [];
  },

  /**
   * 批量搜索多个知识库
   * @请求方式 POST /api/knowledge/batch-search
   * @触发位置 chatStore.ts - sendMessage() 发送消息时
   * @返回 { status: 1, data: [...], msg: "搜索成功" }
   */
  batchSearch: async (
    knowledgeIds: string[], 
    query: string, 
    topK: number = 5
  ): Promise<SearchResult[]> => {
    const response = await apiClient.post<ApiResponse<SearchResult[]>>('/knowledge/batch-search', {
      knowledgeIds,
      query,
      topK,
    });
    return response.data.data || [];
  },

  /**
   * 重建知识库索引
   * @请求方式 POST /api/knowledge/{knowledgeId}/rebuild
   * @触发位置 KnowledgePage.tsx - handleRebuildIndex()
   * @返回 { status: 1, data: null, msg: "重建成功" }
   */
  rebuild: async (knowledgeId: string): Promise<void> => {
    await apiClient.post(`/knowledge/${knowledgeId}/rebuild`);
  },

  /**
   * 创建知识库并上传文件（一键创建）
   * @请求方式 POST /api/knowledge/create-with-files
   * @触发位置 KnowledgePage.tsx - 文件上传后自动创建
   * @返回 { status: 1, data: {...}, msg: "创建成功" }
   */
  createWithFiles: async (
    name: string,
    files: File[],
    onProgress?: (fileName: string, progress: number) => void
  ): Promise<KnowledgeBase> => {
    const formData = new FormData();
    formData.append('name', name);
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await apiClient.post<ApiResponse<KnowledgeBase>>(
      '/knowledge/create-with-files',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total && files.length > 0) {
            const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
            onProgress(files[0].name, progress);
          }
        },
      }
    );
    return response.data.data;
  },

  /**
   * 异步创建知识库（带实时进度）
   * @请求方式 POST /api/knowledge/create-async
   * @触发位置 KnowledgePage.tsx - 文件上传后异步创建
   * @返回 { status: 1, data: { taskId, knowledgeBase }, msg: "创建任务已启动" }
   */
  createAsync: async (
    name: string,
    files: File[],
    description?: string
  ): Promise<{ taskId: string; knowledgeBase: KnowledgeBase }> => {
    const formData = new FormData();
    formData.append('name', name);
    if (description) {
      formData.append('description', description);
    }
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await apiClient.post<ApiResponse<{ taskId: string; knowledgeBase: KnowledgeBase }>>(
      '/knowledge/create-async',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data.data;
  },

  /**
   * 获取创建进度（SSE 流）
   * @请求方式 GET /api/knowledge/create-progress/{taskId}
   * @触发位置 KnowledgePage.tsx - 创建任务启动后
   */
  getCreateProgress: (
    taskId: string,
    onProgress: (data: {
      type: string;
      taskId: string;
      status: string;
      progress: number;
      message: string;
      totalChunks: number;
      processedChunks: number;
    }) => void,
    onError?: (error: Error) => void
  ): (() => void) => {
    const eventSource = new EventSource(`/api/knowledge/create-progress/${taskId}`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onProgress(data);
        
        // 如果任务完成或失败，关闭连接
        if (data.status === 'completed' || data.status === 'error') {
          eventSource.close();
        }
      } catch (error) {
        console.error('解析进度数据失败:', error);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE 连接错误:', error);
      if (onError) {
        onError(new Error('连接失败'));
      }
      eventSource.close();
    };
    
    // 返回关闭函数
    return () => {
      eventSource.close();
    };
  },

  /**
   * 获取任务状态（非流式）
   * @请求方式 GET /api/knowledge/task-status/{taskId}
   * @触发位置 KnowledgePage.tsx - 轮询任务状态
   */
  getTaskStatus: async (taskId: string): Promise<{
    taskId: string;
    status: string;
    progress: number;
    message: string;
    totalChunks: number;
    processedChunks: number;
  } | null> => {
    const response = await apiClient.get<ApiResponse<{
      taskId: string;
      status: string;
      progress: number;
      message: string;
      totalChunks: number;
      processedChunks: number;
    }>>(`/knowledge/task-status/${taskId}`);
    return response.data.data;
  },

  /**
   * 获取知识库映射关系
   * @请求方式 GET /api/knowledge/mapping
   * @触发位置 KnowledgePage.tsx - 页面加载时
   * @返回 { status: 1, data: {...}, msg: "获取成功" }
   */
  getMapping: async (): Promise<Record<string, { files: string[]; createdAt: string; updatedAt: string }>> => {
    const response = await apiClient.get<ApiResponse<Record<string, { files: string[]; createdAt: string; updatedAt: string }>>>('/knowledge/mapping');
    return response.data.data || {};
  },

  /**
   * 根据名称检索知识库（不传名称则检索全部）
   * @请求方式 POST /api/knowledge/retrieve
   * @触发位置 chatStore.ts - sendMessage()
   * @参数 query: 查询文本, knowledgeNames?: 知识库名称列表
   * @返回 { status: 1, data: [...], msg: "检索成功" }
   */
  retrieve: async (
    query: string,
    knowledgeNames?: string[],
    topK: number = 5
  ): Promise<SearchResult[]> => {
    const response = await apiClient.post<ApiResponse<SearchResult[]>>('/knowledge/retrieve', {
      query,
      knowledgeNames,
      topK,
    });
    return response.data.data || [];
  },

  /**
   * 获取所有可用的Agent工具列表
   * @请求方式 GET /api/tools
   * @触发位置 AgentToolsPage.tsx - 页面加载时
   * @返回 { status: 1, data: { tools: [...], defaultSelectedTools: [...] }, msg: "获取成功" }
   */
  listTools: async (): Promise<{ tools: Tool[]; defaultSelectedTools: string[]; msg: string; status: number }> => {
    const response = await apiClient.get<ApiResponse<{ tools: Tool[]; defaultSelectedTools: string[] }>>('/tools');
    const data = response.data?.data;
    const status = response.data?.status;
    return {
      tools: data?.tools || [],
      defaultSelectedTools: data?.defaultSelectedTools || [],
      msg: response.data?.msg || (status === 1 ? '获取成功' : '获取失败'),
      status: status || 0
    };
  },
};

// ============================================================
// 工具服务 API (Agent Tools)
// ============================================================

/**
 * 工具相关API - 用于管理Agent可用的工具
 * 触发位置：AgentToolsPage组件
 */
export const toolsApi = {
  /**
   * 获取所有可用工具
   * @请求方式 GET /api/tools
   * @触发位置 AgentToolsPage.tsx - 页面加载时
   * @返回 { status: 1, data: [...], msg: "获取成功" }
   */
  list: async (): Promise<{ tools: Tool[]; msg: string; status: number }> => {
    return knowledgeApi.listTools();
  },

  /**
   * 启用指定工具
   * @请求方式 POST /api/tools/{toolId}/enable
   * @触发位置 AgentToolsPage.tsx - handleToggleTool()
   * @返回 { status: 1, data: null, msg: "启用成功" }
   */
  enable: async (toolId: string): Promise<void> => {
    await apiClient.post(`/tools/${toolId}/enable`);
  },

  /**
   * 禁用指定工具
   * @请求方式 POST /api/tools/{toolId}/disable
   * @触发位置 AgentToolsPage.tsx - handleToggleTool()
   * @返回 { status: 1, data: null, msg: "禁用成功" }
   */
  disable: async (toolId: string): Promise<void> => {
    await apiClient.post(`/tools/${toolId}/disable`);
  },

  /**
   * 批量设置工具状态
   * @请求方式 POST /api/tools/batch-set
   * @触发位置 AgentToolsPage.tsx - handleBatchSet()
   * @返回 { status: 1, data: null, msg: "设置成功" }
   */
  batchSet: async (toolIds: string[], enabled: boolean): Promise<void> => {
    await apiClient.post('/tools/batch-set', { toolIds, enabled });
  },

  /**
   * 刷新工具缓存 - 强制重新加载 MCP 配置
   * @请求方式 GET /api/tools?refresh=true
   * @触发位置 AgentToolsPage.tsx - 点击刷新按钮
   * @返回 { status: 1, data: { tools: [...], defaultSelectedTools: [...] }, msg: "获取成功" }
   */
  refresh: async (): Promise<{ tools: Tool[]; defaultSelectedTools: string[]; msg: string; status: number }> => {
    const response = await apiClient.get<ApiResponse<{ tools: Tool[]; defaultSelectedTools: string[] }>>('/tools?refresh=true');
    const data = response.data?.data;
    return {
      status: response.data.status,
      tools: data?.tools || [],
      defaultSelectedTools: data?.defaultSelectedTools || [],
      msg: response.data.msg
    };
  },

  /**
   * 流式获取工具列表 - 按服务分组返回，提供更好的用户体验
   * @请求方式 GET /api/tools/stream
   * @触发位置 AgentToolsPage.tsx - 页面加载时
   * @返回 SSE流式响应
   *
   * 事件类型：
   * - status: 状态更新（如"正在连接工具服务..."）
   * - service: 单个服务数据（包含该服务下的所有工具）
   * - warning: 警告信息
   * - complete: 加载完成（包含 defaultSelectedTools: 默认选中的工具ID列表）
   * - error: 错误信息
   */
  listStream: (
    forceRefresh: boolean = false,
    callbacks: {
      onStatus?: (message: string) => void;
      onService?: (service: MCPToolService) => void;
      onComplete?: (total: number, services: number, defaultSelectedTools?: string[]) => void;
      onWarning?: (message: string) => void;
      onError?: (message: string) => void;
    }
  ): (() => void) => {
    const url = forceRefresh ? '/api/tools/stream?refresh=true' : '/api/tools/stream';
    const eventSource = new EventSource(url);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'status':
            callbacks.onStatus?.(data.message);
            break;
          case 'service':
            callbacks.onService?.(data.service);
            break;
          case 'complete':
            callbacks.onComplete?.(data.total, data.services, data.defaultSelectedTools);
            eventSource.close();
            break;
          case 'warning':
            callbacks.onWarning?.(data.message);
            break;
          case 'error':
            callbacks.onError?.(data.message);
            eventSource.close();
            break;
        }
      } catch (error) {
        console.error('解析流式数据失败:', error);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE连接错误:', error);
      callbacks.onError?.('连接失败');
      eventSource.close();
    };
    
    // 返回取消函数
    return () => {
      eventSource.close();
    };
  },
};

// ============================================================
// 默认导出
// ============================================================

// ============================================================
// 模型服务 API (Model Management)
// ============================================================

/**
 * 模型相关API - 用于获取模型列表和管理模型
 * 触发位置：Header组件 - 模型选择下拉框
 */
export const modelApi = {
  /**
   * 获取模型提供商列表
   * @请求方式 GET /api/models/list
   * @触发位置 Header.tsx - 下拉框展开时
   * @返回 { status: 1, data: { providers: {...}, embedding_models: [...] }, msg: "获取成功" }
   */
  list: async (): Promise<any> => {
    const response = await apiClient.get<ApiResponse<any>>('/models/list');
    return response.data;
  },
};

// ============================================================
// 默认导出
// ============================================================

export default {
  chatApi,
  knowledgeApi,
  configApi,
  toolsApi,
  modelApi,
};
