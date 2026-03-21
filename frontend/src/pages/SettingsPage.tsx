import { useState, useMemo, useEffect } from 'react';
import { 
  Bot, 
  Plus, 
  Trash2, 
  X,
  Eye,
  EyeOff,
  Server,
  ChevronRight,
  Power,
  FileText,
  Save,
  RotateCcw
} from 'lucide-react';
import { useSettingsStore } from '@/stores/settingsStore';
import { showToast } from '@/utils/toast';
import { modelApi, promptApi } from '@/services/api';
import type { LLMConfig } from '@/types/config';

const SettingsPage = () => {
  const { 
    configs, 
    activeConfigId, 
    addConfig, 
    removeConfig,
    updateConfig,
    setActiveConfig,
  } = useSettingsStore();

  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({});

  // 提示词状态
  const [prompts, setPrompts] = useState<any>({});
  const [isPromptsLoading, setIsPromptsLoading] = useState(false);
  const [showAddPromptSection, setShowAddPromptSection] = useState(false);
  const [newPromptSectionName, setNewPromptSectionName] = useState('');
  const [showAddPromptItem, setShowAddPromptItem] = useState<string | null>(null); // section name
  const [newPromptItemKey, setNewPromptItemKey] = useState('');

  // 加载提示词
  const fetchPrompts = async () => {
    setIsPromptsLoading(true);
    try {
      const data = await promptApi.list();
      setPrompts(data);
    } catch (error) {
      console.error('获取提示词失败:', error);
      showToast('获取提示词配置失败', 'error');
    } finally {
      setIsPromptsLoading(false);
    }
  };

  useEffect(() => {
    fetchPrompts();
  }, []);

  const handleSavePrompts = async () => {
    try {
      await promptApi.save(prompts);
      showToast('提示词配置已保存', 'success');
    } catch (error) {
      console.error('保存提示词失败:', error);
      showToast('保存提示词配置失败', 'error');
    }
  };

  const handlePromptChange = (section: string, key: string, value: string) => {
    setPrompts((prev: any) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  const handleDeletePromptItem = (section: string, key: string) => {
    if (!confirm('确定要删除此提示词项吗？')) return;
    setPrompts((prev: any) => {
      const newSection = { ...prev[section] };
      delete newSection[key];
      return {
        ...prev,
        [section]: newSection
      };
    });
  };

  const handleDeletePromptSection = (section: string) => {
    if (!confirm(`确定要删除整个 "${section}" 模块吗？这将删除模块下的所有提示词。`)) return;
    setPrompts((prev: any) => {
      const newPrompts = { ...prev };
      delete newPrompts[section];
      return newPrompts;
    });
  };

  const handleAddPromptSection = () => {
    if (!newPromptSectionName.trim()) return;
    if (prompts[newPromptSectionName.trim()]) {
      showToast('该模块已存在', 'error');
      return;
    }
    setPrompts((prev: any) => ({
      ...prev,
      [newPromptSectionName.trim()]: {}
    }));
    setNewPromptSectionName('');
    setShowAddPromptSection(false);
  };

  const handleAddPromptItem = (section: string) => {
    if (!newPromptItemKey.trim()) return;
    if (prompts[section][newPromptItemKey.trim()] !== undefined) {
      showToast('该提示词项已存在', 'error');
      return;
    }
    setPrompts((prev: any) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [newPromptItemKey.trim()]: ''
      }
    }));
    setNewPromptItemKey('');
    setShowAddPromptItem(null);
  };

  const [newConfig, setNewConfig] = useState<Partial<LLMConfig>>({
    name: '',
    provider: '',
    format: 'openai',
    model: '',
    apiKey: '',
    baseUrl: '',
    temperature: 0.7,
    maxTokens: 4096,
    topP: 0.9,
    enabled: true,
  });

  // 按提供商分组配置
  const providersMap = useMemo(() => {
    const map = new Map<string, LLMConfig[]>();
    configs.forEach(config => {
      const providerName = config.provider || '未知提供商';
      if (!map.has(providerName)) {
        map.set(providerName, []);
      }
      map.get(providerName)!.push(config);
    });
    return map;
  }, [configs]);

  const handleAddConfig = () => {
    if (!newConfig.name?.trim() || !newConfig.provider?.trim() || !newConfig.model?.trim()) return;

    const config: LLMConfig = {
      id: `config_${Date.now()}`,
      name: newConfig.name.trim(),
      provider: newConfig.provider.trim(),
      format: newConfig.format as 'openai' | 'google',
      model: newConfig.model.trim(),
      apiKey: newConfig.apiKey?.trim(),
      baseUrl: newConfig.baseUrl?.trim(),
      temperature: newConfig.temperature || 0.7,
      maxTokens: newConfig.maxTokens || 4096,
      topP: newConfig.topP || 0.9,
      enabled: true,
    };

    addConfig(config);
    setShowAddModal(false);
    setNewConfig({
      name: '',
      provider: '',
      format: 'openai',
      model: '',
      apiKey: '',
      baseUrl: '',
      temperature: 0.7,
      maxTokens: 4096,
      topP: 0.9,
      enabled: true,
    });
  };

  const handleToggleModel = async (id: string, modelId: string, currentEnabled: boolean, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const result = await modelApi.toggleModel(modelId, !currentEnabled);
      if (result.status === 1) {
        updateConfig(id, { enabled: !currentEnabled });
        
        // 如果禁用了当前选中的模型，自动切换到其他可用的模型
        if (currentEnabled && activeConfigId === id) {
          const nextConfig = configs.find(c => c.id !== id && c.enabled);
          if (nextConfig) {
            setActiveConfig(nextConfig.id);
          }
        }
        
        showToast(currentEnabled ? '已禁用模型' : '已启用模型', 'success');
      } else {
        showToast('操作失败: ' + result.msg, 'error');
      }
    } catch (error) {
      console.error('切换模型状态失败:', error);
      showToast('操作失败，请重试', 'error');
    }
  };

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-6 bg-bg-primary">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-text-primary">
            设置
          </h1>
          <p className="text-sm text-text-tertiary mt-1">
            配置AI模型、知识库和其他高级设置
          </p>
        </div>

        <div className="space-y-6">
          <section className="bg-bg-secondary rounded-xl border border-border overflow-hidden">
            <div className="p-4 border-b border-border flex items-center gap-3">
              <Bot className="w-5 h-5 text-primary" />
              <h2 className="font-semibold text-text-primary">AI 模型配置</h2>
            </div>

            <div className="p-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Array.from(providersMap.entries()).map(([providerName, models]) => {
                  const enabledCount = models.filter(m => m.enabled).length;
                  const isActive = models.some(m => m.id === activeConfigId);
                  
                  return (
                    <div
                      key={providerName}
                      onClick={() => setSelectedProvider(providerName)}
                      className={`
                        group relative p-5 rounded-xl border cursor-pointer transition-all duration-200
                        ${isActive
                          ? 'bg-primary/5 border-primary/50 shadow-lg shadow-primary/5'
                          : 'bg-bg-secondary/30 border-border hover:border-primary/30 hover:bg-bg-tertiary/30'
                        }
                      `}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-blue-500/10">
                            <Server className="w-6 h-6 text-blue-500" />
                          </div>
                          <div>
                            <h3 className={`font-semibold ${isActive ? 'text-primary' : 'text-text-primary'}`}>
                              {providerName}
                            </h3>
                            <p className="text-sm text-text-tertiary mt-0.5">
                              {enabledCount} / {models.length} 个模型已启用
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="mt-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-1 text-text-tertiary group-hover:text-primary transition-colors">
                            <span className="text-sm">查看详情</span>
                            <ChevronRight className="w-4 h-4" />
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {models.slice(0, 5).map((model) => (
                            <span
                              key={model.id}
                              className={`
                                text-xs px-2 py-0.5 rounded border truncate max-w-[120px]
                                ${model.enabled 
                                  ? 'bg-primary/10 border-primary/30 text-primary' 
                                  : 'bg-bg-tertiary/50 border-border/50 text-text-tertiary'
                                }
                              `}
                              title={model.name}
                            >
                              {model.name}
                            </span>
                          ))}
                          {models.length > 5 && (
                            <span className="text-xs px-2 py-0.5 rounded bg-bg-tertiary/50 text-text-quaternary">
                              +{models.length - 5}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <button
                onClick={() => setShowAddModal(true)}
                className="w-full flex items-center justify-center gap-2 p-3 border-2 border-dashed border-border rounded-lg text-text-tertiary hover:border-primary hover:text-primary transition-all duration-200"
              >
                <Plus className="w-5 h-5" />
                添加模型配置
              </button>
            </div>
          </section>

          <section className="bg-bg-secondary rounded-xl border border-border overflow-hidden">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-primary" />
                <h2 className="font-semibold text-text-primary">提示词配置</h2>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowAddPromptSection(true)}
                  className="p-2 hover:bg-bg-tertiary rounded-lg text-text-secondary hover:text-primary transition-colors"
                  title="添加提示词模块"
                >
                  <Plus className="w-4 h-4" />
                </button>
                <button
                  onClick={fetchPrompts}
                  className="p-2 hover:bg-bg-tertiary rounded-lg text-text-secondary hover:text-primary transition-colors"
                  title="刷新配置"
                >
                  <RotateCcw className={`w-4 h-4 ${isPromptsLoading ? 'animate-spin' : ''}`} />
                </button>
                <button
                  onClick={handleSavePrompts}
                  className="flex items-center gap-2 px-3 py-1.5 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors text-sm"
                >
                  <Save className="w-4 h-4" />
                  保存生效
                </button>
              </div>
            </div>

            <div className="p-4 space-y-6">
              {Object.entries(prompts).map(([section, content]: [string, any]) => (
                <div key={section} className="border border-border rounded-xl overflow-hidden bg-bg-tertiary/20">
                  <div className="px-4 py-3 bg-bg-tertiary/50 border-b border-border flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-text-primary uppercase tracking-wider text-xs bg-bg-tertiary px-2 py-1 rounded">
                        {section}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setShowAddPromptItem(section)}
                        className="p-1.5 hover:bg-bg-tertiary rounded-lg text-text-tertiary hover:text-primary transition-colors text-xs flex items-center gap-1"
                      >
                        <Plus className="w-3 h-3" />
                        添加项
                      </button>
                      <button
                        onClick={() => handleDeletePromptSection(section)}
                        className="p-1.5 hover:bg-error/10 rounded-lg text-text-tertiary hover:text-error transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="p-4 space-y-4">
                    {Object.entries(content || {}).map(([key, value]: [string, any]) => (
                      <div key={key} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <label className="text-sm font-medium text-text-secondary">
                            {key}
                          </label>
                          <button
                            onClick={() => handleDeletePromptItem(section, key)}
                            className="text-xs text-text-quaternary hover:text-error transition-colors"
                          >
                            删除
                          </button>
                        </div>
                        <textarea
                          value={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                          onChange={(e) => handlePromptChange(section, key, e.target.value)}
                          rows={10}
                          className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all resize-y min-h-[200px]"
                        />
                      </div>
                    ))}
                    {Object.keys(content || {}).length === 0 && (
                      <div className="text-center py-4 text-text-quaternary text-sm">
                        暂无配置项
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>


        </div>
      </div>

      {showAddPromptSection && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-bg-secondary rounded-xl p-6 w-full max-w-sm mx-4 shadow-xl border border-border">
            <h3 className="text-lg font-semibold text-text-primary mb-4">添加提示词模块</h3>
            <input
              type="text"
              value={newPromptSectionName}
              onChange={(e) => setNewPromptSectionName(e.target.value)}
              placeholder="模块名称 (例如: custom)"
              className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary mb-4 focus:outline-none focus:border-primary"
              autoFocus
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowAddPromptSection(false)}
                className="px-4 py-2 bg-bg-tertiary hover:bg-border text-text-secondary rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleAddPromptSection}
                className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors"
              >
                添加
              </button>
            </div>
          </div>
        </div>
      )}

      {showAddPromptItem && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-bg-secondary rounded-xl p-6 w-full max-w-sm mx-4 shadow-xl border border-border">
            <h3 className="text-lg font-semibold text-text-primary mb-4">
              在 {showAddPromptItem} 中添加项
            </h3>
            <input
              type="text"
              value={newPromptItemKey}
              onChange={(e) => setNewPromptItemKey(e.target.value)}
              placeholder="键名 (例如: system)"
              className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary mb-4 focus:outline-none focus:border-primary"
              autoFocus
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowAddPromptItem(null)}
                className="px-4 py-2 bg-bg-tertiary hover:bg-border text-text-secondary rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={() => handleAddPromptItem(showAddPromptItem)}
                className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors"
              >
                添加
              </button>
            </div>
          </div>
        </div>
      )}

      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-bg-secondary rounded-xl p-6 w-full max-w-lg mx-4 shadow-xl border border-border max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-text-primary">
                添加模型配置
              </h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1 hover:bg-bg-tertiary rounded transition-colors"
              >
                <X className="w-5 h-5 text-text-tertiary" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  模型供应商名称 *
                </label>
                <input
                  type="text"
                  value={newConfig.provider}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, provider: e.target.value }))}
                  placeholder="例如: 我的 DeepSeek"
                  className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-quaternary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  接口格式 *
                </label>
                <select
                  value={newConfig.format}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, format: e.target.value as 'openai' | 'google' }))}
                  className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                >
                  <option value="openai" className="bg-bg-secondary">OpenAI 格式</option>
                  <option value="google" className="bg-bg-secondary">Google 格式</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  模型显示名称 *
                </label>
                <input
                  type="text"
                  value={newConfig.name}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="例如: DeepSeek V3"
                  className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-quaternary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  模型 ID *
                </label>
                <input
                  type="text"
                  value={newConfig.model}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, model: e.target.value }))}
                  placeholder="例如: deepseek-chat"
                  className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-quaternary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  API Key (可选)
                </label>
                <div className="relative">
                  <input
                    type={showApiKey.newConfig ? 'text' : 'password'}
                    value={newConfig.apiKey || ''}
                    onChange={(e) => setNewConfig(prev => ({ ...prev, apiKey: e.target.value }))}
                    placeholder={newConfig.apiKey ? '已填写' : '请输入 API Key'}
                    className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-quaternary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(prev => ({ ...prev, newConfig: !prev.newConfig }))}
                    className="absolute right-3 top-1/2 -translate-y-1/2"
                  >
                    {showApiKey.newConfig ? (
                      <EyeOff className="w-4 h-4 text-text-tertiary" />
                    ) : (
                      <Eye className="w-4 h-4 text-text-tertiary" />
                    )}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Base URL (可选)
                </label>
                <input
                  type="text"
                  value={newConfig.baseUrl || ''}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, baseUrl: e.target.value }))}
                  placeholder="使用代理时填写"
                  className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-quaternary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Temperature
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={newConfig.temperature}
                    onChange={(e) => setNewConfig(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                    className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    value={newConfig.maxTokens}
                    onChange={(e) => setNewConfig(prev => ({ ...prev, maxTokens: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Top P
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={newConfig.topP}
                    onChange={(e) => setNewConfig(prev => ({ ...prev, topP: parseFloat(e.target.value) }))}
                    className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 bg-bg-tertiary hover:bg-border text-text-secondary rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleAddConfig}
                disabled={!newConfig.name?.trim() || !newConfig.provider?.trim() || !newConfig.model?.trim()}
                className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                添加配置
              </button>
            </div>
          </div>
        </div>
      )}
      {selectedProvider && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-bg-secondary rounded-xl p-6 w-full max-w-2xl mx-4 shadow-xl border border-border max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-blue-500/10">
                  <Server className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-text-primary">
                    {selectedProvider}
                  </h2>
                  <p className="text-sm text-text-tertiary">
                    管理此提供商下的模型
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedProvider(null)}
                className="p-1 hover:bg-bg-tertiary rounded transition-colors"
              >
                <X className="w-5 h-5 text-text-tertiary" />
              </button>
            </div>

            <div className="space-y-3">
              {(providersMap.get(selectedProvider) || []).map((model) => (
                <div
                  key={model.id}
                  className={`p-4 rounded-xl border transition-all duration-200 ${
                    model.enabled
                      ? 'bg-primary/5 border-primary/30'
                      : 'bg-bg-secondary border-border'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className={`font-medium ${model.enabled ? 'text-text-primary' : 'text-text-secondary'}`}>
                          {model.name}
                        </h3>
                        {model.id === activeConfigId && (
                          <span className="text-xs px-2 py-0.5 rounded bg-primary/20 text-primary font-medium">
                            当前选择
                          </span>
                        )}
                        <span className="text-xs px-2 py-0.5 rounded bg-bg-tertiary text-text-tertiary font-mono">
                          {model.model}
                        </span>
                      </div>
                      <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-text-tertiary">
                        <div>
                          <span className="opacity-70">格式:</span>
                          <span className="ml-1 text-text-secondary">{model.format === 'google' ? 'Google' : 'OpenAI'}</span>
                        </div>
                        <div>
                          <span className="opacity-70">API Key:</span>
                          <span className="ml-1 text-primary/80 font-medium">已配置</span>
                        </div>
                        <div>
                          <span className="opacity-70">Temp:</span>
                          <span className="ml-1 text-text-secondary">{model.temperature}</span>
                        </div>
                        <div>
                          <span className="opacity-70">Tokens:</span>
                          <span className="ml-1 text-text-secondary">{model.maxTokens}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3 ml-4">
                      {!model.enabled && (
                        <button
                          onClick={() => removeConfig(model.id)}
                          className="p-2 hover:bg-error/10 text-text-tertiary hover:text-error rounded-lg transition-colors"
                          title="删除模型"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                      {model.id !== activeConfigId && (
                        <button
                          onClick={() => {
                            if (!model.enabled) {
                              showToast('请先打开模型的使用', 'info');
                              return;
                            }
                            setActiveConfig(model.id);
                          }}
                          className={`px-3 py-1.5 text-xs rounded-lg transition-colors font-medium border ${
                            model.enabled 
                              ? 'bg-primary/10 border-primary/30 text-primary hover:bg-primary hover:text-white' 
                              : 'bg-bg-tertiary/50 border-border text-text-tertiary hover:bg-bg-tertiary'
                          }`}
                        >
                          选择模型
                        </button>
                      )}
                      <button
                        onClick={(e) => handleToggleModel(model.id, model.model, model.enabled, e)}
                        className={`p-2 rounded-lg transition-colors ${
                          model.enabled
                            ? 'bg-primary/20 text-primary hover:bg-primary/30'
                            : 'bg-bg-tertiary text-text-tertiary hover:bg-bg-tertiary/80'
                        }`}
                        title={model.enabled ? '禁用模型' : '启用模型'}
                      >
                        <Power className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
