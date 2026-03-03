import { Menu, ChevronDown, Bot, BookOpen, RotateCcw } from 'lucide-react';
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
  const { configs, activeConfigId } = useSettingsStore();
  const { knowledgeBases, selectedKnowledgeIds, toggleKnowledgeSelection } = useKnowledgeStore();
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [showKnowledgeSelector, setShowKnowledgeSelector] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const activeConfig = configs.find(c => c.id === activeConfigId);

  // 获取模型列表
  const fetchModels = async () => {
    setIsLoading(true);
    try {
      const result = await modelApi.list();
      if (result.status === 1) {
        const newConfigs: LLMConfig[] = [];
        let configId = 1;
        
        for (const [providerKey, providerInfo] of Object.entries(result.data.providers)) {
          const provider = providerInfo as any;
          for (const model of provider.models) {
            newConfigs.push({
              id: `config_${configId++}`,
              name: model,
              provider: toLLMProvider(providerKey),
              model: model,
              temperature: 0.7,
              maxTokens: 4096,
              topP: 0.9,
              enabled: true
            });
          }
        }
        
        const currentActiveConfig = useSettingsStore.getState().activeConfigId;
        const currentActiveModel = useSettingsStore.getState().configs.find(c => c.id === currentActiveConfig)?.model;
        
        let newActiveConfigId = currentActiveConfig;
        if (currentActiveModel) {
          const matchedConfig = newConfigs.find(c => c.model === currentActiveModel);
          if (matchedConfig) {
            newActiveConfigId = matchedConfig.id;
          } else if (newConfigs.length > 0) {
            newActiveConfigId = newConfigs[0].id;
          } else {
            newActiveConfigId = null;
          }
        } else if (newConfigs.length > 0) {
          newActiveConfigId = newConfigs[0].id;
        } else {
          newActiveConfigId = null;
        }
        
        useSettingsStore.setState({ 
          configs: newConfigs, 
          activeConfigId: newActiveConfigId
        });
        
        const totalModels = Object.values(result.data.providers).reduce((sum: number, p: any) => sum + (p.models?.length || 0), 0);
        showToast(`获取到 ${totalModels} 个模型`, 'success');
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
    <header className="h-16 px-4 md:px-6 flex items-center justify-between border-b border-border/40 bg-bg-primary/80 backdrop-blur-xl sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleMobileSidebar}
          className="lg:hidden p-2 hover:bg-bg-tertiary rounded-xl transition-all active:scale-95 text-text-secondary hover:text-text-primary"
        >
          <Menu className="w-5 h-5" />
        </button>
        
        <button
          onClick={onToggleSidebar}
          className="hidden lg:flex p-2 hover:bg-bg-tertiary rounded-xl transition-all active:scale-95 text-text-secondary hover:text-text-primary"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="h-6 w-[1px] bg-border/20 hidden sm:block mx-1" />

        <h1 className="text-lg font-bold text-text-primary tracking-tight hidden sm:block">
          JeikChat
        </h1>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        {/* 模型选择器 */}
        <div className="relative group">
          <div className="flex items-center h-10">
            <button
              onClick={() => {
                if (!configs.length) {
                  fetchModels();
                } else {
                  setShowModelSelector(!showModelSelector);
                }
              }}
              className="flex items-center gap-2.5 px-3 h-full bg-[#1E1E1E] hover:bg-[#262626] border border-white/[0.05] rounded-l-xl transition-all hover:border-primary/40 min-w-0 shadow-xl"
            >
              <div className="w-5 h-5 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Bot className="w-3.5 h-3.5 text-primary" />
              </div>
              <span className="max-w-[100px] sm:max-w-[150px] truncate font-semibold text-text-primary text-sm">
                {activeConfig?.name || (configs.length > 0 ? configs[0].name : '选择模型')}
              </span>
              <ChevronDown className={`w-3.5 h-3.5 text-text-quaternary flex-shrink-0 transition-transform duration-200 ${showModelSelector ? 'rotate-180' : ''}`} />
            </button>
            <button 
              onClick={handleRefreshModels}
              disabled={isLoading}
              className={`px-3 h-full bg-[#1E1E1E] hover:bg-[#262626] border-y border-r border-white/[0.05] rounded-r-xl transition-all group shadow-xl flex items-center justify-center ${isLoading ? 'cursor-not-allowed opacity-50' : ''}`}
              title="刷新模型列表"
            >
              <RotateCcw className={`w-3.5 h-3.5 text-text-quaternary group-hover:text-primary transition-all ${isLoading ? 'animate-spin' : 'group-active:rotate-180'}`} />
            </button>
          </div>

          {showModelSelector && (
            <div className="absolute top-full right-0 mt-2 w-64 bg-[#1E1E1E] border border-white/[0.08] rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 z-50">
              <div className="px-4 py-2 mb-1 text-[10px] font-bold text-text-quaternary uppercase tracking-widest">选择模型</div>
              {configs.length === 0 ? (
                <div className="px-4 py-8 text-sm text-text-tertiary text-center flex flex-col items-center gap-2">
                  <Bot className="w-8 h-8 opacity-20" />
                  {isLoading ? '正在获取模型列表...' : '暂无模型，请刷新'}
                </div>
              ) : (
                <div className="space-y-0.5 px-1.5">
                  {configs.map(config => (
                    <button
                      key={config.id}
                      onClick={() => {
                        useSettingsStore.getState().setActiveConfig(config.id);
                        setShowModelSelector(false);
                      }}
                      className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all duration-200 flex items-center justify-between group/item ${
                        activeConfigId === config.id 
                          ? 'bg-primary/10 text-primary font-bold' 
                          : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Bot className={`w-4 h-4 ${activeConfigId === config.id ? 'text-primary' : 'text-text-quaternary group/item:text-text-primary'}`} />
                        <span className="truncate">{config.name}</span>
                      </div>
                      {activeConfigId === config.id && (
                        <div className="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(99,102,241,0.6)]" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 知识库选择器 */}
        <div className="relative">
          <button
            onClick={() => setShowKnowledgeSelector(!showKnowledgeSelector)}
            className={`flex items-center gap-2 px-3 py-2 text-sm rounded-xl font-semibold transition-all shadow-sm ${
              selectedKnowledgeIds.length > 0
                ? 'bg-primary/10 text-primary border border-primary/20'
                : 'bg-bg-secondary/50 hover:bg-bg-secondary border border-border/40 hover:border-primary/40 text-text-secondary'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span className="hidden xs:inline">知识库</span>
            {selectedKnowledgeIds.length > 0 && (
              <div className="flex items-center justify-center min-w-[18px] h-[18px] bg-primary text-white text-[10px] font-bold rounded-full px-1">
                {selectedKnowledgeIds.length}
              </div>
            )}
          </button>

          {showKnowledgeSelector && (
            <div className="absolute right-0 mt-3 w-64 bg-[#1E1E1E] border border-white/[0.08] rounded-2xl shadow-2xl overflow-hidden py-2 z-50 max-h-[400px] overflow-y-auto animate-in fade-in slide-in-from-top-2 duration-200">
              <div className="px-4 py-2 mb-1 text-[10px] font-bold text-text-quaternary uppercase tracking-widest">关联知识库</div>
              {knowledgeBases.length === 0 ? (
                <div className="px-4 py-8 text-sm text-text-tertiary text-center flex flex-col items-center gap-2">
                  <BookOpen className="w-8 h-8 opacity-20" />
                  暂无可用知识库
                </div>
              ) : (
                <div className="space-y-0.5 px-1.5">
                  <button
                    onClick={() => {
                      if (selectedKnowledgeIds.length === knowledgeBases.length) {
                        useKnowledgeStore.getState().setSelectedKnowledgeIds([]);
                      } else {
                        const allIds = knowledgeBases.map(kb => kb.id);
                        useKnowledgeStore.getState().setSelectedKnowledgeIds(allIds);
                      }
                    }}
                    className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm transition-all text-text-secondary hover:bg-bg-tertiary hover:text-text-primary"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-4 h-4 rounded-md border-2 transition-all flex items-center justify-center ${
                        selectedKnowledgeIds.length === knowledgeBases.length
                          ? 'border-primary bg-primary'
                          : selectedKnowledgeIds.length > 0
                          ? 'border-primary bg-primary/50'
                          : 'border-text-quaternary'
                      }`}>
                        {selectedKnowledgeIds.length === knowledgeBases.length && (
                          <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={4} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </div>
                      <span className="font-medium">全部选择</span>
                    </div>
                  </button>
                  
                  <div className="h-[1px] bg-border/10 my-1 mx-2" />
                  
                  {knowledgeBases.map(kb => (
                    <button
                      key={kb.id}
                      onClick={() => toggleKnowledgeSelection(kb.id)}
                      className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm transition-all duration-200 group/kb ${
                        selectedKnowledgeIds.includes(kb.id)
                          ? 'bg-primary/5 text-primary font-medium'
                          : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
                      }`}
                    >
                      <div className="flex items-center gap-3 truncate">
                        <div className={`w-4 h-4 rounded-md border-2 transition-all flex items-center justify-center flex-shrink-0 ${
                          selectedKnowledgeIds.includes(kb.id)
                            ? 'border-primary bg-primary'
                            : 'border-text-quaternary group/kb:border-text-tertiary'
                        }`}>
                          {selectedKnowledgeIds.includes(kb.id) && (
                            <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={4} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </div>
                        <span className="truncate">{kb.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
