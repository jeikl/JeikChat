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

const ImagePreview = ({ src, onClose }: { src: string; onClose: () => void }) => {
  return (
    <div 
      className="fixed inset-0 z-[9999] bg-black/90 flex items-center justify-center cursor-zoom-out animate-in fade-in duration-200"
      onClick={onClose}
    >
      <img 
        src={src} 
        alt="Preview" 
        className="max-w-[95vw] max-h-[95vh] object-contain rounded-lg shadow-2xl"
      />
      <button 
        onClick={onClose}
        className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </button>
    </div>
  );
};

const MessageItem = ({ message }: MessageItemProps) => {
  const [copied, setCopied] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const isUser = message.role === 'user';
  const isThinking = message.thinking && !message.content;
  const hasReasoning = message.reasoning && message.reasoning.length > 0;
  // 默认展开正在生成的推理，历史消息也保持展开（除非用户手动收起）
  const [showReasoning, setShowReasoning] = useState(true);
  const [showInternalScrollButton, setShowInternalScrollButton] = useState(false);
  
  const reasoningRef = useRef<HTMLDivElement>(null);
  const isUserScrolledUpRef = useRef(false);

  // 移除之前的自动收起逻辑

  // 自动滚动到推理内容底部（仅在用户没有手动上滑时）
  useEffect(() => {
    if (reasoningRef.current && showReasoning && hasReasoning) {
      const container = reasoningRef.current;
      // 增加判定阈值，并确保只有在正在生成时才自动跟随
      const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
      
      if ((!isUserScrolledUpRef.current || isAtBottom) && isThinking) {
        container.scrollTop = container.scrollHeight;
        isUserScrolledUpRef.current = false;
        setShowInternalScrollButton(false);
      }
    }
  }, [message.reasoning, showReasoning, hasReasoning, isThinking]);

  // 处理滚动事件，检测用户是否手动上滑
  const handleReasoningScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
    
    if (!isAtBottom) {
      isUserScrolledUpRef.current = true;
      setShowInternalScrollButton(true);
    } else {
      isUserScrolledUpRef.current = false;
      setShowInternalScrollButton(false);
    }
  };

  // 内部推理框滚动到底部
  const scrollReasoningToBottom = () => {
    if (reasoningRef.current) {
      reasoningRef.current.scrollTo({
        top: reasoningRef.current.scrollHeight,
        behavior: 'smooth'
      });
      isUserScrolledUpRef.current = false;
      setShowInternalScrollButton(false);
    }
  };

  // 复制文本到剪贴板的通用函数
  const copyToClipboard = async (text: string) => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return true;
      } else {
        // 兼容性方案：创建临时 textarea
        const textArea = document.createElement("textarea");
        textArea.value = text;
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
        return successful;
      }
    } catch (err) {
      console.error('复制失败:', err);
      return false;
    }
  };

  const handleCopy = async () => {
    const success = await copyToClipboard(message.content);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // 解析消息内容，分离媒体和文本
  const { media, text: cleanText } = (() => {
    const media: { type: 'image' | 'video' | 'audio', url: string }[] = [];
    let text = message.content || '';

    // 1. 提取 Markdown 图片: ![alt](url)
    const imgRegex = /!\[.*?\]\((.*?)\)/g;
    let match;
    while ((match = imgRegex.exec(text)) !== null) {
      media.push({ type: 'image', url: match[1] });
    }
    text = text.replace(imgRegex, '').trim();

    // 2. 提取 HTML 视频: <video src="url"...>
    const videoRegex = /<video[^>]+src="([^"]+)"[^>]*>.*?<\/video>/g;
    while ((match = videoRegex.exec(text)) !== null) {
      media.push({ type: 'video', url: match[1] });
    }
    text = text.replace(videoRegex, '').trim();

    // 3. 提取 HTML 音频: <audio src="url"...>
    const audioRegex = /<audio[^>]+src="([^"]+)"[^>]*>.*?<\/audio>/g;
    while ((match = audioRegex.exec(text)) !== null) {
      media.push({ type: 'audio', url: match[1] });
    }
    text = text.replace(audioRegex, '').trim();

    return { media, text };
  })();

  return (
    <div className={`w-full py-1.5 md:py-2 transition-colors`}>
      <div className={`max-w-[1400px] mx-auto px-3 md:px-8 flex gap-2 md:gap-3 ${isUser ? 'flex-row-reverse items-start' : ''}`}>
        {/* 头像 - 手机端隐藏Bot头像，保留User头像 */}
        <div className={`flex-shrink-0 ${isUser ? 'mt-0.5' : 'hidden md:flex mt-1 md:mt-1'}`}>
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
              <div className={`bg-white/[0.02] backdrop-blur-md border border-white/[0.05] rounded-lg md:rounded-xl overflow-hidden transition-all duration-500 shadow-lg w-full ${isThinking ? 'py-2 px-3' : ''}`}>
                <button
                  onClick={() => !isThinking && setShowReasoning(!showReasoning)}
                  className={`w-full flex items-center gap-1.5 md:gap-2 hover:bg-white/[0.03] transition-colors ${isThinking ? 'py-0 justify-center' : 'px-3 py-2 md:px-4 md:py-2.5 justify-between'}`}
                  disabled={isThinking}
                >
                  <div className="flex items-center gap-1.5 md:gap-2">
                    <div className={`rounded flex items-center justify-center border border-white/10 bg-white/[0.05] w-5 h-5 md:w-6 md:h-6`}>
                      {isThinking ? (
                        <Loader2 className="w-3 h-3 md:w-3.5 md:h-3.5 text-primary animate-spin" />
                      ) : (
                        <ChevronDown className={`w-3 h-3 md:w-4 md:h-4 text-gray-400 transition-transform duration-300 ${showReasoning ? 'rotate-180' : ''}`} />
                      )}
                    </div>
                    <span className={`font-bold tracking-tight md:tracking-widest uppercase opacity-90 ${isThinking ? 'text-[10px] md:text-[12px] bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent animate-pulse' : 'text-[11px] md:text-[13px] text-gray-200'}`}>
                      {isThinking ? 'Thinking...' : '推理过程'}
                    </span>
                  </div>
                  {!isThinking && (
                    <div className="text-[10px] md:text-[11px] text-gray-400 font-medium">
                      {showReasoning ? '收起' : '展开'}
                    </div>
                  )}
                </button>
                
                {showReasoning && (
                  <div className="relative w-full">
                    <div 
                      ref={reasoningRef}
                      onScroll={handleReasoningScroll}
                      className="px-3 md:px-4 pb-3 md:pb-6 animate-in fade-in slide-in-from-top-2 duration-500 w-full overflow-y-auto scrollbar-thin"
                    >
                      <div className="text-[13px] md:text-[14px] text-gray-300/90 leading-relaxed max-w-none border-t border-white/[0.05] pt-2">
                        {/* 推理框也使用 ReactMarkdown 渲染，支持完整的 Markdown 格式 */}
                        <ReactMarkdown 
                          children={message.reasoning || ''} 
                          remarkPlugins={[remarkGfm]}
                          rehypePlugins={[rehypeRaw]}
                          components={{
                            code({ node, className, children, ...props }) {
                              const match = /language-(\w+)/.exec(className || '');
                              const inline = !match;
                              return inline ? (
                                <code className={`px-1 py-0.5 rounded bg-white/[0.05] text-primary text-[12px] font-mono`} {...props}>
                                  {children}
                                </code>
                              ) : (
                                <div className="my-2 rounded-lg overflow-hidden border border-white/[0.08] bg-[#161b22]">
                                  <div className="px-3 py-1.5 bg-[#0d1117] border-b border-white/[0.06] flex items-center justify-between">
                                    <span className="text-[10px] text-text-quaternary font-mono uppercase">{match?.[1] || 'code'}</span>
                                    <button 
                                      onClick={async (e) => {
                                        e.stopPropagation();
                                        const success = await copyToClipboard(String(children).replace(/\n$/, ''));
                                        if (success) {
                                          const btn = e.currentTarget;
                                          const originalText = btn.innerHTML;
                                          btn.innerHTML = 'Copied!';
                                          setTimeout(() => { btn.innerHTML = originalText; }, 2000);
                                        }
                                      }}
                                      className="text-[10px] text-text-quaternary hover:text-text-primary transition-colors flex items-center gap-1"
                                    >
                                      <Copy className="w-3 h-3" />
                                      <span>Copy</span>
                                    </button>
                                  </div>
                                  <div className="p-3 overflow-x-auto text-[12px] code-block-wrapper">
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
                            // 段落样式 - 增加行高和间距
                            p: ({ node, ...props }) => <p className={`mb-3 last:mb-0 leading-relaxed text-gray-300/90`} {...props} />,
                            // 无序列表 - 使用主题色标记
                            ul: ({ node, ...props }) => (
                              <ul className="mb-3 pl-5 list-disc marker:text-primary marker:text-[14px] space-y-1.5" {...props} />
                            ),
                            // 有序列表 - 使用主题色数字
                            ol: ({ node, ...props }) => (
                              <ol className="mb-3 pl-5 list-decimal marker:text-primary marker:font-bold space-y-1.5" {...props} />
                            ),
                            // 列表项 - 智能识别文件夹/文件结构
                            li: ({ node, ...props }) => {
                              const text = props.children?.toString() || '';
                              const isFolder = text.includes(':') || text.endsWith('/');
                              const isFile = !isFolder && text.includes('.');
                              const isToolCall = text.includes('🧠') || text.includes('🛠️');
                              let colorClass = 'text-gray-300';
                              if (isFolder) {
                                colorClass = 'text-green-400';
                              } else if (isFile) {
                                colorClass = 'text-blue-400';
                              } else if (isToolCall) {
                                colorClass = 'text-yellow-400';
                              }
                              return <li className={`text-[13px] md:text-[14px] ${colorClass} leading-relaxed`} {...props} />;
                            },
                            // 标题层级 - 统一使用亮白色，清晰醒目
                            h1: ({ node, ...props }) => (
                              <h1 className="text-lg font-bold mt-4 mb-2 text-white bg-white/[0.08] px-3 py-1.5 rounded-lg border-l-4 border-white/40" {...props} />
                            ),
                            h2: ({ node, ...props }) => (
                              <h2 className="text-base font-bold mt-3 mb-2 text-white bg-white/[0.05] px-2.5 py-1 rounded-lg border-l-3 border-white/30 flex items-center gap-2" {...props} />
                            ),
                            h3: ({ node, ...props }) => (
                              <h3 className="text-[15px] font-semibold mt-3 mb-1.5 text-white flex items-center gap-2 before:content-['▸'] before:text-white/80" {...props} />
                            ),
                            h4: ({ node, ...props }) => (
                              <h4 className="text-[14px] font-semibold mt-2 mb-1 text-white/90 flex items-center gap-2 before:content-['▪'] before:text-white/70" {...props} />
                            ),
                            h5: ({ node, ...props }) => (
                              <h5 className="text-[13px] font-semibold mt-2 mb-1 text-white/80" {...props} />
                            ),
                            h6: ({ node, ...props }) => (
                              <h6 className="text-[12px] font-semibold mt-1.5 mb-1 text-white/70 uppercase tracking-wider" {...props} />
                            ),
                            // 引用块 - 左侧主题色边框
                            blockquote: ({ node, ...props }) => (
                              <blockquote className="border-l-3 border-primary/40 pl-4 my-3 py-2 italic text-gray-400/90 bg-white/[0.02] rounded-r-lg" {...props} />
                            ),
                            // 链接 - 主题色悬停效果
                            a: ({ node, ...props }) => (
                              <a {...props} target="_blank" rel="noopener noreferrer" className="text-primary hover:text-primary/80 underline underline-offset-2 transition-colors" />
                            ),
                            // 图片 - 智能识别视频/音频
                            img: ({ node, ...props }) => {
                              const src = props.src || '';
                              const isVideo = /\.(mp4|webm|ogg|mov)(?:\?|$)/i.test(src);
                              const isAudio = /\.(mp3|wav|ogg|m4a)(?:\?|$)/i.test(src);

                              if (isVideo) {
                                return (
                                  <div className="my-3 rounded-xl overflow-hidden border border-white/[0.08] shadow-lg bg-black/20">
                                    <video 
                                      src={src} 
                                      controls 
                                      className="max-w-full w-full" 
                                      preload="metadata"
                                    />
                                  </div>
                                );
                              }

                              if (isAudio) {
                                return (
                                  <div className="my-3 rounded-lg border border-white/[0.08] shadow-sm bg-white/[0.05] p-2">
                                    <audio 
                                      src={src} 
                                      controls 
                                      className="w-full" 
                                    />
                                  </div>
                                );
                              }

                              return (
                                <img 
                                  {...props} 
                                  className="max-w-full h-auto rounded-xl my-3 border border-white/[0.08] shadow-lg" 
                                  loading="lazy" 
                                />
                              );
                            },
                            // 视频标签支持
                            video: ({ node, ...props }) => (
                              <div className="my-3 rounded-xl overflow-hidden border border-white/[0.08] shadow-lg bg-black/20">
                                <video 
                                  {...props} 
                                  className="max-w-full w-full" 
                                  preload="metadata"
                                />
                              </div>
                            ),
                            // 音频标签支持
                            audio: ({ node, ...props }) => (
                              <div className="my-3 rounded-lg border border-white/[0.08] shadow-sm bg-white/[0.05] p-2">
                                <audio 
                                  {...props} 
                                  className="w-full" 
                                />
                              </div>
                            ),
                            // 表格 - 现代化样式
                            table: ({ node, ...props }) => (
                              <div className="overflow-x-auto my-3 rounded-xl border border-white/[0.08] bg-white/[0.02] shadow-sm">
                                <table className="w-full text-[13px] table-fixed border-collapse" {...props} />
                              </div>
                            ),
                            thead: ({ node, ...props }) => <thead className="bg-primary/10 text-primary/90 text-[12px] font-semibold" {...props} />,
                            th: ({ node, ...props }) => <th className="px-3 py-2 font-semibold border-b border-primary/20 text-center align-middle" {...props} />,
                            td: ({ node, ...props }) => <td className="px-3 py-2 border-b border-white/[0.05] text-gray-300/80 text-center align-middle" {...props} />,
                            tr: ({ node, ...props }) => <tr className="hover:bg-white/[0.03] transition-colors" {...props} />,
                            // 分隔线 - 渐变效果
                            hr: ({ node, ...props }) => <hr className="my-4 border-t border-gradient-to-r from-transparent via-white/10 to-transparent" {...props} />,
                            // 删除线 - 禁用删除线样式，只显示为普通文本
                            del: ({ node, ...props }) => <span className="text-gray-400/80" {...props} />,
                            // 粗体 - 高亮白色
                            strong: ({ node, ...props }) => <strong className="font-bold text-white" {...props} />,
                            // 斜体 - 柔和灰色
                            em: ({ node, ...props }) => <em className="italic text-gray-300/90" {...props} />,
                            // 复选框 - 任务列表
                            input: ({ node, ...props }) => {
                              if (props.type === 'checkbox') {
                                return (
                                  <input 
                                    {...props} 
                                    disabled 
                                    className="mr-2 w-4 h-4 rounded border-primary/30 bg-white/5 text-primary focus:ring-primary/30 cursor-default"
                                  />
                                );
                              }
                              return <input {...props} />;
                            },
                            // 上标/下标
                            sup: ({ node, ...props }) => (
                              <sup className="text-primary text-[10px] font-medium" {...props} />
                            ),
                            sub: ({ node, ...props }) => (
                              <sub className="text-gray-400 text-[10px]" {...props} />
                            ),
                            // 预格式化文本
                            pre: ({ node, ...props }) => (
                              <pre className="bg-[#0d1117] rounded-lg p-3 my-2 overflow-x-auto text-[12px] text-gray-300 border border-white/[0.08]" {...props} />
                            ),
                          }}
                        />
                      </div>

                      {/* 底部收起按钮 - 手机端更明显 */}
                      {!isThinking && (
                        <div className="mt-4 flex justify-center border-t border-white/[0.03] pt-3">
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowReasoning(false);
                            }}
                            className="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-white/[0.05] hover:bg-white/10 border border-white/[0.1] transition-all active:scale-95 group"
                          >
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 rotate-180 group-hover:text-white transition-colors" />
                            <span className="text-[11px] md:text-[12px] text-gray-400 group-hover:text-white font-medium transition-colors">收起</span>
                          </button>
                        </div>
                      )}
                    </div>
                    
                    {/* 内部推理框滚动到底部按钮 */}
                    {showInternalScrollButton && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          scrollReasoningToBottom();
                        }}
                        className="absolute bottom-4 right-4 p-2 rounded-full bg-primary/20 backdrop-blur-sm border border-primary/30 text-primary hover:bg-primary/30 transition-all shadow-lg animate-in fade-in zoom-in duration-200 z-10"
                      >
                        <ChevronDown className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* 媒体展示区 - 独立于气泡之外，类似豆包风格 */}
            {media.length > 0 && (
              <div className={`flex flex-wrap gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
                {media.map((item, index) => (
                  <div key={index} className="relative group overflow-hidden rounded-xl border border-white/10 shadow-lg cursor-zoom-in bg-black/20 hover:border-white/20 transition-all duration-300 hover:shadow-xl hover:scale-[1.02]">
                    {item.type === 'image' && (
                      <img 
                        src={item.url} 
                        alt="media" 
                        className="w-auto h-32 md:h-40 object-cover"
                        onClick={() => setPreviewImage(item.url)}
                      />
                    )}
                    {item.type === 'video' && (
                      <video 
                        src={item.url} 
                        controls 
                        className="w-auto h-32 md:h-40 max-w-[200px]"
                      />
                    )}
                    {item.type === 'audio' && (
                      <div className="w-48 h-12 flex items-center justify-center bg-white/5 p-2">
                        <audio src={item.url} controls className="w-full h-8" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* 文本内容气泡和操作栏 */}
            {(cleanText || (!media.length && !cleanText)) && (
              <>
                {/* 内容气泡 - 采用半透明"磨砂玻璃"质感，优雅悬浮 */}
                <div className={`
                  ${isUser 
                    ? 'bg-[#2b2d31] border border-white/10 rounded-2xl px-3 py-2 text-white max-w-[85%] md:max-w-[75%] text-left text-[15px] md:text-[16px] shadow-md shadow-black/20 w-fit' 
                    : 'bg-transparent px-0 py-0 text-white w-full max-w-full text-left text-[16px] md:text-[17px]'
                  }
                `}>
                  <div className={`prose max-w-none ${isUser ? 'prose-invert' : 'prose-invert'}`}>
                    <ReactMarkdown
                      children={cleanText}
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                      components={{
                        // 移除之前的 img 渲染逻辑，因为已经在外部渲染了
                        img: () => null, 
                        // 移除之前的 video/audio 渲染逻辑，因为已经在外部渲染了
                        video: () => null,
                        audio: () => null,
                        code({ node, className, children, ...props }) {
                          const match = /language-(\w+)/.exec(className || '');
                          const inline = !match;
                          return inline ? (
                            <code className={`px-1.5 py-0.5 rounded-md bg-[#161b22] text-primary text-[14px] border border-white/[0.08] font-mono`} {...props}>
                              {children}
                            </code>
                          ) : (
                            <div className="my-8 rounded-3xl overflow-hidden border border-white/[0.08] bg-[#161b22]">
                              <div className="flex items-center justify-between px-6 py-3 bg-[#0d1117] border-b border-white/[0.06]">
                                <span className="text-[10px] text-text-quaternary font-mono uppercase tracking-[0.2em]">{match?.[1] || 'text'}</span>
                                <button 
                                  onClick={() => navigator.clipboard.writeText(String(children))}
                                  className="text-[10px] text-text-quaternary hover:text-text-secondary flex items-center gap-2 transition-colors uppercase font-bold tracking-wider"
                                >
                                  <Copy className="w-3.5 h-3.5" />
                                  <span>Copy</span>
                                </button>
                              </div>
                              <div className="p-6 overflow-x-auto text-[15px] code-block-wrapper">
                                <SyntaxHighlighter
                                  children={String(children).replace(/\n$/, '')}
                                  style={customCodeTheme as any}
                                  language={match?.[1] || 'text'}
                                  PreTag="div"
                                  customStyle={{ margin: '0', background: 'transparent', padding: '0' }}
                                  wrapLines={false}
                                  showLineNumbers={false}
                                />
                              </div>
                            </div>
                          );
                        },
                        // 段落样式
                        p: ({ node, ...props }) => <p className={`my-2 leading-7 text-[15px] md:text-[16px] text-gray-100`} {...props} />,
                        // 无序列表 - 白色标记
                        ul: ({ node, ...props }) => (
                          <ul className="my-4 pl-6 list-disc marker:text-white/70 marker:text-[16px] space-y-2" {...props} />
                        ),
                        // 有序列表 - 白色数字
                        ol: ({ node, ...props }) => (
                          <ol className="my-4 pl-6 list-decimal marker:text-white/80 marker:font-bold space-y-2" {...props} />
                        ),
                        // 列表项 - 智能识别
                        li: ({ node, ...props }) => {
                          const text = props.children?.toString() || '';
                          const isFolderStructure = text.includes('├──') || text.includes('└──');
                          const isToolCall = text.includes('🧠') || text.includes('🛠️');
                          
                          if (isFolderStructure) {
                             const isFolder = text.includes(':') || text.endsWith('/');
                             const isFile = !isFolder && text.includes('.');
                             let colorClass = 'text-gray-300';
                             if (isFolder) {
                               colorClass = 'text-green-400';
                             } else if (isFile) {
                               colorClass = 'text-blue-400';
                             }
                             return <li className={`font-mono text-[14px] ${colorClass} list-none -ml-4`} {...props} />;
                          }
                          
                          if (isToolCall) {
                            return <li className={`text-yellow-400 leading-relaxed pl-1 text-[15px] md:text-[16px] font-medium`} {...props} />;
                          }
                          
                          return <li className={`text-gray-100 leading-relaxed pl-1 text-[15px] md:text-[16px]`} {...props} />;
                        },
                        // 标题层级 - 统一使用亮白色，清晰醒目
                        h1: ({ node, ...props }) => (
                          <h1 className="text-2xl font-bold my-6 text-white bg-white/[0.08] px-4 py-2 rounded-lg border-l-4 border-white/40" {...props} />
                        ),
                        h2: ({ node, ...props }) => (
                          <h2 className="text-xl font-bold my-5 text-white bg-white/[0.05] px-3 py-1.5 rounded-lg border-l-3 border-white/30 flex items-center gap-2" {...props} />
                        ),
                        h3: ({ node, ...props }) => (
                          <h3 className="text-lg font-semibold my-4 text-white flex items-center gap-2 before:content-['▸'] before:text-white/80" {...props} />
                        ),
                        h4: ({ node, ...props }) => (
                          <h4 className="text-base font-semibold my-3 text-white/90 flex items-center gap-2 before:content-['▪'] before:text-white/70" {...props} />
                        ),
                        h5: ({ node, ...props }) => (
                          <h5 className="text-sm font-semibold my-2 text-white/80" {...props} />
                        ),
                        h6: ({ node, ...props }) => (
                          <h6 className="text-xs font-semibold my-2 text-white/70 uppercase tracking-wider" {...props} />
                        ),
                        // 引用块
                        blockquote: ({ node, ...props }) => (
                          <blockquote className="border-l-4 border-primary/40 pl-4 my-4 py-2 italic text-gray-300 bg-white/[0.03] rounded-r-lg" {...props} />
                        ),
                        // 链接 - 主题色
                        a: ({ node, ...props }) => (
                          <a 
                            {...props} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-primary hover:text-primary/80 underline underline-offset-4 transition-colors"
                          />
                        ),
                        // 图片 - 智能识别视频/音频
                        img: ({ node, ...props }) => {
                          const src = props.src || '';
                          // 支持带参数的 URL (如 ?token=...)
                          const isVideo = /\.(mp4|webm|ogg|mov)(?:\?|$)/i.test(src);
                          const isAudio = /\.(mp3|wav|ogg|m4a)(?:\?|$)/i.test(src);

                          if (isVideo) {
                            return (
                              <div className="my-4 rounded-2xl overflow-hidden border border-white/[0.08] shadow-xl bg-black/20">
                                <video 
                                  src={src} 
                                  controls 
                                  className="max-w-full w-full" 
                                  preload="metadata"
                                />
                              </div>
                            );
                          }

                          if (isAudio) {
                            return (
                              <div className="my-4 rounded-xl border border-white/[0.08] shadow-md bg-white/[0.05] p-2">
                                <audio 
                                  src={src} 
                                  controls 
                                  className="w-full" 
                                />
                              </div>
                            );
                          }

                          return (
                            <img 
                              {...props} 
                              className="max-w-[200px] max-h-[200px] w-auto h-auto rounded-xl my-2 border border-white/[0.08] shadow-md object-cover cursor-zoom-in hover:opacity-90 transition-opacity"
                              loading="lazy"
                              onClick={() => setPreviewImage(src)}
                            />
                          );
                        },
                        // 视频标签支持
                        video: ({ node, ...props }) => (
                          <div className="my-4 rounded-2xl overflow-hidden border border-white/[0.08] shadow-xl bg-black/20">
                            <video 
                              {...props} 
                              className="max-w-full w-full" 
                              preload="metadata"
                            />
                          </div>
                        ),
                        // 音频标签支持
                        audio: ({ node, ...props }) => (
                          <div className="my-4 rounded-xl border border-white/[0.08] shadow-md bg-white/[0.05] p-2">
                            <audio 
                              {...props} 
                              className="w-full" 
                            />
                          </div>
                        ),
                        // 表格 - 主题色表头
                        table: ({ node, ...props }) => (
                          <div className="overflow-x-auto my-6 rounded-2xl border border-white/[0.08] bg-white/[0.02] shadow-sm">
                            <table className="w-full text-[14px] md:text-[15px] table-fixed border-collapse" {...props} />
                          </div>
                        ),
                        thead: ({ node, ...props }) => <thead className="bg-primary/10 text-primary/90 text-xs font-semibold tracking-wider" {...props} />,
                        th: ({ node, ...props }) => <th className="px-4 py-3 font-semibold border-b border-primary/20 text-center align-middle" {...props} />,
                        td: ({ node, ...props }) => <td className="px-4 py-3 border-b border-white/[0.05] text-gray-300/90 text-center align-middle" {...props} />,
                        tr: ({ node, ...props }) => <tr className="hover:bg-white/[0.03] transition-colors" {...props} />,
                        // 分隔线 - 渐变
                        hr: ({ node, ...props }) => <hr className="my-8 border-t border-gradient-to-r from-transparent via-white/10 to-transparent" {...props} />,
                        // 删除线 - 禁用删除线样式，只显示为普通文本
                        del: ({ node, ...props }) => <span className="text-gray-400/80" {...props} />,
                        // 复选框
                        input: ({ node, ...props }) => {
                          if (props.type === 'checkbox') {
                            return (
                              <input 
                                {...props} 
                                disabled 
                                className="mr-2 w-4 h-4 rounded border-primary/30 bg-white/5 text-primary focus:ring-primary/30 cursor-default"
                              />
                            );
                          }
                          return <input {...props} />;
                        },
                        // 上标/下标
                        sup: ({ node, ...props }) => (
                          <sup className="text-primary text-xs font-medium" {...props} />
                        ),
                        sub: ({ node, ...props }) => (
                          <sub className="text-gray-400 text-xs" {...props} />
                        ),
                        // 粗体/斜体
                        strong: ({ node, ...props }) => (
                          <strong className="font-bold text-white" {...props} />
                        ),
                        em: ({ node, ...props }) => (
                          <em className="italic text-gray-200" {...props} />
                        ),
                        // 预格式化文本
                        pre: ({ node, ...props }) => (
                          <pre className="bg-[#0d1117] rounded-xl p-4 my-3 overflow-x-auto text-[13px] text-gray-300 border border-white/[0.08]" {...props} />
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
                  
                  {/* 时间戳 - 安全处理 */}
                  <span className="text-xs text-text-tertiary font-medium tracking-wide opacity-80 px-2 select-none">
                    {(() => {
                      try {
                        return format(new Date(message.timestamp), 'HH:mm');
                      } catch (e) {
                        return '';
                      }
                    })()}
                  </span>
                </div>
              </>
            )}
            
          </div>
        </div>
      </div>
      {/* 图片预览 Modal */}
      {previewImage && <ImagePreview src={previewImage} onClose={() => setPreviewImage(null)} />}
    </div>
  );
};

export default MessageItem;