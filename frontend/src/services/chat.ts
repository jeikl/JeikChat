/**
 * ============================================================
 * 聊天服务 API (已废弃，请使用 @/services/api 中的 chatApi)
 * ============================================================
 * 
 * 此文件仅用于向后兼容，请使用新的导入方式：
 *   import { chatApi } from '@/services/api';
 * 
 * @deprecated 请使用 @/services/api 中的 chatApi
 * ============================================================
 */

import { chatApi } from './api';

export type { SendMessageRequest, SendMessageResponse, ChatHistoryResponse } from './api';
export { chatApi };
export default chatApi;
