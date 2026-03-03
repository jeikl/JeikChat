import { NavLink, useNavigate } from 'react-router-dom';
import { 
  MessageCircle, 
  BookOpen, 
  Settings, 
  Plus,
  Trash2,
  MessageSquare,
  Wrench,
  Copy,
  Check
} from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { useState } from 'react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface SidebarProps {
  isOpen: boolean;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

const Sidebar = ({ isOpen, mobileOpen, onCloseMobile }: SidebarProps) => {
  const navigate = useNavigate();
  const { sessions, currentSessionId, setCurrentSession, addSession, deleteSession, updateSession } = useChatStore();
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const createNewSession = () => {
    const newSession = {
      id: `session_${Date.now()}`,
      title: '新对话',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    addSession(newSession);
  };

  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (confirm('确定要删除这个对话吗？')) {
      deleteSession(sessionId);
    }
  };

  const handleCopySession = async (e: React.MouseEvent, session: typeof sessions[0]) => {
    e.stopPropagation();
    const sessionData = {
      title: session.title,
      messages: session.messages,
      createdAt: session.createdAt,
      updatedAt: session.updatedAt,
    };
    
    try {
      await navigator.clipboard.writeText(JSON.stringify(sessionData, null, 2));
      setCopiedId(session.id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('复制失败:', err);
    }
  };

  return (
    <>
      {mobileOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-[90] lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside className={`
        fixed lg:relative z-[100] lg:z-0
        top-0 left-0 h-full
        bg-bg-secondary/95 backdrop-blur-xl
        border-r border-border/40
        transition-all duration-300 ease-in-out
        ${isOpen ? 'w-[280px]' : 'w-0 lg:w-[80px]'}
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        flex flex-col shadow-2xl lg:shadow-none
      `}>
        <div className="p-6">
          <div className={`flex items-center gap-3 ${!isOpen && 'lg:justify-center'}`}>
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-primary/20">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
            {isOpen && (
              <span className="font-bold text-xl text-text-primary tracking-tight">
                JeikChat
              </span>
            )}
          </div>
        </div>

        <div className="px-4 mb-6">
          <button
            onClick={createNewSession}
            className={`
              w-full flex items-center gap-3 px-4 py-3.5
              bg-primary hover:bg-primary-hover
              text-white rounded-2xl
              transition-all duration-300 shadow-lg shadow-primary/20 hover:shadow-primary/30
              ${!isOpen && 'lg:justify-center lg:px-2'}
            `}
          >
            <Plus className="w-5 h-5 flex-shrink-0" />
            {isOpen && <span className="font-semibold">开启新对话</span>}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 space-y-1 scrollbar-none">
          {isOpen && <div className="px-3 mb-2 text-[11px] font-bold text-text-quaternary uppercase tracking-widest">最近对话</div>}
          {sessions.length === 0 ? (
            <div className={`text-center text-text-tertiary py-8 ${!isOpen && 'lg:hidden'}`}>
              <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              {isOpen && <p className="text-sm">暂无对话记录</p>}
            </div>
          ) : (
            <div className="space-y-1">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => {
                    navigate('/chat');
                    setCurrentSession(session.id);
                    onCloseMobile();
                  }}
                  className={`
                    group relative flex items-center gap-3 px-3 py-3 rounded-xl cursor-pointer transition-all duration-200
                    ${currentSessionId === session.id 
                      ? 'bg-primary/10 text-primary shadow-sm shadow-primary/5' 
                      : 'text-text-secondary hover:bg-bg-tertiary/50 hover:text-text-primary'}
                    ${!isOpen && 'lg:justify-center'}
                  `}
                >
                  <MessageCircle className={`w-5 h-5 flex-shrink-0 ${currentSessionId === session.id ? 'text-primary' : 'text-text-quaternary group-hover:text-text-primary'}`} />
                  {isOpen && (
                    <>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium truncate ${currentSessionId === session.id ? 'text-primary' : ''}`}>{session.title}</p>
                        <p className={`text-[10px] ${currentSessionId === session.id ? 'text-primary/60' : 'text-text-tertiary'}`}>
                          {format(session.updatedAt, 'MM/dd HH:mm', { locale: zhCN })}
                        </p>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                        <button
                          onClick={(e) => handleCopySession(e, session)}
                          className="p-1.5 hover:bg-primary/10 hover:text-primary rounded-lg transition-all"
                          title="复制会话内容"
                        >
                          {copiedId === session.id ? (
                            <Check className="w-4 h-4 text-green-500" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSession(e, session.id);
                          }}
                          className="p-1.5 hover:bg-error/10 hover:text-error rounded-lg transition-all"
                          title="删除会话"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-4 mt-auto border-t border-border/10 space-y-1">
          <NavLink
            to="/knowledge"
            onClick={onCloseMobile}
            className={({ isActive }) => `
              flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
              ${isActive ? 'bg-primary/10 text-primary' : 'text-text-secondary hover:bg-bg-tertiary/50 hover:text-text-primary'}
              ${!isOpen && 'lg:justify-center lg:px-2'}
            `}
          >
            <BookOpen className="w-5 h-5" />
            {isOpen && <span className="text-sm font-semibold">RAG 知识库</span>}
          </NavLink>
          
          <NavLink
            to="/agent-tools"
            onClick={onCloseMobile}
            className={({ isActive }) => `
              flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
              ${isActive ? 'bg-primary/10 text-primary' : 'text-text-secondary hover:bg-bg-tertiary/50 hover:text-text-primary'}
              ${!isOpen && 'lg:justify-center lg:px-2'}
            `}
          >
            <Wrench className="w-5 h-5" />
            {isOpen && <span className="text-sm font-semibold">Agent 工具</span>}
          </NavLink>

          <NavLink
            to="/settings"
            onClick={onCloseMobile}
            className={({ isActive }) => `
              flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
              ${isActive ? 'bg-primary/10 text-primary' : 'text-text-secondary hover:bg-bg-tertiary/50 hover:text-text-primary'}
              ${!isOpen && 'lg:justify-center lg:px-2'}
            `}
          >
            <Settings className="w-5 h-5" />
            {isOpen && <span className="text-sm font-semibold">设置中心</span>}
          </NavLink>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
