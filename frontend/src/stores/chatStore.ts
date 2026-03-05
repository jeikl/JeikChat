import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Message, ChatSession } from '@/types/chat';
import { useSettingsStore } from './settingsStore';
import { useKnowledgeStore } from './knowledgeStore';
import { chatApi } from '@/services/api';

interface ChatStore {
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  isStreaming: boolean;
  thinkingMode: 'auto' | 'deep' | 'false';
  abortController: AbortController | null;
  
  addSession: (session: ChatSession) => void;
  removeSession: (sessionId: string) => void;
  setCurrentSession: (sessionId: string | null) => void;
  addMessage: (sessionId: string, message: Message) => void;
  updateMessage: (sessionId: string, messageId: string, updates: Partial<Message>) => void;
  deleteMessage: (sessionId: string, messageId: string) => void;
  deleteSession: (sessionId: string) => void;
  updateSession: (sessionId: string, updates: Partial<ChatSession>) => void;
  setLoading: (loading: boolean) => void;
  setStreaming: (streaming: boolean) => void;
  setThinkingMode: (mode: 'auto' | 'deep' | 'false') => void;
  clearAllSessions: () => void;
  sendMessage: (content: string) => Promise<void>;
  stopGenerating: () => Promise<void>;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      sessions: [{
        id: 'default-session',
        title: '默认对话',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
        isDefault: true
      }],
      currentSessionId: 'default-session',
      isLoading: false,
      isStreaming: false,
      thinkingMode: 'auto',
      abortController: null,

      setThinkingMode: (mode) => set({ thinkingMode: mode }),

      addSession: (session) =>
        set((state) => ({
          sessions: [session, ...state.sessions],
          currentSessionId: session.id,
        })),

      removeSession: (sessionId) =>
        set((state) => ({
          sessions: state.sessions.filter((s) => s.id !== sessionId),
          currentSessionId:
            state.currentSessionId === sessionId ? null : state.currentSessionId,
        })),

      deleteSession: (sessionId) =>
        set((state) => ({
          sessions: state.sessions.filter((s) => s.id !== sessionId),
          currentSessionId:
            state.currentSessionId === sessionId ? null : state.currentSessionId,
        })),

