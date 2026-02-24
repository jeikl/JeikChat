import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { KnowledgeBase } from '@/types/knowledge';

interface KnowledgeState {
  knowledgeBases: KnowledgeBase[];
  selectedKnowledgeIds: string[];
  isLoading: boolean;
  isUploading: boolean;
  uploadProgress: number;

  setKnowledgeBases: (knowledgeBases: KnowledgeBase[]) => void;
  addKnowledgeBase: (knowledgeBase: KnowledgeBase) => void;
  updateKnowledgeBase: (id: string, updates: Partial<KnowledgeBase>) => void;
  removeKnowledgeBase: (id: string) => void;
  setSelectedKnowledgeIds: (ids: string[]) => void;
  toggleKnowledgeSelection: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setUploading: (uploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
}

export const useKnowledgeStore = create<KnowledgeState>()(
  persist(
    (set) => ({
      knowledgeBases: [],
      selectedKnowledgeIds: [],
      isLoading: false,
      isUploading: false,
      uploadProgress: 0,

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

      setSelectedKnowledgeIds: (ids) => set({ selectedKnowledgeIds: ids }),

      toggleKnowledgeSelection: (id: string) =>
    set((state) => {
      if (id === '') {
        // 如果id为空字符串，表示要清空所有选择
        return {
          selectedKnowledgeIds: [],
        };
      }
      const isSelected = state.selectedKnowledgeIds.includes(id);
      return {
        selectedKnowledgeIds: isSelected
          ? state.selectedKnowledgeIds.filter((kid) => kid !== id)
          : [...state.selectedKnowledgeIds, id],
      };
    }),

      setLoading: (loading) => set({ isLoading: loading }),
      setUploading: (uploading) => set({ isUploading: uploading }),
      setUploadProgress: (progress) => set({ uploadProgress: progress }),
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
