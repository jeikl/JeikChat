import { Message } from '@/types/chat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { Copy, Check, ChevronDown, Bot, User, Loader2, Sparkles, ChevronRight, Ban, BookOpen, Globe, RotateCcw, ThumbsUp, ThumbsDown } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

// 自定义简洁代码块主题 - 无背景色
const customCodeTheme = {
  'code[class*="language-"]': {
    color: '#e5e7eb',
    background: 'transparent',
    textShadow: 'none',
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
    fontSize: '14px',
    lineHeight: '1.5',
  },
  'pre[class*="language-"]': {
    color: '#e5e7eb',
    background: 'transparent',
    textShadow: 'none',
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
    fontSize: '14px',
    lineHeight: '1.5',
    margin: '0',
    padding: '0',
    borderRadius: '0',
  },
  'pre': {
    background: 'transparent',
  },
  'code': {
    background: 'transparent',
  },
  'comment': { color: '#6b7280' },
  'block-comment': { color: '#6b7280' },
  'prolog': { color: '#6b7280' },
  'doctype': { color: '#6b7280' },
  'cdata': { color: '#6b7280' },
  'punctuation': { color: '#9ca3af' },
  'property': { color: '#60a5fa' },
  'tag': { color: '#f472b6' },
  'boolean': { color: '#f472b6' },
  'number': { color: '#f472b6' },
  'constant': { color: '#f472b6' },
  'symbol': { color: '#f472b6' },
  'deleted': { color: '#f472b6' },
  'selector': { color: '#34d399' },
  'attr-name': { color: '#fbbf24' },
  'string': { color: '#34d399' },
  'char': { color: '#34d399' },
  'builtin': { color: '#f472b6' },
  'inserted': { color: '#34d399' },
  'operator': { color: '#9ca3af' },
  'entity': { color: '#60a5fa' },
  'url': { color: '#60a5fa' },
  'variable': { color: '#e5e7eb' },
  'attr-value': { color: '#34d399' },
  'keyword': { color: '#c084fc' },
  'function': { color: '#60a5fa' },
  'class-name': { color: '#fbbf24' },
  'regex': { color: '#fbbf24' },
  'important': { color: '#f472b6', fontWeight: 'bold' },
  'bold': { fontWeight: 'bold' },
  'italic': { fontStyle: 'italic' },
};

function hasSourceProperty(obj: any): obj is { source: any } {
  return 'source' in obj;
}

interface MessageItemProps {
  message: Message;
}

