import { useState, useCallback, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  Plus, Upload, FileText, Trash2, RefreshCw, Loader2, X, 
  Check, BookOpen, FolderOpen, FileUp, AlertCircle, Edit2
} from 'lucide-react';
import { showToast } from '@/utils/toast';
import { useKnowledgeStore } from '@/stores/knowledgeStore';
import { knowledgeApi } from '@/services/api';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import type { UploadStatus } from '@/types/knowledge';

const showToastOnce = (() => {
  const shown = new Set<string>();
  return (key: string, callback: () => void) => {
    if (!shown.has(key)) {
      shown.add(key);
      callback();
    }
  };
})();

// 支持的所有文件类型
const ALLOWED_FILE_TYPES = [
  { type: 'application/pdf', label: 'PDF', icon: '📄', extensions: ['.pdf'] },
  { type: 'application/vnd.ms-excel', label: 'Excel', icon: '📊', extensions: ['.xls'] },
  { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', label: 'Excel', icon: '📊', extensions: ['.xlsx'] },
  { type: 'text/csv', label: 'CSV', icon: '📋', extensions: ['.csv'] },
  { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', label: 'Word', icon: '📝', extensions: ['.docx'] },
  { type: 'application/msword', label: 'Word', icon: '📝', extensions: ['.doc'] },
  { type: 'application/vnd.ms-powerpoint', label: 'PPT', icon: '📽️', extensions: ['.ppt'] },
  { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', label: 'PPT', icon: '📽️', extensions: ['.pptx'] },
  { type: 'text/plain', label: 'TXT', icon: '📃', extensions: ['.txt'] },
  { type: 'text/markdown', label: 'Markdown', icon: '📋', extensions: ['.md', '.markdown'] },
  { type: 'text/html', label: 'HTML', icon: '🌐', extensions: ['.html', '.htm'] },
];

// 获取文件扩展名
const getFileExtension = (filename: string): string => {
  return filename.slice(filename.lastIndexOf('.')).toLowerCase();
};

// 检查文件类型是否允许
const isFileTypeAllowed = (file: File): boolean => {
  // 先检查 MIME 类型
  if (ALLOWED_FILE_TYPES.some(t => t.type === file.type)) {
    return true;
  }
  // 再检查扩展名
  const ext = getFileExtension(file.name);
  return ALLOWED_FILE_TYPES.some(t => t.extensions.includes(ext));
};

// 获取文件类型标签
const getFileTypeLabel = (file: File): string => {
  const type = ALLOWED_FILE_TYPES.find(t => t.type === file.type);
  if (type) return type.label;
  const ext = getFileExtension(file.name);
  const typeByExt = ALLOWED_FILE_TYPES.find(t => t.extensions.includes(ext));
  return typeByExt?.label || '未知';
};

const KnowledgePage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    knowledgeBases,
    selectedKnowledgeIds,
    isUploading,
    uploadProgress,
    uploadStatuses,
    currentUploadFile,
    addKnowledgeBase,
    removeKnowledgeBase,
    updateKnowledgeBase,
    setUploading,
    setUploadProgress,
    setUploadStatuses,
    updateUploadStatus,
    setCurrentUploadFile,
    clearUploadStatuses,
    toggleKnowledgeSelection,
    selectAllKnowledge,
    setKnowledgeBases,
  } = useKnowledgeStore();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingKnowledgeId, setEditingKnowledgeId] = useState<string | null>(null);
  const [newKnowledgeName, setNewKnowledgeName] = useState('');
  const [newKnowledgeDescription, setNewKnowledgeDescription] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadDragging, setUploadDragging] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 获取知识库列表
  useQuery({
    queryKey: ['knowledgeBases'],
    queryFn: async () => {
      const result = await knowledgeApi.list();
      setKnowledgeBases(result.data);
      if (result.status === 0) {
        showToastOnce('kb-empty', () => {
          showToast(result.msg || '未获取到知识库', 'empty');
        });
      }
      return result.data;
    },
  });

  // 处理文件选择
  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;
    
    const fileArray = Array.from(files);
    const validFiles: File[] = [];
    const invalidFiles: string[] = [];

    fileArray.forEach(file => {
      if (isFileTypeAllowed(file)) {
        validFiles.push(file);
      } else {
        invalidFiles.push(file.name);
      }
    });

    if (invalidFiles.length > 0) {
      showToast(`不支持的文件类型: ${invalidFiles.join(', ')}`, 'error');
    }

    if (validFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validFiles]);
      // 自动设置知识库名称为第一个文件名（去掉扩展名）
      if (newKnowledgeName === '' && validFiles.length > 0) {
        const firstFileName = validFiles[0].name;
        const nameWithoutExt = firstFileName.substring(0, firstFileName.lastIndexOf('.')) || firstFileName;
        setNewKnowledgeName(nameWithoutExt);
      }
    }
  };

  // 移除已选择的文件
  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // 清空所有已选择的文件
  const handleClearFiles = () => {
    setSelectedFiles([]);
    setNewKnowledgeName('');
  };

  // 处理拖拽
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
    handleFileSelect(e.dataTransfer.files);
  };

  // 创建知识库并上传文件（使用异步API，支持实时进度）
  const handleCreateKnowledge = async () => {
    if (!newKnowledgeName.trim()) {
      showToast('请输入知识库名称', 'error');
      return;
    }
    if (selectedFiles.length === 0) {
      showToast('请至少选择一个文件', 'error');
      return;
    }

    setIsCreating(true);
    setUploading(true);
    clearUploadStatuses();

    // 初始化上传状态
    const initialStatuses: UploadStatus[] = selectedFiles.map(file => ({
      fileName: file.name,
      progress: 0,
      status: 'uploading',
    }));
    setUploadStatuses(initialStatuses);

    let closeProgressStream: (() => void) | null = null;

    try {
      // 使用异步创建API，启动创建任务
      const { taskId, knowledgeBase } = await knowledgeApi.createAsync(
        newKnowledgeName.trim(),
        selectedFiles,
        newKnowledgeDescription
      );

      // 立即将知识库添加到列表（状态为processing）
      addKnowledgeBase(knowledgeBase);
      setShowCreateModal(false);
      setNewKnowledgeName('');
      setNewKnowledgeDescription('');
      setSelectedFiles([]);

      // 连接SSE获取实时进度
      closeProgressStream = knowledgeApi.getCreateProgress(
        taskId,
        (data) => {
          // 更新进度
          setUploadProgress(data.progress);
          setCurrentUploadFile(data.message);
          
          // 更新上传状态
          selectedFiles.forEach(file => {
            updateUploadStatus(file.name, { 
              progress: data.progress, 
              status: data.status === 'error' ? 'error' : 'uploading',
              errorMessage: data.status === 'error' ? data.message : undefined
            });
          });

          // 更新知识库状态和进度
          if (knowledgeBase && knowledgeBase.id) {
            updateKnowledgeBase(knowledgeBase.id, {
              status: data.status === 'error' ? 'error' : 'processing',
              progress: data.progress,
              progressMessage: data.message,
              totalChunks: data.totalChunks,
              processedChunks: data.processedChunks,
            });
          }

          // 如果完成，更新知识库状态
          if (data.status === 'completed') {
            selectedFiles.forEach(file => {
              updateUploadStatus(file.name, { status: 'success', progress: 100 });
            });
            if (knowledgeBase && knowledgeBase.id) {
              updateKnowledgeBase(knowledgeBase.id, { 
                status: 'ready',
                progress: 100,
                progressMessage: '创建完成',
              });
            }
            clearUploadStatuses();
            showToast('知识库创建成功', 'success');
          } else if (data.status === 'error') {
            selectedFiles.forEach(file => {
              updateUploadStatus(file.name, { 
                status: 'error', 
                errorMessage: data.message 
              });
            });
            if (knowledgeBase && knowledgeBase.id) {
              updateKnowledgeBase(knowledgeBase.id, { 
                status: 'error',
                progress: 0,
                progressMessage: data.message,
              });
            }
            showToast(data.message, 'error');
          }
        },
        (error) => {
          console.error('进度流错误:', error);
          showToast('获取进度失败', 'error');
        }
      );

    } catch (error) {
      console.error('创建知识库失败:', error);
      showToast('创建知识库失败', 'error');
      // 更新文件状态为错误
      selectedFiles.forEach(file => {
        updateUploadStatus(file.name, { 
          status: 'error', 
          errorMessage: '上传失败' 
        });
      });
    } finally {
      setIsCreating(false);
      setUploading(false);
      // 注意：这里不清理进度，因为SSE还在运行
      // 清理工作会在SSE回调中完成
    }
  };

  // 删除知识库
  const handleDeleteKnowledge = async (id: string, name: string) => {
    if (!confirm(`确定要删除知识库"${name}"吗？此操作不可恢复。`)) return;

    try {
      await knowledgeApi.delete(id);
      removeKnowledgeBase(id);
      showToast('知识库已删除', 'success');
    } catch (error) {
      console.error('删除知识库失败:', error);
      showToast('删除知识库失败', 'error');
    }
  };

  // 批量删除知识库
  const handleBatchDelete = async () => {
    if (selectedKnowledgeIds.length === 0) return;
    
    if (!confirm(`确定要删除选中的 ${selectedKnowledgeIds.length} 个知识库吗？此操作不可恢复。`)) return;

    let successCount = 0;
    let failCount = 0;

    for (const id of selectedKnowledgeIds) {
      try {
        await knowledgeApi.delete(id);
        removeKnowledgeBase(id);
        successCount++;
      } catch (error) {
        console.error(`删除知识库 ${id} 失败:`, error);
        failCount++;
      }
    }

    if (failCount === 0) {
      showToast(`成功删除 ${successCount} 个知识库`, 'success');
    } else {
      showToast(`删除完成：成功 ${successCount} 个，失败 ${failCount} 个`, 'error');
    }
  };

  // 打开编辑弹窗
  const handleOpenEdit = (e: React.MouseEvent, kb: KnowledgeBase) => {
    e.stopPropagation();
    setEditingKnowledgeId(kb.id);
    setNewKnowledgeDescription(kb.description || '');
    setShowEditModal(true);
  };

  // 保存编辑
  const handleSaveEdit = async () => {
    if (!editingKnowledgeId) return;
    
    setIsCreating(true);
    try {
      await knowledgeApi.update(editingKnowledgeId, { description: newKnowledgeDescription });
      updateKnowledgeBase(editingKnowledgeId, { description: newKnowledgeDescription });
      showToast('知识库已更新', 'success');
      setShowEditModal(false);
      setEditingKnowledgeId(null);
      setNewKnowledgeDescription('');
    } catch (error) {
      console.error('更新知识库失败:', error);
      showToast('更新知识库失败', 'error');
    } finally {
      setIsCreating(false);
    }
  };

  // 全选/取消全选
  const handleSelectAll = () => {
    const allSelected = selectedKnowledgeIds.length === knowledgeBases.length && knowledgeBases.length > 0;
    selectAllKnowledge(!allSelected);
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

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

        {/* 标签页切换 */}
        <div className="flex items-center border-b border-border">
          <button className="flex items-center gap-2 px-4 py-3 text-sm font-medium text-primary border-b-2 border-primary transition-colors bg-primary/5">
            <BookOpen className="w-4 h-4" />
            <span>知识库列表</span>
          </button>
        </div>
      </div>

      {/* 全选操作栏 */}
      {knowledgeBases.length > 0 && (
        <div className="flex items-center justify-between mb-4 px-2">
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 cursor-pointer group">
              <div className={`
                w-5 h-5 rounded border-2 flex items-center justify-center transition-all duration-200
                ${selectedKnowledgeIds.length === knowledgeBases.length && knowledgeBases.length > 0
                  ? 'bg-primary border-primary' 
                  : 'border-border group-hover:border-primary/50'
                }
              `}>
                {(selectedKnowledgeIds.length === knowledgeBases.length && knowledgeBases.length > 0) && (
                  <Check className="w-3.5 h-3.5 text-white" />
                )}
              </div>
              <input
                type="checkbox"
                className="hidden"
                checked={selectedKnowledgeIds.length === knowledgeBases.length && knowledgeBases.length > 0}
                onChange={handleSelectAll}
              />
              <span className="text-sm text-text-secondary">全选</span>
            </label>
            {selectedKnowledgeIds.length > 0 && (
              <span className="text-xs text-text-tertiary">
                已选择 {selectedKnowledgeIds.length} 个知识库
              </span>
            )}
          </div>
          
          {/* 批量删除按钮 */}
          {selectedKnowledgeIds.length > 0 && (
            <button
              onClick={handleBatchDelete}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-error hover:bg-error/10 rounded-lg transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              批量删除
            </button>
          )}
        </div>
      )}

      {/* 知识库列表 */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {knowledgeBases.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8">
            <div className="w-20 h-20 rounded-full bg-bg-tertiary flex items-center justify-center mb-4">
              <BookOpen className="w-10 h-10 text-text-quaternary" />
            </div>
            <h3 className="text-lg font-medium text-text-primary mb-2">
              暂无知识库
            </h3>
            <p className="text-text-tertiary max-w-md mb-6">
              点击上方"创建知识库"按钮，上传文档创建您的第一个知识库
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-all"
            >
              <Plus className="w-4 h-4" />
              立即创建
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {knowledgeBases.map((kb) => (
              <div
                key={kb.id}
                className={`
                  group relative p-4 rounded-xl border transition-all duration-300
                  ${selectedKnowledgeIds.includes(kb.id)
                    ? 'border-primary bg-primary/5 shadow-md shadow-primary/10'
                    : 'border-border bg-bg-secondary hover:border-primary/30 hover:shadow-sm'
                  }
                `}
              >
                {/* 勾选框 */}
                <label className="absolute top-3 left-3 cursor-pointer z-10">
                  <div className={`
                    w-5 h-5 rounded border-2 flex items-center justify-center transition-all duration-200
                    ${selectedKnowledgeIds.includes(kb.id)
                      ? 'bg-primary border-primary' 
                      : 'border-border group-hover:border-primary/50 bg-bg-primary'
                    }
                  `}>
                    {selectedKnowledgeIds.includes(kb.id) && (
                      <Check className="w-3.5 h-3.5 text-white" />
                    )}
                  </div>
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={selectedKnowledgeIds.includes(kb.id)}
                    onChange={() => toggleKnowledgeSelection(kb.id)}
                  />
                </label>

                {/* 内容区 */}
                <div className="pl-8 pr-1" onClick={() => toggleKnowledgeSelection(kb.id)}>
                  <div className="flex items-start justify-between mb-2 gap-2">
                    <h3 className="font-medium text-text-primary truncate" title={kb.name}>
                      {kb.name}
                    </h3>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <div className={`
                        w-2 h-2 rounded-full
                        ${kb.status === 'ready' ? 'bg-success' :
                          kb.status === 'processing' ? 'bg-warning animate-pulse' :
                          'bg-error'
                        }
                      `} title={kb.status === 'ready' ? '就绪' : kb.status === 'processing' ? '处理中' : '错误'} />
                    </div>
                  </div>
                  
                  {kb.description && (
                    <p className="text-xs text-text-tertiary mb-3 line-clamp-2">
                      {kb.description}
                    </p>
                  )}

                  {/* 处理中状态显示进度条 */}
                  {kb.status === 'processing' && (
                    <div className="mb-3">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-success flex items-center gap-1">
                          <Loader2 className="w-3 h-3 animate-spin" />
                          处理中...
                        </span>
                        <span className="text-text-tertiary">
                          {kb.progressMessage 
                            ? kb.progressMessage
                            : (kb.totalChunks && kb.totalChunks > 0)
                              ? `已添加 ${kb.processedChunks || 0}/${kb.totalChunks} 个文档块`
                              : '正在处理文档...'}
                        </span>
                      </div>
                      <div className="h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-success rounded-full transition-all duration-300"
                          style={{ width: `${kb.progress || 0}%` }}
                        />
                      </div>
                      <div className="text-right text-xs text-text-quaternary mt-0.5">
                        {kb.progress || 0}%
                      </div>
                    </div>
                  )}

                  {/* 底部信息和操作按钮 */}
                  <div className="flex items-center justify-between text-xs text-text-tertiary mt-3">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1">
                        <FolderOpen className="w-3.5 h-3.5" />
                        {kb.fileCount || 0} 个文件
                      </span>
                      <span>{format(new Date(kb.updatedAt || kb.createdAt || Date.now()), 'yyyy-MM-dd', { locale: zhCN })}</span>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={(e) => handleOpenEdit(e, kb)}
                        className="p-1.5 hover:bg-primary/10 rounded-lg transition-colors"
                        title="编辑知识库描述"
                      >
                        <Edit2 className="w-4 h-4 text-text-tertiary hover:text-primary" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteKnowledge(kb.id, kb.name);
                        }}
                        className="p-1.5 hover:bg-error/10 hover:text-error rounded-lg transition-colors"
                        title="删除知识库"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 创建知识库弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-bg-secondary rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-xl border border-border flex flex-col">
            {/* 弹窗头部 */}
            <div className="flex items-center justify-between p-5 border-b border-border">
              <div>
                <h2 className="text-lg font-semibold text-text-primary">
                  创建知识库
                </h2>
                <p className="text-xs text-text-tertiary mt-0.5">
                  上传文档，AI 将基于这些文档回答问题
                </p>
              </div>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setSelectedFiles([]);
                  setNewKnowledgeName('');
                  setNewKnowledgeDescription('');
                }}
                className="p-2 hover:bg-bg-tertiary rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-text-tertiary" />
              </button>
            </div>

            {/* 弹窗内容 */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5">
              {/* 文件上传区域 */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  上传文件 <span className="text-error">*</span>
                </label>
                
                {/* 拖拽上传区 */}
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`
                    border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer
                    ${uploadDragging
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:border-primary/50 hover:bg-bg-tertiary/50'
                    }
                    ${selectedFiles.length > 0 ? 'bg-success/5 border-success/30' : ''}
                  `}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.xls,.xlsx,.csv,.docx,.doc,.ppt,.pptx,.txt,.md,.markdown,.html,.htm"
                    className="hidden"
                    onChange={(e) => handleFileSelect(e.target.files)}
                  />
                  
                  {isCreating ? (
                    <div className="py-4">
                      <Loader2 className="w-10 h-10 mx-auto mb-3 text-primary animate-spin" />
                      <p className="text-text-secondary mb-2">
                        正在创建知识库...
                      </p>
                      {currentUploadFile && (
                        <p className="text-xs text-text-tertiary">
                          正在上传: {currentUploadFile}
                        </p>
                      )}
                      <div className="w-64 mx-auto bg-bg-tertiary rounded-full h-2 mt-3">
                        <div
                          className="bg-primary h-2 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                      <p className="text-sm text-text-tertiary mt-2">{uploadProgress}%</p>
                    </div>
                  ) : selectedFiles.length > 0 ? (
                    <div className="py-2">
                      <div className="w-12 h-12 rounded-full bg-success/20 flex items-center justify-center mx-auto mb-3">
                        <Check className="w-6 h-6 text-success" />
                      </div>
                      <p className="text-success font-medium">
                        已选择 {selectedFiles.length} 个文件
                      </p>
                      <p className="text-xs text-text-tertiary mt-1">
                        点击或拖拽可继续添加文件
                      </p>
                    </div>
                  ) : (
                    <>
                      <div className="w-14 h-14 rounded-full bg-bg-tertiary flex items-center justify-center mx-auto mb-3">
                        <FileUp className="w-7 h-7 text-text-tertiary" />
                      </div>
                      <p className="text-text-secondary mb-1">
                        拖拽文件到此处，或点击选择文件
                      </p>
                      <p className="text-xs text-text-tertiary">
                        支持 PDF、Word、Excel、PPT、CSV、Markdown、TXT 等格式
                      </p>
                    </>
                  )}
                </div>

                {/* 已选择的文件列表 */}
                {selectedFiles.length > 0 && !isCreating && (
                  <div className="mt-3 space-y-2 max-h-40 overflow-y-auto">
                    {selectedFiles.map((file, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-2.5 bg-bg-tertiary rounded-lg"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <FileText className="w-4 h-4 text-text-tertiary flex-shrink-0" />
                          <span className="text-sm text-text-secondary truncate">
                            {file.name}
                          </span>
                          <span className="text-xs text-text-quaternary flex-shrink-0">
                            ({formatFileSize(file.size)})
                          </span>
                        </div>
                        <button
                          onClick={() => handleRemoveFile(index)}
                          className="p-1 hover:bg-error/10 rounded transition-colors flex-shrink-0"
                        >
                          <X className="w-4 h-4 text-text-tertiary hover:text-error" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 知识库名称 */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  知识库名称 <span className="text-error">*</span>
                </label>
                <input
                  type="text"
                  value={newKnowledgeName}
                  onChange={(e) => setNewKnowledgeName(e.target.value)}
                  placeholder="输入知识库名称，默认为第一个文件名"
                  className="w-full px-3 py-2.5 bg-bg-tertiary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary text-text-primary"
                />
              </div>
              
              {/* 知识库描述 */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  描述 <span className="text-text-tertiary">（可选）</span>
                </label>
                <textarea
                  value={newKnowledgeDescription}
                  onChange={(e) => setNewKnowledgeDescription(e.target.value)}
                  placeholder="输入知识库描述，帮助您区分不同的知识库"
                  rows={3}
                  className="w-full px-3 py-2.5 bg-bg-tertiary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary text-text-primary resize-none"
                />
              </div>
            </div>

            {/* 弹窗底部 */}
            <div className="flex items-center justify-between p-5 border-t border-border bg-bg-tertiary/30">
              <div className="flex items-center gap-2 text-xs text-text-tertiary">
                <AlertCircle className="w-4 h-4" />
                <span>文件将保存在 backend/agent/knowledges/ 目录</span>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setSelectedFiles([]);
                    setNewKnowledgeName('');
                    setNewKnowledgeDescription('');
                  }}
                  disabled={isCreating}
                  className="px-4 py-2 border border-border rounded-lg text-text-secondary hover:bg-bg-tertiary transition-colors disabled:opacity-50"
                >
                  取消
                </button>
                <button
                  onClick={handleCreateKnowledge}
                  disabled={!newKnowledgeName.trim() || selectedFiles.length === 0 || isCreating}
                  className="flex items-center gap-2 px-5 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isCreating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      创建中...
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4" />
                      创建知识库
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 编辑知识库弹窗 */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-bg-secondary w-full max-w-lg rounded-2xl shadow-2xl border border-border overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200">
            {/* 弹窗头部 */}
            <div className="flex items-center justify-between p-5 border-b border-border bg-bg-tertiary/30">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Edit2 className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-text-primary">编辑知识库</h3>
                  <p className="text-xs text-text-tertiary mt-0.5">修改知识库的描述信息</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingKnowledgeId(null);
                  setNewKnowledgeDescription('');
                }}
                className="p-2 hover:bg-bg-tertiary rounded-lg transition-colors text-text-tertiary hover:text-text-primary"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 弹窗内容 */}
            <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
              {/* 知识库描述 */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  描述 <span className="text-text-tertiary">（可选）</span>
                </label>
                <textarea
                  value={newKnowledgeDescription}
                  onChange={(e) => setNewKnowledgeDescription(e.target.value)}
                  placeholder="输入知识库描述，帮助您区分不同的知识库"
                  rows={4}
                  className="w-full px-3 py-2.5 bg-bg-tertiary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary text-text-primary resize-none"
                />
              </div>
            </div>

            {/* 弹窗底部 */}
            <div className="flex items-center justify-end p-5 border-t border-border bg-bg-tertiary/30">
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingKnowledgeId(null);
                    setNewKnowledgeDescription('');
                  }}
                  disabled={isCreating}
                  className="px-4 py-2 border border-border rounded-lg text-text-secondary hover:bg-bg-tertiary transition-colors disabled:opacity-50"
                >
                  取消
                </button>
                <button
                  onClick={handleSaveEdit}
                  disabled={isCreating}
                  className="flex items-center gap-2 px-5 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isCreating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      保存中...
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4" />
                      保存修改
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgePage;
