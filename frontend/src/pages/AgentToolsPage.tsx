import { useEffect, useRef, useState, useCallback } from 'react';
import { Wrench, Check, Loader2, Wifi, WifiOff, Server, CheckSquare, Square, X, ChevronRight, RefreshCw, Settings, Plus, Trash2, Save, Terminal, Globe, AlertCircle, CheckCircle, AlertTriangle, Play } from 'lucide-react';
import { showToast } from '@/utils/toast';
import { useSettingsStore } from '@/stores/settingsStore';
import { toolsApi, mcpConfigApi, type MCPToolService, type Tool, type ToolConfig, type MCPConfig, type MCPServerConfig } from '@/services/api';

interface LoadingStatus {
  message: string;
  type: 'connecting' | 'loading' | 'complete' | 'error' | 'warning';
}

// 传输类型选项
const TRANSPORT_TYPES = [
  { value: 'stdio', label: 'STDIO', icon: Terminal },
  { value: 'sse', label: 'SSE', icon: Server },
  { value: 'streamable_http', label: 'HTTP', icon: Globe },
];

// 默认设置
const DEFAULT_SETTINGS = {
  timeout: 30,
  auto_reload: true,
  log_level: 'info',
};

// 空服务器模板
const EMPTY_SERVER: MCPServerConfig = {
  name: '',
  transport: 'stdio',
  command: '',
  args: [],
  env: {},
  url: '',
  headers: {},
  timeout: 30,
  enabled: true,
};

// 工具详情弹窗组件
interface ToolDetailModalProps {
  service: MCPToolService | null;
  isOpen: boolean;
  onClose: () => void;
  selectedTools: ToolConfig[];
  onToggleTool: (tool: Tool) => void;
  onToggleService: (serviceId: string, tools: Tool[]) => void;
}

// 格式化工具显示名称
const formatToolDisplayName = (tool: Tool, _serviceSource: string): string => {
  return tool.name || tool.toolid;
};

