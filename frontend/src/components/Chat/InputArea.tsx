import { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Paperclip, Globe, Square, Brain, ChevronDown, Check } from 'lucide-react';

type ReasoningMode = 'auto' | true | false;

interface InputAreaProps {
  onSend: (content: string, reasoning?: ReasoningMode) => void;
  onStop?: () => void;
  disabled?: boolean;
  isGenerating?: boolean;
}

const InputArea = ({ onSend, onStop, disabled, isGenerating }: InputAreaProps) => {
  const [content, setContent] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isWebSearch, setIsWebSearch] = useState(false);
  const [reasoningMode, setReasoningMode] = useState<ReasoningMode>('auto');
  const [showReasoningDropdown, setShowReasoningDropdown] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [content]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowReasoningDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = () => {
    if (content.trim() && !disabled) {
      onSend(content, reasoningMode);
      setContent('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const getReasoningLabel = (mode: ReasoningMode) => {
    if (mode === 'auto') return '自动';
    if (mode === true) return '开启';
    return '关闭';
  };

  const getReasoningIcon = (mode: ReasoningMode) => {
    return <Brain className={`w-3.5 h-3.5 ${mode === 'auto' ? 'text-amber-500' : mode ? 'text-green-500' : 'text-red-500'}`} />;
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-6 pt-2">
      <div className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-primary via-purple-500 to-pink-500 rounded-2xl blur opacity-20 group-hover:opacity-30 transition-opacity duration-300"></div>
        <div className="relative bg-bg-secondary/95 backdrop-blur-md border border-border/60 rounded-2xl p-4 shadow-2xl shadow-black/20">
          <div className="flex items-center justify-between mb-3 px-1 gap-2">
            <div className="flex items-center gap-1 flex-wrap sm:flex-nowrap">
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setShowReasoningDropdown(!showReasoningDropdown)}
                  className={`flex items-center gap-1.5 px-2 sm:px-3 py-1.5 text-xs rounded-full transition-all duration-200 whitespace-nowrap ${
                    reasoningMode !== 'auto' 
                      ? reasoningMode === true 
                        ? 'bg-green-500/20 text-green-600 dark:text-green-400 border border-green-500/30'
                        : 'bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/30'
                      : 'bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {getReasoningIcon(reasoningMode)}
                  <span className="hidden sm:inline">{getReasoningLabel(reasoningMode)}</span>
                  <ChevronDown className={`w-3 h-3 transition-transform ${showReasoningDropdown ? 'rotate-180' : ''}`} />
                </button>
                
                {showReasoningDropdown && (
                  <div className="absolute top-full left-0 mt-1 bg-bg-secondary border border-border rounded-lg shadow-lg py-1 z-50 min-w-[160px] sm:min-w-[140px]">
                    <button
                      onClick={() => { setReasoningMode('auto'); setShowReasoningDropdown(false); }}
                      className={`w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-bg-tertiary transition-colors whitespace-nowrap ${
                        reasoningMode === 'auto' ? 'text-amber-600 dark:text-amber-400 font-medium' : 'text-text-secondary'
                      }`}
                    >
                      {reasoningMode === 'auto' && <Check className="w-3 h-3" />}
                      <Brain className="w-3.5 h-3.5 text-amber-500" />
                      <span className="truncate">自动</span>
                    </button>
                    <button
                      onClick={() => { setReasoningMode(true); setShowReasoningDropdown(false); }}
                      className={`w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-bg-tertiary transition-colors whitespace-nowrap ${
                        reasoningMode === true ? 'text-green-600 dark:text-green-400 font-medium' : 'text-text-secondary'
                      }`}
                    >
                      {reasoningMode === true && <Check className="w-3 h-3" />}
                      <Brain className="w-3.5 h-3.5 text-green-500" />
                      <span className="truncate">开启深度思考</span>
                    </button>
                    <button
                      onClick={() => { setReasoningMode(false); setShowReasoningDropdown(false); }}
                      className={`w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-bg-tertiary transition-colors whitespace-nowrap ${
                        reasoningMode === false ? 'text-red-600 dark:text-red-400 font-medium' : 'text-text-secondary'
                      }`}
                    >
                      {reasoningMode === false && <Check className="w-3 h-3" />}
                      <Brain className="w-3.5 h-3.5 text-red-500" />
                      <span className="truncate">关闭深度思考</span>
                    </button>
                  </div>
                )}
              </div>

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
          </div>

          <div className="flex items-end gap-3">
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息..."
              disabled={disabled}
              className="flex-1 min-h-[44px] max-h-32 px-4 py-2.5 bg-bg-primary/60 border border-border/40 rounded-xl resize-none focus:outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/15 transition-all duration-200 text-text-primary placeholder-text-tertiary disabled:opacity-50 disabled:cursor-not-allowed shadow-inner"
              rows={1}
            />
            
            {isGenerating ? (
              <button
                onClick={onStop}
                className="flex-shrink-0 w-10 h-10 bg-error/90 hover:bg-error text-white rounded-xl flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Square className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={disabled || !content.trim()}
                className="flex-shrink-0 w-10 h-10 bg-primary/90 hover:bg-primary text-white rounded-xl flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
          
          <p className="text-center text-xs text-text-quaternary mt-2">
            AI 可能会产生错误信息，请核实重要内容
          </p>
        </div>
      </div>
    </div>
  );
};

export default InputArea;
