import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Sidebar from './components/Common/Sidebar';
import Header from './components/Common/Header';
import ChatPage from './pages/ChatPage';
import KnowledgePage from './pages/KnowledgePage';
import SettingsPage from './pages/SettingsPage';
import AgentToolsPage from './pages/AgentToolsPage';
import { useKnowledgeStore } from './stores/knowledgeStore';
import { useSettingsStore } from './stores/settingsStore';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // 设置知识库选择变化回调，自动处理 retrieve_documents 工具
  useEffect(() => {
    const { setOnSelectionChangeCallback } = useKnowledgeStore.getState();

    const handleSelectionChange = (selectedIds: string[]) => {
      // 在回调内部获取最新的工具状态
      const { selectedTools, setSelectedTools } = useSettingsStore.getState();
      const hasRetrieveTool = selectedTools.some(tool => tool.toolid === 'retrieve_documents');
      
      if (selectedIds.length > 0 && !hasRetrieveTool) {
        // 选中了知识库，自动添加 retrieve_documents 工具
        setSelectedTools([
          ...selectedTools,
          {
            toolid: 'retrieve_documents',
            mcp: 0,
            name: 'retrieve_documents',
            description: '从知识库检索文档',
          }
        ]);
        console.log('自动添加 retrieve_documents 工具');
      } else if (selectedIds.length === 0 && hasRetrieveTool) {
        // 取消所有知识库选择，移除 retrieve_documents 工具
        setSelectedTools(selectedTools.filter(tool => tool.toolid !== 'retrieve_documents'));
        console.log('自动移除 retrieve_documents 工具');
      }
    };

    setOnSelectionChangeCallback(handleSelectionChange);

    return () => {
      setOnSelectionChangeCallback(null);
    };
  }, []);

  return (
    <div className="fixed inset-0 w-full h-full flex overflow-hidden bg-bg-primary">
      <Sidebar 
        isOpen={sidebarOpen} 
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />
      
      <div className="flex-1 flex flex-col min-w-0">
        <Header 
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
        />
        
        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/agent-tools" element={<AgentToolsPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;
