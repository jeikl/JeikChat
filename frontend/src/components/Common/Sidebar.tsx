import { NavLink, useNavigate } from 'react-router-dom';
import { 
  MessageCircle, 
  BookOpen, 
  Settings, 
  Plus,
  Trash2,
  MessageSquare,
  Wrench
} from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
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

  return (
    <>
      {mobileOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside className={`
        fixed lg:relative z-50 lg:z-0
        top-0 left-0 h-full
        glass-effect
        border-r border-border
        transition-all duration-300 ease-in-out
        ${isOpen ? 'w-64' : 'w-0 lg:w-16'}
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        flex flex-col
      `}>
        <div className="p-4 border-b border-border">
          <div className={`flex items-center gap-3 ${!isOpen && 'lg:justify-center'}`}>
            <div className="w-8 h-8 rounded-lg gradient-bg flex items-center justify-center flex-shrink-0 shadow-md">
              <MessageSquare className="w-5 h-5 text-white" />
            </div>
            {isOpen && (
              <span className="font-semibold text-text-primary truncate">
                AI 客服
              </span>
            )}
          </div>
        </div>

        <div className="p-2">
          <button
            onClick={createNewSession}
            className={`
              w-full flex items-center gap-3 px-3 py-2.5
              bg-primary hover:bg-primary-hover
              text-white rounded-lg
              transition-all duration-200 shadow-md hover:shadow-lg
              ${!isOpen && 'lg:justify-center lg:px-2'}
            `}
          >
            <Plus className="w-5 h-5 flex-shrink-0" />
            {isOpen && <span className="font-medium">新建对话</span>}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="px-3 py-2">
            <NavLink
              to="/chat"
              className={({ isActive }) => `
                sidebar-item ${isActive ? 'active' : ''} ${!isOpen && 'lg:justify-center'}
              `}
              onClick={onCloseMobile}
            >
              <MessageCircle className="w-5 h-5" />
              {isOpen && <span>对话</span>}
            </NavLink>
            
            {isOpen && (
              <h3 className="text-xs font-medium text-text-tertiary uppercase tracking-wider mb-2 mt-4">
                对话历史
              </h3>
            )}
            
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
                      group flex items-center gap-3 px-3 py-2 rounded-lg
                      cursor-pointer transition-all duration-200
                      ${currentSessionId === session.id 
                        ? 'selected-item' 
                        : 'hover:bg-bg-tertiary text-text-secondary hover:text-text-primary'
                      }
                      ${!isOpen && 'lg:justify-center lg:px-2'}
                    `}
                  >
                    <MessageCircle className={`w-4 h-4 flex-shrink-0 ${currentSessionId === session.id ? 'text-white' : ''}`} />
                    {isOpen && (
                      <>
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium truncate ${currentSessionId === session.id ? 'text-white' : ''}`}>{session.title}</p>
                          <p className={`text-xs ${currentSessionId === session.id ? 'text-white/70' : 'text-text-tertiary'}`}>
                            {format(session.updatedAt, 'MM/dd HH:mm', { locale: zhCN })}
                          </p>
                        </div>
                        <button
                          onClick={(e) => handleDeleteSession(e, session.id)}
                          className={`opacity-0 group-hover:opacity-100 p-1 hover:bg-error/10 hover:text-error rounded transition-all ${currentSessionId === session.id ? 'group-hover:text-white' : ''}`}
                        >
                          <Trash2 className={`w-4 h-4 ${currentSessionId === session.id ? 'text-white/70 group-hover:text-white' : 'text-text-tertiary'}`} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            // 这里需要实现重命名功能
                            const newName = prompt('请输入新的对话名称:', session.title);
                            if (newName && newName.trim() !== session.title) {
                              // 更新会话标题
                              updateSession(session.id, { title: newName.trim() });
                            }
                          }}
                          className={`opacity-0 group-hover:opacity-100 p-1 hover:bg-text-secondary/10 hover:text-text-secondary rounded transition-all ml-1 ${currentSessionId === session.id ? 'group-hover:text-white' : ''}`}
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`w-4 h-4 ${currentSessionId === session.id ? 'text-white/70 group-hover:text-white' : 'text-text-tertiary'}`}>
                            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                          </svg>
                        </button>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="p-2 border-t border-border">
          <NavLink
            to="/agent-tools"
            className={({ isActive }) => `
              sidebar-item ${isActive ? 'active' : ''} ${!isOpen && 'lg:justify-center'}
            `}
            onClick={onCloseMobile}
          >
            <Wrench className="w-5 h-5" />
            {isOpen && <span>Agent Tools</span>}
          </NavLink>
          
          <NavLink
            to="/knowledge"
            className={({ isActive }) => `
              sidebar-item ${isActive ? 'active' : ''} ${!isOpen && 'lg:justify-center'}
            `}
            onClick={onCloseMobile}
          >
            <BookOpen className="w-5 h-5" />
            {isOpen && <span>知识库</span>}
          </NavLink>
          
          <NavLink
            to="/settings"
            className={({ isActive }) => `
              sidebar-item ${isActive ? 'active' : ''} ${!isOpen && 'lg:justify-center'}
            `}
            onClick={onCloseMobile}
          >
            <Settings className="w-5 h-5" />
            {isOpen && <span>设置</span>}
          </NavLink>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
