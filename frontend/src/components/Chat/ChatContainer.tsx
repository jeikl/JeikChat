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
  const { sessions, currentSessionId, isLoading, sendMessage } = useChatStore();
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

  const handleSend = async (content: string) => {
    await sendMessage(content, selectedToolIds);
  };

  return (
    <div className="h-full flex flex-col bg-bg-primary">
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-4">
          <div className="relative mb-6">
            <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-primary via-purple-500 to-pink-500 flex items-center justify-center shadow-2xl shadow-purple-500/20 animate-pulse">
              <Bot className="w-12 h-12 text-white" />
            </div>
            <div className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
          </div>
          
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary via-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
            AI 智能客服
          </h2>
          <p className="text-text-tertiary mb-10">有什么可以帮助您的？</p>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl w-full">
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
        <div className="flex-1 overflow-y-auto">
          <div className="pb-4">
            {messages.map((message) => (
              <MessageItem key={message.id} message={message} />
            ))}
            
            {isLoading && (
              <div className="flex items-start gap-4 px-4 md:px-12 py-4">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="bg-bg-secondary border border-border rounded-2xl rounded-tl-sm px-4 py-3 mt-0.5">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      <InputArea 
        onSend={handleSend}
        disabled={isLoading}
      />
    </div>
  );
};

export default ChatContainer;