import { useEffect } from 'react';
import { Wrench, Check } from 'lucide-react';
import { useSettingsStore } from '@/stores/settingsStore';
import { knowledgeApi } from '@/services/knowledge';

const AgentToolsPage = () => {
  const { tools, selectedToolIds, toggleTool } = useSettingsStore();
  
  useEffect(() => {
    // 初始化工具列表
    if (tools.length === 0) {
      knowledgeApi.listTools().then((backendTools) => {
        useSettingsStore.getState().setTools(backendTools.map(t => ({ ...t, enabled: selectedToolIds.includes(t.id) })));
      }).catch(console.error);
    }
  }, [tools.length, selectedToolIds]);

  return (
    <div className="h-full overflow-y-auto p-6 bg-bg-primary">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-text-primary">
            Agent Tools
          </h1>
          <p className="text-sm text-text-tertiary mt-1">
            选择和配置 AI Agent 可使用的工具
          </p>
        </div>

        <div className="space-y-4">
          {tools.length === 0 ? (
            <div className="text-center py-12">
              <Wrench className="w-12 h-12 mx-auto text-text-tertiary mb-4" />
              <p className="text-text-tertiary">暂无可用工具</p>
            </div>
          ) : (
            tools.map(tool => (
              <div
                key={tool.id}
                onClick={() => toggleTool(tool.id)}
                className={`
                  p-4 rounded-lg border cursor-pointer transition-all duration-200
                  ${selectedToolIds.includes(tool.id)
                    ? 'selected-item'
                    : 'border-border hover:border-primary/50 hover:bg-bg-tertiary'
                  }
                `}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className={`font-medium ${selectedToolIds.includes(tool.id) ? 'text-white' : 'text-text-primary'}`}>
                      {tool.name}
                    </h3>
                    <p className={`text-sm mt-1 ${selectedToolIds.includes(tool.id) ? 'text-white/70' : 'text-text-tertiary'}`}>
                      {tool.description}
                    </p>
                  </div>
                  
                  <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                    selectedToolIds.includes(tool.id)
                      ? 'border-primary bg-primary'
                      : 'border-text-quaternary'
                  }`}>
                    {selectedToolIds.includes(tool.id) && (
                      <Check className="w-3 h-3 text-white" />
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentToolsPage;