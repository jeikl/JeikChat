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
  hasUserSelection: boolean;  // 标记用户是否有过选择行为

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
  applyDefaultTools: (defaultToolIds: string[]) => void;  // 应用默认选中工具
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
      hasUserSelection: false,

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
            hasUserSelection: true,  // 标记用户有过选择行为
          };
        }),
      toggleServiceTools: (_serviceId, tools) =>
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
              hasUserSelection: true,
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
              hasUserSelection: true,
            };
          }
        }),
      setSelectedTools: (tools) =>
        set({
          selectedTools: tools,
          hasUserSelection: true,
        }),
      applyDefaultTools: (defaultToolIds) =>
        set((state) => {
          // 如果用户已经有过选择行为，不应用默认设置
          if (state.hasUserSelection || state.selectedTools.length > 0) {
            console.log('[applyDefaultTools] 用户已有选择，跳过默认设置');
            return state;
          }

          console.log('[applyDefaultTools] 应用默认工具:', defaultToolIds);
          console.log('[applyDefaultTools] 当前服务列表:', state.toolServices.map(s => ({ id: s.id, toolCount: s.tools.length })));

          // 辅助函数：检查工具ID是否匹配模式（支持通配符 * 和 ?）
          const matchesPattern = (toolId: string, pattern: string): boolean => {
            if (pattern.includes('*') || pattern.includes('?')) {
              // 将通配符模式转换为正则表达式
              const regexPattern = pattern
                .replace(/[.+^${}()|[\]\\]/g, '\\$&') // 转义特殊字符
                .replace(/\*/g, '.*') // * 匹配任意字符
                .replace(/\?/g, '.'); // ? 匹配单个字符
              const regex = new RegExp(`^${regexPattern}$`);
              return regex.test(toolId);
            }
            return toolId === pattern;
          };

          // 从所有服务中查找默认工具
          const defaultTools: ToolConfig[] = [];
          for (const service of state.toolServices) {
            for (const tool of service.tools) {
              // 检查是否匹配任一模式
              const isMatch = defaultToolIds.some(pattern => matchesPattern(tool.toolid, pattern));
              if (isMatch) {
                console.log('[applyDefaultTools] 匹配工具:', tool.toolid);
                defaultTools.push({
                  toolid: tool.toolid,
                  mcp: tool.mcp,
                  name: tool.name,
                  description: tool.description,
                });
              }
            }
          }

          console.log('[applyDefaultTools] 最终选中工具数:', defaultTools.length);

          return {
            selectedTools: defaultTools,
          };
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
      name: 'settings-storage-v5',  // 修改版本号，强制清除旧缓存
      partialize: (state) => ({
        // 持久化用户选择，这样后端重启后不会丢失
        configs: state.configs,
        activeConfigId: state.activeConfigId,
        defaultSystemPrompt: state.defaultSystemPrompt,
        tools: state.tools,
        toolServices: state.toolServices,
        selectedTools: state.selectedTools,
        hasUserSelection: state.hasUserSelection,
      }),
    }
  )
);
