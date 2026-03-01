import { useRef, useEffect } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { useSettingsStore } from '@/stores/settingsStore';
import MessageItem from './MessageItem';
import InputArea from './InputArea';
import { Bot, Sparkles } from 'lucide-react';

const PROMPTS = [
  '如何创建数据库？',
  '如何连接数据库？',
  '如何进行数据迁移？',
  '如何优化查询性能？',
];

const ChatContainer = () => {
  const { sessions, currentSessionId, isLoading, sendMessage, stopGenerating } = useChatStore();
  const { selectedToolIds } = useSettingsStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const currentSession = sessions.find(session => session.id === currentSessionId);
  const messages = currentSession ? currentSession.messages : [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (content: string, reasoning?: 'auto' | boolean) => {
    await sendMessage(content, selectedToolIds, reasoning);
  };

  const handleStop = () => {
    stopGenerating();
  };

  return (
    <div className="h-full flex flex-col bg-bg-primary">
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-4 pt-10 pb-32 md:pb-10">
          <div className="relative mb-4 sm:mb-6">
            <div className="w-16 h-16 sm:w-20 sm:h-20 md:w-24 md:h-24 rounded-2xl bg-gradient-to-br from-primary via-purple-500 to-pink-500 flex items-center justify-center shadow-2xl shadow-purple-500/20 animate-pulse">
              <Bot className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 text-white" />
            </div>
            <div className="absolute -bottom-1 -right-1 w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg">
              <Sparkles className="w-3 h-3 sm:w-3.5 sm:h-3.5 md:w-4 md:h-4 text-white" />
            </div>
          </div>
          
          <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold bg-gradient-to-r from-primary via-purple-400 to-pink-400 bg-clip-text text-transparent mb-1 sm:mb-2 text-center">
            JeikChat-多模型智能体bot
          </h2>
          <p className="text-text-tertiary mb-4 sm:mb-6 md:mb-10 text-center text-xs sm:text-sm md:text-base px-4">有什么可以帮助您的？</p>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 max-w-2xl w-full">
            {PROMPTS.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleSend(prompt)}
                disabled={isLoading}
                className="p-4 text-left bg-bg-secondary/50 hover:bg-bg-secondary border border-border/50 hover:border-primary/30 rounded-xl transition-all duration-300 text-text-secondary hover:text-text-primary hover:shadow-lg hover:shadow-primary/5 disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                <span className="group-hover:translate-x-1 transition-transform inline-block">{prompt}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto pb-20 md:pb-4">
          <div className="pb-4">
            {messages.map((message) => (
              <MessageItem key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      <div className="fixed bottom-0 left-0 right-0 md:relative md:sticky md:bottom-auto">
        <InputArea 
          onSend={handleSend}
          onStop={handleStop}
          disabled={isLoading}
          isGenerating={isLoading}
        />
      </div>
    </div>
  );
};

export default ChatContainer;