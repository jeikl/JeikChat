import { NavLink, useNavigate } from 'react-router-dom';
import { 
  MessageCircle, 
  BookOpen, 
  Settings, 
  Plus,
  Trash2,
  MessageSquare,
  Wrench,
  Edit2,
  CheckSquare,
  Square
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

const NAV_ITEMS = [
  { path: '/knowledge', label: 'RAG 知识库', icon: BookOpen },
  { path: '/agent-tools', label: 'Agent 工具', icon: Wrench },
  { path: '/settings', label: '设置中心', icon: Settings },
];

const Sidebar = ({ isOpen, mobileOpen, onCloseMobile }: SidebarProps) => {
  const navigate = useNavigate();
  const {
    sessions,
    currentSessionId,
    setCurrentSession,
    deleteSessionWithApi,
    updateSession,
    skipDeleteConfirm,
    setSkipDeleteConfirm
  } = useChatStore();
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [logoError, setLogoError] = useState(false);

  const handleSelectSession = (sessionId: string) => {
    setCurrentSession(sessionId);
    if (window.innerWidth < 1024) { // 移动端自动关闭
      onCloseMobile();
    }
    navigate('/chat');
  };

  const handleCreateNewSession = () => {
    // 不创建新会话，只是清空当前会话状态
    // 新会话会在用户发送第一条消息后自动创建
    setCurrentSession(null);
    
    // 导航到聊天页面
    navigate('/chat');
    
    // 移动端关闭侧边栏
    if (window.innerWidth < 1024) {
      onCloseMobile();
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (sessionId === 'default-session') return; // 禁止删除默认对话
    
    if (skipDeleteConfirm || confirm('确定要删除这个对话吗？')) {
      await deleteSessionWithApi(sessionId);
    }
  };

  const startEditing = (e: React.MouseEvent, session: typeof sessions[0]) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditTitle(session.title);
  };

  const saveTitle = (sessionId: string) => {
    if (editTitle.trim()) {
      updateSession(sessionId, { title: editTitle.trim() });
    }
    setEditingSessionId(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent, sessionId: string) => {
    if (e.key === 'Enter') {
      saveTitle(sessionId);
    } else if (e.key === 'Escape') {
      setEditingSessionId(null);
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
          <div 
            className={`flex items-center gap-3 ${!isOpen && 'lg:justify-center'} cursor-pointer`} 
            onClick={() => handleSelectSession('default-session')}
          >
            <div className="w-10 h-10 flex-shrink-0">
              {!logoError ? (
                <img 
                  src="/logo.png" 
                  alt="Logo" 
                  className="w-full h-full object-cover rounded-full" 
                  onError={() => setLogoError(true)} 
                />
              ) : (
                <div className="w-full h-full rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg shadow-primary/20">
                  <MessageSquare className="w-6 h-6 text-white" />
                </div>
              )}
            </div>
            {isOpen && (
              <span className="font-bold text-xl text-text-primary tracking-tight">
                JeikChat
              </span>
            )}
          </div>
        </div>

        {isOpen && (
          <div className="px-4 mb-2">
            <button
              onClick={() => handleSelectSession('default-session')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 border group ${
                currentSessionId === 'default-session'
                  ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20'
                  : 'bg-bg-tertiary text-text-secondary border-border hover:border-primary/50 hover:bg-bg-tertiary/80'
              }`}
            >
              <MessageSquare className={`w-5 h-5 ${currentSessionId === 'default-session' ? 'text-white' : 'text-primary'}`} />
              <span className="font-medium">默认对话</span>
            </button>
          </div>
        )}

        <div className="px-4 mb-6">
          <button
            onClick={handleCreateNewSession}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 border group ${
              !isOpen ? 'justify-center px-0' : ''
            } ${
              // 当前没有选中会话（点击了开启新对话）或者是非默认会话时高亮
              !currentSessionId || (currentSessionId !== 'default-session' && !sessions.find(s => s.id === currentSessionId)?.isDefault)
                ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20'
                : 'bg-bg-tertiary text-text-secondary border-border hover:border-primary/50 hover:bg-bg-tertiary/80'
            }`}
            title="开启新对话"
          >
            <Plus className={`w-5 h-5 ${!isOpen ? 'w-6 h-6' : ''} ${
              !currentSessionId || (currentSessionId !== 'default-session' && !sessions.find(s => s.id === currentSessionId)?.isDefault)
                ? 'text-white' 
                : 'text-primary'
            }`} />
            {isOpen && <span className="font-medium">开启新对话</span>}
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
              {sessions
                .filter(session => session.id !== 'default-session') // 过滤掉默认会话
                .map((session) => (
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
                        {editingSessionId === session.id ? (
                          <input
                            autoFocus
                            type="text"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onBlur={() => saveTitle(session.id)}
                            onKeyDown={(e) => handleKeyDown(e, session.id)}
                            onClick={(e) => e.stopPropagation()}
                            className="w-full bg-bg-tertiary text-text-primary text-sm px-1.5 py-0.5 rounded border border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary"
                          />
                        ) : (
                          <p className={`text-sm font-medium truncate ${currentSessionId === session.id ? 'text-primary' : ''}`}>{session.title}</p>
                        )}
                        <p className={`text-[10px] ${currentSessionId === session.id ? 'text-primary/60' : 'text-text-tertiary'}`}>
                          {format(session.updatedAt, 'MM/dd HH:mm', { locale: zhCN })}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={(e) => startEditing(e, session)}
                          className="p-1.5 hover:bg-primary/10 hover:text-primary rounded-lg transition-all text-text-quaternary"
                          title="重命名"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSession(e, session.id);
                          }}
                          className="p-1.5 hover:bg-error/10 hover:text-error rounded-lg transition-all text-text-quaternary"
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
          
          {/* 删除不再提示选项 - 放在会话列表底部 */}
          {isOpen && sessions.filter(s => s.id !== 'default-session').length > 0 && (
            <div className="py-3 mt-2 border-t border-border/10">
              <button
                onClick={() => setSkipDeleteConfirm(!skipDeleteConfirm)}
                className="flex items-center justify-center w-full gap-2 text-text-tertiary hover:text-text-secondary transition-colors py-2 rounded-lg hover:bg-bg-tertiary/50"
              >
                {skipDeleteConfirm ? (
                  <CheckSquare className="w-4 h-4 text-primary" />
                ) : (
                  <Square className="w-4 h-4" />
                )}
                <span className="text-xs">删除不再提示</span>
              </button>
            </div>
          )}
        </div>

        <div className="p-4 mt-auto border-t border-border/10 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onCloseMobile}
                className={({ isActive }) => `
                  flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
                  ${isActive ? 'bg-primary/10 text-primary' : 'text-text-secondary hover:bg-bg-tertiary/50 hover:text-text-primary'}
                  ${!isOpen && 'lg:justify-center lg:px-2'}
                `}
              >
                <Icon className="w-5 h-5" />
                {isOpen && <span className="text-sm font-semibold">{item.label}</span>}
              </NavLink>
            );
          })}
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
