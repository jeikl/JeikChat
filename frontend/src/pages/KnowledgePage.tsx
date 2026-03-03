import { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Plus, Upload, FileText, Trash2, RefreshCw, Loader2, X } from 'lucide-react';
import { showToast } from '@/utils/toast';
import { useKnowledgeStore } from '@/stores/knowledgeStore';
import { knowledgeApi } from '@/services/knowledge';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

const showToastOnce = (() => {
  const shown = new Set<string>();
  return (key: string, callback: () => void) => {
    if (!shown.has(key)) {
      shown.add(key);
      callback();
    }
  };
})();

const ALLOWED_FILE_TYPES = [
  { type: 'application/pdf', label: 'PDF', icon: '📄' },
  { type: 'application/vnd.ms-excel', label: 'Excel', icon: '📊' },
  { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', label: 'Excel', icon: '📊' },
  { type: 'text/csv', label: 'CSV', icon: '📋' },
  { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', label: 'Word', icon: '📝' },
  { type: 'application/msword', label: 'Word', icon: '📝' },
  { type: 'text/plain', label: 'TXT', icon: '📃' },
  { type: 'text/markdown', label: 'Markdown', icon: '📋' },
];

const KnowledgePage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    knowledgeBases,
    isUploading,
    uploadProgress,
    addKnowledgeBase,
    removeKnowledgeBase,
    setUploading,
    setUploadProgress,
  } = useKnowledgeStore();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKnowledgeName, setNewKnowledgeName] = useState('');
  const [newKnowledgeDescription, setNewKnowledgeDescription] = useState('');
  const [selectedKnowledgeId, setSelectedKnowledgeId] = useState<string | null>(null);
  const [uploadDragging, setUploadDragging] = useState(false);
  const knowledgeList = useKnowledgeStore(state => state.knowledgeBases);

  useEffect(() => {
    const tabParam = searchParams.get('tab');
    if (tabParam === 'tools') {
      setSearchParams({ tab: 'knowledge' });
    }
  }, [searchParams]);

  useQuery({
    queryKey: ['knowledgeBases'],
    queryFn: async () => {
      const result = await knowledgeApi.list();
      useKnowledgeStore.getState().setKnowledgeBases(result.data);
      if (result.status === 0) {
        showToastOnce('kb-empty', () => {
          showToast(result.msg || '未获取到知识库', 'empty');
        });
      }
      return result.data;
    },
  });

  useEffect(() => {
    if (knowledgeList && knowledgeList.length > 0) {
      showToastOnce('kb-loaded', () => {
        showToast(`已加载 ${knowledgeList.length} 个知识库`, 'success');
      });
    }
  }, [knowledgeList]);

  useEffect(() => {
    if (knowledgeList && knowledgeList.length === 0) {
      showToastOnce('kb-empty-page', () => {
        showToast('暂无知识库，请先创建', 'empty');
      });
    }
  }, [knowledgeList]);

  const handleCreateKnowledge = async () => {
    if (!newKnowledgeName.trim()) return;

    try {
      const newKB = await knowledgeApi.create({
        name: newKnowledgeName.trim(),
        description: newKnowledgeDescription.trim(),
      });
      addKnowledgeBase(newKB);
      setShowCreateModal(false);
      setNewKnowledgeName('');
      setNewKnowledgeDescription('');
      showToast('知识库创建成功', 'success');
    } catch (error) {
      console.error('创建知识库失败:', error);
      showToast('创建知识库失败', 'error');
    }
  };

  const handleDeleteKnowledge = async (id: string) => {
    if (!confirm('确定要删除这个知识库吗？此操作不可恢复。')) return;

    try {
      await knowledgeApi.delete(id);
      removeKnowledgeBase(id);
      showToast('知识库已删除', 'success');
    } catch (error) {
      console.error('删除知识库失败:', error);
      showToast('删除知识库失败', 'error');
    }
  };

  const handleFileUpload = useCallback(async (files: FileList | File[]) => {
    if (!selectedKnowledgeId) {
      showToast('请先选择一个知识库', 'error');
      return;
    }

    const fileArray = Array.from(files);
    setUploading(true);
    setUploadProgress(0);

    try {
      for (let i = 0; i < fileArray.length; i++) {
        const file = fileArray[i];
        await knowledgeApi.uploadFile(selectedKnowledgeId, file, (progress) => {
          setUploadProgress(Math.round(((i + progress / 100) / fileArray.length) * 100));
        });
      }
      showToast(`成功上传 ${fileArray.length} 个文件，正在处理向量...`, 'success');
    } catch (error) {
      console.error('上传文件失败:', error);
      showToast('文件上传失败，请重试', 'error');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  }, [selectedKnowledgeId, setUploading, setUploadProgress]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setUploadDragging(true);
  };

  const handleDragLeave = () => {
    setUploadDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setUploadDragging(false);
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  const selectedKnowledge = knowledgeBases.find(kb => kb.id === selectedKnowledgeId);

  return (
    <div className="h-full flex flex-col p-6 bg-bg-primary overflow-hidden">
      {/* 顶部标题与操作区 */}
      <div className="flex flex-col gap-4 sm:gap-6 mb-6 flex-shrink-0">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-text-primary tracking-tight truncate">
              知识库管理
            </h1>
            <p className="text-xs sm:text-sm text-text-tertiary mt-1 sm:mt-1.5 opacity-80 line-clamp-2">
              上传文档并创建知识库，让 AI 能够基于这些文档回答问题
            </p>
          </div>
          
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center justify-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-xl transition-all duration-300 shadow-lg shadow-primary/20 hover:shadow-primary/40 active:scale-95 group flex-shrink-0 w-full sm:w-auto"
          >
            <Plus className="w-5 h-5 transition-transform group-hover:rotate-90 flex-shrink-0" />
            <span className="font-medium whitespace-nowrap">创建知识库</span>
          </button>
        </div>

        {/* 标签页切换 - 即使只有一个也保留结构以便未来扩展 */}
        <div className="flex items-center border-b border-border">
          <button
            className="flex items-center gap-2 px-4 py-3 text-sm font-medium text-primary border-b-2 border-primary transition-colors bg-primary/5"
          >
            <FileText className="w-4 h-4" />
            <span>知识库列表</span>
          </button>
        </div>
      </div>

      <div className="flex-1 flex gap-6 min-h-0 overflow-hidden">
        {/* 左侧列表 */}
        <div className="w-80 flex-shrink-0 bg-bg-secondary/50 backdrop-blur-sm rounded-2xl border border-border overflow-hidden flex flex-col shadow-sm">
          <div className="p-4 border-b border-border">
            <h2 className="font-medium text-text-primary">知识库列表</h2>
          </div>
          
          <div className="overflow-y-auto scrollbar-thin" style={{ maxHeight: 'calc(100% - 57px)' }}>
            {knowledgeBases.length === 0 ? (
              <div className="p-8 text-center">
                <FileText className="w-12 h-12 mx-auto mb-3 text-text-quaternary" />
                <p className="text-sm text-text-tertiary">暂无知识库</p>
              </div>
            ) : (
              <div className="p-2 space-y-2">
                {knowledgeBases.map(kb => (
                  <div
                    key={kb.id}
                    onClick={() => setSelectedKnowledgeId(kb.id)}
                    className={`p-3 rounded-lg cursor-pointer transition-all duration-200 ${
                      selectedKnowledgeId === kb.id
                        ? 'selected-item'
                        : 'hover:bg-bg-tertiary border border-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className={`font-medium truncate ${selectedKnowledgeId === kb.id ? 'text-white' : 'text-text-primary'}`}>
                          {kb.name}
                        </h3>
                        <p className={`text-xs ${selectedKnowledgeId === kb.id ? 'text-white/70' : 'text-text-tertiary'} mt-1`}>
                          {kb.fileCount} 个文件
                        </p>
                      </div>
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 mt-1.5 ${
                        kb.status === 'ready' ? 'bg-success' :
                        kb.status === 'processing' ? 'bg-warning animate-pulse' :
                        'bg-error'
                      }`} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 bg-bg-secondary rounded-xl border border-border overflow-hidden">
          {selectedKnowledge ? (
            <>
              <div className="p-4 border-b border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-semibold text-text-primary text-lg">
                      {selectedKnowledge.name}
                    </h2>
                    <p className="text-sm text-text-tertiary mt-1">
                      创建于 {format(selectedKnowledge.createdAt, 'yyyy年MM月dd日', { locale: zhCN })}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => knowledgeApi.rebuild(selectedKnowledge.id)}
                      className="p-2 hover:bg-bg-tertiary rounded-lg transition-colors"
                      title="重建索引"
                    >
                      <RefreshCw className="w-5 h-5 text-text-tertiary" />
                    </button>
                    <button
                      onClick={() => handleDeleteKnowledge(selectedKnowledge.id)}
                      className="p-2 hover:bg-error/10 rounded-lg transition-colors"
                      title="删除知识库"
                    >
                      <Trash2 className="w-5 h-5 text-error" />
                    </button>
                  </div>
                </div>
              </div>

              <div className="p-6">
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
                    uploadDragging
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  {isUploading ? (
                    <div className="py-4">
                      <Loader2 className="w-12 h-12 mx-auto mb-4 text-primary animate-spin" />
                      <p className="text-text-secondary mb-2">
                        正在上传文件...
                      </p>
                      <div className="w-64 mx-auto bg-bg-tertiary rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                      <p className="text-sm text-text-tertiary mt-2">{uploadProgress}%</p>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-12 h-12 mx-auto mb-4 text-text-tertiary" />
                      <p className="text-text-secondary mb-2">
                        拖拽文件到此处上传，或点击选择文件
                      </p>
                      <p className="text-sm text-text-tertiary mb-4">
                        支持 {ALLOWED_FILE_TYPES.map(t => t.label).join('、')} 等格式
                      </p>
                      <label className="inline-flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg cursor-pointer transition-all duration-200 shadow-md hover:shadow-lg">
                        <Upload className="w-4 h-4" />
                        选择文件
                        <input
                          type="file"
                          multiple
                          accept={ALLOWED_FILE_TYPES.map(t => t.type).join(',')}
                          className="hidden"
                          onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                        />
                      </label>
                    </>
                  )}
                </div>

                {selectedKnowledge.systemPrompt && (
                  <div className="mt-6 p-4 bg-bg-tertiary rounded-lg border border-border">
                    <h3 className="font-medium text-text-primary mb-2">
                      System Prompt
                    </h3>
                    <p className="text-sm text-text-secondary whitespace-pre-wrap">
                      {selectedKnowledge.systemPrompt}
                    </p>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-8">
              <FileText className="w-16 h-16 text-text-quaternary mb-4" />
              <h3 className="text-lg font-medium text-text-primary mb-2">
                选择一个知识库
              </h3>
              <p className="text-text-tertiary max-w-md">
                从左侧选择一个知识库来查看详情、上传文件或编辑配置
              </p>
            </div>
          )}
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-bg-secondary rounded-xl p-6 w-full max-w-md mx-4 shadow-xl border border-border">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-text-primary">
                创建知识库
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 hover:bg-bg-tertiary rounded transition-colors"
              >
                <X className="w-5 h-5 text-text-tertiary" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  名称
                </label>
                <input
                  type="text"
                  value={newKnowledgeName}
                  onChange={(e) => setNewKnowledgeName(e.target.value)}
                  placeholder="输入知识库名称"
                  className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  描述
                </label>
                <textarea
                  value={newKnowledgeDescription}
                  onChange={(e) => setNewKnowledgeDescription(e.target.value)}
                  placeholder="输入知识库描述"
                  rows={3}
                  className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-border rounded-lg text-text-secondary hover:bg-bg-tertiary transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreateKnowledge}
                disabled={!newKnowledgeName.trim()}
                className="flex-1 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgePage;