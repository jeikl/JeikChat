import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { KnowledgeBase, UploadStatus } from '@/types/knowledge';

// 工具选择回调类型
type OnKnowledgeSelectionChange = (selectedIds: string[]) => void;

interface KnowledgeState {
  knowledgeBases: KnowledgeBase[];
  selectedKnowledgeIds: string[];
  isLoading: boolean;
  isUploading: boolean;
  uploadProgress: number;
  uploadStatuses: UploadStatus[]; // 多个文件的上传状态
  currentUploadFile: string | null; // 当前正在上传的文件名
  onSelectionChangeCallback: OnKnowledgeSelectionChange | null;

  setKnowledgeBases: (knowledgeBases: KnowledgeBase[]) => void;
  addKnowledgeBase: (knowledgeBase: KnowledgeBase) => void;
  updateKnowledgeBase: (id: string, updates: Partial<KnowledgeBase>) => void;
  removeKnowledgeBase: (id: string) => void;
  setSelectedKnowledgeIds: (ids: string[]) => void;
  toggleKnowledgeSelection: (id: string) => void;
  selectAllKnowledge: (select: boolean) => void; // 全选/取消全选
  setOnSelectionChangeCallback: (callback: OnKnowledgeSelectionChange | null) => void;
  setLoading: (loading: boolean) => void;
  setUploading: (uploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  setUploadStatuses: (statuses: UploadStatus[]) => void;
  updateUploadStatus: (fileName: string, status: Partial<UploadStatus>) => void;
  setCurrentUploadFile: (fileName: string | null) => void;
  clearUploadStatuses: () => void;
}

export const useKnowledgeStore = create<KnowledgeState>()(
  persist(
    (set) => ({
      knowledgeBases: [],
      selectedKnowledgeIds: [],
      isLoading: false,
      isUploading: false,
      uploadProgress: 0,
      uploadStatuses: [],
      currentUploadFile: null,
      onSelectionChangeCallback: null,

      setKnowledgeBases: (knowledgeBases) => set({ knowledgeBases }),

      addKnowledgeBase: (knowledgeBase) =>
        set((state) => ({
          knowledgeBases: [...state.knowledgeBases, knowledgeBase],
        })),

      updateKnowledgeBase: (id, updates) =>
        set((state) => ({
          knowledgeBases: state.knowledgeBases.map((kb) =>
            kb.id === id ? { ...kb, ...updates } : kb
          ),
        })),

      removeKnowledgeBase: (id) =>
        set((state) => ({
          knowledgeBases: state.knowledgeBases.filter((kb) => kb.id !== id),
          selectedKnowledgeIds: state.selectedKnowledgeIds.filter((kid) => kid !== id),
        })),

      setSelectedKnowledgeIds: (ids) =>
        set((state) => {
          // 触发回调通知工具选择变化
          if (state.onSelectionChangeCallback) {
            state.onSelectionChangeCallback(ids);
          }
          return { selectedKnowledgeIds: ids };
        }),

      toggleKnowledgeSelection: (id: string) =>
        set((state) => {
          if (id === '') {
            const newIds: string[] = [];
            if (state.onSelectionChangeCallback) {
              state.onSelectionChangeCallback(newIds);
            }
            return { selectedKnowledgeIds: newIds };
          }
          const isSelected = state.selectedKnowledgeIds.includes(id);
          const newIds = isSelected
            ? state.selectedKnowledgeIds.filter((kid) => kid !== id)
            : [...state.selectedKnowledgeIds, id];
          if (state.onSelectionChangeCallback) {
            state.onSelectionChangeCallback(newIds);
          }
          return { selectedKnowledgeIds: newIds };
        }),

      selectAllKnowledge: (select: boolean) =>
        set((state) => {
          const newIds = select
            ? state.knowledgeBases.map((kb) => kb.id)
            : [];
          if (state.onSelectionChangeCallback) {
            state.onSelectionChangeCallback(newIds);
          }
          return { selectedKnowledgeIds: newIds };
        }),

      setOnSelectionChangeCallback: (callback) =>
        set({ onSelectionChangeCallback: callback }),

      setLoading: (loading) => set({ isLoading: loading }),
      setUploading: (uploading) => set({ isUploading: uploading }),
      setUploadProgress: (progress) => set({ uploadProgress: progress }),
      
      setUploadStatuses: (statuses) => set({ uploadStatuses: statuses }),
      
      updateUploadStatus: (fileName: string, status: Partial<UploadStatus>) =>
        set((state) => ({
          uploadStatuses: state.uploadStatuses.map((s) =>
            s.fileName === fileName ? { ...s, ...status } : s
          ),
        })),
      
      setCurrentUploadFile: (fileName) => set({ currentUploadFile: fileName }),
      
      clearUploadStatuses: () => set({ uploadStatuses: [], currentUploadFile: null }),
    }),
    {
      name: 'knowledge-storage',
      partialize: (state) => ({
        knowledgeBases: state.knowledgeBases,
        selectedKnowledgeIds: state.selectedKnowledgeIds,
      }),
    }
  )
);
