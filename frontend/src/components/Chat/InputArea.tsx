import { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Paperclip, Globe, Sparkles, ChevronDown, Zap, Ban, Square } from 'lucide-react';
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
    <div className="w-full max-w-4xl mx-auto px-4 pb-6 pt-2">
      {/* 功能按钮栏 */}
      <div className="flex items-center justify-between mb-3 px-1 gap-2">
        <div className="flex items-center gap-1 flex-wrap sm:flex-nowrap">
          <button
            onClick={() => setIsWebSearch(!isWebSearch)}
            className={`flex items-center gap-1.5 px-2 sm:px-3 py-1.5 text-xs rounded-full transition-all duration-200 whitespace-nowrap ${
              isWebSearch 
                ? 'bg-primary text-white' 
                : 'bg-bg-tertiary text-text-secondary hover:bg-bg-secondary hover:text-text-primary'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">联网搜索</span>
          </button>
          
          <button
            onClick={() => setIsRecording(!isRecording)}
            className={`flex items-center gap-1.5 px-2 sm:px-3 py-1.5 text-xs rounded-full transition-all duration-200 whitespace-nowrap ${
              isRecording 
                ? 'bg-error text-white' 
                : 'bg-bg-tertiary text-text-secondary hover:bg-bg-secondary hover:text-text-primary'
            }`}
          >
            {isRecording ? (
              <>
                <MicOff className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">关闭</span>
              </>
            ) : (
              <>
                <Mic className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">语音</span>
              </>
            )}
          </button>

          <button
            className="flex items-center gap-1.5 px-2 sm:px-3 py-1.5 text-xs rounded-full bg-bg-tertiary text-text-secondary hover:bg-bg-secondary hover:text-text-primary transition-all duration-200 whitespace-nowrap"
          >
            <Paperclip className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">附件</span>
          </button>
        </div>

        {/* 思考模式选择器 */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowThinkingDropdown(!showThinkingDropdown)}
            className="flex items-center gap-1.5 px-2 sm:px-3 py-1.5 text-xs rounded-full bg-bg-tertiary text-text-secondary hover:bg-bg-secondary hover:text-text-primary transition-all duration-200 whitespace-nowrap"
          >
            <CurrentIcon className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{currentOption.label}</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${showThinkingDropdown ? 'rotate-180' : ''}`} />
          </button>
          
          {showThinkingDropdown && (
            <div className="absolute right-0 top-full mt-1 py-1 bg-bg-secondary border border-border rounded-lg shadow-lg z-50 min-w-[120px]">
              {thinkingOptions.map((option) => {
                const Icon = option.icon;
                return (
                  <button
                    key={option.value}
                    onClick={() => {
                      setThinkingMode(option.value);
                      setShowThinkingDropdown(false);
                    }}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-xs transition-colors ${
                      thinkingMode === option.value
                        ? 'bg-primary/10 text-primary'
                        : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {option.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* 输入框 */}
      <div className="relative">
        <div className="relative border border-border rounded-2xl bg-bg-secondary overflow-hidden focus-within:border-primary/50 focus-within:shadow-[0_0_0_1px_rgba(99,102,241,0.1)] transition-all duration-200">
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isStreaming ? "正在生成回答..." : "发送消息..."}
            disabled={disabled}
            className="w-full resize-none bg-transparent py-3.5 pl-4 pr-12 focus:outline-none text-[15px] leading-relaxed text-text-primary placeholder-text-quaternary max-h-40"
            rows={1}
          />
          
          <button
            onClick={isStreaming ? onStop : handleSubmit}
            disabled={isStreaming ? false : (!content.trim() || disabled)}
            className={`absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-all duration-200 ${
              isStreaming 
                ? 'bg-error text-white hover:bg-red-600' 
                : (content.trim() && !disabled
                  ? 'bg-primary text-white hover:bg-primary-hover' 
                  : 'bg-bg-tertiary text-text-quaternary')
            }`}
          >
            {isStreaming ? <Square className="w-4 h-4" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>
      
      <p className="text-center text-xs text-text-quaternary mt-2">
        AI 可能会产生错误信息，请核实重要内容
      </p>
    </div>
  );
};

export default InputArea;