// 格式化工具描述
const formatToolDescription = (description: string): string => {
  if (!description) return '';
  const hintIndex = description.indexOf('💡');
  if (hintIndex !== -1) {
    return description.substring(0, hintIndex).trim();
  }
  const servicePrefixMatch = description.match(/^【[^】]+】\s*/);
  if (servicePrefixMatch) {
    return description.substring(servicePrefixMatch[0].length).trim();
  }
  return description;
};

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
            {isAllSelected ? '取消全选' : '全选'}
            <span className="text-text-quaternary">
              ({selectedCount}/{service.tools.length})
            </span>
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[50vh]">
          <div className="space-y-3">
            {service.tools.map((tool) => {
              const isSelected = selectedTools.find(t => t.toolid === tool.toolid) !== undefined;
              const displayName = formatToolDisplayName(tool, service.source);

              return (
                <div
                  key={tool.toolid}
                  onClick={() => onToggleTool(tool)}
                  className={`
                    group flex items-start gap-3 p-3 rounded-xl border cursor-pointer
                    transition-all duration-200
                    ${isSelected
                      ? 'bg-primary/5 border-primary/50'
                      : 'bg-bg-secondary/30 border-border hover:border-primary/30 hover:bg-bg-tertiary/30'
                    }
                  `}
                >
                  <div className="mt-0.5">
                    {isSelected ? (
                      <CheckSquare className="w-5 h-5 text-primary" />
                    ) : (
                      <Square className="w-5 h-5 text-text-quaternary group-hover:text-primary/50" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className={`font-medium ${isSelected ? 'text-primary' : 'text-text-primary'}`}>
                        {displayName}
                      </h4>
                      {tool.mcp === 1 && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-500">
                          MCP
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-text-tertiary mt-1">
                      {formatToolDescription(tool.description)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

// MCP 配置弹窗组件
interface MCPConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
}

const MCPConfigModal = ({ isOpen, onClose, onSave }: MCPConfigModalProps) => {
  const [config, setConfig] = useState<MCPConfig>({
    servers: [],
    settings: DEFAULT_SETTINGS,
    default_selected_tools: [],
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    errors: string[];
    warnings: string[];
  } | null>(null);
  const [expandedServers, setExpandedServers] = useState<Set<number>>(new Set());
  const [configPath, setConfigPath] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const originalConfigRef = useRef<string>('');

  // 加载配置
  const loadConfig = async () => {
    setIsLoading(true);
    try {
      const response = await mcpConfigApi.get();
      const loadedConfig = response.config;
      setConfig(loadedConfig);
      originalConfigRef.current = JSON.stringify(loadedConfig);
      setConfigPath(response.config_path);
      setHasChanges(false);
      // 不默认展开任何服务
      setExpandedServers(new Set());
    } catch (error) {
      console.error('加载 MCP 配置失败:', error);
      showToast('加载配置失败', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // 保存配置
  const handleSave = async () => {
    setIsSaving(true);
    try {
      const result = await mcpConfigApi.save(config);
      originalConfigRef.current = JSON.stringify(config);
      setHasChanges(false);
      
      // 根据结果显示不同的提示
      const { changes } = result;
      const messages: string[] = [];
      
      if (changes.deleted.length > 0) {
        messages.push(`删除 ${changes.deleted.length} 个服务`);
      }
      if (changes.cached.length > 0) {
        messages.push(`使用缓存 ${changes.cached.length} 个服务`);
      }
      if (changes.pending.length > 0) {
        messages.push(`后台连接 ${changes.pending.length} 个服务`);
      }
      
      const msg = messages.length > 0 ? messages.join('，') : '配置已保存';
      showToast(msg, 'success');
      
      // 立即关闭弹窗（不等待后台连接）
      onClose();
      // 通知父组件刷新工具列表（立即刷新，显示当前缓存中的工具）
      onSave();
      
      // 如果有后台处理的服务，5秒后再次刷新以获取新工具
      if (changes.pending.length > 0) {
        setTimeout(() => {
          showToast('后台连接完成，刷新工具列表...', 'info');
          onSave();
        }, 5000);
      }
    } catch (error) {
      console.error('保存 MCP 配置失败:', error);
      showToast('保存配置失败', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  // 验证配置
  const validateConfig = async () => {
    try {
      const result = await mcpConfigApi.validate();
      setValidationResult(result);
      if (result.valid) {
        showToast('配置验证通过', 'success');
      } else {
        showToast('配置存在问题', 'info');
      }
    } catch (error) {
      console.error('验证 MCP 配置失败:', error);
    }
  };

  // 添加服务器
  const addServer = () => {
    const newServer = { ...EMPTY_SERVER, name: `server-${config.servers.length + 1}` };
    setConfig(prev => ({
      ...prev,
      servers: [...prev.servers, newServer],
    }));
    setExpandedServers(prev => new Set([...prev, config.servers.length]));
    setHasChanges(true);
  };

  // 删除服务器
  const removeServer = (index: number) => {
    if (!confirm('确定要删除这个 MCP 服务器配置吗？')) return;
    setConfig(prev => ({
      ...prev,
      servers: prev.servers.filter((_, i) => i !== index),
    }));
    setExpandedServers(prev => {
      const newSet = new Set(prev);
      newSet.delete(index);
      return newSet;
    });
    setHasChanges(true);
  };

  // 更新服务器
  const updateServer = (index: number, field: keyof MCPServerConfig, value: any) => {
    setConfig(prev => ({
      ...prev,
      servers: prev.servers.map((server, i) =>
        i === index ? { ...server, [field]: value } : server
      ),
    }));
    setHasChanges(true);
  };

  // 切换服务器展开状态
  const toggleServerExpand = (index: number) => {
    setExpandedServers(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  // 初始加载
  useEffect(() => {
    if (isOpen) {
      loadConfig();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-3xl max-h-[85vh] bg-bg-primary rounded-2xl border border-border shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-bg-secondary">
          <div className="flex items-center gap-3">
            <Settings className="w-5 h-5 text-primary" />
            <div>
              <h2 className="text-lg font-semibold text-text-primary">MCP 配置</h2>
              <p className="text-xs text-text-tertiary">
                {configPath && <span>{configPath}</span>}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {hasChanges && (
              <span className="text-xs text-yellow-500 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                有修改
              </span>
            )}
            <button
              onClick={validateConfig}
              disabled={isLoading}
              className="px-3 py-1.5 text-sm bg-bg-tertiary hover:bg-border text-text-secondary rounded-lg transition-colors flex items-center gap-1.5"
            >
              <CheckCircle className="w-4 h-4" />
              验证
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !hasChanges}
              className="px-3 py-1.5 text-sm bg-primary hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-1.5"
            >
              <Save className="w-4 h-4" />
              {isSaving ? '保存中...' : '保存'}
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-bg-tertiary text-text-tertiary hover:text-text-primary transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 验证结果 */}
        {validationResult && (
          <div className={`mx-6 mt-4 p-3 rounded-lg border ${
            validationResult.valid
              ? 'bg-success/10 border-success/20 text-success'
              : 'bg-warning/10 border-warning/20 text-warning'
          }`}>
            <div className="flex items-start gap-2">
              {validationResult.valid ? (
                <CheckCircle className="w-5 h-5 mt-0.5" />
              ) : (
                <AlertTriangle className="w-5 h-5 mt-0.5" />
              )}
              <div className="flex-1">
                <p className="font-medium text-sm">
                  {validationResult.valid ? '配置验证通过' : '配置存在问题'}
                </p>
                {validationResult.errors.length > 0 && (
                  <ul className="mt-1 text-xs space-y-0.5">
                    {validationResult.errors.map((error, i) => (
                      <li key={i} className="flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {error}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <button
                onClick={() => setValidationResult(null)}
                className="p-1 hover:bg-black/10 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* 内容区 */}
        <div className="overflow-y-auto p-6 space-y-6 max-h-[calc(85vh-140px)]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
          ) : (
            <>
              {/* MCP 服务器列表 */}
              <section className="bg-bg-secondary rounded-xl border border-border overflow-hidden">
                <div className="p-4 border-b border-border flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Server className="w-5 h-5 text-primary" />
                    <h3 className="font-semibold text-text-primary">MCP 服务器</h3>
                    <span className="text-xs text-text-tertiary bg-bg-tertiary px-2 py-0.5 rounded-full">
                      {config.servers.length}
                    </span>
                  </div>
                  <button
                    onClick={addServer}
                    className="px-3 py-1.5 text-sm bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors flex items-center gap-1.5"
                  >
                    <Plus className="w-4 h-4" />
                    添加
                  </button>
                </div>

                <div className="divide-y divide-border">
                  {config.servers.length === 0 ? (
                    <div className="p-8 text-center text-text-tertiary">
                      <Server className="w-12 h-12 mx-auto mb-3 opacity-30" />
                      <p>暂无 MCP 服务器配置</p>
                    </div>
                  ) : (
                    config.servers.map((server, index) => (
                      <div key={index} className="bg-bg-secondary">
                        <div
                          className="p-4 flex items-center gap-3 cursor-pointer hover:bg-bg-tertiary/50 transition-colors"
                          onClick={() => toggleServerExpand(index)}
                        >
                          {expandedServers.has(index) ? (
                            <ChevronRight className="w-4 h-4 text-text-tertiary rotate-90 transition-transform" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-text-tertiary transition-transform" />
                          )}
                          <input
                            type="checkbox"
                            checked={server.enabled}
                            onChange={(e) => updateServer(index, 'enabled', e.target.checked)}
                            onClick={(e) => e.stopPropagation()}
                            className="w-4 h-4 rounded border-border text-primary focus:ring-primary"
                          />
                          <span className={`font-medium text-sm ${server.enabled ? 'text-text-primary' : 'text-text-tertiary line-through'}`}>
                            {server.name || `服务器 #${index + 1}`}
                          </span>
                          <span className="text-xs px-2 py-0.5 bg-bg-tertiary rounded text-text-secondary">
                            {TRANSPORT_TYPES.find(t => t.value === server.transport)?.label || server.transport}
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              removeServer(index);
                            }}
                            className="ml-auto p-1.5 text-error hover:bg-error/10 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>

                        {expandedServers.has(index) && (
                          <div className="px-4 pb-4 space-y-3 border-t border-border/50 pt-3">
                            <div className="grid grid-cols-2 gap-3">
                              <div>
                                <label className="block text-xs font-medium text-text-secondary mb-1">名称</label>
                                <input
                                  type="text"
                                  value={server.name}
                                  onChange={(e) => updateServer(index, 'name', e.target.value)}
                                  className="w-full px-2 py-1.5 bg-bg-tertiary border border-border rounded text-sm text-text-primary focus:outline-none focus:border-primary"
                                />
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-text-secondary mb-1">传输类型</label>
                                <select
                                  value={server.transport}
                                  onChange={(e) => updateServer(index, 'transport', e.target.value)}
                                  className="w-full px-2 py-1.5 bg-bg-tertiary border border-border rounded text-sm text-text-primary focus:outline-none focus:border-primary"
                                >
                                  {TRANSPORT_TYPES.map(type => (
                                    <option key={type.value} value={type.value}>{type.label}</option>
                                  ))}
                                </select>
                              </div>
                            </div>

                            {server.transport === 'stdio' && (
                              <>
                                <div>
                                  <label className="block text-xs font-medium text-text-secondary mb-1">命令</label>
                                  <input
                                    type="text"
                                    value={server.command || ''}
                                    onChange={(e) => updateServer(index, 'command', e.target.value)}
                                    placeholder="npx"
                                    className="w-full px-2 py-1.5 bg-bg-tertiary border border-border rounded text-sm text-text-primary focus:outline-none focus:border-primary"
                                  />
                                </div>
                                <div>
                                  <label className="block text-xs font-medium text-text-secondary mb-1">参数 (每行一个)</label>
                                  <textarea
                                    value={server.args?.join('\n') || ''}
                                    onChange={(e) => updateServer(index, 'args', e.target.value.split('\n').filter(Boolean))}
                                    rows={2}
                                    className="w-full px-2 py-1.5 bg-bg-tertiary border border-border rounded text-sm text-text-primary focus:outline-none focus:border-primary font-mono"
                                  />
                                </div>
                              </>
                            )}

                            {(server.transport === 'sse' || server.transport === 'streamable_http') && (
                              <div>
                                <label className="block text-xs font-medium text-text-secondary mb-1">URL</label>
                                <input
                                  type="text"
                                  value={server.url || ''}
                                  onChange={(e) => updateServer(index, 'url', e.target.value)}
                                  placeholder="https://example.com/api/mcp"
                                  className="w-full px-2 py-1.5 bg-bg-tertiary border border-border rounded text-sm text-text-primary focus:outline-none focus:border-primary"
                                />
                              </div>
                            )}

                            <div className="grid grid-cols-2 gap-3">
                              <div>
                                <label className="block text-xs font-medium text-text-secondary mb-1">超时 (秒)</label>
                                <input
                                  type="number"
                                  value={server.timeout}
                                  onChange={(e) => updateServer(index, 'timeout', parseInt(e.target.value) || 30)}
                                  className="w-full px-2 py-1.5 bg-bg-tertiary border border-border rounded text-sm text-text-primary focus:outline-none focus:border-primary"
                                />
                              </div>
                            </div>

                            {server.transport === 'stdio' && (
                              <div>
                                <label className="block text-xs font-medium text-text-secondary mb-1">环境变量 (KEY=VALUE)</label>
                                <textarea
                                  value={Object.entries(server.env || {}).map(([k, v]) => `${k}=${v}`).join('\n')}
                                  onChange={(e) => {
                                    const env: Record<string, string> = {};
                                    e.target.value.split('\n').forEach(line => {
                                      const [key, ...valueParts] = line.split('=');
                                      if (key && valueParts.length > 0) {
                                        env[key.trim()] = valueParts.join('=').trim();
                                      }
                                    });
                                    updateServer(index, 'env', env);
                                  }}
                                  rows={2}
                                  className="w-full px-2 py-1.5 bg-bg-tertiary border border-border rounded text-sm text-text-primary focus:outline-none focus:border-primary font-mono"
                                />
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </section>

              {/* 全局设置 */}
              <section className="bg-bg-secondary rounded-xl border border-border overflow-hidden">
                <div className="p-4 border-b border-border flex items-center gap-3">
                  <Settings className="w-5 h-5 text-primary" />
                  <h3 className="font-semibold text-text-primary">全局设置</h3>
                </div>
                <div className="p-4 grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-text-secondary mb-1">超时 (秒)</label>
                    <input
                      type="number"
                      value={config.settings.timeout}
                      onChange={(e) => {
                        setConfig(prev => ({
                          ...prev,
                          settings: { ...prev.settings, timeout: parseInt(e.target.value) || 30 }
                        }));
                        setHasChanges(true);
                      }}
                      className="w-full px-2 py-1.5 bg-bg-tertiary border border-border rounded text-sm text-text-primary focus:outline-none focus:border-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-text-secondary mb-1">日志级别</label>
                    <select
                      value={config.settings.log_level}
                      onChange={(e) => {
                        setConfig(prev => ({
                          ...prev,
                          settings: { ...prev.settings, log_level: e.target.value }
                        }));
                        setHasChanges(true);
                      }}
                      className="w-full px-2 py-1.5 bg-bg-tertiary border border-border rounded text-sm text-text-primary focus:outline-none focus:border-primary"
                    >
                      <option value="debug">Debug</option>
                      <option value="info">Info</option>
                      <option value="warning">Warning</option>
                      <option value="error">Error</option>
                    </select>
                  </div>
                  <div className="flex items-end">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.settings.auto_reload}
                        onChange={(e) => {
                          setConfig(prev => ({
                            ...prev,
                            settings: { ...prev.settings, auto_reload: e.target.checked }
                          }));
                          setHasChanges(true);
                        }}
                        className="w-4 h-4 rounded border-border text-primary focus:ring-primary"
                      />
                      <span className="text-sm text-text-secondary">自动重载</span>
                    </label>
                  </div>
                </div>
              </section>

              {/* 默认选中工具 */}
              <section className="bg-bg-secondary rounded-xl border border-border overflow-hidden">
                <div className="p-4 border-b border-border flex items-center gap-3">
                  <Play className="w-5 h-5 text-primary" />
                  <h3 className="font-semibold text-text-primary">默认选中工具</h3>
                </div>
                <div className="p-4">
                  <textarea
                    value={config.default_selected_tools.join('\n')}
                    onChange={(e) => {
                      setConfig(prev => ({
                        ...prev,
                        default_selected_tools: e.target.value.split('\n').filter(Boolean)
                      }));
                      setHasChanges(true);
                    }}
                    placeholder="get_current_time&#10;zhipu-web-search-sse_*&#10;github_*"
                    rows={3}
                    className="w-full px-2 py-1.5 bg-bg-tertiary border border-border rounded text-sm text-text-primary focus:outline-none focus:border-primary font-mono"
                  />
                  <p className="text-xs text-text-tertiary mt-2">
                    每行一个工具ID，支持通配符 *
                  </p>
                </div>
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// 服务卡片组件
interface ServiceCardProps {
  service: MCPToolService;
  selectedTools: ToolConfig[];
  onToggle: () => void;
  onOpenDetail: () => void;
}

const ServiceCard = ({ service, selectedTools, onToggle, onOpenDetail }: ServiceCardProps) => {
  const selectedCount = service.tools.filter(tool => selectedTools.find(t => t.toolid === tool.toolid)).length;
  const isAllSelected = selectedCount === service.tools.length;
  const isPartialSelected = selectedCount > 0 && !isAllSelected;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggle();
  };

  return (
    <div
      onClick={onOpenDetail}
      className={`
        group relative p-4 sm:p-5 rounded-xl border cursor-pointer
        transition-all duration-200
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

      <div className="mt-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2 py-1 rounded-full ${
              service.source === 'built-in' 
                ? 'bg-blue-500/10 text-blue-500' 
                : 'bg-purple-500/10 text-purple-500'
            }`}>
              {service.source === 'built-in' ? '内置' : 'MCP'}
            </span>
            <span className="text-sm text-text-tertiary">
              <span className={selectedCount > 0 ? "text-primary font-medium" : ""}>
                {selectedCount}
              </span>
              <span className="text-text-quaternary"> / {service.toolCount} 个工具</span>
            </span>
          </div>

          <div className="flex items-center gap-1 text-text-tertiary group-hover:text-primary transition-colors">
            <span className="text-sm">查看详情</span>
            <ChevronRight className="w-4 h-4" />
          </div>
        </div>
        
        <div className="flex flex-wrap gap-1.5 mt-2">
          {service.tools.slice(0, 5).map((tool) => {
            const isToolSelected = selectedTools.find(t => t.toolid === tool.toolid) !== undefined;
            const displayName = formatToolDisplayName(tool, service.source);
            return (
              <span
                key={tool.toolid}
                className={`
                  text-xs px-2 py-0.5 rounded border truncate max-w-[120px]
                  ${isToolSelected 
                    ? 'bg-primary/10 border-primary/30 text-primary' 
                    : 'bg-bg-tertiary/50 border-border/50 text-text-tertiary'
                  }
                `}
                title={displayName}
              >
                {displayName}
              </span>
            );
          })}
          {service.tools.length > 5 && (
            <span className="text-xs px-2 py-0.5 rounded bg-bg-tertiary/50 text-text-quaternary">
              +{service.tools.length - 5}
            </span>
          )}
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
  const [selectedService, setSelectedService] = useState<MCPToolService | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);

  const cancelRef = useRef<(() => void) | null>(null);
  const loadedRef = useRef(false);

  const allTools = toolServices.flatMap(s => s.tools);
  const isAllSelected = allTools.length > 0 && allTools.every(tool => selectedTools.find(t => t.toolid === tool.toolid));

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
  
  const loadedServicesListRef = useRef<MCPToolService[]>([]);

  const loadToolsStream = useCallback((forceRefresh: boolean = false) => {
    if (loadedRef.current && !forceRefresh) return;
    loadedRef.current = true;

    loadedServicesListRef.current = [];

    setIsLoading(true);
    setLoadingStatus({ message: forceRefresh ? '正在刷新工具缓存...' : '正在连接工具服务...', type: 'connecting' });

    cancelRef.current = toolsApi.listStream(forceRefresh, {
      onStatus: (message) => {
        setLoadingStatus({ message, type: 'loading' });
      },

      onService: (service) => {
        loadedServicesListRef.current.push(service);
        setToolServices([...loadedServicesListRef.current]);
        setLoadingStatus({
          message: `已加载 ${service.name}...`,
          type: 'loading'
        });
      },

      onComplete: (total, services, defaultSelectedTools) => {
        setIsLoading(false);
        setLoadingStatus({
          message: `共加载 ${services} 个服务，${total} 个工具`,
          type: 'complete'
        });

        const store = useSettingsStore.getState();
        const userHasSelection = store.hasUserSelection;
        const currentSelectedTools = store.selectedTools;

        if (!userHasSelection && currentSelectedTools.length === 0 && defaultSelectedTools && defaultSelectedTools.length > 0 && loadedServicesListRef.current.length > 0) {
          const matchedTools: ToolConfig[] = [];
          for (const service of loadedServicesListRef.current) {
            for (const tool of service.tools) {
              const isMatch = defaultSelectedTools.some(pattern => {
                if (pattern.includes('*') || pattern.includes('?')) {
                  const regexPattern = pattern
                    .replace(/[.+^${}()|[\]\\]/g, '\\$&')
                    .replace(/\*/g, '.*')
                    .replace(/\?/g, '.');
                  const regex = new RegExp(`^${regexPattern}$`);
                  return regex.test(tool.toolid);
                }
                return tool.toolid === pattern;
              });
              if (isMatch) {
                matchedTools.push({
                  toolid: tool.toolid,
                  mcp: tool.mcp,
                  name: tool.name,
                  description: tool.description,
                });
              }
            }
          }

          if (matchedTools.length > 0) {
            setSelectedTools(matchedTools);
            showToast(`已默认选中 ${matchedTools.length} 个工具`, 'success');
          }
        }

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

  const handleRefreshTools = useCallback(async () => {
    if (isLoading) return;

    setIsLoading(true);
    setLoadingStatus({ message: '正在刷新工具缓存...', type: 'loading' });

    try {
      loadedRef.current = false;
      setToolServices([]);
      loadedRef.current = false;
      loadToolsStream(true);
    } catch (error) {
      console.error('刷新工具失败:', error);
      showToast('刷新工具失败', 'error');
      setIsLoading(false);
      setLoadingStatus({ message: '刷新失败', type: 'error' });
      loadedRef.current = false;
    }
  }, [isLoading, loadToolsStream, setToolServices]);

  const handleConfigSave = () => {
    // 配置已保存，强制刷新工具列表以获取新增的 MCP 服务
    // 重置 loadedRef，确保能重新加载
    loadedRef.current = false;
    // 清空当前服务列表，确保UI立即更新（删除的服务会消失）
    setToolServices([]);
    loadedServicesListRef.current = [];
    // 使用强制刷新模式（forceRefresh=true），触发后台连接新服务
    setTimeout(() => {
      loadToolsStream(true);
    }, 300);
  };

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-6 bg-bg-primary">
      <div className="max-w-4xl mx-auto">
        {/* 标题区域 */}
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-xl sm:text-2xl font-semibold text-text-primary">
                Agent Tools
              </h1>
              {isLoading && (
                <Loader2 className="w-5 h-5 text-primary animate-spin" />
              )}
            </div>
            {/* 刷新和配置按钮 */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsConfigModalOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 bg-bg-secondary hover:bg-bg-tertiary text-text-secondary hover:text-text-primary border border-border"
                title="配置 MCP 服务器"
              >
                <Settings className="w-4 h-4" />
                <span className="hidden sm:inline">配置</span>
              </button>
              <button
                onClick={handleRefreshTools}
                disabled={isLoading}
                className={`
                  flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium
                  transition-all duration-200
                  ${isLoading 
                    ? 'opacity-50 cursor-not-allowed bg-bg-tertiary text-text-tertiary' 
                    : 'bg-bg-secondary hover:bg-bg-tertiary text-text-secondary hover:text-text-primary border border-border'
                  }
                `}
                title="强制刷新 MCP 工具缓存"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">刷新</span>
              </button>
            </div>
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
                已选择 <span className="text-primary font-medium">{selectedTools.length}</span> 个工具
              </span>
              <button
                onClick={handleSelectAll}
                className="flex items-center gap-2 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
              >
                {isAllSelected ? (
                  <CheckSquare className="w-4 h-4 text-primary" />
                ) : (
                  <Square className="w-4 h-4 text-text-tertiary" />
                )}
                {isAllSelected ? '取消全选' : '全选所有工具'}
              </button>
            </div>
          )}

          {/* 服务卡片网格 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {toolServices.map((service) => (
              <ServiceCard
                key={service.id}
                service={service}
                selectedTools={selectedTools}
                onToggle={() => toggleServiceTools(service.id, service.tools)}
                onOpenDetail={() => handleOpenDetail(service)}
              />
            ))}
          </div>

          {/* 空状态 */}
          {!isLoading && toolServices.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-bg-secondary flex items-center justify-center">
                <Wrench className="w-8 h-8 text-text-tertiary" />
              </div>
              <h3 className="text-lg font-medium text-text-primary mb-2">暂无可用工具</h3>
              <p className="text-sm text-text-tertiary mb-4">请检查 MCP 配置或刷新工具列表</p>
              <button
                onClick={handleRefreshTools}
                className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors"
              >
                刷新工具列表
              </button>
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
        onToggleService={(serviceId, tools) => toggleServiceTools(serviceId, tools)}
      />

      {/* MCP 配置弹窗 */}
      <MCPConfigModal
        isOpen={isConfigModalOpen}
        onClose={() => setIsConfigModalOpen(false)}
        onSave={handleConfigSave}
      />
    </div>
  );
};

export default AgentToolsPage;
