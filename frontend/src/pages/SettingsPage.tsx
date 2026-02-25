import { useState } from 'react';
import { 
  Bot, 
  Database, 
  Plus, 
  Trash2, 
  Check, 
  X,
  Eye,
  EyeOff,
  Sparkles,
} from 'lucide-react';
import { useSettingsStore } from '@/stores/settingsStore';
import { PROVIDER_LABELS, type LLMProvider } from '@/types/config';

const MODEL_OPTIONS: Record<LLMProvider, string[]> = {
  openai: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  anthropic: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
  google: ['gemini-pro', 'gemini-pro-vision'],
  qwen: ['qwen-turbo', 'qwen-plus', 'qwen-max'],
  doubao: ['doubao-pro-32k', 'doubao-pro-4k'],
  moonshot: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'],
  ollama: ['llama2', 'mistral', 'qwen', 'codellama'],
};

const EMBEDDING_MODELS = [
  { id: 'all-MiniLM-L6-v2', name: 'all-MiniLM-L6-v2 (速度快)', description: '适合轻量级使用' },
  { id: 'text-embedding-ada-002', name: 'text-embedding-ada-002', description: 'OpenAI官方' },
  { id: 'text-embedding-3-small', name: 'text-embedding-3-small', description: '新一代小型模型' },
  { id: 'bge-small-zh-v1.5', name: 'bge-small-zh-v1.5', description: '中文优化' },
  { id: 'bge-base-zh-v1.5', name: 'bge-base-zh-v1.5', description: '中文基础模型' },
];

