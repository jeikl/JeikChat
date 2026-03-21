import { useState, useRef, useEffect } from 'react';
import { Sparkles, Brain, Ban, Plus, Globe, Mic, Square, Send, Loader2, BookOpen, X, File as FileIcon, Video as VideoIcon, Music as AudioIcon, FileText as PdfIcon } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { useKnowledgeStore } from '@/stores/knowledgeStore';
import { toolsApi, knowledgeApi, fileApi } from '@/services/api';
import type { Tool } from '@/services/api';
import type { KnowledgeBase } from '@/types/knowledge';
import { showToast } from '@/utils/toast';

interface InputAreaProps {
  onSend: (content: string | any[]) => void;
  onStop?: () => void;
  disabled?: boolean;
  isStreaming?: boolean;
}

// ... thinkingOptions & WEB_SEARCH_TOOL_IDS ...

// 文件上传状态类型
interface UploadingFile {
  id: string;
  file: File;
  previewUrl: string;
  progress: number;
  status: 'uploading' | 'success' | 'error';
  url?: string; // 上传成功后的直链
}

const thinkingOptions = [
  { value: 'auto', label: 'Auto', icon: Sparkles },
  { value: 'deep', label: 'Think', icon: Brain },
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

  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const knowledgeDropdownRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const loadedRef = useRef(false);
  
  // ... stores ...
  const thinkingMode = useChatStore((state) => state.thinkingMode);
  const setThinkingMode = useChatStore((state) => state.setThinkingMode);
  const selectedTools = useSettingsStore((state) => state.selectedTools);
  const toolServices = useSettingsStore((state) => state.toolServices);
  const toggleTool = useSettingsStore((state) => state.toggleTool);
  const setToolServices = useSettingsStore((state) => state.setToolServices);
  const applyDefaultTools = useSettingsStore((state) => state.applyDefaultTools);
  const selectedKnowledgeIds = useKnowledgeStore((state) => state.selectedKnowledgeIds);
  const toggleKnowledgeSelection = useKnowledgeStore((state) => state.toggleKnowledgeSelection);
  const setSelectedKnowledgeIds = useKnowledgeStore((state) => state.setSelectedKnowledgeIds);
  const knowledgeBases = useKnowledgeStore((state) => state.knowledgeBases);
  const setKnowledgeBases = useKnowledgeStore((state) => state.setKnowledgeBases);
  
  const isWebSearch = selectedTools.some(t => WEB_SEARCH_TOOL_IDS.includes(t.toolid));
  const hasSelectedKnowledge = selectedKnowledgeIds.length > 0;

  // ... loadKnowledgeBases & loadTools ...
  useEffect(() => {
    const loadKnowledgeBases = async () => {
      try {
        const result = await knowledgeApi.list();
        if (result.status === 1) {
          setKnowledgeBases(result.data);
          
          // 清理已选择但已不存在的知识库ID
          const validIds = result.data.map((kb: KnowledgeBase) => kb.id);
          const cleanedIds = selectedKnowledgeIds.filter(id => validIds.includes(id));
          if (cleanedIds.length !== selectedKnowledgeIds.length) {
            setSelectedKnowledgeIds(cleanedIds);
          }
        }
      } catch (error) {
        console.error('加载知识库失败:', error);
      }
    };
    loadKnowledgeBases();
  }, [setKnowledgeBases, setSelectedKnowledgeIds, selectedKnowledgeIds]);

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
        if (defaultSelectedTools && defaultSelectedTools.length > 0) {
          applyDefaultTools(defaultSelectedTools);
        }
      },
      onError: (error) => {
        console.error('[InputArea] 工具加载失败:', error);
        setIsLoadingTools(false);
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

  // ... handleWebSearchToggle ...
  const handleWebSearchToggle = () => {
    const webSearchTools: Tool[] = [];
    for (const service of toolServices) {
      for (const tool of service.tools) {
        if (WEB_SEARCH_TOOL_IDS.includes(tool.toolid)) {
          webSearchTools.push(tool);
        }
      }
    }
    if (webSearchTools.length === 0) return;
    const hasSelectedWebSearch = selectedTools.some(t => WEB_SEARCH_TOOL_IDS.includes(t.toolid));
    if (hasSelectedWebSearch) {
      for (const tool of webSearchTools) {
        const isSelected = selectedTools.some(t => t.toolid === tool.toolid);
        if (isSelected) toggleTool(tool);
      }
    } else {
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

  // ... handleClickOutside ...
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

  // 处理文件上传
  const handleFileUpload = async (files: FileList | File[]) => {
    const newFiles: UploadingFile[] = Array.from(files).map(file => ({
      id: Math.random().toString(36).substring(7),
      file,
      previewUrl: URL.createObjectURL(file),
      progress: 0,
      status: 'uploading'
    }));

    setUploadingFiles(prev => [...prev, ...newFiles]);

    // 逐个上传
    for (const uploadFile of newFiles) {
      try {
        // 模拟进度 (真实进度需要 axios onUploadProgress 支持，当前 api 封装暂不支持)
        setUploadingFiles(prev => prev.map(f => 
          f.id === uploadFile.id ? { ...f, progress: 50 } : f
        ));

        const result = await fileApi.uploadFile(uploadFile.file);
        
        if (result.url) {
          setUploadingFiles(prev => prev.map(f => 
            f.id === uploadFile.id ? { ...f, status: 'success', progress: 100, url: result.url } : f
          ));
        } else {
          throw new Error("上传返回无效");
        }
      } catch (error) {
        console.error("上传失败:", error);
        showToast("文件上传失败", "error");
        setUploadingFiles(prev => prev.map(f => 
          f.id === uploadFile.id ? { ...f, status: 'error', progress: 0 } : f
        ));
      }
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    if (e.clipboardData.files.length > 0) {
      e.preventDefault();
      handleFileUpload(e.clipboardData.files);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files);
      // 清空 input 允许重复选择同一文件
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // 拖拽状态
  const [isDragging, setIsDragging] = useState(false);

  // 处理拖拽事件
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // 检查是否真的离开了容器（而不是进入了子元素）
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileUpload(files);
    }
  };

  const removeFile = (id: string) => {
    setUploadingFiles(prev => prev.filter(f => f.id !== id));
  };

  const handleSubmit = () => {
    // 如果有文件正在上传，阻止发送
    if (uploadingFiles.some(f => f.status === 'uploading')) {
      showToast("请等待文件上传完成", "info");
      return;
    }

    if ((content.trim() || uploadingFiles.length > 0) && !disabled) {
      const uploadedFiles = uploadingFiles.filter(f => f.status === 'success' && f.url);
      
      if (uploadedFiles.length > 0) {
        // 多模态数组格式发送
        const messageContent: any[] = [];
        
        // 1. 添加文本内容
        if (content.trim()) {
          messageContent.push({ type: "text", text: content.trim() });
        } else {
          messageContent.push({ type: "text", text: "请分析以下文件" });
        }
        
        // 2. 添加文件内容
        uploadedFiles.forEach(f => {
          if (f.file.type.startsWith("image/")) {
            // 图片类型使用嵌套格式
            messageContent.push({
              type: "image_url",
              image_url: {
                url: f.url
              }
            });
          } else if (f.file.type.startsWith("video/")) {
            // 视频类型使用嵌套格式
            messageContent.push({
              type: "video_url",
              video_url: {
                url: f.url
              }
            });
          } else if (f.file.type.startsWith("audio/")) {
            // 音频类型使用嵌套格式
            messageContent.push({
              type: "audio_url",
              audio_url: {
                url: f.url
              }
            });
          } else {
            // 其他文件类型
            messageContent.push({
              type: "file",
              url: f.url
            });
          }
        });
        
        // @ts-ignore - 临时允许传递数组，实际需要在父组件和API类型中修改
        console.log("InputArea 发送多模态数组:", messageContent);
        onSend(messageContent);
      } else {
        // 纯文本格式发送
        if (content.trim()) {
          console.log("InputArea 发送纯文本:", content.trim());
          onSend(content.trim()); 
        }
      }
      
      setContent('');
      setUploadingFiles([]);
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
      {/* 隐藏的文件输入框 */}
      <input 
        type="file" 
        ref={fileInputRef} 
        className="hidden" 
        multiple 
        onChange={handleFileSelect}
      />

      <div 
        className="relative group gemini-aura pointer-events-auto z-[60]"
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {/* 拖拽时的遮罩层 */}
        {isDragging && (
          <div className="absolute inset-0 z-50 bg-primary/10 border-2 border-dashed border-primary rounded-[24px] flex items-center justify-center backdrop-blur-sm">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-primary/20 flex items-center justify-center">
                <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <p className="text-primary font-medium text-lg">释放以上传文件</p>
              <p className="text-text-tertiary text-sm mt-1">支持图片、视频、音频、PDF 等格式</p>
            </div>
          </div>
        )}
        <div className={`
          relative flex flex-col w-full
          bg-[#1E1E1E] transition-all duration-500
          rounded-[24px]
          ${isStreaming ? 'ring-[0.5px] ring-primary/20' : ''}
          ${isDragging ? 'scale-[0.98] opacity-50' : ''}
        `}>
          {/* 文件预览区 */}
          {uploadingFiles.length > 0 && (
            <div className="flex gap-2 px-5 pt-3.5 overflow-x-auto scrollbar-thin pb-2">
              {uploadingFiles.map(file => {
                const isImage = file.file.type.startsWith('image/');
                const isVideo = file.file.type.startsWith('video/');
                const isAudio = file.file.type.startsWith('audio/');
                const isPdf = file.file.type === 'application/pdf';

                return (
                  <div key={file.id} className="relative group/file flex-shrink-0 flex items-center gap-2 pr-2 h-16 rounded-xl overflow-hidden bg-black/20 border border-white/10" title={file.file.name}>
                    {/* 图标/缩略图部分 */}
                    <div className="w-16 h-16 flex-shrink-0 bg-[#2a2a2a] relative">
                      {isImage ? (
                        <img src={file.previewUrl} alt="preview" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          {isVideo ? <VideoIcon className="w-7 h-7 text-blue-400" /> :
                           isAudio ? <AudioIcon className="w-7 h-7 text-purple-400" /> :
                           isPdf ? <PdfIcon className="w-7 h-7 text-red-400" /> :
                           <FileIcon className="w-7 h-7 text-gray-400" />}
                        </div>
                      )}
                      
                      {/* 加载/进度遮罩 */}
                      {file.status === 'uploading' && (
                        <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                          <Loader2 className="w-5 h-5 text-white animate-spin" />
                        </div>
                      )}
                    </div>
                    
                    {/* 文件名部分 (图片也显示文件名，统一风格) */}
                    <div className="flex flex-col justify-center max-w-[120px] min-w-[60px]">
                      <span className="text-[12px] text-text-primary truncate font-medium">
                        {file.file.name}
                      </span>
                      <span className="text-[10px] text-text-quaternary uppercase tracking-wider">
                        {file.file.name.split('.').pop() || 'FILE'}
                      </span>
                    </div>
                    
                    {/* 删除按钮 */}
                    <button 
                      onClick={() => removeFile(file.id)}
                      className="absolute top-1 right-1 p-1 rounded-full bg-black/50 text-white hover:bg-red-500/80 transition-colors opacity-0 group-hover/file:opacity-100"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          {/* 文本输入区 */}
          <div className="flex flex-col px-5 pt-3.5 pb-0">
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              placeholder="Ask anything..."
              className="w-full bg-transparent border-none focus:border-none focus:ring-0 focus:outline-none resize-none p-0 text-text-primary placeholder:text-text-quaternary text-[15px] max-h-[160px] leading-relaxed scrollbar-none min-h-[24px] selection:bg-primary/30"
              style={{ boxShadow: 'none', border: 'none', outline: 'none' }}
            />
          </div>

          {/* 底部操作区 */}
          <div className="flex items-center justify-between px-2 md:px-4 pb-2 gap-2">
            {/* 左侧附件按钮 */}
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="p-1.5 rounded-lg hover:bg-white/5 text-text-tertiary hover:text-text-primary transition-all active:scale-90 flex-shrink-0"
            >
              <Plus className="w-4 h-4" />
            </button>
            
            {/* 中间功能区 - 支持横向滚动，但在大屏上移除 overflow 和遮罩以防裁剪绝对定位的下拉框 */}
            <div className="flex-1 overflow-x-auto sm:overflow-visible scrollbar-none mask-linear-fade sm:mask-none min-w-0">
              <div className="flex items-center gap-1 md:gap-2 w-max px-1">
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setShowThinkingDropdown(!showThinkingDropdown)}
                    className={`flex items-center gap-1.5 px-2 md:px-3 py-1.5 rounded-lg text-[11px] md:text-[13px] font-bold tracking-tight transition-all duration-300 min-w-fit whitespace-nowrap ${
                      thinkingMode === 'deep' 
                        ? 'bg-primary/10 text-primary' 
                        : 'text-text-quaternary hover:bg-white/5 hover:text-text-primary'
                    }`}
                  >
                    <CurrentIcon className={`w-3.5 h-3.5 md:w-4 md:h-4 flex-shrink-0 ${thinkingMode === 'deep' ? 'animate-pulse' : ''}`} />
                    <span className="inline whitespace-nowrap">{currentOption.label}</span>
                  </button>
                  
                  {showThinkingDropdown && (
                    <div className="fixed sm:absolute sm:bottom-full bottom-[80px] left-[5vw] sm:left-0 mb-2 w-[90vw] sm:w-36 md:w-48 bg-[#161616] border border-white/10 rounded-2xl shadow-2xl p-1.5 animate-in fade-in slide-in-from-bottom-2 duration-200 z-[9999] sm:translate-x-0 sm:mb-2 sm:transform-none">
                      {thinkingOptions.map((option) => {
                        const Icon = option.icon;
                        return (
                          <button
                            key={option.value}
                            onClick={() => {
                              setThinkingMode(option.value);
                              setShowThinkingDropdown(false);
                            }}
                            className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-[12px] md:text-[13px] transition-all duration-200 ${
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
                  className={`flex items-center gap-1.5 px-2 md:px-3 py-1.5 rounded-lg text-[11px] md:text-[13px] font-bold tracking-tight transition-all duration-300 min-w-fit whitespace-nowrap ${
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
                    <Loader2 className="w-3.5 h-3.5 md:w-4 md:h-4 flex-shrink-0 animate-spin" />
                  ) : toolServices.length === 0 ? (
                    <Globe className="w-3.5 h-3.5 md:w-4 md:h-4 flex-shrink-0 opacity-50" />
                  ) : (
                    <Globe className="w-3.5 h-3.5 md:w-4 md:h-4 flex-shrink-0" />
                  )}
                  <span className="inline whitespace-nowrap">
                    {isLoadingTools ? 'Loading...' : toolServices.length === 0 ? 'Retry' : 'Web'}
                  </span>
                </button>

                {/* 知识库选择按钮 */}
                <div className="relative" ref={knowledgeDropdownRef}>
                  <button
                    onClick={() => setShowKnowledgeDropdown(!showKnowledgeDropdown)}
                    className={`flex items-center gap-1.5 px-2 md:px-3 py-1.5 rounded-lg text-[11px] md:text-[13px] font-bold tracking-tight transition-all duration-300 min-w-fit whitespace-nowrap ${
                      hasSelectedKnowledge
                        ? 'bg-primary/10 text-primary'
                        : 'text-text-quaternary hover:bg-white/5 hover:text-text-primary'
                    }`}
                    title={hasSelectedKnowledge ? `已选择 ${selectedKnowledgeIds.length} 个知识库` : '点击选择知识库'}
                  >
                    <BookOpen className="w-3.5 h-3.5 md:w-4 md:h-4 flex-shrink-0" />
                    <span className="inline whitespace-nowrap">
                      {hasSelectedKnowledge ? `知识库 (${selectedKnowledgeIds.length})` : '知识库'}
                    </span>
                  </button>

                  {showKnowledgeDropdown && (
                    <div className="fixed sm:absolute sm:bottom-full bottom-[80px] left-[5vw] sm:left-auto sm:right-0 mb-2 w-[90vw] sm:w-[280px] md:w-[320px] bg-[#161616] border border-white/10 rounded-2xl shadow-2xl p-1.5 animate-in fade-in slide-in-from-bottom-2 duration-200 z-[9999] flex flex-col h-[160px] sm:h-[200px] sm:translate-x-0 sm:mb-2 sm:transform-none">
                      <div className="px-2 py-2 border-b border-white/10 flex-shrink-0 flex items-center justify-between">
                        <p className="text-xs text-text-tertiary">选择要检索的知识库</p>
                        {knowledgeBases.length > 0 && (
                          <button
                            onClick={() => {
                              if (selectedKnowledgeIds.length === knowledgeBases.length) {
                                setSelectedKnowledgeIds([]);
                              } else {
                                setSelectedKnowledgeIds(knowledgeBases.map(kb => kb.id));
                              }
                            }}
                            className="text-[10px] text-primary hover:text-primary-hover transition-colors"
                          >
                            {selectedKnowledgeIds.length === knowledgeBases.length ? '取消全选' : '全选'}
                          </button>
                        )}
                      </div>
                      <div className="overflow-y-scroll overflow-x-scroll flex-1 min-h-0 dropdown-scrollbar [scrollbar-gutter:stable_both-edges]" style={{ touchAction: 'pan-x pan-y' }}>
                        {knowledgeBases.length === 0 ? (
                          <div className="px-3 py-4 text-center">
                            <p className="text-xs text-text-tertiary">暂无知识库</p>
                            <p className="text-[10px] text-text-quaternary mt-1">请先在知识库管理页面创建</p>
                          </div>
                        ) : (
                          <div className="py-1 min-w-max">
                            {knowledgeBases.map((kb) => (
                              <button
                                key={kb.id}
                                onClick={() => toggleKnowledgeSelection(kb.id)}
                                className={`min-w-full w-max flex items-center gap-2 px-2 py-2 rounded-xl text-[13px] transition-all duration-200 ${
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
                              <span className="whitespace-nowrap text-left flex-1 pr-4 min-w-max">{kb.name}</span>
                            </button>
                          ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 右侧发送与语音 - 圆形按钮风格 */}
            <div className="flex items-center gap-1 flex-shrink-0 pl-1">
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
