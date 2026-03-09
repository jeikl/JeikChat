import { useRef, useEffect, useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
// import { useSettingsStore } from '@/stores/settingsStore';
import MessageItem from './MessageItem';
import InputArea from './InputArea';
import { Bot, ChevronDown } from 'lucide-react';

const PROMPTS = [
  {
    title: '分析企业财报数据',
    icon: '📊',
    description: '快速提取关键财务指标，分析营收、利润及现金流状况，为投资决策提供深度参考。'
  },
  {
    title: '帮我构思一个 Agent 方案',
    icon: '⚡',
    description: '针对特定场景，设计一套高效的 AI 智能体工作流，包括角色设定、工具调用及任务拆解。'
  },
  {
    title: '设计一个现代化的 AI UI',
    icon: '🎨',
    description: '探讨当下最流行的 AI 交互界面趋势，从布局到交互细节，打造极致的用户体验。'
  },
  {
    title: '关于 RAG 技术的深度分析',
    icon: '🔍',
    description: '深入了解检索增强生成技术的核心原理，包括向量数据库、嵌入模型及重排序策略。'
  }
];

const ChatContainer = () => {
  const { sessions, currentSessionId, isLoading, isStreaming, sendMessage, stopGeneration } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputContainerRef = useRef<HTMLDivElement>(null);
  const [inputHeight, setInputHeight] = useState(0);
  const [logoError, setLogoError] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const isUserScrolledUpRef = useRef(false);

  const currentSession = sessions.find(session => session.id === currentSessionId);
  const messages = currentSession ? currentSession.messages : [];

  // 进入页面时，如果没有选中会话且不在新对话状态，自动进入默认会话
  useEffect(() => {
    // 注意：不自动设置默认会话，因为用户可能点击了"开启新对话"
    // 新会话会在用户发送第一条消息时自动创建
  }, []);

  // 监听输入框高度变化
  useEffect(() => {
    if (!inputContainerRef.current) return;

    const updateHeight = () => {
      if (inputContainerRef.current) {
        setInputHeight(inputContainerRef.current.offsetHeight);
      }
    };

    // 初始测量
    updateHeight();

    const resizeObserver = new ResizeObserver(() => {
      updateHeight();
    });

    resizeObserver.observe(inputContainerRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  // 处理移动端软键盘弹出导致的布局问题
  useEffect(() => {
    // 防止移动端键盘顶起页面
    const metaViewport = document.querySelector('meta[name=viewport]');
    if (metaViewport) {
      metaViewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, interactive-widget=resizes-content');
    }
  }, []);

  // 处理窗口大小变化时保持滚动位置在底部
  useEffect(() => {
    const handleResize = () => {
      // 只有在有消息且用户没有手动上滑时才滚动到底部
      if (scrollContainerRef.current && messages.length > 0 && !isUserScrolledUpRef.current) {
        scrollToBottom(true);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [messages.length]);

  // 监听全局滚动事件
  const handleGlobalScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    // 使用更严格的阈值来判定是否在底部，并增加防抖判断
    const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
    
    if (!isAtBottom) {
      // 只要不在底部，且有明显的上滑动作，就标记为已上滑
      isUserScrolledUpRef.current = true;
      setShowScrollButton(true);
    } else {
      isUserScrolledUpRef.current = false;
      setShowScrollButton(false);
    }
  };

  // 全局滚动到底部
  const scrollToBottom = (instant = false) => {
    if (scrollContainerRef.current) {
      if (instant) {
        scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
      } else {
        scrollContainerRef.current.scrollTo({
          top: scrollContainerRef.current.scrollHeight,
          behavior: 'smooth'
        });
      }
      isUserScrolledUpRef.current = false;
      setShowScrollButton(false);
    }
  };

  // 自动滚动逻辑 - 只有在非上滑状态且正在生成内容时才执行
  useEffect(() => {
    if (scrollContainerRef.current && !isUserScrolledUpRef.current && isStreaming) {
      scrollToBottom(true);
    }
  }, [messages, isStreaming]);

  // 当会话改变或新消息增加时，如果没上滑，则滚到底部
  useEffect(() => {
    if (!isUserScrolledUpRef.current) {
      scrollToBottom(false);
    }
  }, [messages.length, currentSessionId]);

  const handleSend = async (content: string) => {
    // 直接调用 sendMessage，让 sendMessage 内部处理会话创建逻辑
    // 如果 currentSessionId 为 null，sendMessage 会自动创建新会话
    console.log('handleSend 调用:', { content, currentSessionId });
    await sendMessage(content, currentSessionId || undefined);
  };

  return (
    <div className="relative flex flex-col w-full h-full mesh-gradient overflow-hidden">
      {/* 动态背景光源 */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 blur-[120px] rounded-full pointer-events-none animate-pulse duration-[10000ms]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/5 blur-[120px] rounded-full pointer-events-none animate-pulse duration-[15000ms]" />
      
      {/* 消息展示区 - 使用 Spacer 替代 padding-bottom 以避免布局计算问题 */}
      <div
        ref={scrollContainerRef}
        onScroll={handleGlobalScroll}
        className="absolute inset-0 w-full h-full overflow-y-auto chat-scrollbar z-10"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-4 py-2 md:py-12 max-w-6xl mx-auto w-full min-h-full">
            <div className="flex-1" /> {/* 顶部弹簧 */}
            <div className="w-full flex flex-col items-center">
              {/* ... 保持原有欢迎页内容不变 ... */}
              <div className="relative mb-3 md:mb-8 group">
                <div className="relative">
                  {/* 外发光效果 */}
                  <div className={`absolute -inset-1 rounded-full bg-gradient-to-br from-primary via-purple-600 to-pink-500 opacity-70 blur-md group-hover:opacity-100 group-hover:blur-lg transition-all duration-500 ${logoError ? 'hidden' : ''}`}></div>
                  
                  {/* LOGO 主体 */}
                  <div className={`relative w-12 h-12 md:w-28 md:h-28 flex items-center justify-center transform group-hover:scale-105 transition-transform duration-500 z-10 ${logoError ? 'rounded-full bg-gradient-to-br from-primary via-purple-600 to-pink-500 shadow-2xl shadow-primary/20' : ''}`}>
                    {!logoError ? (
                      <img 
                        src="/logo.png" 
                        alt="Logo" 
                        className="w-full h-full object-cover rounded-full shadow-2xl ring-2 ring-white/10" 
                        onError={() => setLogoError(true)} 
                      />
                    ) : (
                      <Bot className="w-6 h-6 md:w-14 md:h-14 text-white" />
                    )}
                  </div>
                </div>
              </div>
              
              <div className="text-center mb-6 md:mb-12">
                <h1 className="text-lg md:text-4xl lg:text-5xl font-extrabold mb-1.5 md:mb-4 tracking-tight">
                  <span className="text-text-primary"> </span>
                  <span className="bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">
                    JeikChat
                  </span>
                </h1>
                <p className="text-text-secondary text-[11px] md:text-base max-w-lg mx-auto leading-relaxed opacity-90">
                  超越对话，开启智能交互的新维度。
                  <br />
                  全能 AI 助手，可快速集成tools、MCP、API等三方服务。
                  <br />
                  随时为您服务
                </p>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-2 gap-2 md:gap-4 w-full max-w-4xl px-1 md:px-0">
                {PROMPTS.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => handleSend(prompt.title)}
                    disabled={isLoading}
                    className="p-2.5 md:p-5 text-left bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.05] hover:border-white/[0.1] rounded-xl md:rounded-2xl transition-all duration-300 group disabled:opacity-50"
                  >
                    <div className="flex items-start gap-2.5 md:gap-4">
                      <div className="w-7 h-7 md:w-10 md:h-10 rounded-lg md:rounded-xl bg-white/[0.03] flex items-center justify-center text-base md:text-xl group-hover:scale-110 transition-transform duration-300">
                        {prompt.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-text-primary text-xs md:text-base mb-0.5 md:mb-1 group-hover:text-primary transition-colors tracking-tight truncate">
                          {prompt.title}
                        </h3>
                        <p className="text-[10px] md:text-xs text-text-tertiary line-clamp-2 leading-relaxed opacity-70">
                          {prompt.description}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
            <div className="flex-[1.2]" /> {/* 底部弹簧 */}
            {/* 底部 Spacer */}
            <div style={{ height: Math.max(0, inputHeight - 10) }} className="flex-shrink-0 w-full" />
          </div>
        ) : (
          <div className="w-full max-w-[1400px] mx-auto py-2 md:py-4 min-h-full px-3 md:px-8 flex flex-col">
            <div className="mt-auto flex flex-col gap-0">
              {messages.map((message) => (
                <MessageItem key={message.id} message={message} />
              ))}
              {/* 底部 Spacer - 确保内容不被输入框遮挡，但允许部分重叠以减少视觉空隙 */}
              <div style={{ height: Math.max(0, inputHeight - 10) }} className="flex-shrink-0 w-full" />
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>

      {/* 底部输入框容器 - 移除毛玻璃背景，改为透明，并重新定位滚动按钮 */}
      <div 
        ref={inputContainerRef}
        className="fixed lg:absolute bottom-0 left-0 right-0 z-50 w-full pb-0 pointer-events-none"
        style={{
          paddingBottom: 'env(safe-area-inset-bottom)'
        }}
      >
        <div className="max-w-[1400px] mx-auto w-full relative flex flex-col items-center px-0">
          {/* 全局滚动到底部按钮 - 移动到左侧空白处并提高位置 */}
          {showScrollButton && (
            <div className="absolute left-4 bottom-[180px] md:left-8 md:bottom-[220px] pointer-events-auto">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  scrollToBottom();
                }}
                className="p-2.5 rounded-full bg-[#1E1E1E] border border-white/10 text-primary hover:text-white hover:bg-primary transition-all shadow-2xl animate-in fade-in zoom-in duration-300 group"
                title="滚动到底部"
              >
                <ChevronDown className="w-5 h-5 group-hover:translate-y-0.5 transition-transform" />
              </button>
            </div>
          )}
          
          <InputArea 
            onSend={handleSend}
            onStop={stopGeneration}
            disabled={isStreaming}
            isStreaming={isStreaming}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;