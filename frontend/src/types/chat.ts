export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  reasoning?: string;
  timestamp: number;
  references?: KnowledgeReference[];
  isStreaming?: boolean;
  thinking?: boolean;
  isCancelled?: boolean;  // 标记消息是否被取消生成
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
  modelId?: string;
  knowledgeBaseIds?: string[];
  isDefault?: boolean;
}

export interface KnowledgeReference {
  source: any;
  knowledgeId: string;
  knowledgeName: string;
  content: string;
  similarity: number;
}