      updateSession: (sessionId, updates) =>
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId ? { ...s, ...updates } : s
          ),
        })),

      setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),

      addMessage: (sessionId, message) =>
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId
              ? { ...s, messages: [...s.messages, message], updatedAt: Date.now() }
              : s
          ),
        })),

      updateMessage: (sessionId, messageId, updates) =>
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId
              ? {
                  ...s,
                  messages: s.messages.map((m) =>
                    m.id === messageId ? { ...m, ...updates } : m
                  ),
                }
              : s
          ),
        })),

      deleteMessage: (sessionId, messageId) =>
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId
              ? { ...s, messages: s.messages.filter((m) => m.id !== messageId) }
              : s
          ),
        })),

      setLoading: (loading) => set({ isLoading: loading }),
      setStreaming: (streaming) => set({ isStreaming: streaming }),

      clearAllSessions: () => set({ sessions: [], currentSessionId: null }),

      sendMessage: async (content) => {
        set({ isLoading: true, isStreaming: true });
        
        const activeConfig = useSettingsStore.getState().getActiveConfig();
        const model = activeConfig?.model;
        const selectedToolIds = useSettingsStore.getState().selectedToolIds;
        const selectedKnowledgeBaseIds = useKnowledgeStore.getState().selectedKnowledgeIds;

        let sessionId = get().currentSessionId;
        
        // 如果没有当前会话，创建一个新的
        if (!sessionId) {
          const newSessionId = `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
          // 使用用户输入的前30个字符作为标题
          const title = content.trim().substring(0, 30) + (content.length > 30 ? '...' : '');
          const newSession: ChatSession = {
            id: newSessionId,
            title: title || '新对话', // 确保有标题
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
          };
          get().addSession(newSession);
          sessionId = newSessionId;
        } else {
          // 如果是现有会话，检查是否是"新对话"且消息为空（刚创建），则重命名
          const currentSession = get().sessions.find(s => s.id === sessionId);
          // 注意：default-session 不应该被重命名
          if (currentSession && 
              currentSession.id !== 'default-session' && 
              currentSession.title === '新对话' && 
              currentSession.messages.length === 0) {
            const title = content.trim().substring(0, 30) + (content.length > 30 ? '...' : '');
            get().updateSession(sessionId, { title: title || '新对话' });
          }
          
          // 确保 currentSession 存在，防止 default-session 被意外删除后这里为 undefined
          if (!currentSession && sessionId === 'default-session') {
            const newDefaultSession: ChatSession = {
              id: 'default-session',
              title: '默认对话',
              messages: [],
              createdAt: Date.now(),
              updatedAt: Date.now(),
              isDefault: true
            };
            get().addSession(newDefaultSession);
          }
        }

        // 再次确认 sessionId 有效
        if (!get().sessions.some(s => s.id === sessionId)) {
           console.error('Session not found, attempting to recover:', sessionId);
           // 如果 session 真的不见了，强制新建一个临时 session 避免崩溃
           const recoverySession: ChatSession = {
             id: sessionId,
             title: 'Recovered Session',
             messages: [],
             createdAt: Date.now(),
             updatedAt: Date.now(),
             isDefault: sessionId === 'default-session'
           };
           get().addSession(recoverySession);
        }

        const userMessageId = `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        const userMessage: Message = {
          id: userMessageId,
          role: 'user',
          content,
          timestamp: Date.now(),
        };
        get().addMessage(sessionId, userMessage);

        const assistantMessageId = `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        const assistantMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          thinking: true,
          reasoning: '',
          hasReasoning: false,
          reasoningExpanded: true,
        };
        get().addMessage(sessionId, assistantMessage);

        let fullContent = '';
        let fullReasoning = '';
        let fullInternalContent = '';
        const abortController = new AbortController();
        set({ abortController });

        try {
          console.log('发送请求:', { content, sessionId, model, thinking: get().thinkingMode });
          
          const response = await fetch('/api/chat/send', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              content,
              sessionId,
              model,
              knowledgeBaseIds: selectedKnowledgeBaseIds,
              tools: selectedToolIds,
              stream: true,
              thinking: get().thinkingMode,
            }),
            signal: abortController.signal,
          });

          console.log('收到响应:', response.status, response.statusText);
          console.log('响应类型:', response.type);

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const reader = response.body?.getReader();
          console.log('Reader:', reader);
          
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
                  
                  if (parsed.reasoning) {
                    if (get().thinkingMode !== 'false') {
                      get().updateMessage(sessionId, assistantMessageId, {
                        thinking: false,
                      });
                    }
                    fullReasoning += parsed.reasoning;
                    get().updateMessage(sessionId, assistantMessageId, {
                      reasoning: fullReasoning,
                    });
                  }
                  
                  if (parsed.content) {
                    console.log('Received content:', parsed.content, 'thinking:', parsed.thinking);
                    
                    if (get().thinkingMode !== 'false') {
                      get().updateMessage(sessionId, assistantMessageId, {
                        thinking: false,
                      });
                    }
                    
                    // 如果是 thinking 内容，添加到 internalContent
                    if (parsed.thinking) {
                      fullInternalContent += parsed.content;
                      get().updateMessage(sessionId, assistantMessageId, {
                        internalContent: fullInternalContent,
                      });
                    } else {
                      fullContent += parsed.content;
                      get().updateMessage(sessionId, assistantMessageId, {
                        content: fullContent,
                      });
                    }
                  }
                  
                  if (parsed.done) {
                    break;
                  }
                  
                  if (parsed.error) {
                    throw new Error(parsed.error);
                  }
                } catch (e) {
                  // 跳过无效 JSON
                }
              }
            }
          }

          // 如果被取消，更新消息状态
          if (isCancelled) {
            get().updateMessage(sessionId, assistantMessageId, {
              content: fullContent, // 仅使用已生成的内容，不强制替换为“生成已停止”
              isCancelled: true,
            });
          }

        } catch (error) {
          if ((error as Error).name === 'AbortError') {
            console.log('请求被用户取消');
            // 更新消息显示已停止，但保留已生成的内容
            get().updateMessage(sessionId, assistantMessageId, {
              thinking: false,
              content: fullContent,
              isCancelled: true,
            });
          } else {
            console.error('发送消息失败:', error);
            const errorMessage: Message = {
              id: `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
              role: 'assistant',
              content: '抱歉，发送消息时出现错误，请稍后再试。',
              timestamp: Date.now(),
            };
            get().addMessage(sessionId!, errorMessage);
          }
        } finally {
          set({ isLoading: false, isStreaming: false, abortController: null });
        }
      },

      stopGenerating: async () => {
        const { abortController, currentSessionId } = get();
        
        // 1. 先中断前端请求
        if (abortController) {
          abortController.abort();
        }
        
        // 2. 调用后端 API 真正停止与大模型的通信
        if (currentSessionId) {
          try {
            const result = await chatApi.stopGeneration(currentSessionId);
            console.log('后端停止生成:', result);
          } catch (error) {
            console.error('停止生成失败:', error);
          }
        }
        
        set({ isLoading: false, isStreaming: false, abortController: null });
      },
    }),
    {
      name: 'chat-storage',
      partialize: (state) => ({
        sessions: state.sessions.slice(0, 50),
        currentSessionId: state.currentSessionId,
      }),
    }
  )
);
