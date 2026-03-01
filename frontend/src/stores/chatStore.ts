import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Message, ChatSession } from '@/types/chat';
import { useSettingsStore } from './settingsStore';

interface ChatStore {
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  isStreaming: boolean;
  thinkingMode: 'auto' | 'deep' | 'false';
  
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
  sendMessage: (content: string, toolIds?: string[]) => Promise<void>;
  stopGenerating: () => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      sessions: [],
      currentSessionId: null,
      isLoading: false,
      isStreaming: false,
      thinkingMode: 'auto',

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

      sendMessage: async (content, toolIds = []) => {
        set({ isLoading: true });
        
        const activeConfig = useSettingsStore.getState().getActiveConfig();
        const model = activeConfig?.model;

        let sessionId = get().currentSessionId;
        
        if (!sessionId) {
          const newSessionId = `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
          const newSession: ChatSession = {
            id: newSessionId,
            title: content.substring(0, 30) + (content.length > 30 ? '...' : ''),
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
          };
          get().addSession(newSession);
          sessionId = newSessionId;
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
        };
        get().addMessage(sessionId, assistantMessage);

        let hasContent = false;

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
              knowledgeBaseIds: toolIds,
              stream: true,
              thinking: get().thinkingMode,
            }),
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

          let fullContent = '';
          console.log('开始读取流...');

          while (true) {
            console.log('读取中...');
            const { done, value } = await reader.read();
            console.log('读取结果:', done, value?.length);
            
            if (done) break;
            
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
                  
                  if (parsed.content) {
                    if (!hasContent) {
                      hasContent = true;
                      get().updateMessage(sessionId, assistantMessageId, {
                        thinking: false,
                      });
                    }
                    fullContent += parsed.content;
                    get().updateMessage(sessionId, assistantMessageId, {
                      content: fullContent,
                    });
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
        } catch (error) {
          console.error('发送消息失败:', error);
          const errorMessage: Message = {
            id: `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
            role: 'assistant',
            content: '抱歉，发送消息时出现错误，请稍后再试。',
            timestamp: Date.now(),
          };
          get().addMessage(sessionId!, errorMessage);
        } finally {
          set({ isLoading: false });
        }
      },

      stopGenerating: () => {
        set({ isLoading: false });
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
