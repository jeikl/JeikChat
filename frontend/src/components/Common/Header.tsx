import { Menu, ChevronDown, Bot, Volume2, RotateCcw } from 'lucide-react';
import { useSettingsStore } from '@/stores/settingsStore';
import { useKnowledgeStore } from '@/stores/knowledgeStore';
import { useState, useEffect } from 'react';
import { showToast } from '@/utils/toast';
import { modelApi } from '@/services/api';
import type { LLMProvider, LLMConfig } from '@/types/config';

const toLLMProvider = (provider: string): LLMProvider => {
  return provider as LLMProvider;
};

interface HeaderProps {
  onToggleSidebar: () => void;
  onToggleMobileSidebar: () => void;
}

const Header = ({ onToggleSidebar, onToggleMobileSidebar }: HeaderProps) => {
  const { configs, activeConfigId, setConfigs, clearConfigs } = useSettingsStore();
  const { knowledgeBases, selectedKnowledgeIds, toggleKnowledgeSelection } = useKnowledgeStore();
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [showKnowledgeSelector, setShowKnowledgeSelector] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const activeConfig = configs.find(c => c.id === activeConfigId);

  // 获取模型列表
  const fetchModels = async () => {
    // 直接从后端获取，不使用缓存
    setIsLoading(true);
    try {
      const result = await modelApi.list();
      if (result.status === 1) {
        // 生成配置列表
        const newConfigs: LLMConfig[] = [];
        let configId = 1;
        
        for (const [providerKey, providerInfo] of Object.entries(result.data.providers)) {
          const provider = providerInfo as any;
          for (const model of provider.models) {
            newConfigs.push({
              id: `config_${configId++}`,
              name: `${provider.name}-${model}`,
              provider: toLLMProvider(providerKey),
              model: model,
              temperature: 0.7,
              maxTokens: 4096,
              topP: 0.9,
              enabled: true
            });
          }
        }
        
        // 先清空再设置，确保触发更新
        clearConfigs();
        setConfigs([...newConfigs]);
        
        // 显示成功提示
        const totalModels = Object.values(result.data.providers).reduce((sum: number, p: any) => sum + (p.models?.length || 0), 0);
        showToast(`获取到 ${totalModels} 个模型`, 'success');
        
        // 如果当前选中的模型不在新列表中，重置为第一个
        const currentActiveId = useSettingsStore.getState().activeConfigId;
        if (currentActiveId && !newConfigs.find(c => c.id === currentActiveId)) {
          useSettingsStore.getState().setActiveConfig(newConfigs[0]?.id || null);
        }
      } else {
        showToast('获取模型列表失败，请稍后重试', 'error');
      }
    } catch (error) {
      console.error('获取模型列表失败:', error);
      showToast('获取模型列表失败，请稍后重试', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // 首次加载时获取模型列表
  useEffect(() => {
    fetchModels();
  }, []);

  // 当模型列表更新时，自动选择第一个模型
  useEffect(() => {
    if (configs.length > 0 && !activeConfigId) {
      useSettingsStore.getState().setActiveConfig(configs[0].id);
    }
  }, [configs, activeConfigId]);

  const handleRefreshModels = () => {
    fetchModels();
  };

  return (
    <header className="h-16 px-4 flex items-center justify-between border-b border-border/50 bg-bg-primary/80 backdrop-blur-sm">
      <div className="flex items-center gap-3 pl-2">
        <button
          onClick={onToggleMobileSidebar}
          className="lg:hidden p-2 hover:bg-bg-tertiary rounded-lg transition-colors"
        >
          <Menu className="w-5 h-5 text-text-primary" />
        </button>
        
        <button
          onClick={onToggleSidebar}
          className="hidden lg:block p-2 hover:bg-bg-tertiary rounded-lg transition-colors"
        >
          <Menu className="w-5 h-5 text-text-primary" />
        </button>

        <h1 className="text-lg font-semibold text-text-primary hidden sm:block">
          JeikChat
        </h1>
      </div>

      <div className="flex items-center gap-1 pr-2">
        <div className="relative">
          <div className="flex items-center gap-1">
            <button
              onClick={() => {
                if (!configs.length) {
                  fetchModels();
                } else {
                  setShowModelSelector(!showModelSelector);
                }
              }}
              className="flex items-center gap-2 px-2 sm:px-3 py-1.5 text-sm bg-bg-secondary/80 hover:bg-bg-secondary border border-border/50 rounded-l-lg transition-all hover:border-primary/30 min-w-0"
            >
              <Bot className="w-4 h-4 text-primary flex-shrink-0" />
              <span className="max-w-[80px] sm:max-w-[120px] md:max-w-[180px] truncate text-text-primary">{activeConfig?.name || (configs.length > 0 ? configs[0].name : '选择模型')}</span>
              <ChevronDown className="w-3.5 h-3.5 text-text-tertiary flex-shrink-0" />
            </button>
            <button
              onClick={handleRefreshModels}
              disabled={isLoading}
              className="px-1.5 sm:px-2 py-1.5 text-sm bg-bg-secondary/80 hover:bg-bg-tertiary border border-l-0 border-border/50 rounded-r-lg transition-all disabled:opacity-50 flex-shrink-0"
            >
              {isLoading ? (
                <RotateCcw className="w-4 h-4 text-text-tertiary animate-spin" />
              ) : (
                <RotateCcw className="w-4 h-4 text-text-tertiary" />
              )}
            </button>
          </div>

          {showModelSelector && (
            <div className="absolute right-0 mt-2 w-72 bg-bg-secondary rounded-xl shadow-xl border border-border/50 py-1 z-50 overflow-y-auto max-h-64">
              {configs.length === 0 ? (
                <div className="px-4 py-3 text-sm text-text-tertiary text-center">
                  {isLoading ? '加载中...' : '暂无模型，请刷新'}
                </div>
              ) : (
                configs.map(config => (
                  <button
                    key={config.id}
                    onClick={() => {
                      useSettingsStore.getState().setActiveConfig(config.id);
                      setShowModelSelector(false);
                    }}
                    className={`w-full text-left px-4 py-2.5 text-sm hover:bg-bg-tertiary transition-colors flex items-center gap-2 ${
                      activeConfigId === config.id 
                        ? 'text-white bg-primary/20' 
                        : 'text-text-secondary'
                    }`}
                  >
                    <Bot className={`w-4 h-4 ${activeConfigId === config.id ? 'text-primary' : 'text-text-tertiary'}`} />
                    {config.name}
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        <div className="relative flex-shrink-0">
          <button
            onClick={() => setShowKnowledgeSelector(!showKnowledgeSelector)}
            className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 text-sm rounded-lg transition-all ${
              selectedKnowledgeIds.length > 0
                ? 'bg-primary/10 text-primary border border-primary/20'
                : 'bg-bg-secondary/80 hover:bg-bg-secondary border border-border/50 hover:border-primary/30 text-text-secondary'
            }`}
          >
            <span className="hidden xs:inline">知识库</span>
            <span className="xs:hidden text-xs">库</span>
            {selectedKnowledgeIds.length > 0 && (
              <span className="bg-primary text-white text-xs px-1.5 py-0.5 rounded-full">
                {selectedKnowledgeIds.length}
              </span>
            )}
            <ChevronDown className="w-3.5 h-3.5 text-text-tertiary" />
          </button>

          {showKnowledgeSelector && (
            <div className="absolute right-0 mt-2 w-60 bg-bg-secondary rounded-xl shadow-xl border border-border/50 py-1 z-50 max-h-64 overflow-y-auto">
              {knowledgeBases.length === 0 ? (
                <div className="px-4 py-3 text-sm text-text-tertiary">
                  暂无知识库，请先创建
                </div>
              ) : (
                <>
                  <button
                    onClick={() => {
                      if (selectedKnowledgeIds.length === knowledgeBases.length) {
                        toggleKnowledgeSelection('');
                      } else {
                        const allIds = knowledgeBases.map(kb => kb.id);
                        useKnowledgeStore.getState().setSelectedKnowledgeIds(allIds);
                      }
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-bg-tertiary transition-colors text-text-secondary"
                  >
                    <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                      selectedKnowledgeIds.length === knowledgeBases.length
                        ? 'border-primary bg-primary'
                        : selectedKnowledgeIds.length > 0 && selectedKnowledgeIds.length < knowledgeBases.length
                        ? 'border-primary bg-primary/50'
                        : 'border-text-quaternary'
                    }`}>
                      {selectedKnowledgeIds.length === knowledgeBases.length ? (
                        <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : selectedKnowledgeIds.length > 0 && selectedKnowledgeIds.length < knowledgeBases.length ? (
                        <div className="w-2 h-2 bg-white rounded-sm"></div>
                      ) : null}
                    </div>
                    <span>全选</span>
                  </button>
                  
                  <div className="border-t border-border/50 my-1"></div>
                  
                  {knowledgeBases.map(kb => (
                    <button
                      key={kb.id}
                      onClick={() => toggleKnowledgeSelection(kb.id)}
                      className="w-full flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-bg-tertiary transition-colors text-text-secondary"
                    >
                      <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                        selectedKnowledgeIds.includes(kb.id)
                          ? 'border-primary bg-primary'
                          : 'border-text-quaternary'
                      }`}>
                        {selectedKnowledgeIds.includes(kb.id) && (
                          <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </div>
                      <span className="truncate">{kb.name}</span>
                    </button>
                  ))}
                </>
              )}
            </div>
          )}
        </div>

        <button className="p-2 hover:bg-bg-tertiary rounded-lg transition-colors">
          <Volume2 className="w-5 h-5 text-text-secondary" />
        </button>
      </div>
    </header>
  );
};

export default Header;