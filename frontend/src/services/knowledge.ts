/**
 * ============================================================
 * 知识库服务 API (已废弃，请使用 @/services/api 中的 knowledgeApi)
 * ============================================================
 * 
 * 此文件仅用于向后兼容，请使用新的导入方式：
 *   import { knowledgeApi } from '@/services/api';
 * 
 * @deprecated 请使用 @/services/api 中的 knowledgeApi
 * ============================================================
 */

import { knowledgeApi, type CreateKnowledgeRequest } from './api';

export type { CreateKnowledgeRequest };
export { knowledgeApi };
export default knowledgeApi;
