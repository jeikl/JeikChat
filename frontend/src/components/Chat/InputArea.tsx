import { useState, useRef, useEffect } from 'react';
import { Sparkles, Zap, Ban, Plus, Globe, Mic, Square, Send, Loader2, BookOpen, X } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { useKnowledgeStore } from '@/stores/knowledgeStore';
import { toolsApi, knowledgeApi } from '@/services/api';
import type { Tool } from '@/services/api';
import type { KnowledgeBase } from '@/types/knowledge';

interface InputAreaProps {
  onSend: (content: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  isStreaming?: boolean;
}

const thinkingOptions = [
  { value: 'auto', label: 'Auto', icon: Sparkles },
  { value: 'deep', label: 'Thinking', icon: Zap },
  { value: 'false', label: 'Close', icon: Ban },
] as const;

// Web 搜索工具的 toolid 列表
const WEB_SEARCH_TOOL_IDS = [
  'bing-search_bing_search',
  'zhipu-web-search-sse_webSearchSogou',
  'zhipu-web-search-sse_webSearchQuark',
  'zhipu-web-search-sse_webSearchPro',
  'zhipu-web-search-sse_webSearchStd'
];

const InputArea = ({ onSend, onStop, disabled, isStreaming }: InputAreaProps) => {
  const [content, setContent] = useState('');
  const [showThinkingDropdown, setShowThinkingDropdown] = useState(false);
  const [showKnowledgeDropdown, setShowKnowledgeDropdown] = useState(false);
  const [isLoadingTools, setIsLoadingTools] = useState(false);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const knowledgeDropdownRef = useRef<HTMLDivElement>(null);
  const loadedRef = useRef(false);
  
  const thinkingMode = useChatStore((state) => state.thinkingMode);
  const setThinkingMode = useChatStore((state) => state.setThinkingMode);
  
  // 从 settingsStore 获取工具状态
  const selectedTools = useSettingsStore((state) => state.selectedTools);
  const toolServices = useSettingsStore((state) => state.toolServices);
  const toggleTool = useSettingsStore((state) => state.toggleTool);
  const setToolServices = useSettingsStore((state) => state.setToolServices);
  const applyDefaultTools = useSettingsStore((state) => state.applyDefaultTools);
  
  // 从 knowledgeStore 获取知识库状态
  const selectedKnowledgeIds = useKnowledgeStore((state) => state.selectedKnowledgeIds);
  const toggleKnowledgeSelection = useKnowledgeStore((state) => state.toggleKnowledgeSelection);
  const setSelectedKnowledgeIds = useKnowledgeStore((state) => state.setSelectedKnowledgeIds);
  
  // 检查是否选中了 web 搜索工具
  const isWebSearch = selectedTools.some(t => WEB_SEARCH_TOOL_IDS.includes(t.toolid));
  
  // 检查是否选中了知识库
  const hasSelectedKnowledge = selectedKnowledgeIds.length > 0;
  
  // 加载知识库列表
  useEffect(() => {
    const loadKnowledgeBases = async () => {
      try {
        const result = await knowledgeApi.list();
        if (result.status === 1) {
          setKnowledgeBases(result.data);
        }
      } catch (error) {
        console.error('加载知识库失败:', error);
      }
    };
    loadKnowledgeBases();
  }, []);
  
  // 自动加载工具（如果未加载）
  // 加载工具的函数
  const loadTools = () => {
    setIsLoadingTools(true);
    
    const loadedServicesList: any[] = [];

    toolsApi.listStream(false, {
      onStatus: () => {},
      onService: (service) => {
        loadedServicesList.push(service);
        setToolServices([...loadedServicesList]);
      },
      onComplete: (_total, _services, defaultSelectedTools) => {
        setIsLoadingTools(false);
        // 应用后端配置的默认选中工具（仅在用户无选择记录时）
        if (defaultSelectedTools && defaultSelectedTools.length > 0) {
          applyDefaultTools(defaultSelectedTools);
        }
      },
      onError: (error) => {
        console.error('[InputArea] 工具加载失败:', error);
        setIsLoadingTools(false);
        // 3秒后重试
        setTimeout(() => {
          if (toolServices.length === 0) {
            console.log('[InputArea] 尝试重新加载工具...');
            loadTools();
          }
        }, 3000);
      },
    });
  };
  
  useEffect(() => {
    if (!loadedRef.current && toolServices.length === 0) {
      loadedRef.current = true;
      loadTools();
    }
  }, [toolServices.length, setToolServices]);
  
  // 切换 web 搜索工具
  const handleWebSearchToggle = () => {
    // 获取所有 web 搜索工具
    const webSearchTools: Tool[] = [];
    for (const service of toolServices) {
      for (const tool of service.tools) {
        if (WEB_SEARCH_TOOL_IDS.includes(tool.toolid)) {
          webSearchTools.push(tool);
        }
      }
    }

    if (webSearchTools.length === 0) return;

    // 检查当前是否已选中任何 web 搜索工具
    const hasSelectedWebSearch = selectedTools.some(t =>
      WEB_SEARCH_TOOL_IDS.includes(t.toolid)
    );

    if (hasSelectedWebSearch) {
      // 如果已选中，则取消选中所有 web 搜索工具
      for (const tool of webSearchTools) {
        const isSelected = selectedTools.some(t => t.toolid === tool.toolid);
        if (isSelected) {
          toggleTool(tool);
        }
      }
    } else {
      // 如果未选中，则选中第一个 web 搜索工具
      toggleTool(webSearchTools[0]);
    }
  };
  
  const currentOption = thinkingOptions.find(o => o.value === thinkingMode) || thinkingOptions[0];
  const CurrentIcon = currentOption.icon;

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [content]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowThinkingDropdown(false);
      }
      if (knowledgeDropdownRef.current && !knowledgeDropdownRef.current.contains(event.target as Node)) {
        setShowKnowledgeDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = () => {
    if (content.trim() && !disabled) {
      onSend(content);
      setContent('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-[1000px] relative px-4 md:px-8">
      {/* 输入框主体 - 极致纤长且扁平的"指挥棒"感 */}
      <div className="relative group gemini-aura pointer-events-auto">
        <div className={`
          relative flex flex-col w-full
          bg-[#1E1E1E] transition-all duration-500
          rounded-[24px] overflow-visible
          ${isStreaming ? 'ring-[0.5px] ring-primary/20' : ''}
        `}>
          {/* 文本输入区 - 纵向极致压缩 50% */}
          <div className="flex flex-col px-5 pt-3.5 pb-0">
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything..."
              className="w-full bg-transparent border-none focus:border-none focus:ring-0 focus:outline-none resize-none p-0 text-text-primary placeholder:text-text-quaternary text-[15px] max-h-[160px] leading-relaxed scrollbar-none min-h-[24px] selection:bg-primary/30"
              style={{ boxShadow: 'none', border: 'none', outline: 'none' }}
            />
          </div>

          {/* 底部操作区 - 纵向极度紧凑 */}
          <div className="flex items-center justify-between px-4 pb-2.5">
            <div className="flex items-center gap-2">
              {/* 左侧附件按钮 - 极小化 */}
              <button className="p-1.5 rounded-lg hover:bg-white/5 text-text-tertiary hover:text-text-primary transition-all active:scale-90 flex-shrink-0">
                <Plus className="w-4 h-4" />
              </button>
              
              {/* 思考模式与搜索 - 极简扁平 */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setShowThinkingDropdown(!showThinkingDropdown)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-bold tracking-tight transition-all duration-300 min-w-fit whitespace-nowrap ${
                      thinkingMode === 'deep' 
                        ? 'bg-primary/10 text-primary' 
                        : 'text-text-quaternary hover:bg-white/5 hover:text-text-primary'
                    }`}
                  >
                    <CurrentIcon className={`w-4 h-4 flex-shrink-0 ${thinkingMode === 'deep' ? 'animate-pulse' : ''}`} />
                    <span className="inline whitespace-nowrap">{currentOption.label}</span>
                  </button>
                  
                  {showThinkingDropdown && (
                    <div className="absolute bottom-full left-0 mb-4 w-48 bg-[#161616] border border-white/10 rounded-2xl shadow-2xl p-1.5 animate-in fade-in slide-in-from-bottom-2 duration-200 z-[100]">
                      {thinkingOptions.map((option) => {
                        const Icon = option.icon;
                        return (
                          <button
                            key={option.value}
                            onClick={() => {
                              setThinkingMode(option.value);
                              setShowThinkingDropdown(false);
                            }}
                            className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-[13px] transition-all duration-200 ${
                              thinkingMode === option.value
                                ? 'bg-white/10 text-white font-bold'
                                : 'text-text-tertiary hover:bg-white/5 hover:text-text-primary'
                            }`}
                          >
                            <Icon className="w-4 h-4 flex-shrink-0" />
                            <span className="whitespace-nowrap">{option.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>

                <button
                  onClick={toolServices.length === 0 && !isLoadingTools ? loadTools : handleWebSearchToggle}
                  disabled={isLoadingTools}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-bold tracking-tight transition-all duration-300 min-w-fit whitespace-nowrap ${
                    isWebSearch
                      ? 'bg-primary/10 text-primary'
                      : isLoadingTools
                        ? 'text-text-quaternary/50 cursor-not-allowed'
                        : toolServices.length === 0
                          ? 'text-text-quaternary/50 hover:text-text-tertiary hover:bg-white/5'
                          : 'text-text-quaternary hover:bg-white/5 hover:text-text-primary'
                  }`}
                  title={isLoadingTools ? '正在加载工具...' : isWebSearch ? '点击取消网络搜索' : toolServices.length === 0 ? '点击重新加载工具' : '点击启用网络搜索'}
                >
                  {isLoadingTools ? (
                    <Loader2 className="w-4 h-4 flex-shrink-0 animate-spin" />
                  ) : toolServices.length === 0 ? (
                    <Globe className="w-4 h-4 flex-shrink-0 opacity-50" />
                  ) : (
                    <Globe className="w-4 h-4 flex-shrink-0" />
                  )}
                  <span className="inline whitespace-nowrap">
                    {isLoadingTools ? 'Loading...' : toolServices.length === 0 ? 'Retry' : 'Search'}
                  </span>
                </button>

                {/* 知识库选择按钮 */}
                <div className="relative" ref={knowledgeDropdownRef}>
                  <button
                    onClick={() => setShowKnowledgeDropdown(!showKnowledgeDropdown)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-bold tracking-tight transition-all duration-300 min-w-fit whitespace-nowrap ${
                      hasSelectedKnowledge
                        ? 'bg-primary/10 text-primary'
                        : 'text-text-quaternary hover:bg-white/5 hover:text-text-primary'
                    }`}
                    title={hasSelectedKnowledge ? `已选择 ${selectedKnowledgeIds.length} 个知识库` : '点击选择知识库'}
                  >
                    <BookOpen className="w-4 h-4 flex-shrink-0" />
                    <span className="inline whitespace-nowrap">
                      {hasSelectedKnowledge ? `知识库 (${selectedKnowledgeIds.length})` : '知识库'}
                    </span>
                  </button>

                  {showKnowledgeDropdown && (
                    <div className="absolute bottom-full left-0 mb-4 w-64 bg-[#161616] border border-white/10 rounded-2xl shadow-2xl p-1.5 animate-in fade-in slide-in-from-bottom-2 duration-200 z-[100]">
                      <div className="px-3 py-2 border-b border-white/10">
                        <p className="text-xs text-text-tertiary">选择要检索的知识库</p>
                      </div>
                      {knowledgeBases.length === 0 ? (
                        <div className="px-3 py-4 text-center">
                          <p className="text-xs text-text-tertiary">暂无知识库</p>
                          <p className="text-[10px] text-text-quaternary mt-1">请先在知识库管理页面创建</p>
                        </div>
                      ) : (
                        <div className="max-h-48 overflow-y-auto py-1">
                          {knowledgeBases.map((kb) => (
                            <button
                              key={kb.id}
                              onClick={() => toggleKnowledgeSelection(kb.id)}
                              className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-[13px] transition-all duration-200 ${
                                selectedKnowledgeIds.includes(kb.id)
                                  ? 'bg-white/10 text-white font-bold'
                                  : 'text-text-tertiary hover:bg-white/5 hover:text-text-primary'
                              }`}
                            >
                              <div className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 ${
                                selectedKnowledgeIds.includes(kb.id)
                                  ? 'bg-primary border-primary'
                                  : 'border-text-tertiary'
                              }`}>
                                {selectedKnowledgeIds.includes(kb.id) && (
                                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                  </svg>
                                )}
                              </div>
                              <span className="truncate text-left flex-1">{kb.name}</span>
                            </button>
                          ))}
                        </div>
                      )}
                      {hasSelectedKnowledge && (
                        <div className="px-3 py-2 border-t border-white/10">
                          <button
                            onClick={() => setSelectedKnowledgeIds([])}
                            className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-[12px] text-text-tertiary hover:bg-white/5 hover:text-text-primary transition-all duration-200"
                          >
                            <X className="w-3.5 h-3.5" />
                            <span>清除选择</span>
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 右侧发送与语音 - 圆形按钮风格 */}
            <div className="flex items-center gap-2">
              <button className="p-1.5 rounded-full hover:bg-white/5 text-text-tertiary hover:text-text-primary transition-all active:scale-90">
                <Mic className="w-4 h-4" />
              </button>
              
              {isStreaming ? (
                <button
                  onClick={onStop}
                  className="p-1.5 bg-white text-black rounded-full hover:bg-white/90 transition-all shadow-xl active:scale-95"
                >
                  <Square className="w-3.5 h-3.5 fill-current" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!content.trim() || disabled}
                  className={`p-1.5 rounded-full transition-all active:scale-95 ${
                    content.trim() && !disabled
                      ? 'bg-white text-black hover:bg-white/90 shadow-xl'
                      : 'bg-white/5 text-white/20 cursor-not-allowed'
                  }`}
                >
                  <Send className="w-3.5 h-3.5 fill-current translate-x-[0.5px]" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 底部免责声明 - 移出流光边框，消除“蓝色分界线” */}
      <div className="mt-1 flex justify-center pb-0 pointer-events-auto">
        <p className="text-[10px] text-text-quaternary font-medium tracking-wide opacity-60 scale-100 origin-top leading-tight">
          JeikChat can make mistakes. Check important info.
        </p>
      </div>
    </div>
  );
};

export default InputArea;
