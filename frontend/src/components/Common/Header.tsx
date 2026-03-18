import { Menu, ChevronDown, Bot, RotateCcw, Github, Mail, Code } from 'lucide-react';
import { useSettingsStore } from '@/stores/settingsStore';
import { useState, useEffect } from 'react';
import { showToast } from '@/utils/toast';
import { modelApi, configApi } from '@/services/api';
import type { LLMConfig } from '@/types/config';


// 自定义 Gitee 图标组件 (官方简化版 Logo)
const GiteeIcon = ({ className, style }: { className?: string; style?: React.CSSProperties }) => (
  <svg 
    className={className} 
    style={{...style, width: '1.25rem', height: '1.25rem'}}
    viewBox="0 0 1024 1024" 
    xmlns="http://www.w3.org/2000/svg"
  >
    <path 
      fill="currentColor" 
      d="M512 1024C230.4 1024 0 793.6 0 512S230.4 0 512 0s512 230.4 512 512-230.4 512-512 512z m259.2-569.6H480c-12.8 0-25.6 12.8-25.6 25.6v64c0 12.8 12.8 25.6 25.6 25.6h176c12.8 0 25.6 12.8 25.6 25.6v12.8c0 41.6-35.2 76.8-76.8 76.8h-240c-41.6 0-76.8-35.2-76.8-76.8V416c0-41.6 35.2-76.8 76.8-76.8h214.4c12.8 0 25.6-12.8 25.6-25.6v-64c0-12.8-12.8-25.6-25.6-25.6H364.8C259.2 224 176 307.2 176 412.8v201.6c0 105.6 83.2 188.8 188.8 188.8h294.4c105.6 0 188.8-83.2 188.8-188.8v-60.8c0-54.4-35.2-99.2-76.8-99.2z"
    />
  </svg>
);

// 图标映射
const ICON_MAP: Record<string, any> = {
  Github,
  Mail,
  Code,
  Gitee: GiteeIcon
};

interface HeaderProps {
  onToggleSidebar: () => void;
  onToggleMobileSidebar: () => void;
}

