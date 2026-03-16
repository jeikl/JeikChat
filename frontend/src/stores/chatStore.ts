import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ChatSession, Message } from '@/types/chat';
import { v4 as uuidv4 } from 'uuid';
import { useSettingsStore } from './settingsStore';
import { useKnowledgeStore } from './knowledgeStore';

interface ChatState {
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  isStreaming: boolean;
  abortController: AbortController | null;
  thinkingMode: 'auto' | 'deep' | 'false';
  selectedKnowledgeBaseIds: string[];
  skipDeleteConfirm: boolean; // 删除不再提示
  
  // Actions
  addSession: (session: ChatSession) => void;
  deleteSession: (sessionId: string) => void;
  deleteSessionWithApi: (sessionId: string) => Promise<void>; // 调用后端删除
  setCurrentSession: (sessionId: string | null) => void;
  addMessage: (sessionId: string, message: Message) => void;
  updateMessage: (sessionId: string, messageId: string, updates: Partial<Message>) => void;
  clearMessages: (sessionId: string) => void;
  sendMessage: (content: string, sessionId?: string) => Promise<void>;
  stopGeneration: () => void;
  setThinkingMode: (mode: 'auto' | 'deep' | 'false') => void;
  updateSession: (sessionId: string, updates: Partial<ChatSession>) => void;
  setSelectedKnowledgeBaseIds: (ids: string[]) => void;
  setSkipDeleteConfirm: (skip: boolean) => void; // 设置删除不再提示
  createNewSession: (content?: string) => ChatSession; // 创建新会话
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      sessions: [],
      currentSessionId: null,
      isLoading: false,
      isStreaming: false,
      abortController: null,
      thinkingMode: 'auto',
      selectedKnowledgeBaseIds: [],
      skipDeleteConfirm: false, // 默认需要确认
      
      addSession: (session) => set((state) => ({
        sessions: [session, ...state.sessions], // 新会话插入到数组开头（顶部）
        currentSessionId: session.id,
      })),
      
