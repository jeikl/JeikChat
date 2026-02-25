import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { chatApi } from '@/services/chat';
import { useSettingsStore } from './settingsStore';
import type { ChatSession, Message } from '@/types/chat';

interface ChatState {
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  isStreaming: boolean;
  
  addSession: (session: ChatSession) => void;
  updateSession: (sessionId: string, updates: Partial<ChatSession>) => void;
  deleteSession: (sessionId: string) => void;
  setCurrentSession: (sessionId: string | null) => void;
  addMessage: (sessionId: string, message: Message) => void;
  updateMessage: (sessionId: string, messageId: string, updates: Partial<Message>) => void;
  setLoading: (loading: boolean) => void;
  setStreaming: (streaming: boolean) => void;
  clearAllSessions: () => void;
  sendMessage: (content: string, toolIds?: string[]) => Promise<void>;
  stopGenerating: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      sessions: [],
      currentSessionId: null,
      isLoading: false,
      isStreaming: false,

      addSession: (session) =>
        set((state) => ({
          sessions: [session, ...state.sessions],
          currentSessionId: session.id,
        })),

      updateSession: (sessionId, updates) =>
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId ? { ...s, ...updates, updatedAt: Date.now() } : s
          ),
        })),

      deleteSession: (sessionId) =>
        set((state) => ({
          sessions: state.sessions.filter((s) => s.id !== sessionId),
          currentSessionId:
            state.currentSessionId === sessionId
              ? state.sessions[0]?.id || null
              : state.currentSessionId,
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

      setLoading: (loading) => set({ isLoading: loading }),
      setStreaming: (streaming) => set({ isStreaming: streaming }),

      clearAllSessions: () => set({ sessions: [], currentSessionId: null }),

      sendMessage: async (content, toolIds = []) => {
        set({ isLoading: true });
        try {
          // 获取当前选中的模型配置
          const activeConfig = useSettingsStore.getState().getActiveConfig();
          const model = activeConfig?.model;

          // 如果没有当前会话，则创建一个新的
          let sessionId = useChatStore.getState().currentSessionId;
          if (!sessionId) {
            const newSession: ChatSession = {
              id: Date.now().toString(),
              title: content.substring(0, 30) + (content.length > 30 ? '...' : ''),
              messages: [],
              createdAt: Date.now(),
              updatedAt: Date.now(),
            };
            useChatStore.getState().addSession(newSession);
            sessionId = newSession.id;
          }

          // 添加用户消息
          const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content,
            timestamp: Date.now(),
          };
          useChatStore.getState().addMessage(sessionId, userMessage);

          // 发送请求到后端，传递模型名称
          const response = await chatApi.sendMessage({
            content,
            sessionId,
            model, // 传递当前选中的模型名称
            knowledgeBaseIds: toolIds,
          });

          // 添加助手回复
          useChatStore.getState().addMessage(sessionId, response.message);
        } catch (error) {
          console.error('发送消息失败:', error);
          // 添加错误消息
          let sessionId = useChatStore.getState().currentSessionId;
          if (sessionId) {
            const errorMessage: Message = {
              id: Date.now().toString(),
              role: 'assistant',
              content: '抱歉，发送消息时出现错误，请稍后再试。',
              timestamp: Date.now(),
            };
            useChatStore.getState().addMessage(sessionId, errorMessage);
          }
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
