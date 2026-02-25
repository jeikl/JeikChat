import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { LLMConfig } from '@/types/config';

interface Tool {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

interface SettingsState {
  configs: LLMConfig[];
  activeConfigId: string | null;
  defaultSystemPrompt: string;
  tools: Tool[];
  selectedToolIds: string[];
  
  addConfig: (config: LLMConfig) => void;
  updateConfig: (id: string, updates: Partial<LLMConfig>) => void;
  removeConfig: (id: string) => void;
  setActiveConfig: (id: string | null) => void;
  setConfigs: (configs: LLMConfig[]) => void;
  setDefaultSystemPrompt: (prompt: string) => void;
  setTools: (tools: Tool[]) => void;
  toggleTool: (toolId: string) => void;
}

const DEFAULT_CONFIGS: LLMConfig[] = [
  {
    id: 'openai-default',
    name: 'GPT-4',
    provider: 'openai',
    model: 'gpt-4',
    temperature: 0.7,
    maxTokens: 4096,
    topP: 0.9,
    enabled: true,
  },
  {
    id: 'openai-gpt35',
    name: 'GPT-3.5 Turbo',
    provider: 'openai',
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    maxTokens: 4096,
    topP: 0.9,
    enabled: true,
  },
];

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      configs: DEFAULT_CONFIGS,
      activeConfigId: 'openai-default',
      defaultSystemPrompt: '你是一个专业的AI客服助手，请用友好、专业的方式回答用户的问题。',
      tools: [],
      selectedToolIds: [],

      addConfig: (config) =>
        set((state) => ({
          configs: [...state.configs, config],
        })),

      updateConfig: (id, updates) =>
        set((state) => ({
          configs: state.configs.map((c) =>
            c.id === id ? { ...c, ...updates } : c
          ),
        })),

      removeConfig: (id) =>
        set((state) => ({
          configs: state.configs.filter((c) => c.id !== id),
          activeConfigId:
            state.activeConfigId === id ? state.configs[0]?.id || null : state.activeConfigId,
        })),

      setActiveConfig: (id) => set({ activeConfigId: id }),
      setConfigs: (configs) => set({ configs }),
      setDefaultSystemPrompt: (prompt) => set({ defaultSystemPrompt: prompt }),
      setTools: (tools) => set({ tools }),
      toggleTool: (toolId) =>
        set((state) => ({
          selectedToolIds: state.selectedToolIds.includes(toolId)
            ? state.selectedToolIds.filter((id) => id !== toolId)
            : [...state.selectedToolIds, toolId],
        })),
    }),
    {
      name: 'settings-storage',
    }
  )
);