const MessageItem = ({ message }: MessageItemProps) => {
  const [copied, setCopied] = useState(false);
  const [showReferences, setShowReferences] = useState(true);
  const [showReasoning, setShowReasoning] = useState(true);
  
  const isUser = message.role === 'user';
  const isThinking = message.thinking && !message.content;
  const hasReasoning = message.reasoning && message.reasoning.length > 0;
  

  
  const reasoningRef = useRef<HTMLDivElement>(null);
  const isUserScrolledUpRef = useRef(false);

  // 自动滚动到推理内容底部（仅在用户没有手动上滑时）
  useEffect(() => {
    if (reasoningRef.current && showReasoning && hasReasoning) {
      const container = reasoningRef.current;
      // 检查用户是否在底部（允许 20px 的误差）
      const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 20;
      
      // 如果用户在底部或从未滚动过，则自动滚动到最新内容
      if (!isUserScrolledUpRef.current || isAtBottom) {
        container.scrollTop = container.scrollHeight;
        isUserScrolledUpRef.current = false;
      }
    }
  }, [message.reasoning, showReasoning, hasReasoning]);

  // 处理滚动事件，检测用户是否手动上滑
  const handleReasoningScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 20;
    isUserScrolledUpRef.current = !isAtBottom;
  };

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
    <div className={`w-full py-2 transition-colors ${isUser ? '' : ''}`}>
      <div className={`max-w-[1400px] mx-auto px-6 md:px-8 flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
        {/* 头像 - 仅在非 thinking 状态显示 */}
        {!isThinking && (
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
        )}

        {/* 消息主体 */}
        <div className={`flex flex-col min-w-0 flex-1 ${isUser ? 'items-end' : 'items-start'} ${isThinking ? 'w-full' : ''}`}>
          <div className={`w-full flex flex-col gap-2 group ${isUser ? 'items-end' : 'items-start'}`}>
            {/* 推理框 - thinking 状态时显示紧凑版本 */}
            {(hasReasoning || isThinking) && (
              <div className={`bg-white/[0.02] backdrop-blur-md border border-white/[0.05] rounded-xl overflow-hidden transition-all duration-500 shadow-lg ${isThinking ? 'w-full py-2 px-3' : 'w-full'}`}>
                <button
                  onClick={() => !isThinking && setShowReasoning(!showReasoning)}
                  className={`w-full flex items-center gap-2 hover:bg-white/[0.03] transition-colors ${isThinking ? 'py-0 justify-center' : 'px-5 py-2.5 justify-between'}`}
                  disabled={isThinking}
                >
                  <div className="flex items-center gap-2">
                    <div className={`rounded-lg flex items-center justify-center border border-white/10 bg-white/[0.05] ${isThinking ? 'w-4 h-4' : 'w-5 h-5'}`}>
                      {isThinking ? (
                        <div className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
                      ) : (
                        <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-500 ${showReasoning ? 'rotate-180' : ''}`} />
                      )}
                    </div>
                    <span className={`font-bold tracking-widest uppercase opacity-40 ${isThinking ? 'text-[9px]' : 'text-[10px]'}`}>
                      {isThinking ? 'Thinking' : 'Thought process'}
                    </span>
                  </div>
                  {!isThinking && (
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="text-[9px] text-text-quaternary">{showReasoning ? '收起' : '展开'}</span>
                    </div>
                  )}
                </button>
                
                {showReasoning && (
                  <div 
                    ref={reasoningRef}
                    onScroll={handleReasoningScroll}
                    className="px-6 pb-5 max-h-48 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent animate-in fade-in slide-in-from-top-2 duration-500"
                  >
                    <div className="text-[13.5px] text-text-tertiary/80 whitespace-pre-wrap font-mono leading-relaxed prose prose-invert prose-sm max-w-none italic opacity-90 border-t border-white/[0.03] pt-4">
                      <ReactMarkdown 
                        children={message.reasoning} 
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeRaw]}
                        components={{
                          code({ node, className, children, ...props }) {
                            const match = /language-(\w+)/.exec(className || '');
                            const inline = !match;
                            return inline ? (
                              <code className={`px-1 py-0.5 rounded bg-white/[0.05] text-primary text-[12px] border border-white/[0.05] font-mono`} {...props}>
                                {children}
                              </code>
                            ) : (
                              <div className="my-4 rounded-xl overflow-hidden border border-white/[0.05] bg-black">
                                <div className="px-3 py-2 bg-white/[0.02] border-b border-white/[0.02]">
                                  <span className="text-[9px] text-text-quaternary font-mono uppercase">{match?.[1] || 'code'}</span>
                                </div>
                                <div className="p-3 overflow-x-auto text-[12px] code-block-wrapper">
                                  <SyntaxHighlighter
                                    children={String(children).replace(/\n$/, '')}
                                    style={customCodeTheme as any}
                                    language={match?.[1] || 'text'}
                                    PreTag="div"
                                    customStyle={{ margin: '0', background: 'transparent', padding: '0', fontSize: '12px' }}
                                    wrapLines={false}
                                    showLineNumbers={false}
                                  />
                                </div>
                              </div>
                            );
                          },
                          p: ({ node, ...props }) => <p className={`my-2 leading-relaxed`} {...props} />,
                          ul: ({ node, ...props }) => <ul className="list-disc my-3 pl-6 space-y-1" {...props} />,
                          ol: ({ node, ...props }) => <ol className="list-decimal my-3 pl-6 space-y-1" {...props} />,
                          li: ({ node, ...props }) => <li className="my-1 text-text-tertiary/90" {...props} />,
                          h1: ({ node, ...props }) => <h1 className="text-lg font-bold my-4 text-white/90" {...props} />,
                          h2: ({ node, ...props }) => <h2 className="text-base font-bold my-3 text-white/80" {...props} />,
                          h3: ({ node, ...props }) => <h3 className="text-sm font-bold my-2 text-white/70" {...props} />,
                          blockquote: ({ node, ...props }) => (
                            <blockquote className="border-l-2 border-primary/30 pl-3 my-3 italic text-text-quaternary/80" {...props} />
                          ),
                          a: ({ node, ...props }) => (
                            <a {...props} target="_blank" rel="noopener noreferrer" className="text-primary/80 hover:text-primary underline" />
                          ),
                          img: ({ node, ...props }) => (
                            <img {...props} className="max-w-full h-auto rounded-lg my-3 border border-white/[0.05]" loading="lazy" />
                          ),
                          table: ({ node, ...props }) => (
                            <div className="overflow-x-auto my-3 rounded-lg border border-white/[0.05] bg-white/[0.02]">
                              <table className="w-full text-xs table-auto" {...props} />
                            </div>
                          ),
                          thead: ({ node, ...props }) => <thead className="bg-white/[0.05] text-text-tertiary text-[10px] whitespace-nowrap" {...props} />,
                          th: ({ node, ...props }) => <th className="px-2 py-1.5 font-medium border-b border-white/[0.08] min-w-[40px] text-center" {...props} />,
                          td: ({ node, ...props }) => <td className="px-2 py-1.5 border-b border-white/[0.05] text-center align-middle" {...props} />,
                          tr: ({ node, ...props }) => <tr className="hover:bg-white/[0.03]" {...props} />,
                          hr: ({ node, ...props }) => <hr className="my-4 border-white/[0.08]" {...props} />,
                          del: ({ node, ...props }) => <del className="line-through text-text-quaternary/60" {...props} />,
                          strong: ({ node, ...props }) => <strong className="font-bold text-white/90" {...props} />,
                          em: ({ node, ...props }) => <em className="italic text-text-tertiary/80" {...props} />,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 内容气泡和操作栏 */}
            <>
              {/* 内容气泡 - 采用半透明"磨砂玻璃"质感，优雅悬浮 */}
                <div className={`
                  ${isUser 
                    ? 'bg-white/[0.04] backdrop-blur-2xl border border-white/[0.08] shadow-[0_8px_32px_rgba(0,0,0,0.3)] rounded-[12px] rounded-tr-[4px] px-3 py-1.5 text-text-primary max-w-[85%] text-left font-medium' 
                    : 'bg-primary/[0.02] backdrop-blur-3xl border border-white/[0.05] shadow-[0_8px_32px_rgba(0,0,0,0.2)] rounded-[12px] rounded-tl-[4px] px-3 py-1.5 text-text-primary w-fit max-w-full'
                  }
                `}>
                  <div className={`prose max-w-none ${isUser ? 'prose-invert' : 'prose-p:text-text-primary prose-strong:text-white prose-code:text-primary'}`}>
                    <ReactMarkdown
                      children={message.content}
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                      components={{
                        code({ node, className, children, ...props }) {
                          const match = /language-(\w+)/.exec(className || '');
                          const inline = !match;
                          return inline ? (
                            <code className={`px-1.5 py-0.5 rounded-md bg-white/[0.05] text-primary text-[13px] border border-white/[0.05] font-mono`} {...props}>
                              {children}
                            </code>
                          ) : (
                            <div className="my-8 rounded-3xl overflow-hidden border border-white/[0.05] bg-black shadow-2xl group/code">
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
                              <div className="p-6 overflow-x-auto text-[14.5px] code-block-wrapper">
                                <SyntaxHighlighter
                                  children={String(children).replace(/\n$/, '')}
                                  style={customCodeTheme as any}
                                  language={match[1]}
                                  PreTag="div"
                                  customStyle={{ margin: '0', background: 'transparent', padding: '0' }}
                                  wrapLines={false}
                                  showLineNumbers={false}
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
                        h4: ({ node, ...props }) => <h4 className="text-base font-bold my-5 text-white/90" {...props} />,
                        h5: ({ node, ...props }) => <h5 className="text-sm font-bold my-4 text-white/80" {...props} />,
                        h6: ({ node, ...props }) => <h6 className="text-xs font-bold my-3 text-white/70 uppercase tracking-wider" {...props} />,
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
                        img: ({ node, ...props }) => (
                          <img 
                            {...props} 
                            className="max-w-full h-auto rounded-2xl my-6 border border-white/[0.05] shadow-xl"
                            loading="lazy"
                          />
                        ),
                        table: ({ node, ...props }) => (
                          <div className="overflow-x-auto my-6 rounded-2xl border border-white/[0.05] bg-white/[0.02]">
                            <table className="w-full text-left table-auto" {...props} />
                          </div>
                        ),
                        thead: ({ node, ...props }) => <thead className="bg-white/[0.05] text-text-secondary text-xs tracking-wider whitespace-nowrap" {...props} />,
                        th: ({ node, ...props }) => <th className="px-3 py-2.5 font-semibold border-b border-white/[0.08] min-w-[60px] text-center" {...props} />,
                        td: ({ node, ...props }) => <td className="px-3 py-2.5 border-b border-white/[0.05] text-text-primary text-center align-middle" {...props} />,
                        tr: ({ node, ...props }) => <tr className="hover:bg-white/[0.03] transition-colors" {...props} />,
                        hr: ({ node, ...props }) => <hr className="my-8 border-white/[0.08]" {...props} />,
                        del: ({ node, ...props }) => <del className="line-through text-text-tertiary" {...props} />,
                        input: ({ node, ...props }) => {
                          if (props.type === 'checkbox') {
                            return (
                              <input 
                                {...props} 
                                disabled 
                                className="mr-2 w-4 h-4 rounded border-white/20 bg-white/5 text-primary focus:ring-primary/50"
                              />
                            );
                          }
                          return <input {...props} />;
                        },
                        sup: ({ node, ...props }) => (
                          <sup className="text-primary text-xs" {...props} />
                        ),
                        sub: ({ node, ...props }) => (
                          <sub className="text-text-tertiary text-xs" {...props} />
                        ),
                        strong: ({ node, ...props }) => (
                          <strong className="font-bold text-white" {...props} />
                        ),
                        em: ({ node, ...props }) => (
                          <em className="italic text-text-secondary" {...props} />
                        ),
                      }}
                    />
                  </div>
                </div>

                {/* 操作栏 - 类似豆包风格 */}
                <div className={`flex items-center gap-1 mt-1 opacity-100 transition-all duration-300 relative z-50 ${isUser ? 'flex-row-reverse' : ''}`}>
                  {/* 复制按钮 */}
                  <button
                    onClick={handleCopy}
                    className="flex items-center justify-center w-8 h-8 text-text-quaternary hover:text-text-secondary hover:bg-white/5 rounded-lg transition-all pointer-events-auto cursor-pointer"
                    title="复制"
                  >
                    {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                  </button>
                  
                  {/* 重新生成 - 仅 AI 消息显示 */}
                  {!isUser && (
                    <button
                      className="flex items-center justify-center w-8 h-8 text-text-quaternary hover:text-text-secondary hover:bg-white/5 rounded-lg transition-all pointer-events-auto cursor-pointer"
                      title="重新生成"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  )}
                  
                  {/* 点赞 - 仅 AI 消息显示 */}
                  {!isUser && (
                    <button
                      className="flex items-center justify-center w-8 h-8 text-text-quaternary hover:text-text-secondary hover:bg-white/5 rounded-lg transition-all pointer-events-auto cursor-pointer"
                      title="有用"
                    >
                      <ThumbsUp className="w-4 h-4" />
                    </button>
                  )}
                  
                  {/* 点踩 - 仅 AI 消息显示 */}
                  {!isUser && (
                    <button
                      className="flex items-center justify-center w-8 h-8 text-text-quaternary hover:text-text-secondary hover:bg-white/5 rounded-lg transition-all pointer-events-auto cursor-pointer"
                      title="无用"
                    >
                      <ThumbsDown className="w-4 h-4" />
                    </button>
                  )}
                  
                  {/* 时间戳 */}
                  <span className="text-[10px] text-text-quaternary font-mono tracking-tighter opacity-50 px-2">
                    {format(message.timestamp, 'HH:mm')}
                  </span>
                </div>
            </>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageItem;
