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

// 聊天相关类型
export interface SendMessageRequest {
  content: string;
  sessionId?: string;
  model?: string;
  knowledgeBaseIds?: string[];
  stream?: boolean;
  tools?: string[];
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
  id: string;
  name: string;
  description: string;
  enabled?: boolean;
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
  clearAllHistory: async (): Promise<void> => {
    await apiClient.delete('/chat/history');
  },

  /**
   * 重命名会话
   * @请求方式 PUT /api/chat/history/{sessionId}/title
   * @触发位置 Sidebar.tsx - handleRenameSession()
   * @返回 { status: 1, data: null, msg: "重命名成功" }
   */
  renameSession: async (sessionId: string, newTitle: string): Promise<void> => {
    await apiClient.put(`/chat/history/${sessionId}/title`, { title: newTitle });
  },

  /**
   * 停止指定会话的生成
   * @请求方式 POST /api/chat/stop/{sessionId}
   * @触发位置 InputArea.tsx - 点击停止按钮
   * @返回 { status: 1, data: { cancelled_tasks: number }, msg: "已停止 X 个生成任务" }
   */
  stopGeneration: async (sessionId: string): Promise<{ cancelled_tasks: number }> => {
    const response = await apiClient.post<ApiResponse<{ cancelled_tasks: number }>>(`/chat/stop/${sessionId}`);
    return response.data.data || { cancelled_tasks: 0 };
  },

  /**
   * 停止所有生成任务
   * @请求方式 POST /api/chat/stop
   * @触发位置 紧急情况使用
   * @返回 { status: 1, data: { cancelled_tasks: number }, msg: "已停止 X 个生成任务" }
   */
  stopAllGeneration: async (): Promise<{ cancelled_tasks: number }> => {
    const response = await apiClient.post<ApiResponse<{ cancelled_tasks: number }>>('/chat/stop');
    return response.data.data || { cancelled_tasks: 0 };
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
   * 获取所有可用的Agent工具列表
   * @请求方式 GET /api/tools
   * @触发位置 AgentToolsPage.tsx - 页面加载时
   * @返回 { status: 1, data: [...], msg: "获取成功" } 或 { status: 0, data: [], msg: "未获取到任何 Agent Tool" }
   */
  listTools: async (): Promise<{ tools: Tool[]; msg: string; status: number }> => {
    const response = await apiClient.get<ApiResponse<Tool[]>>('/tools');
    const tools = response.data?.data || [];
    const status = response.data?.status;
    return {
      tools: tools,
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
