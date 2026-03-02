import { Message } from '@/types/chat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, ChevronDown, Bot, User, Loader2, Sparkles, ChevronRight, Ban, BookOpen, Globe } from 'lucide-react';
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
        customStyle={{ margin: '0', borderRadius: '0.5rem', background: 'transparent' }}
      />
    </div>
  );
};

const MessageItem = ({ message }: MessageItemProps) => {
  const [copied, setCopied] = useState(false);
  const [showReferences, setShowReferences] = useState(true);
  const [showReasoning, setShowReasoning] = useState(false);

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
    <div className={`w-full py-4 sm:py-6 transition-colors ${isUser ? '' : ''}`}>
      <div className={`max-w-6xl mx-auto px-4 md:px-12 flex gap-4 md:gap-6 ${isUser ? 'flex-row-reverse' : ''}`}>
        {/* 头像 - Grok 风格：高级感艺术化 */}
        <div className="flex-shrink-0 mt-0.5">
          {isUser ? (
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#6366f1] via-[#a855f7] to-[#ec4899] flex items-center justify-center shadow-xl shadow-indigo-500/10 border border-white/10 transform hover:scale-105 transition-transform duration-300">
              <User className="w-5 h-5 text-white" />
            </div>
          ) : (
            <div className="w-9 h-9 rounded-xl gemini-gradient p-[1.5px] shadow-xl shadow-primary/10 transform hover:scale-105 transition-transform duration-300">
              <div className="w-full h-full rounded-xl bg-[#1E1E1E] flex items-center justify-center border border-white/5">
                <Sparkles className="w-4.5 h-4.5 text-primary" />
              </div>
            </div>
          )}
        </div>

        {/* 消息主体 */}
        <div className={`flex flex-col min-w-0 flex-1 ${isUser ? 'items-end' : 'items-start'}`}>
          {isThinking ? (
            <div className="flex items-center gap-3 text-text-tertiary px-5 py-3 bg-white/[0.03] backdrop-blur-xl rounded-2xl border border-white/[0.05] shadow-2xl">
              <div className="relative">
                <Loader2 className="w-4.5 h-4.5 animate-spin text-primary" />
                <div className="absolute inset-0 bg-primary/40 blur-lg rounded-full animate-pulse" />
              </div>
              <span className="text-xs font-bold tracking-[0.2em] uppercase opacity-50">Synthesizing</span>
            </div>
          ) : (
            <div className={`w-full flex flex-col gap-3 ${isUser ? 'items-end' : 'items-start'}`}>
              {/* 推理框 - 更加透明、更明显 */}
              {hasReasoning && (
                <div className="w-full max-w-[90%]">
                  <div className="bg-white/[0.02] backdrop-blur-md border border-white/[0.05] rounded-2xl overflow-hidden transition-all duration-500 shadow-xl">
                    <button
                      onClick={() => setShowReasoning(!showReasoning)}
                      className="w-full flex items-center justify-between gap-2.5 px-5 py-2.5 hover:bg-white/[0.03] transition-colors group"
                    >
                      <div className="flex items-center gap-2.5">
                        <div className={`w-5 h-5 rounded-lg flex items-center justify-center border border-white/10 bg-white/[0.05] group-hover:bg-white/[0.1] transition-colors shadow-inner`}>
                          <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-500 ${showReasoning ? 'rotate-180' : ''}`} />
                        </div>
                        <span className="font-bold tracking-widest text-[10px] uppercase opacity-40 group-hover:opacity-70 transition-opacity">Thought process</span>
                      </div>
                    </button>
                    
                    {showReasoning && (
                      <div className="px-6 pb-5 max-h-48 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent animate-in fade-in slide-in-from-top-2 duration-500">
                        <div className="text-[13.5px] text-text-tertiary/80 whitespace-pre-wrap font-mono leading-relaxed prose prose-invert prose-sm max-w-none italic opacity-90 border-t border-white/[0.03] pt-4">
                          <ReactMarkdown 
                            children={message.reasoning} 
                            remarkPlugins={[remarkGfm]}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 内容气泡 - 采用半透明“磨砂玻璃”质感，优雅悬浮 */}
              <div className={`
                ${isUser 
                  ? 'bg-white/[0.04] backdrop-blur-2xl border border-white/[0.08] shadow-[0_8px_32px_rgba(0,0,0,0.3)] rounded-[24px] rounded-tr-[4px] px-6 py-4 text-text-primary max-w-[85%] text-left font-medium' 
                  : 'bg-primary/[0.02] backdrop-blur-3xl border border-white/[0.05] shadow-[0_8px_32px_rgba(0,0,0,0.2)] rounded-[24px] rounded-tl-[4px] px-6 py-4 text-text-primary w-full'
                }
              `}>
                <div className={`prose max-w-none ${isUser ? 'prose-invert' : 'prose-p:text-text-primary prose-strong:text-white prose-code:text-primary'}`}>
                  <ReactMarkdown
                    children={message.content}
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code({ node, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '');
                        const inline = !match;
                        return inline ? (
                          <code className={`px-1.5 py-0.5 rounded-md bg-white/[0.05] text-primary text-[13px] border border-white/[0.05] font-mono`} {...props}>
                            {children}
                          </code>
                        ) : (
                          <div className="my-8 rounded-3xl overflow-hidden border border-white/[0.05] bg-black/40 backdrop-blur-md shadow-2xl group/code">
                            <div className="flex items-center justify-between px-6 py-3 bg-white/[0.02] border-b border-white/[0.02]">
                              <span className="text-[10px] text-text-quaternary font-mono uppercase tracking-[0.2em]">{match[1]}</span>
                              <button 
                                onClick={() => navigator.clipboard.writeText(String(children))}
                                className="text-[10px] text-text-quaternary hover:text-text-secondary flex items-center gap-2 transition-colors uppercase font-bold tracking-wider"
                              >
                                <Copy className="w-3.5 h-3.5" />
                                <span>Copy</span>
                              </button>
                            </div>
                            <div className="p-6 overflow-x-auto text-[14.5px]">
                              <SyntaxHighlighter
                                children={String(children).replace(/\n$/, '')}
                                style={oneDark as any}
                                language={match[1]}
                                PreTag="div"
                                customStyle={{ margin: '0', background: 'transparent', padding: '0' }}
                              />
                            </div>
                          </div>
                        );
                      },
                      p: ({ node, ...props }) => <p className={`my-4 leading-relaxed text-[16.5px] tracking-wide`} {...props} />,
                      ul: ({ node, ...props }) => <ul className="list-disc my-6 pl-8 space-y-3.5" {...props} />,
                      ol: ({ node, ...props }) => <ol className="list-decimal my-6 pl-8 space-y-3.5" {...props} />,
                      li: ({ node, ...props }) => <li className="my-2 text-text-secondary leading-relaxed" {...props} />,
                      h1: ({ node, ...props }) => <h1 className="text-2xl font-black my-10 text-white tracking-tight leading-tight" {...props} />,
                      h2: ({ node, ...props }) => <h2 className="text-xl font-bold my-8 text-white tracking-tight leading-tight" {...props} />,
                      h3: ({ node, ...props }) => <h3 className="text-lg font-bold my-6 text-white" {...props} />,
                      blockquote: ({ node, ...props }) => (
                        <blockquote className="border-l-4 border-primary/20 pl-6 my-8 italic text-text-tertiary bg-white/[0.02] py-3 rounded-r-3xl" {...props} />
                      ),
                      a: ({ node, ...props }) => (
                        <a 
                          {...props} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-primary hover:text-primary-hover underline underline-offset-4 transition-all font-bold"
                        />
                      ),
                    }}
                  />
                </div>
              </div>

              {/* 操作栏 */}
              {!isUser && (
                <div className="flex items-center gap-6 mt-1 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-1 group-hover:translate-y-0">
                  <button
                    onClick={handleCopy}
                    className="text-text-quaternary hover:text-text-secondary transition-colors p-1 hover:bg-white/5 rounded-lg"
                    title="Copy"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                  <span className="text-[9px] text-text-quaternary font-mono tracking-tighter opacity-50">
                    {format(message.timestamp, 'HH:mm')}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageItem;
