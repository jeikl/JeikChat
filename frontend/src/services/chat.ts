import apiClient from './api';
import type { ChatSession, Message, KnowledgeReference } from '@/types/chat';

export interface SendMessageRequest {
  content: string;
  sessionId?: string;
  modelId?: string;
  knowledgeBaseIds?: string[];
  stream?: boolean;
}

export interface SendMessageResponse {
  sessionId: string;
  message: Message;
}

export interface ChatHistoryResponse {
  sessions: ChatSession[];
}

export const chatApi = {
  sendMessage: async (data: SendMessageRequest): Promise<SendMessageResponse> => {
    const response = await apiClient.post<SendMessageResponse>('/chat/send', data);
    return response.data;
  },

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
            // Skip invalid JSON
          }
        }
      });

      response.data.on('error', reject);
    });
  },

  getHistory: async (sessionId: string): Promise<ChatSession> => {
    const response = await apiClient.get<ChatSession>(`/chat/history/${sessionId}`);
    return response.data;
  },

  getAllSessions: async (): Promise<ChatHistoryResponse> => {
    const response = await apiClient.get<ChatHistoryResponse>('/chat/history');
    return response.data;
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/chat/history/${sessionId}`);
  },

  clearAllHistory: async (): Promise<void> => {
    await apiClient.delete('/chat/history');
  },
};
