import { Message } from '@/types/chat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, ChevronDown, Bot, User, Loader2, Sparkles, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

function hasSourceProperty(obj: any): obj is { source: any } {
  return 'source' in obj;
}

interface MessageItemProps {
  message: Message;
}

const CodeBlock = ({ language, children }: { language: string; children: string }) => {
  const [copied, setCopied] = useState(false);
  const codeContent = String(children).replace(/\n$/, '');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('复制失败:', err);
    }
  };

  return (
    <div className="relative group">
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 flex items-center gap-1 px-2 py-1 text-xs bg-bg-tertiary hover:bg-border rounded opacity-0 group-hover:opacity-100 transition-opacity z-10"
      >
        {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
        {copied ? '已复制' : '复制'}
      </button>
      <SyntaxHighlighter
        children={codeContent}
        style={oneDark as any}
        language={language}
        PreTag="div"
        customStyle={{ margin: '0.5rem 0', borderRadius: '0.5rem' }}
      />
    </div>
  );
};

const MessageItem = ({ message }: MessageItemProps) => {
  const [copied, setCopied] = useState(false);
  const [showReferences, setShowReferences] = useState(true);
  const [showReasoning, setShowReasoning] = useState(true);

  const isUser = message.role === 'user';
  const isThinking = message.thinking && !message.content;
  const hasReasoning = message.reasoning && message.reasoning.length > 0;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('复制失败:', err);
    }
  };

  return (
    <div className={`flex gap-4 px-4 md:px-12 py-3 items-center ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser 
          ? 'bg-gradient-to-r from-primary to-purple-500' 
          : 'bg-gradient-to-br from-primary to-purple-500'
      }`}>
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>

      <div className={`${isUser ? 'max-w-[70%]' : 'max-w-[80%]'} ${isUser ? 'flex justify-end' : ''}`}>
        {isThinking ? (
          <div className={`rounded-2xl px-4 py-3 ${
            isUser 
              ? 'bg-gradient-to-r from-primary to-purple-500 text-white shadow-lg shadow-primary/20 rounded-tr-sm' 
              : 'bg-bg-secondary border border-border rounded-tl-sm'
          }`}>
            <div className="flex items-center gap-2 text-text-tertiary">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>正在思考...</span>
            </div>
          </div>
        ) : (
          <div>
            {hasReasoning && (
              <div className="mb-2">
                {message.thinking ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs text-amber-500">
                      <Sparkles className="w-3.5 h-3.5 animate-pulse" />
                      <span>正在思考中...</span>
                    </div>
                    <div className="px-4 py-3 rounded-xl border border-amber-500/20 bg-amber-500/5">
                      <div className="text-xs text-text-tertiary whitespace-pre-wrap font-mono leading-relaxed">
                        {message.reasoning}
                      </div>
                    </div>
                  </div>
                ) : showReasoning ? (
                  <div>
                    <button
                      onClick={() => setShowReasoning(false)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors bg-bg-tertiary/60 hover:bg-bg-tertiary rounded-lg"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                      <span>深度思考</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                    <div className="mt-2 px-4 py-3 rounded-xl border border-border/20">
                      <div className="text-xs text-text-tertiary whitespace-pre-wrap font-mono leading-relaxed">
                        {message.reasoning}
                      </div>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowReasoning(true)}
                    className="flex items-center gap-2 px-3 py-2 text-xs text-text-secondary hover:text-text-primary transition-colors bg-bg-tertiary/40 hover:bg-bg-tertiary/60 rounded-lg border border-border/10"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                    <span className="font-medium">深度思考</span>
                    <span className="text-text-quaternary">·</span>
                    <span className="text-text-tertiary line-clamp-1 max-w-[200px]">
                      {message.reasoning.slice(-100)}
                    </span>
                  </button>
                )}
              </div>
            )}
            <div className={`rounded-2xl px-4 py-3 ${
              isUser 
                ? 'bg-gradient-to-r from-primary to-purple-500 text-white shadow-lg shadow-primary/20 rounded-tr-sm' 
                : 'bg-bg-secondary border border-border rounded-tl-sm'
            }`}>
              <div className={`prose ${isUser ? 'prose-invert' : ''} max-w-none`}>
                <ReactMarkdown
                  children={message.content}
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ node, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      const inline = !match;
                      return inline ? (
                        <code className={`${className || ''} px-1.5 py-0.5 rounded ${isUser ? 'bg-white/20' : 'bg-bg-tertiary'}`} {...props}>
                          {children}
                        </code>
                      ) : (
                        <CodeBlock language={match[1]}>
                          {String(children).replace(/\n$/, '')}
                        </CodeBlock>
                      );
                    },
                    a: ({ node, ...props }) => (
                      <a 
                        {...props} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className={`${isUser ? 'text-white underline' : 'text-primary hover:underline'}`}
                      />
                    ),
                    p: ({ node, ...props }) => <p className={`my-1.5 ${isUser ? '' : 'text-text-primary'}`} {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc my-2 pl-5" {...props} />,
                    ol: ({ node, ...props }) => <ol className="list-decimal my-2 pl-5" {...props} />,
                    li: ({ node, ...props }) => <li className="my-1" {...props} />,
                    strong: ({ node, ...props }) => <strong className="font-semibold" {...props} />,
                    em: ({ node, ...props }) => <em className="italic" {...props} />,
                    blockquote: ({ node, ...props }) => (
                      <blockquote 
                        className={`border-l-4 pl-4 my-2 ${isUser ? 'border-white/30 text-white/90' : 'border-primary/50 text-text-secondary'}`} 
                        {...props} 
                      />
                    ),
                  }}
                />
              </div>

              {message.references && message.references.length > 0 && (
                <div className="mt-3 pt-3 border-t border-border/50">
                  <button
                    onClick={() => setShowReferences(!showReferences)}
                    className={`flex items-center gap-2 text-xs ${isUser ? 'text-white/70 hover:text-white' : 'text-text-tertiary hover:text-text-primary'} transition-colors`}
                  >
                    <ChevronDown className={`w-3 h-3 transition-transform ${showReferences ? 'rotate-180' : ''}`} />
                    参考资料 ({message.references.length})
                  </button>
                  
                  {showReferences && (
                    <div className="mt-2 space-y-2">
                      {message.references.map((ref, idx) => (
                        <div key={idx} className={`text-xs p-2 rounded-lg ${isUser ? 'bg-white/10' : 'bg-bg-tertiary'}`}>
                          <p className={isUser ? 'text-white/90' : 'text-text-secondary'}>{ref.content}</p>
                          {hasSourceProperty(ref) && ref.source && <p className={`mt-1 ${isUser ? 'text-white/50' : 'text-text-tertiary'}`}>来源: {typeof ref.source === 'string' ? ref.source : String(ref.source)}</p>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {!isUser && (
                <div className="flex items-center gap-3 mt-2 ml-1">
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-1 text-xs text-text-tertiary hover:text-text-primary transition-colors"
                  >
                    {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    {copied ? '已复制' : '复制'}
                  </button>
                  {message.isCancelled && (
                    <span className="text-xs text-amber-500 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                      生成已停止
                    </span>
                  )}
                  <span className="text-xs text-text-tertiary">
                    {format(message.timestamp, 'HH:mm', { locale: zhCN })}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageItem;