const SettingsPage = () => {
  const { 
    configs, 
    activeConfigId, 
    defaultSystemPrompt,
    addConfig, 
    removeConfig, 
    setActiveConfig,
    setDefaultSystemPrompt,
  } = useSettingsStore();

  const [showAddModal, setShowAddModal] = useState(false);
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({});

  const [newConfig, setNewConfig] = useState({
    name: '',
    provider: 'openai' as LLMProvider,
    model: 'gpt-3.5-turbo',
    apiKey: '',
    baseUrl: '',
    temperature: 0.7,
    maxTokens: 4096,
    topP: 0.9,
  });

  const handleAddConfig = () => {
    if (!newConfig.name.trim() || !newConfig.apiKey.trim()) return;

    const config = {
      id: `config_${Date.now()}`,
      name: newConfig.name.trim(),
      provider: newConfig.provider,
      model: newConfig.model,
      apiKey: newConfig.apiKey.trim(),
      baseUrl: newConfig.baseUrl.trim() || undefined,
      temperature: newConfig.temperature,
      maxTokens: newConfig.maxTokens,
      topP: newConfig.topP,
      enabled: true,
    };

    addConfig(config);
    setShowAddModal(false);
    setNewConfig({
      name: '',
      provider: 'openai',
      model: 'gpt-3.5-turbo',
      apiKey: '',
      baseUrl: '',
      temperature: 0.7,
      maxTokens: 4096,
      topP: 0.9,
    });
  };

  const handleProviderChange = (provider: LLMProvider) => {
    setNewConfig(prev => ({
      ...prev,
      provider,
      model: MODEL_OPTIONS[provider][0],
    }));
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
              {configs.map(config => (
                <div
                  key={config.id}
                  className={`p-4 rounded-lg border transition-all duration-200 ${
                    activeConfigId === config.id
                      ? 'selected-item'
                      : 'border-border hover:border-primary/50 hover:bg-bg-tertiary'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => setActiveConfig(config.id)}
                        className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                          activeConfigId === config.id
                            ? 'border-primary bg-primary'
                            : 'border-text-quaternary hover:border-primary'
                        }`}
                      >
                        {activeConfigId === config.id && (
                          <Check className="w-3 h-3 text-white" />
                        )}
                      </button>
                      <div>
                        <h3 className={`font-medium ${activeConfigId === config.id ? 'text-white' : 'text-text-primary'}`}>
                          {config.name}
                        </h3>
                        <p className={`text-xs ${activeConfigId === config.id ? 'text-white/70' : 'text-text-tertiary'}`}>
                          {PROVIDER_LABELS[config.provider]} · {config.model}
                        </p>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => removeConfig(config.id)}
                      className="p-1.5 hover:bg-error/10 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4 text-error" />
                    </button>
                  </div>

                  <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 text-sm ${activeConfigId === config.id ? 'text-white/80' : ''}`}>
                    <div>
                      <span className={activeConfigId === config.id ? 'text-white/60' : 'text-text-tertiary'}>Temperature:</span>
                      <span className={`ml-2 ${activeConfigId === config.id ? 'text-white' : 'text-text-secondary'}`}>{config.temperature}</span>
                    </div>
                    <div>
                      <span className={activeConfigId === config.id ? 'text-white/60' : 'text-text-tertiary'}>Max Tokens:</span>
                      <span className={`ml-2 ${activeConfigId === config.id ? 'text-white' : 'text-text-secondary'}`}>{config.maxTokens}</span>
                    </div>
                    <div>
                      <span className={activeConfigId === config.id ? 'text-white/60' : 'text-text-tertiary'}>Top P:</span>
                      <span className={`ml-2 ${activeConfigId === config.id ? 'text-white' : 'text-text-secondary'}`}>{config.topP}</span>
                    </div>
                    <div>
                      <span className={activeConfigId === config.id ? 'text-white/60' : 'text-text-tertiary'}>API Key:</span>
                      <span className={`ml-2 ${activeConfigId === config.id ? 'text-white' : 'text-text-secondary'}`}>
                        {config.apiKey ? '••••••••' : '未设置'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}

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
            <div className="p-4 border-b border-border flex items-center gap-3">
              <Sparkles className="w-5 h-5 text-primary" />
              <h2 className="font-semibold text-text-primary">默认 System Prompt</h2>
            </div>

            <div className="p-4">
              <textarea
                value={defaultSystemPrompt}
                onChange={(e) => setDefaultSystemPrompt(e.target.value)}
                placeholder="设置默认的系统提示词..."
                rows={4}
                className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-quaternary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all resize-none"
              />
              <p className="text-xs text-text-tertiary mt-2">
                这个提示词将作为所有新对话的默认系统消息
              </p>
            </div>
          </section>

          <section className="bg-bg-secondary rounded-xl border border-border overflow-hidden">
            <div className="p-4 border-b border-border flex items-center gap-3">
              <Database className="w-5 h-5 text-primary" />
              <h2 className="font-semibold text-text-primary">向量数据库配置</h2>
            </div>

            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Embedding 模型
                </label>
                <select className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all">
                  {EMBEDDING_MODELS.map(model => (
                    <option key={model.id} value={model.id} className="bg-bg-secondary">
                      {model.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-text-tertiary mt-2">
                  用于将文本转换为向量表示，影响检索质量
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  向量库类型
                </label>
                <select className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all">
                  <option value="chroma" className="bg-bg-secondary">ChromaDB (轻量级)</option>
                  <option value="milvus" className="bg-bg-secondary">Milvus (企业级)</option>
                  <option value="pinecone" className="bg-bg-secondary">Pinecone (云服务)</option>
                  <option value="qdrant" className="bg-bg-secondary">Qdrant (开源)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Chunk Size
                  </label>
                  <input
                    type="number"
                    defaultValue={1000}
                    className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Chunk Overlap
                  </label>
                  <input
                    type="number"
                    defaultValue={200}
                    className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                  />
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>

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
                  配置名称 *
                </label>
                <input
                  type="text"
                  value={newConfig.name}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="例如: GPT-4 API"
                  className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary placeholder-text-quaternary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  模型供应商 *
                </label>
                <select
                  value={newConfig.provider}
                  onChange={(e) => handleProviderChange(e.target.value as LLMProvider)}
                  className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                >
                  {Object.entries(PROVIDER_LABELS).map(([key, label]) => (
                    <option key={key} value={key} className="bg-bg-secondary">{label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  模型 *
                </label>
                <select
                  value={newConfig.model}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, model: e.target.value }))}
                  className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-text-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                >
                  {MODEL_OPTIONS[newConfig.provider].map(model => (
                    <option key={model} value={model} className="bg-bg-secondary">{model}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  API Key *
                </label>
                <div className="relative">
                  <input
                    type={showApiKey.newConfig ? 'text' : 'password'}
                    value={newConfig.apiKey}
                    onChange={(e) => setNewConfig(prev => ({ ...prev, apiKey: e.target.value }))}
                    placeholder="请输入 API Key"
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
                  value={newConfig.baseUrl}
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
                disabled={!newConfig.name.trim() || !newConfig.apiKey.trim()}
                className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                添加配置
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