const Header = ({ onToggleSidebar, onToggleMobileSidebar }: HeaderProps) => {
  const { configs, activeConfigId } = useSettingsStore();
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [appInfo, setAppInfo] = useState<any>(null);

  // 获取应用信息
  useEffect(() => {
    const fetchAppInfo = async () => {
      try {
        const info = await configApi.getAppInfo();
        setAppInfo(info);
      } catch (error) {
        console.error('获取应用信息失败:', error);
      }
    };
    fetchAppInfo();
  }, []);

  const activeConfig = configs.find(c => c.id === activeConfigId);

  // 获取模型列表
  const fetchModels = async () => {
    setIsLoading(true);
    try {
      const result = await modelApi.list();
      if (result.status === 1) {
        const newConfigs: LLMConfig[] = [];
        let configId = 1;

        // 新的 API 直接返回扁平化的模型列表
        const models = result.data.models || [];
        for (const model of models) {
          newConfigs.push({
            id: `config_${configId++}`,
            name: model.name || model.id,
            provider: model.provider,
            model: model.id,
            temperature: 0.7,
            maxTokens: 4096,
            topP: 0.9,
            enabled: model.enabled !== false,
            tags: model.tags || []
          });
        }

        // 优先使用服务器返回的默认模型
        const serverDefaultModel = result.data.default_model;
        // console.log('[DEBUG] Server default model:', serverDefaultModel);
        // console.log('[DEBUG] Available models:', newConfigs.map(c => c.model));
        
        const defaultConfig = newConfigs.find(c => c.model === serverDefaultModel);
        // console.log('[DEBUG] Found default config:', defaultConfig);
        
        let newActiveConfigId: string | null = null;
        if (defaultConfig) {
          newActiveConfigId = defaultConfig.id;
        } else if (newConfigs.length > 0) {
          newActiveConfigId = newConfigs[0].id;
        }
        // console.log('[DEBUG] Selected config ID:', newActiveConfigId);

        useSettingsStore.setState({
          configs: newConfigs,
          activeConfigId: newActiveConfigId
        });

        const totalModels = models.length;
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

        {/* 社交链接图标 */}
        {appInfo?.social_links && (
          <div className="flex items-center gap-0.5 sm:gap-1 ml-2 sm:ml-4 border-l border-border/20 pl-2 sm:pl-4">
            {appInfo.social_links.map((link: any, index: number) => {
              const Icon = ICON_MAP[link.icon] || Code;
              const isEmail = link.url.startsWith('mailto:');
              
              return (
                <a
                  key={index}
                  href={link.url}
                  target={isEmail ? "_self" : "_blank"}
                  rel="noopener noreferrer"
                  className="p-1.5 sm:p-2 text-text-tertiary hover:text-text-primary hover:bg-bg-tertiary rounded-lg transition-all flex items-center justify-center cursor-pointer"
                  title={link.name}
                  onClick={() => {
                    if (isEmail) {
                      const emailAddress = link.url.replace('mailto:', '');
                      navigator.clipboard.writeText(emailAddress)
                        .then(() => {
                          showToast('邮箱已复制到剪贴板', 'success');
                        })
                        .catch(() => {
                          console.error('复制失败');
                        });
                    }
                  }}
                >
                  {link.icon_url ? (
                    <img 
                      src={link.icon_url} 
                      alt={link.name} 
                      className="w-4 h-4 sm:w-5 sm:h-5 object-contain" 
                      onError={(e) => {
                        // 图片加载失败时，隐藏 img 标签并显示备用图标
                        e.currentTarget.style.display = 'none';
                        const fallbackIcon = e.currentTarget.nextElementSibling as HTMLElement;
                        if (fallbackIcon) fallbackIcon.style.display = 'block';
                      }}
                    />
                  ) : null}
                  
                  {/* 默认图标作为 fallback 或首选 */}
                  <Icon 
                    className="w-4 h-4 sm:w-5 sm:h-5" 
                    style={{ display: link.icon_url ? 'none' : 'block' }} 
                  />
                </a>
              );
            })}
          </div>
        )}
      </div>

      <div className="flex items-center gap-1 sm:gap-3 ml-auto">
        {/* 模型选择器 */}
        <div className="relative group">
          <div className="flex items-center h-8 sm:h-10">
            <button
              onClick={() => {
                if (!configs.length) {
                  fetchModels();
                } else {
                  setShowModelSelector(!showModelSelector);
                }
              }}
              className="flex items-center gap-1.5 sm:gap-2.5 px-2 sm:px-3 h-full bg-[#1E1E1E] hover:bg-[#262626] border border-white/[0.05] rounded-l-xl transition-all hover:border-primary/40 min-w-0 shadow-xl"
            >
              <div className="w-4 h-4 sm:w-5 sm:h-5 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Bot className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-primary" />
              </div>
              <span className="max-w-[70px] sm:max-w-[150px] truncate font-semibold text-text-primary text-[11px] sm:text-sm">
                {activeConfig?.name || (configs.length > 0 ? configs[0].name : '选择模型')}
              </span>
              <ChevronDown className={`w-3 h-3 sm:w-3.5 sm:h-3.5 text-text-quaternary flex-shrink-0 transition-transform duration-200 ${showModelSelector ? 'rotate-180' : ''}`} />
            </button>
            <button 
              onClick={handleRefreshModels}
              disabled={isLoading}
              className={`px-2 sm:px-3 h-full bg-[#1E1E1E] hover:bg-[#262626] border-y border-r border-white/[0.05] rounded-r-xl transition-all group shadow-xl flex items-center justify-center ${isLoading ? 'cursor-not-allowed opacity-50' : ''}`}
              title="刷新模型列表"
            >
              <RotateCcw className={`w-3 h-3 sm:w-3.5 sm:h-3.5 text-text-quaternary group-hover:text-primary transition-all ${isLoading ? 'animate-spin' : 'group-active:rotate-180'}`} />
            </button>
          </div>

          {showModelSelector && (
            <div className="absolute top-full right-0 mt-2 w-[min(90vw,280px)] sm:w-[280px] bg-[#1E1E1E] border border-white/[0.08] rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 z-50 flex flex-col h-[200px] sm:h-[260px]">
              <div className="px-3 py-2 mb-1 text-[10px] font-bold text-text-quaternary uppercase tracking-widest flex-shrink-0">选择模型</div>
              <div className="overflow-y-scroll overflow-x-scroll flex-1 min-h-0 dropdown-scrollbar [scrollbar-gutter:stable_both-edges]" style={{ touchAction: 'pan-x pan-y' }}>
                {configs.length === 0 ? (
                  <div className="px-4 py-8 text-sm text-text-tertiary text-center flex flex-col items-center gap-2">
                    <Bot className="w-8 h-8 opacity-20" />
                    {isLoading ? '正在获取模型列表...' : '暂无模型，请刷新'}
                  </div>
                ) : (
                  <div className="space-y-0.5 px-1.5 pb-2 min-w-max">
                    {configs.filter(c => c.enabled).map(config => (
                      <button
                        key={config.id}
                        onClick={() => {
                          useSettingsStore.getState().setActiveConfig(config.id);
                          setShowModelSelector(false);
                        }}
                        className={`min-w-full w-max text-left px-2 py-2 rounded-xl text-sm transition-all duration-200 flex items-center justify-between group/item ${
                          activeConfigId === config.id
                            ? 'bg-primary/10 text-primary font-bold'
                            : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
                        }`}
                      >
                        <div className="flex items-center gap-2 flex-1 min-w-max">
                          <Bot className={`w-4 h-4 flex-shrink-0 ${activeConfigId === config.id ? 'text-primary' : 'text-text-quaternary group/item:text-text-primary'}`} />
                          <div className="flex flex-col gap-1 flex-1 pr-4 min-w-max">
                            <span className="whitespace-nowrap">{config.name}</span>
                            {/* 显示模型标签 */}
                            {config.tags && config.tags.length > 0 && (
                              <div className="flex items-center gap-1 flex-nowrap">
                                {config.tags.map((tag, idx) => (
                                  <span
                                    key={idx}
                                    className={`text-[10px] px-1.5 py-0.5 rounded-full whitespace-nowrap ${
                                      activeConfigId === config.id
                                        ? 'bg-primary/20 text-primary'
                                        : 'bg-bg-tertiary text-text-quaternary'
                                    }`}
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        {activeConfigId === config.id && (
                          <div className="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(99,102,241,0.6)] flex-shrink-0 ml-2" />
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
