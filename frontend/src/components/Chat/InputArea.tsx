import { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Paperclip, Globe } from 'lucide-react';

interface InputAreaProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

const InputArea = ({ onSend, disabled }: InputAreaProps) => {
  const [content, setContent] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isWebSearch, setIsWebSearch] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [content]);

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
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsWebSearch(!isWebSearch)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-full transition-all duration-200 ${
              isWebSearch 
                ? 'bg-primary text-white' 
                : 'bg-bg-tertiary text-text-secondary hover:bg-bg-secondary hover:text-text-primary'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>联网搜索</span>
          </button>
          
          <button
            onClick={() => setIsRecording(!isRecording)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-full transition-all duration-200 ${
              isRecording 
                ? 'bg-error text-white' 
                : 'bg-bg-tertiary text-text-secondary hover:bg-bg-secondary hover:text-text-primary'
            }`}
          >
            {isRecording ? (
              <>
                <MicOff className="w-3.5 h-3.5" />
                <span>关闭麦克风</span>
              </>
            ) : (
              <>
                <Mic className="w-3.5 h-3.5" />
                <span>语音输入</span>
              </>
            )}
          </button>

          <button
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-full bg-bg-tertiary text-text-secondary hover:bg-bg-secondary hover:text-text-primary transition-all duration-200"
          >
            <Paperclip className="w-3.5 h-3.5" />
            <span>附件</span>
          </button>
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
            placeholder="发送消息..."
            disabled={disabled}
            className="w-full resize-none bg-transparent py-3.5 pl-4 pr-12 focus:outline-none text-[15px] leading-relaxed text-text-primary placeholder-text-quaternary max-h-40"
            rows={1}
          />
          
          <button
            onClick={handleSubmit}
            disabled={!content.trim() || disabled}
            className={`absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-all duration-200 ${
              content.trim() && !disabled
                ? 'bg-primary text-white hover:bg-primary-hover' 
                : 'bg-bg-tertiary text-text-quaternary'
            }`}
          >
            <Send className="w-4 h-4" />
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