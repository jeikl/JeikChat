import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { LLMConfig } from '@/types/config';
import type { MCPToolService, Tool, ToolConfig } from '@/services/api';

interface SettingsState {
  configs: LLMConfig[];
  activeConfigId: string | null;
  defaultSystemPrompt: string;
  tools: Tool[];
  toolServices: MCPToolService[];  // 按服务分组的工具
  selectedTools: ToolConfig[];  // 改为存储完整的 ToolConfig 对象

  addConfig: (config: LLMConfig) => void;
  updateConfig: (id: string, updates: Partial<LLMConfig>) => void;
  removeConfig: (id: string) => void;
  setActiveConfig: (id: string | null) => void;
  setConfigs: (configs: LLMConfig[]) => void;
  clearConfigs: () => void;
  setDefaultSystemPrompt: (prompt: string) => void;
  setTools: (tools: Tool[]) => void;
  setToolServices: (services: MCPToolService[]) => void;  // 设置服务分组
  toggleTool: (tool: Tool) => void;  // 改为接收 Tool 对象
  toggleServiceTools: (serviceId: string, tools: Tool[]) => void;  // 改为接收 Tool 对象数组
  setSelectedTools: (tools: ToolConfig[]) => void;  // 改为设置 ToolConfig 数组
  getActiveConfig: () => LLMConfig | null;
  getSelectedTools: () => ToolConfig[];  // 获取选中的工具配置
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
      toolServices: [],
      selectedTools: [],

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
      clearConfigs: () => set({ configs: [], activeConfigId: null }),
      setDefaultSystemPrompt: (prompt) => set({ defaultSystemPrompt: prompt }),
      setTools: (tools) => set({ tools }),
      setToolServices: (services) => set({ toolServices: services }),
      toggleTool: (tool) =>
        set((state) => {
          const toolConfig: ToolConfig = {
            toolid: tool.toolid,
            mcp: tool.mcp,
            name: tool.name,
            description: tool.description,
          };
          const exists = state.selectedTools.find((t) => t.toolid === tool.toolid);
          return {
            selectedTools: exists
              ? state.selectedTools.filter((t) => t.toolid !== tool.toolid)
              : [...state.selectedTools, toolConfig],
          };
        }),
      toggleServiceTools: (serviceId, tools) =>
        set((state) => {
          // 检查该服务的工具是否全部选中
          const toolConfigs = tools.map((t): ToolConfig => ({
            toolid: t.toolid,
            mcp: t.mcp,
            name: t.name,
            description: t.description,
          }));
          const allSelected = toolConfigs.every((tc) =>
            state.selectedTools.find((t) => t.toolid === tc.toolid)
          );

          if (allSelected) {
            // 如果全部选中，则取消选中该服务的所有工具
            return {
              selectedTools: state.selectedTools.filter(
                (t) => !toolConfigs.find((tc) => tc.toolid === t.toolid)
              ),
            };
          } else {
            // 否则，选中该服务的所有工具（去重）
            const newSelectedTools = [...state.selectedTools];
            toolConfigs.forEach((tc) => {
              if (!newSelectedTools.find((t) => t.toolid === tc.toolid)) {
                newSelectedTools.push(tc);
              }
            });
            return {
              selectedTools: newSelectedTools,
            };
          }
        }),
      setSelectedTools: (tools) =>
        set({
          selectedTools: tools,
        }),
      getActiveConfig: (): LLMConfig | null => {
        const state = useSettingsStore.getState();
        return state.configs.find((c) => c.id === state.activeConfigId) || null;
      },
      getSelectedTools: (): ToolConfig[] => {
        const state = useSettingsStore.getState();
        return state.selectedTools;
      },
    }),
    {
      name: 'settings-storage',
    }
  )
);
