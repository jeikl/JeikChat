import { useRef, useEffect, useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { useSettingsStore } from '@/stores/settingsStore';
import MessageItem from './MessageItem';
import InputArea from './InputArea';
import { Bot, Sparkles } from 'lucide-react';

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
  const { sessions, currentSessionId, isLoading, isStreaming, sendMessage, stopGenerating } = useChatStore();
  const { selectedToolIds } = useSettingsStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputContainerRef = useRef<HTMLDivElement>(null);
  const [inputHeight, setInputHeight] = useState(0);
  const [viewportHeight, setViewportHeight] = useState('100%');

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

  const currentSession = sessions.find(session => session.id === currentSessionId);
  const messages = currentSession ? currentSession.messages : [];

  const scrollToBottom = (instant = false) => {
    if (messagesEndRef.current) {
      // 只有在消息列表不为空时才滚动
      if (messages.length > 0) {
        messagesEndRef.current.scrollIntoView({ behavior: instant ? 'auto' : 'smooth' });
      }
    }
  };

  // 仅在消息数量变化或流式输出开始时进行平滑滚动
  useEffect(() => {
    // 首次加载或切换会话时，如果消息很少，不要强制滚到底部，而是让它自然显示
    // 但如果有足够多的消息需要滚动，才执行
    scrollToBottom(isStreaming);
  }, [messages.length, isStreaming, currentSessionId]);

  // 流式输出内容变化时，使用即时滚动以减少抖动
  useEffect(() => {
    if (isStreaming) {
      scrollToBottom(true);
    }
  }, [messages]);

  const handleSend = async (content: string) => {
    await sendMessage(content, selectedToolIds);
  };

  return (
    <div className="relative flex flex-col w-full h-[100dvh] mesh-gradient overflow-hidden">
      {/* 动态背景光源 */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 blur-[120px] rounded-full pointer-events-none animate-pulse duration-[10000ms]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/5 blur-[120px] rounded-full pointer-events-none animate-pulse duration-[15000ms]" />
      
      {/* 消息展示区 - 使用 padding-bottom 动态避让输入框 */}
      <div 
        ref={scrollContainerRef} 
        className="absolute inset-0 w-full h-full overflow-y-auto scrollbar-thin z-10"
        style={{ paddingBottom: inputHeight }}
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-4 py-2 md:py-12 max-w-6xl mx-auto w-full min-h-full">
            <div className="flex-1" /> {/* 顶部弹簧 */}
            <div className="w-full flex flex-col items-center">
              {/* ... 保持原有欢迎页内容不变 ... */}
              <div className="relative mb-3 md:mb-8 group">
                <div className="w-12 h-12 md:w-28 md:h-28 rounded-[1rem] md:rounded-[2rem] bg-gradient-to-br from-primary via-purple-600 to-pink-500 flex items-center justify-center shadow-2xl shadow-primary/20 transform group-hover:scale-105 transition-transform duration-500">
                  <Bot className="w-6 h-6 md:w-14 md:h-14 text-white" />
                </div>
                <div className="absolute -bottom-1 -right-1 md:-bottom-2 md:-right-2 w-5 h-5 md:w-10 md:h-10 rounded-full bg-white dark:bg-bg-secondary flex items-center justify-center shadow-xl border-2 md:border-4 border-bg-primary">
                  <Sparkles className="w-2.5 h-2.5 md:w-5 md:h-5 text-amber-500 animate-pulse" />
                </div>
              </div>
              
              <div className="text-center mb-6 md:mb-12">
                <h1 className="text-lg md:text-4xl lg:text-5xl font-extrabold mb-1.5 md:mb-4 tracking-tight">
                  <span className="text-text-primary">您好，我是 </span>
                  <span className="bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">
                    JeikChat
                  </span>
                </h1>
                <p className="text-text-secondary text-[11px] md:text-base max-w-lg mx-auto leading-relaxed opacity-90">
                  超越对话，开启智能交互的新维度。
                  <br className="hidden md:block" />
                  我是您的全能 AI 助手，随时准备为您提供帮助。
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
            <div className="flex-[1.2]" /> {/* 底部弹簧，比顶部稍大以视觉平衡 */}
          </div>
        ) : (
          <div className="w-full max-w-[1400px] mx-auto py-2 md:py-4 min-h-full px-3 md:px-8 flex flex-col">
            <div className="mt-auto flex flex-col gap-0">
              {messages.map((message) => (
                <MessageItem key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>

      {/* 底部输入框容器 - 绝对定位到底部，通过 ResizeObserver 动态计算高度 */}
      <div 
        ref={inputContainerRef}
        className="absolute bottom-0 left-0 right-0 z-50 w-full backdrop-blur-md bg-gradient-to-t from-bg-primary/95 via-bg-primary/70 to-transparent pb-2"
      >
        <div className="max-w-[1400px] mx-auto w-full flex justify-center px-0">
          <InputArea 
            onSend={handleSend}
            onStop={stopGenerating}
            isStreaming={isStreaming}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;