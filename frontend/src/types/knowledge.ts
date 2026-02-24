export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  fileCount: number;
  status: 'ready' | 'processing' | 'error';
  createdAt: number;
  updatedAt: number;
  systemPrompt?: string;
  vectorStoreConfig?: VectorStoreConfig;
}

export interface KnowledgeFile {
  id: string;
  name: string;
  type: string;
  size: number;
  status: 'pending' | 'processing' | 'ready' | 'error';
  errorMessage?: string;
  createdAt: number;
}

export interface VectorStoreConfig {
  type: 'chroma' | 'milvus' | 'pinecone' | 'qdrant';
  embeddingModel: string;
  chunkSize: number;
  chunkOverlap: number;
}

export interface SearchResult {
  content: string;
  metadata: Record<string, unknown>;
  score: number;
}
