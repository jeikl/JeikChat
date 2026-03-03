import { Message } from '@/types/chat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { Copy, Check, ChevronDown, Bot, User, Loader2, RotateCcw, ThumbsUp, ThumbsDown } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { format } from 'date-fns';

// 自定义代码块主题 - GitHub Dark 风格
const customCodeTheme = {
  'code[class*="language-"]': {
    color: '#e6edf3',
    background: 'transparent',
    textShadow: 'none',
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
    fontSize: '14px',
    lineHeight: '1.6',
  },
  'pre[class*="language-"]': {
    color: '#e6edf3',
    background: 'transparent',
    textShadow: 'none',
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
    fontSize: '14px',
    lineHeight: '1.6',
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
  'comment': { color: '#8b949e' },
  'block-comment': { color: '#8b949e' },
  'prolog': { color: '#8b949e' },
  'doctype': { color: '#8b949e' },
  'cdata': { color: '#8b949e' },
  'punctuation': { color: '#c9d1d9' },
  'property': { color: '#79c0ff' },
  'tag': { color: '#7ee787' },
  'boolean': { color: '#79c0ff' },
  'number': { color: '#79c0ff' },
  'constant': { color: '#79c0ff' },
  'symbol': { color: '#79c0ff' },
  'deleted': { color: '#f85149' },
  'selector': { color: '#7ee787' },
  'attr-name': { color: '#79c0ff' },
  'string': { color: '#a5d6ff' },
  'char': { color: '#a5d6ff' },
  'builtin': { color: '#ffa657' },
  'inserted': { color: '#7ee787' },
  'operator': { color: '#c9d1d9' },
  'entity': { color: '#ffa657' },
  'url': { color: '#a5d6ff' },
  'variable': { color: '#e6edf3' },
  'attr-value': { color: '#a5d6ff' },
  'keyword': { color: '#ff7b72' },
  'function': { color: '#d2a8ff' },
  'class-name': { color: '#ffa657' },
  'regex': { color: '#7ee787' },
  'important': { color: '#ff7b72', fontWeight: 'bold' },
  'bold': { fontWeight: 'bold' },
  'italic': { fontStyle: 'italic' },
};

interface MessageItemProps {
  message: Message;
}

const MessageItem = ({ message }: MessageItemProps) => {
  const [copied, setCopied] = useState(false);
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
      // 优先尝试使用现代 Clipboard API
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(message.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } else {
        throw new Error('Clipboard API unavailable');
      }
    } catch (err) {
      console.warn('Clipboard API failed, falling back to execCommand:', err);
      // 降级方案：使用传统的 textarea + execCommand
      // 这种方式兼容性更好，特别是在非 HTTPS 环境或某些移动端浏览器中
      try {
        const textArea = document.createElement("textarea");
        textArea.value = message.content;
        
        // 确保 textarea 不可见但存在于 DOM 中，且不会导致滚动
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        textArea.style.top = "0";
        textArea.setAttribute('readonly', ''); // 防止在 iOS 上弹出键盘
        document.body.appendChild(textArea);
        
        textArea.focus();
        textArea.select();
        
        // iOS 需要额外的 range 选择
        if (navigator.userAgent.match(/ipad|iphone/i)) {
          const range = document.createRange();
          range.selectNodeContents(textArea);
          const selection = window.getSelection();
          if (selection) {
            selection.removeAllRanges();
            selection.addRange(range);
            textArea.setSelectionRange(0, 999999);
          }
        }

        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        
        if (successful) {
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        } else {
          console.error('Fallback copy failed');
        }
      } catch (fallbackErr) {
        console.error('Copy failed:', fallbackErr);
      }
    }
  };

  return (
    <div className={`w-full py-1.5 md:py-2 transition-colors ${isUser ? '' : ''}`}>
      <div className={`max-w-[1400px] mx-auto px-3 md:px-8 flex gap-2 md:gap-3 ${isUser ? 'flex-row-reverse items-start' : ''}`}>
        {/* 头像 - 始终显示 */}
        <div className={`flex-shrink-0 ${isUser ? 'mt-0.5' : 'mt-6 md:mt-1'}`}>
          {isUser ? (
            <div className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-gradient-to-br from-[#4f46e5] to-[#9333ea] flex items-center justify-center shadow-lg shadow-indigo-500/20 border border-white/10 transform hover:scale-105 transition-transform duration-300">
              <User className="w-4.5 h-4.5 md:w-5.5 md:h-5.5 text-white/90" />
            </div>
          ) : (
            <div className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-gradient-to-br from-[#0052D4] via-[#4364F7] to-[#6FB1FC] flex items-center justify-center shadow-lg shadow-blue-500/20 border border-white/10 transform hover:scale-105 transition-transform duration-300">
              <Bot className="w-4.5 h-4.5 md:w-5.5 md:h-5.5 text-white/95" />
            </div>
          )}
        </div>

        {/* 消息主体 */}
        <div className={`flex flex-col min-w-0 flex-1 ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`w-full flex flex-col gap-2 group ${isUser ? 'items-end' : 'items-start'}`}>
            {/* 推理框 - 放在AI头像旁边 */}
            {(hasReasoning || isThinking) && (
              <div className={`bg-white/[0.02] backdrop-blur-md border border-white/[0.05] rounded-xl overflow-hidden transition-all duration-500 shadow-lg w-full -mx-1 md:mx-0 ${isThinking ? 'py-2 px-3' : ''}`}>
                <button
                  onClick={() => !isThinking && setShowReasoning(!showReasoning)}
                  className={`w-full flex items-center gap-2 hover:bg-white/[0.03] transition-colors ${isThinking ? 'py-0 justify-center' : 'px-2 py-1.5 md:px-5 md:py-2.5 justify-between'}`}
                  disabled={isThinking}
                >
                  <div className="flex items-center gap-2">
                    <div className={`rounded-lg flex items-center justify-center border border-white/10 bg-white/[0.05] w-5 h-5`}>
                      {isThinking ? (
                        <Loader2 className="w-3 h-3 text-primary animate-spin" />
                      ) : (
                        <ChevronDown className={`w-3 h-3 text-gray-400 transition-transform duration-500 ${showReasoning ? 'rotate-180' : ''}`} />
                      )}
                    </div>
                    <span className={`font-bold tracking-tighter md:tracking-widest uppercase opacity-80 ${isThinking ? 'text-[9px] bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent animate-pulse' : 'text-[10px] md:text-[11px] text-gray-300'}`}>
                      {isThinking ? 'Thinking...' : 'Thought Process'}
                    </span>
                  </div>
                  {!isThinking && (
                    <div className="text-[9px] text-gray-500 pr-1">
                      {showReasoning ? '点击收起' : '点击展开'}
                    </div>
                  )}
                </button>
                
                {showReasoning && (
                  <div 
                    ref={reasoningRef}
                    onScroll={handleReasoningScroll}
                    className="px-3 md:px-4 pb-8 md:pb-5 animate-in fade-in slide-in-from-top-2 duration-500 w-full"
                  >
                    <div className="text-[12px] md:text-[13px] text-gray-300/85 font-mono leading-[1.3] max-w-none italic border-t border-white/[0.05] pt-2">
                      {/* 移动端：直接显示纯文本，确保布局稳定 */}
                      <div className="block md:hidden whitespace-pre-wrap break-words w-full">
                        {message.reasoning}
                      </div>

                      {/* 桌面端：显示Markdown渲染 */}
                      <div className="hidden md:block">
                        <ReactMarkdown 
                          children={message.reasoning} 
                          remarkPlugins={[remarkGfm]}
                          rehypePlugins={[rehypeRaw]}
                          components={{
                            code({ node, className, children, ...props }) {
                              const match = /language-(\w+)/.exec(className || '');
                              const inline = !match;
                              return inline ? (
                                <code className={`px-1 py-0 rounded bg-white/[0.05] text-primary text-[12px] font-mono`} {...props}>
                                  {children}
                                </code>
                              ) : (
                                <div className="my-1 rounded-lg overflow-hidden border border-white/[0.08] bg-[#161b22]">
                                  <div className="px-2 py-1 bg-[#0d1117] border-b border-white/[0.06]">
                                    <span className="text-[9px] text-text-quaternary font-mono uppercase">{match?.[1] || 'code'}</span>
                                  </div>
                                  <div className="p-2 overflow-x-auto text-[12px] code-block-wrapper">
                                    <SyntaxHighlighter
                                      children={String(children).replace(/\n$/, '')}
                                      style={customCodeTheme as any}
                                      language={match?.[1] || 'text'}
                                      PreTag="div"
                                      customStyle={{ margin: '0', background: 'transparent', padding: '0', fontSize: 'inherit' }}
                                      wrapLines={false}
                                      showLineNumbers={false}
                                    />
                                  </div>
                                </div>
                              );
                            },
                            p: ({ node, ...props }) => <p className={`mb-0.5 last:mb-0`} {...props} />,
                            ul: ({ node, ...props }) => (
                              <ul className="mb-0.5 pl-4 list-disc marker:text-gray-500 space-y-0" {...props} />
                            ),
                            ol: ({ node, ...props }) => (
                              <ol className="mb-0.5 pl-4 list-decimal marker:text-gray-500 space-y-0" {...props} />
                            ),
                            li: ({ node, ...props }) => {
                              const text = props.children?.toString() || '';
                              const isFolder = text.includes(':') || text.endsWith('/');
                              const isFile = !isFolder && text.includes('.');
                              let colorClass = 'text-[#c9d1d9]';
                              if (isFolder) {
                                colorClass = 'text-[#7ee787]';
                              } else if (isFile) {
                                colorClass = 'text-[#79c0ff]';
                              }
                              return <li className={`text-[13px] font-mono ${colorClass} leading-tight`} {...props} />;
                            },
                            h1: ({ node, ...props }) => <h1 className="text-sm font-bold mt-1 mb-0.5 text-white/90" {...props} />,
                            h2: ({ node, ...props }) => <h2 className="text-xs font-bold mt-1 mb-0.5 text-white/80" {...props} />,
                            h3: ({ node, ...props }) => <h3 className="text-[11px] font-bold mt-0.5 mb-0.5 text-white/70" {...props} />,
                            blockquote: ({ node, ...props }) => (
                              <blockquote className="border-l-2 border-primary/30 pl-2 my-1 italic text-text-quaternary/80" {...props} />
                            ),
                            a: ({ node, ...props }) => (
                              <a {...props} target="_blank" rel="noopener noreferrer" className="text-primary/80 hover:text-primary underline" />
                            ),
                            img: ({ node, ...props }) => (
                              <img {...props} className="max-w-full h-auto rounded-lg my-1 border border-white/[0.05]" loading="lazy" />
                            ),
                            table: ({ node, ...props }) => (
                              <div className="overflow-x-auto my-1 rounded-lg border border-white/[0.05] bg-white/[0.02]">
                                <table className="w-full text-xs table-auto" {...props} />
                              </div>
                            ),
                            thead: ({ node, ...props }) => <thead className="bg-white/[0.05] text-text-tertiary text-[10px] whitespace-nowrap" {...props} />,
                            th: ({ node, ...props }) => <th className="px-1.5 py-0.5 font-medium border-b border-white/[0.08] min-w-[40px] text-center" {...props} />,
                            td: ({ node, ...props }) => <td className="px-1.5 py-0.5 border-b border-white/[0.05] text-center align-middle" {...props} />,
                            tr: ({ node, ...props }) => <tr className="hover:bg-white/[0.03]" {...props} />,
                            hr: ({ node, ...props }) => <hr className="my-1 border-white/[0.08]" {...props} />,
                            del: ({ node, ...props }) => <del className="line-through text-text-quaternary/60" {...props} />,
                            strong: ({ node, ...props }) => <strong className="font-bold text-white/90" {...props} />,
                            em: ({ node, ...props }) => <em className="italic text-text-tertiary/80" {...props} />,
                          }}
                        />
                      </div>
                    </div>
                    
                    {/* 底部收起按钮 - 更加紧凑且明显 */}
                    {!isThinking && (
                      <div className="mt-1 flex justify-center pb-1 relative z-10">
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowReasoning(false);
                          }}
                          className="group/btn flex items-center gap-1 px-3 py-0.5 rounded-full bg-white/[0.08] hover:bg-white/15 border border-white/[0.1] transition-all duration-300 shadow-sm"
                        >
                          <ChevronDown className="w-2.5 h-2.5 text-gray-400 group-hover/btn:text-gray-200 rotate-180 transition-transform duration-300" />
                          <span className="text-[10px] text-gray-400 group-hover/btn:text-gray-200 transition-colors">收起</span>
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* 内容气泡和操作栏 */}
            <>
              {/* 内容气泡 - 采用半透明"磨砂玻璃"质感，优雅悬浮 */}
                <div className={`
                  ${isUser 
                    ? 'bg-[#2b2d31] border border-white/10 rounded-2xl px-3 py-2 text-white max-w-[85%] md:max-w-[75%] text-left text-[14px] md:text-[15px] shadow-md shadow-black/20 w-fit' 
                    : 'bg-transparent px-0 py-0 text-white w-full max-w-full text-left text-[15px] md:text-[16px]'
                  }
                `}>
                  <div className={`prose max-w-none ${isUser ? 'prose-invert' : 'prose-invert'}`}>
                    <ReactMarkdown
                      children={message.content}
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                      components={{
                        code({ node, className, children, ...props }) {
                          const match = /language-(\w+)/.exec(className || '');
                          const inline = !match;
                          return inline ? (
                            <code className={`px-1.5 py-0.5 rounded-md bg-[#161b22] text-primary text-[13px] border border-white/[0.08] font-mono`} {...props}>
                              {children}
                            </code>
                          ) : (
                            <div className="my-8 rounded-3xl overflow-hidden border border-white/[0.08] bg-[#161b22]">
                              <div className="flex items-center justify-between px-6 py-3 bg-[#0d1117] border-b border-white/[0.06]">
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
                        p: ({ node, ...props }) => <p className={`my-1.5 leading-6 text-[14px] md:text-[15px] text-gray-100`} {...props} />,
                        ul: ({ node, ...props }) => (
                          <ul className="my-3 pl-6 list-disc marker:text-gray-400 space-y-1" {...props} />
                        ),
                        ol: ({ node, ...props }) => (
                          <ol className="my-3 pl-6 list-decimal marker:text-gray-400 space-y-1" {...props} />
                        ),
                        li: ({ node, ...props }) => {
                          // 检查是否是文件夹结构（简单的启发式检查）
                          const text = props.children?.toString() || '';
                          const isFolderStructure = text.includes('├──') || text.includes('└──');
                          
                          if (isFolderStructure) {
                             const isFolder = text.includes(':') || text.endsWith('/');
                             const isFile = !isFolder && text.includes('.');
                             let colorClass = 'text-gray-300';
                             if (isFolder) {
                               colorClass = 'text-green-400';
                             } else if (isFile) {
                               colorClass = 'text-blue-400';
                             }
                             return <li className={`font-mono text-sm ${colorClass} list-none -ml-4`} {...props} />;
                          }
                          
                          return <li className={`text-gray-100 leading-relaxed pl-1`} {...props} />;
                        },
                        h1: ({ node, ...props }) => <h1 className="text-2xl font-bold my-6 text-white pb-2 border-b border-white/10" {...props} />,
                        h2: ({ node, ...props }) => <h2 className="text-xl font-bold my-5 text-white" {...props} />,
                        h3: ({ node, ...props }) => <h3 className="text-lg font-bold my-4 text-white" {...props} />,
                        h4: ({ node, ...props }) => <h4 className="text-base font-bold my-3 text-white" {...props} />,
                        h5: ({ node, ...props }) => <h5 className="text-sm font-bold my-2 text-white" {...props} />,
                        h6: ({ node, ...props }) => <h6 className="text-xs font-bold my-2 text-white uppercase tracking-wider" {...props} />,
                        blockquote: ({ node, ...props }) => (
                          <blockquote className="border-l-4 border-primary/40 pl-4 my-4 italic text-gray-300 bg-white/[0.03] py-2 pr-2 rounded-r-lg" {...props} />
                        ),
                        a: ({ node, ...props }) => (
                          <a 
                            {...props} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-400 hover:text-blue-300 underline underline-offset-4 transition-colors"
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
                          <em className="italic text-gray-200" {...props} />
                        ),
                      }}
                    />
                  </div>
                </div>

                {/* 操作栏 - 类似豆包风格 */}
                <div className={`flex items-center gap-2 mt-1 opacity-100 transition-all duration-300 ${isUser ? 'flex-row-reverse self-end mr-1' : ''}`}>
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
                  <span className="text-xs text-text-tertiary font-medium tracking-wide opacity-80 px-2 select-none">
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
