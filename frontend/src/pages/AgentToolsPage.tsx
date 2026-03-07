import { useEffect, useRef, useState, useCallback } from 'react';
import { Wrench, Check, Loader2, Wifi, WifiOff, Server, CheckSquare, Square, X, ChevronRight } from 'lucide-react';
import { showToast } from '@/utils/toast';
import { useSettingsStore } from '@/stores/settingsStore';
import { toolsApi, type MCPToolService, type Tool, type ToolConfig } from '@/services/api';

interface LoadingStatus {
  message: string;
  type: 'connecting' | 'loading' | 'complete' | 'error' | 'warning';
}

// 工具详情弹窗组件
interface ToolDetailModalProps {
  service: MCPToolService | null;
  isOpen: boolean;
  onClose: () => void;
  selectedTools: ToolConfig[];
  onToggleTool: (tool: Tool) => void;
  onToggleService: (serviceId: string, tools: Tool[]) => void;
}

const ToolDetailModal = ({
  service,
  isOpen,
  onClose,
  selectedTools,
  onToggleTool,
  onToggleService,
}: ToolDetailModalProps) => {
  if (!isOpen || !service) return null;

  const selectedCount = service.tools.filter(tool => selectedTools.find(t => t.toolid === tool.toolid)).length;
  const isAllSelected = selectedCount === service.tools.length;

  const handleSelectAllInService = () => {
    onToggleService(service.id, service.tools);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl max-h-[80vh] bg-bg-primary rounded-2xl border border-border shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* 弹窗头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-bg-secondary/50">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              service.source === 'built-in' ? 'bg-blue-500/10' : 'bg-purple-500/10'
            }`}>
              {service.source === 'built-in' ? (
                <Server className="w-5 h-5 text-blue-500" />
              ) : (
                <Wifi className="w-5 h-5 text-purple-500" />
              )}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">{service.name}</h3>
              <p className="text-sm text-text-tertiary">{service.description}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-bg-tertiary text-text-tertiary hover:text-text-primary transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 全选按钮 */}
        <div className="px-6 py-3 border-b border-border bg-bg-secondary/30">
          <button
            onClick={handleSelectAllInService}
            className="flex items-center gap-2 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
          >
            {isAllSelected ? (
              <CheckSquare className="w-4 h-4 text-primary" />
            ) : (
              <Square className="w-4 h-4 text-text-tertiary" />
            )}
            <span>{isAllSelected ? '取消全选' : '全选'} ({selectedCount}/{service.tools.length})</span>
          </button>
        </div>

        {/* 工具列表 */}
        <div className="overflow-y-auto max-h-[50vh] p-4 space-y-2">
          {service.tools.map((tool) => {
            const isSelected = selectedTools.find(t => t.toolid === tool.toolid) !== undefined;
            return (
              <div
                key={tool.toolid}
                onClick={() => onToggleTool(tool)}
                className={`
                  p-4 rounded-xl border cursor-pointer transition-all duration-200
                  ${isSelected
                    ? 'bg-primary/10 border-primary/50'
                    : 'bg-bg-secondary/50 border-border hover:border-primary/30 hover:bg-bg-tertiary/50'
                  }
                `}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className={`font-medium ${isSelected ? 'text-primary' : 'text-text-primary'}`}>
                      {tool.name}
                    </h4>
                    <p className={`text-sm mt-1 ${isSelected ? 'text-blue-400' : 'text-text-secondary'}`}>
                      {tool.description}
                    </p>
                  </div>
                  <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ml-3 ${
                    isSelected
                      ? 'border-primary bg-primary'
                      : 'border-text-quaternary'
                  }`}>
                    {isSelected && <Check className="w-3 h-3 text-white" />}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* 弹窗底部 */}
        <div className="px-6 py-4 border-t border-border bg-bg-secondary/50">
          <div className="flex items-center justify-between">
            <span className="text-sm text-text-tertiary">
              已选择 {selectedCount} 个工具
            </span>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
            >
              完成
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// MCP 服务卡片组件
interface ServiceCardProps {
  service: MCPToolService;
  selectedTools: ToolConfig[];
  onToggleService: (serviceId: string, tools: Tool[]) => void;
  onOpenDetail: (service: MCPToolService) => void;
}

