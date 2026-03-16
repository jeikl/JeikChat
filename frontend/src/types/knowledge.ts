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
  files?: KnowledgeFile[]; // 关联的文件列表
  // 处理进度信息（仅在processing状态时有效）
  progress?: number;
  progressMessage?: string;
  totalChunks?: number;
  processedChunks?: number;
}

export interface KnowledgeFile {
  id: string;
  name: string;
  type: string;
  size: number;
  status: 'pending' | 'processing' | 'ready' | 'error';
  errorMessage?: string;
  createdAt: number;
  path?: string; // 文件存储路径
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
  source?: string;
  page?: number;
}

// 知识库映射关系（用于knowledge_mapping.json）
export interface KnowledgeMapping {
  [knowledgeName: string]: {
    files: string[]; // 文件路径列表
    createdAt: string;
    updatedAt: string;
  };
}

// 上传进度状态
export interface UploadStatus {
  fileName: string;
  progress: number;
  status: 'uploading' | 'processing' | 'success' | 'error';
  errorMessage?: string;
}
