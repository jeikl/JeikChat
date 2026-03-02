import { useRef, useEffect } from 'react';
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

  const currentSession = sessions.find(session => session.id === currentSessionId);
  const messages = currentSession ? currentSession.messages : [];

  const scrollToBottom = (instant = false) => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: instant ? 'auto' : 'smooth' });
    }
  };

  // 仅在消息数量变化或流式输出开始时进行平滑滚动
  useEffect(() => {
    scrollToBottom(isStreaming);
  }, [messages.length, isStreaming]);

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
    <div className="fixed inset-0 lg:left-[var(--sidebar-width)] flex flex-col mesh-gradient overflow-hidden h-screen">
      {/* 动态背景光源 */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 blur-[120px] rounded-full pointer-events-none animate-pulse duration-[10000ms]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/5 blur-[120px] rounded-full pointer-events-none animate-pulse duration-[15000ms]" />
      
      {/* 消息展示区 - 增加底部 padding 以免被输入框遮挡 */}
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto scrollbar-thin relative z-10 flex flex-col">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center px-4 py-12 max-w-6xl mx-auto w-full">
            {/* ... 保持原有欢迎页内容不变 ... */}
            <div className="relative mb-8 group">
              <div className="w-20 h-20 sm:w-24 sm:h-24 md:w-28 md:h-28 rounded-[2rem] bg-gradient-to-br from-primary via-purple-600 to-pink-500 flex items-center justify-center shadow-2xl shadow-primary/20 transform group-hover:scale-105 transition-transform duration-500">
                <Bot className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 text-white" />
              </div>
              <div className="absolute -bottom-2 -right-2 w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-white dark:bg-bg-secondary flex items-center justify-center shadow-xl border-4 border-bg-primary">
                <Sparkles className="w-4 h-4 sm:w-5 h-5 text-amber-500 animate-pulse" />
              </div>
            </div>
            
            <div className="text-center mb-12">
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold mb-4 tracking-tight">
                <span className="text-text-primary">您好，我是 </span>
                <span className="bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">
                  JeikChat
                </span>
              </h1>
              <p className="text-text-secondary text-sm sm:text-base md:text-lg max-w-lg mx-auto leading-relaxed opacity-90">
                超越对话，开启智能交互的新维度。
                <br className="hidden sm:block" />
                我是您的全能 AI 助手，随时准备为您提供帮助。
              </p>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-4xl">
              {PROMPTS.map((prompt, index) => (
                <button
                  key={index}
                  onClick={() => handleSend(prompt.title)}
                  disabled={isLoading}
                  className="p-5 text-left bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.05] hover:border-white/[0.1] rounded-2xl transition-all duration-300 group disabled:opacity-50"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-xl bg-white/[0.03] flex items-center justify-center text-xl group-hover:scale-110 transition-transform duration-300">
                      {prompt.icon}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-text-primary mb-1 group-hover:text-primary transition-colors tracking-tight">
                        {prompt.title}
                      </h3>
                      <p className="text-xs text-text-tertiary line-clamp-2 leading-relaxed opacity-70">
                        {prompt.description}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="w-full max-w-[1400px] mx-auto py-6 flex-1">
            <div className="flex flex-col min-h-full">
              {messages.map((message) => (
                <MessageItem key={message.id} message={message} />
              ))}
              {/* 底部占位，高度等于输入框高度 + 间距 */}
              <div className="h-48 flex-shrink-0" />
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>

      {/* 固定底部的输入框容器 - 极低位置，贴合底部边缘 */}
      <div className="absolute bottom-0 left-0 right-0 z-30 pointer-events-none">
        <div className="max-w-[1400px] mx-auto w-full flex justify-center pb-0.5 px-6 pointer-events-auto">
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