      deleteSession: (sessionId) => set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId),
        currentSessionId: state.currentSessionId === sessionId ? null : state.currentSessionId,
      })),
      
      // 调用后端 API 删除会话
      deleteSessionWithApi: async (sessionId: string) => {
        const { deleteSession } = get();
        
        try {
          // 获取会话的 UUID
          const sessionUuid = localStorage.getItem(`session-uuid-${sessionId}`);
          
          if (sessionUuid) {
            // 调用后端删除接口
            const { chatApi } = await import('@/services/api');
            await chatApi.deleteSession(sessionUuid);
            
            // 清除本地存储的 UUID
            localStorage.removeItem(`session-uuid-${sessionId}`);
          }
          
          // 从前端状态中删除
          deleteSession(sessionId);
        } catch (error) {
          console.error('删除会话失败:', error);
          // 即使后端删除失败，也从前端状态中删除
          deleteSession(sessionId);
        }
      },
      
      // 创建新会话（发送第一条消息后调用）
      createNewSession: (content?: string) => {
        const { addSession } = get();
        // 生成标题：取内容前20字，如果超过20字加省略号
        const title = content && content.length > 20 ? content.slice(0, 20) + '...' : (content || '新对话');
        const newSession: ChatSession = {
          id: uuidv4(),
          title: title,
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        addSession(newSession);
        return newSession;
      },
      
      setSkipDeleteConfirm: (skip) => set({ skipDeleteConfirm: skip }),
      
      setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),
      
      addMessage: (sessionId, message) => set((state) => ({
        sessions: state.sessions.map((session) =>
          session.id === sessionId
            ? { ...session, messages: [...session.messages, message] }
            : session
        ),
      })),
      
      updateMessage: (sessionId, messageId, updates) => set((state) => ({
        sessions: state.sessions.map((session) =>
          session.id === sessionId
            ? {
                ...session,
                messages: session.messages.map((msg) =>
                  msg.id === messageId ? { ...msg, ...updates } : msg
                ),
              }
            : session
        ),
      })),
      
      clearMessages: (sessionId) => set((state) => ({
        sessions: state.sessions.map((session) =>
          session.id === sessionId ? { ...session, messages: [] } : session
        ),
      })),
      
      setThinkingMode: (mode) => set({ thinkingMode: mode }),
      
      updateSession: (sessionId, updates) => set((state) => ({
        sessions: state.sessions.map((session) =>
          session.id === sessionId ? { ...session, ...updates } : session
        ),
      })),
      
      setSelectedKnowledgeBaseIds: (ids) => set({ selectedKnowledgeBaseIds: ids }),

      stopGeneration: () => {
        const { abortController } = get();
        if (abortController) {
          abortController.abort();
          set({ abortController: null, isStreaming: false });
        }
      },
      
      sendMessage: async (content: string, sessionId?: string) => {
        const { 
          currentSessionId, 
          addSession, 
          addMessage,
          createNewSession,
          setCurrentSession,
          thinkingMode,
        } = get();
        
        // 从 SettingsStore 获取当前激活的模型配置，如果没有则尝试获取第一个配置，再没有则使用默认值
        const settingsState = useSettingsStore.getState();
        const activeConfig = settingsState.getActiveConfig();
        const firstConfig = settingsState.configs?.[0];
        const activeModelId = activeConfig?.model || firstConfig?.model || 'qwen3.5-plus';
        
        console.log('模型选择调试:', {
          activeConfigId: settingsState.activeConfigId,
          activeConfig,
          firstConfig,
          activeModelId,
          allConfigs: settingsState.configs
        });

        // 优先使用传入的 sessionId，否则使用 currentSessionId
        let targetSessionId = sessionId || currentSessionId;
        
        // 如果当前没有会话（点击了"开启新对话"），创建一个新会话
        if (!targetSessionId) {
          const newSession = createNewSession(content);
          targetSessionId = newSession.id;
          setCurrentSession(newSession.id);
          console.log('创建新会话:', { sessionId: newSession.id, title: newSession.title });
        }
        
        // 如果是默认会话且不存在，创建它
        if (targetSessionId === 'default-session') {
          const existingDefaultSession = get().sessions.find(s => s.id === 'default-session');
          if (!existingDefaultSession) {
            const defaultSession: ChatSession = {
              id: 'default-session',
              title: '默认对话',
              messages: [],
              createdAt: Date.now(),
              updatedAt: Date.now(),
              isDefault: true,
            };
            addSession(defaultSession);
            console.log('创建默认会话');
          }
        }
        
        sessionId = targetSessionId;
        
        // 获取或生成会话的UUID（永久唯一）
        let sessionUuid = null;
        if (sessionId) {
          sessionUuid = localStorage.getItem(`session-uuid-${sessionId}`);
          if (!sessionUuid) {
            sessionUuid = uuidv4();
            localStorage.setItem(`session-uuid-${sessionId}`, sessionUuid);
          }
          console.log('UUID 生成/获取:', { sessionId, sessionUuid });
        } else {
          console.warn('sessionId 为 null，无法生成 UUID');
        }
        
        // 添加用户消息
        const userMessage: Message = {
          id: uuidv4(),
          role: 'user',
          content,
          timestamp: Date.now(),
        };
        addMessage(sessionId!, userMessage);
        
        set({ isLoading: true, isStreaming: true });
        
        // 创建助手消息（初始为空，用于流式更新）
        const assistantMessageId = uuidv4();
        const assistantMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          isStreaming: true,
          thinking: true,
          reasoning: '',
          reasoningExpanded: true,
        };
        addMessage(sessionId!, assistantMessage);

        let fullContent = '';
        let fullReasoning = '';
        const abortController = new AbortController();
        set({ abortController });

        try {
          // 使用全局设置的模型，而不是会话级别的设置
          const modelIdToSend = activeModelId;
          
          // 在发送前重新获取最新的状态，避免缓存问题
          const latestKnowledgeState = useKnowledgeStore.getState();
          const latestSettingsState = useSettingsStore.getState();
          const finalKnowledgeIds = latestKnowledgeState.selectedKnowledgeIds;
          let finalTools = latestSettingsState.getSelectedTools();

          // 如果选中了知识库，自动添加 retrieve_documents 工具
          if (finalKnowledgeIds.length > 0) {
            const hasRetrieveTool = finalTools.some(tool => tool.toolid === 'retrieve_documents');
            if (!hasRetrieveTool) {
              finalTools = [
                ...finalTools,
                {
                  toolid: 'retrieve_documents',
                  mcp: 0,
                  name: 'retrieve_documents',
                  description: '从知识库检索文档',
                }
              ];
              console.log('自动添加 retrieve_documents 工具');
            }
          }

          console.log('发送请求调试:', {
            content,
            sessionId,
            model: modelIdToSend,
            thinking: thinkingMode,
            sessionUuid,
            knowledgeBaseIds: finalKnowledgeIds,
            tools: finalTools,
            knowledgeStoreState: latestKnowledgeState.selectedKnowledgeIds,
            settingsStoreState: latestSettingsState.selectedTools
          });

          const response = await fetch('/api/chat/send', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              content,
              sessionId,
              model: modelIdToSend,
              knowledgeBaseIds: finalKnowledgeIds,
              tools: finalTools,  // 传递 ToolConfig 对象数组
              stream: true,
              thinking: thinkingMode,
              sessionUuid: sessionUuid,
            }),
            signal: abortController.signal,
          });

          console.log('收到响应:', response.status, response.statusText);

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const reader = response.body?.getReader();
          const decoder = new TextDecoder();
          
          if (!reader) {
            throw new Error('Response body is null');
          }

          let isCancelled = false;
          console.log('开始读取流...');

          while (true) {
            console.log('读取中...');
            const { done, value } = await reader.read();
            console.log('读取结果:', done, value?.length);
            
            if (done) break;
            
            // 检查是否已取消
            if (abortController.signal.aborted) {
              console.log('请求已取消，停止读取');
              isCancelled = true;
              break;
            }
            
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                
                if (data === '[DONE]') {
                  break;
                }
                
                try {
                  const parsed = JSON.parse(data);
                  console.log('Parsed:', parsed);
                  
                  // 检查是否被取消
                  if (parsed.cancelled) {
                    isCancelled = true;
                    console.log('后端报告生成被取消');
                  }
                  
                  // Agent 流的工具调用信息通过 reasoning 字段返回
                  if (parsed.reasoning) {
                    fullReasoning += parsed.reasoning;
                    get().updateMessage(sessionId!, assistantMessageId, {
                      reasoning: fullReasoning,
                    });
                  }
                  
                  // 普通内容通过 content 字段返回
                  if (parsed.content !== undefined) {
                    fullContent += parsed.content;
                    get().updateMessage(sessionId!, assistantMessageId, {
                      content: fullContent,
                      thinking: false,
                    });
                  }
                  
                  if (parsed.done) {
                    // 保存后端返回的 UUID（如果是后端生成的）
                    if (parsed.sessionUuid && sessionId) {
                      const storedUuid = localStorage.getItem(`session-uuid-${sessionId}`);
                      if (!storedUuid) {
                        localStorage.setItem(`session-uuid-${sessionId}`, parsed.sessionUuid);
                        console.log('保存后端生成的 UUID:', { sessionId, sessionUuid: parsed.sessionUuid });
                      }
                    }
                    break;
                  }
                  
                  if (parsed.error) {
                    throw new Error(parsed.error);
                  }
                } catch (e) {
                  // 跳过无效 JSON
                  console.error('Parse error:', e);
                }
              }
            }
          }

          // 如果被取消，更新消息状态
          if (isCancelled) {
            get().updateMessage(sessionId!, assistantMessageId, {
              content: fullContent,
              isCancelled: true,
            });
          }

        } catch (error) {
          if ((error as Error).name === 'AbortError') {
            console.log('请求被用户取消');
            // 更新消息显示已停止，但保留已生成的内容
            get().updateMessage(sessionId!, assistantMessageId, {
              thinking: false,
              content: fullContent,
              isCancelled: true,
            });
          } else {
            console.error('发送消息失败:', error);
            const errorMessage: Message = {
              id: uuidv4(),
              role: 'assistant',
              content: '抱歉，发送消息时出现错误，请稍后再试。',
              timestamp: Date.now(),
            };
            get().addMessage(sessionId!, errorMessage);
          }
        } finally {
          set({ isLoading: false, isStreaming: false, abortController: null });
          // 最终更新，标记流式传输结束
          get().updateMessage(sessionId!, assistantMessageId, {
            isStreaming: false,
            thinking: false,
          });
        }
      },
    }),
    {
      name: 'chat-storage',
      partialize: (state) => ({
        sessions: state.sessions.map(session => ({
          id: session.id,
          title: session.title,
          messages: session.messages,
          createdAt: session.createdAt,
          updatedAt: session.updatedAt,
          // 移除 modelId 和 knowledgeBaseIds，避免持久化会话级别的设置
          // 这些设置由全局设置管理，每次请求时使用当前设置
        })),
        currentSessionId: state.currentSessionId,
        thinkingMode: state.thinkingMode,
      }),
    }
  )
);
