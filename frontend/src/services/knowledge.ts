import apiClient from './api';
import type { KnowledgeBase, KnowledgeFile, SearchResult } from '@/types/knowledge';

export interface CreateKnowledgeRequest {
  name: string;
  description?: string;
  systemPrompt?: string;
  vectorStoreConfig?: {
    type: 'chroma' | 'milvus' | 'pinecone' | 'qdrant';
    embeddingModel: string;
    chunkSize: number;
    chunkOverlap: number;
  };
}

export interface UploadFileRequest {
  knowledgeId: string;
  file: File;
}

export const knowledgeApi = {
  list: async (): Promise<KnowledgeBase[]> => {
    const response = await apiClient.get<KnowledgeBase[]>('/knowledge/list');
    return response.data;
  },

  create: async (data: CreateKnowledgeRequest): Promise<KnowledgeBase> => {
    const response = await apiClient.post<KnowledgeBase>('/knowledge/create', data);
    return response.data;
  },

  update: async (id: string, data: Partial<CreateKnowledgeRequest>): Promise<KnowledgeBase> => {
    const response = await apiClient.put<KnowledgeBase>(`/knowledge/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/knowledge/${id}`);
  },

  getFiles: async (knowledgeId: string): Promise<KnowledgeFile[]> => {
    const response = await apiClient.get<KnowledgeFile[]>(`/knowledge/${knowledgeId}/files`);
    return response.data;
  },

  uploadFile: async (knowledgeId: string, file: File, onProgress?: (progress: number) => void): Promise<KnowledgeFile> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<KnowledgeFile>(
      `/knowledge/${knowledgeId}/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
            onProgress(progress);
          }
        },
      }
    );
    return response.data;
  },

  deleteFile: async (knowledgeId: string, fileId: string): Promise<void> => {
    await apiClient.delete(`/knowledge/${knowledgeId}/files/${fileId}`);
  },

  search: async (knowledgeId: string, query: string, topK: number = 5): Promise<SearchResult[]> => {
    const response = await apiClient.get<SearchResult[]>(`/knowledge/${knowledgeId}/search`, {
      params: { query, topK },
    });
    return response.data;
  },

  batchSearch: async (knowledgeIds: string[], query: string, topK: number = 5): Promise<SearchResult[]> => {
    const response = await apiClient.post<SearchResult[]>('/knowledge/batch-search', {
      knowledgeIds,
      query,
      topK,
    });
    return response.data;
  },

  rebuild: async (knowledgeId: string): Promise<void> => {
    await apiClient.post(`/knowledge/${knowledgeId}/rebuild`);
  },

  listTools: async (): Promise<{ id: string; name: string; description: string }[]> => {
    const response = await apiClient.get<{ id: string; name: string; description: string }[]>('/knowledge/tools');
    return response.data;
  },
};
