import { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Paperclip, Globe, Sparkles, ChevronDown, Zap, Ban, Square, Plus } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';

interface InputAreaProps {
  onSend: (content: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  isStreaming?: boolean;
}

const thinkingOptions = [
  { value: 'auto', label: '自动', icon: Sparkles },
  { value: 'deep', label: '深度思考', icon: Zap },
  { value: 'false', label: '关闭思考', icon: Ban },
] as const;

const InputArea = ({ onSend, onStop, disabled, isStreaming }: InputAreaProps) => {
  const [content, setContent] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isWebSearch, setIsWebSearch] = useState(false);
  const [showThinkingDropdown, setShowThinkingDropdown] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const thinkingMode = useChatStore((state) => state.thinkingMode);
  const setThinkingMode = useChatStore((state) => state.setThinkingMode);
  
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
    <div className="w-full max-w-[1400px] relative px-6 md:px-8">
      {/* 输入框主体 - 极致纤长且扁平的"指挥棒"感 */}
      <div className="relative group gemini-aura">
        <div className={`
          relative flex flex-col w-full
          bg-[#1E1E1E] transition-all duration-500
          rounded-[20px] overflow-visible
          ${isStreaming ? 'ring-[0.5px] ring-primary/20' : ''}
        `}>
          {/* 文本输入区 - 纵向极致压缩 50% */}
          <div className="flex flex-col px-5 pt-4 pb-0.5">
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything..."
              className="w-full bg-transparent border-none focus:border-none focus:ring-0 focus:outline-none resize-none p-0 text-text-primary placeholder:text-text-quaternary text-[15px] max-h-[160px] leading-relaxed scrollbar-none min-h-[32px] selection:bg-primary/30"
              style={{ boxShadow: 'none', border: 'none', outline: 'none' }}
            />
          </div>

          {/* 底部操作区 - 纵向极度紧凑 */}
          <div className="flex items-center justify-between px-4 pb-2">
            <div className="flex items-center gap-2">
              {/* 左侧附件按钮 - 极小化 */}
              <button className="p-1.5 rounded-lg hover:bg-white/5 text-text-tertiary hover:text-text-primary transition-all active:scale-90">
                <Plus className="w-4 h-4" />
              </button>
              
              {/* 思考模式与搜索 - 极简扁平 */}
              <div className="flex items-center gap-2">
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setShowThinkingDropdown(!showThinkingDropdown)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-bold tracking-tight transition-all duration-300 ${
                      thinkingMode === 'deep' 
                        ? 'bg-primary/10 text-primary' 
                        : 'text-text-quaternary hover:bg-white/5 hover:text-text-primary'
                    }`}
                  >
                    <CurrentIcon className={`w-4 h-4 ${thinkingMode === 'deep' ? 'animate-pulse' : ''}`} />
                    <span>{currentOption.label}</span>
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
                            <Icon className="w-4 h-4" />
                            {option.label}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>

                <button
                  onClick={() => setIsWebSearch(!isWebSearch)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-bold tracking-tight transition-all duration-300 ${
                    isWebSearch 
                      ? 'bg-primary/10 text-primary' 
                      : 'text-text-quaternary hover:bg-white/5 hover:text-text-primary'
                  }`}
                >
                  <Globe className="w-4 h-4" />
                  <span>Search</span>
                </button>
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
      <div className="mt-2.5 flex justify-center">
        <p className="text-[10px] text-text-quaternary font-medium tracking-wide opacity-60">
          JeikChat can make mistakes. Check important info.
        </p>
      </div>
    </div>
  );
};

export default InputArea;