const ServiceCard = ({ service, selectedTools, onToggleService, onOpenDetail }: ServiceCardProps) => {
  const selectedCount = service.tools.filter(tool => selectedTools.find(t => t.toolid === tool.toolid)).length;
  const isAllSelected = selectedCount === service.tools.length && service.tools.length > 0;
  const isPartialSelected = selectedCount > 0 && !isAllSelected;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleService(service.id, service.tools);
  };

  return (
    <div
      onClick={() => onOpenDetail(service)}
      className={`
        group relative p-5 rounded-xl border cursor-pointer transition-all duration-200
        ${isAllSelected
          ? 'bg-primary/5 border-primary/50 shadow-lg shadow-primary/5'
          : 'bg-bg-secondary/30 border-border hover:border-primary/30 hover:bg-bg-tertiary/30'
        }
      `}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
            service.source === 'built-in' ? 'bg-blue-500/10' : 'bg-purple-500/10'
          }`}>
            {service.source === 'built-in' ? (
              <Server className="w-6 h-6 text-blue-500" />
            ) : (
              <Wifi className="w-6 h-6 text-purple-500" />
            )}
          </div>
          <div>
            <h3 className={`font-semibold ${isAllSelected ? 'text-primary' : 'text-text-primary'}`}>
              {service.name}
            </h3>
            <p className="text-sm text-text-tertiary mt-0.5">{service.description}</p>
          </div>
        </div>

        {/* 选中状态指示器 */}
        <button
          onClick={handleToggle}
          className={`
            w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all
            ${isAllSelected
              ? 'border-primary bg-primary'
              : isPartialSelected
                ? 'border-primary bg-primary/20'
                : 'border-text-quaternary group-hover:border-primary/50'
            }
          `}
        >
          {isAllSelected && <Check className="w-4 h-4 text-white" />}
          {isPartialSelected && <div className="w-2 h-2 rounded-full bg-primary" />}
        </button>
      </div>

      {/* 工具数量信息 */}
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-1 rounded-full ${
            service.source === 'built-in' 
              ? 'bg-blue-500/10 text-blue-500' 
              : 'bg-purple-500/10 text-purple-500'
          }`}>
            {service.source === 'built-in' ? '内置' : 'MCP'}
          </span>
          <span className="text-sm text-text-tertiary">
            {selectedCount > 0 ? (
              <span className="text-primary font-medium">{selectedCount}</span>
            ) : (
              <span>{service.toolCount}</span>
            )}
            <span className="text-text-quaternary"> / {service.toolCount} 个工具</span>
          </span>
        </div>

        <div className="flex items-center gap-1 text-text-tertiary group-hover:text-primary transition-colors">
          <span className="text-sm">查看详情</span>
          <ChevronRight className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
};

const AgentToolsPage = () => {
  const {
    toolServices,
    selectedTools,
    toggleTool,
    toggleServiceTools,
    setToolServices,
    setSelectedTools
  } = useSettingsStore();

  const [loadingStatus, setLoadingStatus] = useState<LoadingStatus>({
    message: '正在初始化...',
    type: 'connecting'
  });
  const [isLoading, setIsLoading] = useState(true);
  const [loadedServices, setLoadedServices] = useState(0);
  const [expectedServices, setExpectedServices] = useState(0);
  const [selectedService, setSelectedService] = useState<MCPToolService | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const cancelRef = useRef<(() => void) | null>(null);
  const loadedRef = useRef(false);

  // 检查是否全部选中
  const allTools = toolServices.flatMap(s => s.tools);
  const isAllSelected = allTools.length > 0 && allTools.every(tool => selectedTools.find(t => t.toolid === tool.toolid));

  // 一键全选/取消全选
  const handleSelectAll = () => {
    if (isAllSelected) {
      setSelectedTools([]);
      showToast('已取消全选', 'info');
    } else {
      const allToolConfigs = allTools.map(tool => ({
        toolid: tool.toolid,
        mcp: tool.mcp,
        name: tool.name,
        description: tool.description
      }));
      setSelectedTools(allToolConfigs);
      showToast(`已选中 ${allToolConfigs.length} 个工具`, 'success');
    }
  };
  
  const loadToolsStream = useCallback(() => {
    if (loadedRef.current) return;
    loadedRef.current = true;
    
    setIsLoading(true);
    setLoadingStatus({ message: '正在连接工具服务...', type: 'connecting' });
    
    const loadedServicesList: MCPToolService[] = [];
    
    cancelRef.current = toolsApi.listStream({
      onStatus: (message) => {
        setLoadingStatus({ message, type: 'loading' });
      },
      
      onService: (service) => {
        loadedServicesList.push(service);
        setLoadedServices(loadedServicesList.length);
        
        // 实时更新服务列表
        setToolServices([...loadedServicesList]);
        
        setLoadingStatus({ 
          message: `已加载 ${service.name}...`, 
          type: 'loading' 
        });
      },
      
      onComplete: (total, services) => {
        setIsLoading(false);
        setExpectedServices(services);
        setLoadingStatus({ 
          message: `共加载 ${services} 个服务，${total} 个工具`, 
          type: 'complete' 
        });
        
        if (services > 0) {
          showToast(`成功加载 ${services} 个服务`, 'success');
        } else {
          showToast('暂无可用工具', 'empty');
        }
      },
      
      onWarning: (message) => {
        console.warn('[Tools]', message);
        setLoadingStatus({ message, type: 'warning' });
      },
      
      onError: (message) => {
        setIsLoading(false);
        setLoadingStatus({ message, type: 'error' });
        showToast(message, 'error');
        loadedRef.current = false;
      }
    });
  }, [setToolServices]);
  
  useEffect(() => {
    loadToolsStream();
    
    return () => {
      if (cancelRef.current) {
        cancelRef.current();
      }
    };
  }, [loadToolsStream]);

  // 获取状态图标
  const getStatusIcon = () => {
    switch (loadingStatus.type) {
      case 'connecting':
        return <Wifi className="w-4 h-4 text-primary animate-pulse" />;
      case 'loading':
        return <Loader2 className="w-4 h-4 text-primary animate-spin" />;
      case 'complete':
        return <Wifi className="w-4 h-4 text-green-500" />;
      case 'error':
        return <WifiOff className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <Server className="w-4 h-4 text-yellow-500" />;
      default:
        return null;
    }
  };

  // 获取状态样式
  const getStatusStyle = () => {
    switch (loadingStatus.type) {
      case 'connecting':
        return 'bg-primary/10 text-primary border-primary/20';
      case 'loading':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'complete':
        return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'error':
        return 'bg-red-500/10 text-red-500 border-red-500/20';
      case 'warning':
        return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      default:
        return 'bg-bg-tertiary text-text-secondary';
    }
  };

  const handleOpenDetail = (service: MCPToolService) => {
    setSelectedService(service);
    setIsModalOpen(true);
  };

  const handleCloseDetail = () => {
    setIsModalOpen(false);
    setTimeout(() => setSelectedService(null), 200);
  };

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-6 bg-bg-primary">
      <div className="max-w-4xl mx-auto">
        {/* 标题区域 */}
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-semibold text-text-primary">
              Agent Tools
            </h1>
            {isLoading && (
              <Loader2 className="w-5 h-5 text-primary animate-spin" />
            )}
          </div>
          <p className="text-sm text-text-tertiary mt-1">
            选择和配置 AI Agent 可使用的工具服务
          </p>
        </div>

        {/* 状态显示区域 */}
        {isLoading && (
          <div className={`mb-6 p-4 rounded-lg border ${getStatusStyle()}`}>
            <div className="flex items-center gap-3">
              {getStatusIcon()}
              <div className="flex-1">
                <p className="text-sm font-medium">{loadingStatus.message}</p>
              </div>
            </div>
          </div>
        )}

        {/* 完成状态显示 */}
        {!isLoading && toolServices.length > 0 && (
          <div className={`mb-6 p-3 rounded-lg border ${getStatusStyle()}`}>
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <p className="text-sm">{loadingStatus.message}</p>
            </div>
          </div>
        )}

        {/* 服务列表 */}
        <div className="space-y-4">
          {/* 全选/取消全选按钮 */}
          {toolServices.length > 0 && (
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
              <span className="text-sm text-text-tertiary">
                已选择 {selectedTools.length} / {allTools.length} 个工具
              </span>
              <button
                onClick={handleSelectAll}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 hover:bg-bg-tertiary"
              >
                {isAllSelected ? (
                  <>
                    <CheckSquare className="w-4 h-4 text-primary" />
                    <span className="text-text-secondary">取消全选</span>
                  </>
                ) : (
                  <>
                    <Square className="w-4 h-4 text-text-tertiary" />
                    <span className="text-text-secondary">全选</span>
                  </>
                )}
              </button>
            </div>
          )}

          {toolServices.length === 0 && !isLoading ? (
            <div className="text-center py-12">
              <Wrench className="w-12 h-12 mx-auto text-text-tertiary mb-4" />
              <p className="text-text-tertiary">暂无可用工具服务</p>
              {loadingStatus.type === 'error' && (
                <button
                  onClick={() => {
                    loadedRef.current = false;
                    loadToolsStream();
                  }}
                  className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
                >
                  重新加载
                </button>
              )}
            </div>
          ) : (
            <div className="grid gap-4">
              {toolServices.map((service) => (
                <ServiceCard
                  key={service.id}
                  service={service}
                  selectedTools={selectedTools}
                  onToggleService={toggleServiceTools}
                  onOpenDetail={handleOpenDetail}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 工具详情弹窗 */}
      <ToolDetailModal
        service={selectedService}
        isOpen={isModalOpen}
        onClose={handleCloseDetail}
        selectedTools={selectedTools}
        onToggleTool={toggleTool}
        onToggleService={toggleServiceTools}
      />
    </div>
  );
};

export default AgentToolsPage;
