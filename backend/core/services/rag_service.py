from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import logging

from .singleton import ThreadSafeLazyInitializer

logger = logging.getLogger(__name__)

knowledge_bases: Dict[str, Dict[str, Any]] = {}


class RAGService:
    """
    RAG (检索增强生成) 服务
    管理知识库和向量存储
    使用单例模式避免重复创建
    """
    
    def __init__(self):
        self.vector_stores: Dict[str, Any] = {}
        self._initialized = False
        logger.info("RAGService 初始化完成")

    async def retrieve_context(
        self,
        knowledge_base_ids: List[str],
        query: str,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """从知识库检索相关上下文"""
        results = []
        
        for kb_id in knowledge_base_ids:
            if kb_id in knowledge_bases:
                kb = knowledge_bases[kb_id]
                results.append({
                    "knowledge_id": kb_id,
                    "knowledge_name": kb.get("name", "Unknown"),
                    "content": f"Sample content from {kb.get('name', 'knowledge base')}",
                    "similarity": 0.85,
                })
        
        return {
            "context": "\n\n".join([r["content"] for r in results]),
            "references": results,
        }

    async def create_vector_store(self, knowledge_base_id: str):
        """创建向量存储"""
        logger.info(f"创建向量存储: {knowledge_base_id}")
        pass

    async def add_documents(self, knowledge_base_id: str, documents: List[str]):
        """添加文档到向量存储"""
        logger.info(f"添加文档到知识库: {knowledge_base_id}, 文档数: {len(documents)}")
        pass

    async def delete_vector_store(self, knowledge_base_id: str):
        """删除向量存储"""
        if knowledge_base_id in self.vector_stores:
            del self.vector_stores[knowledge_base_id]
            logger.info(f"向量存储已删除: {knowledge_base_id}")

    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            "vector_stores_count": len(self.vector_stores),
            "knowledge_bases_count": len(knowledge_bases),
        }


class KnowledgeBaseService:
    """知识库管理服务"""
    
    def __init__(self):
        self.knowledge_bases = knowledge_bases
        logger.info("KnowledgeBaseService 初始化完成")

    async def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """获取所有知识库列表"""
        return [
            {
                "id": kb_id,
                "name": kb.get("name", "Unknown"),
                "description": kb.get("description", ""),
                "created_at": kb.get("created_at"),
                "updated_at": kb.get("updated_at"),
            }
            for kb_id, kb in self.knowledge_bases.items()
        ]

    async def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        """创建新知识库"""
        kb_id = str(uuid4())
        now = int(datetime.now().timestamp() * 1000)
        
        knowledge_bases[kb_id] = {
            "id": kb_id,
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "created_at": now,
            "updated_at": now,
            "files": [],
        }
        
        logger.info(f"知识库创建成功: {kb_id} - {name}")
        return knowledge_bases[kb_id]

    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库"""
        if kb_id in knowledge_bases:
            del knowledge_bases[kb_id]
            logger.info(f"知识库已删除: {kb_id}")
            return True
        return False


# 全局单例实例
_rag_service_instance = ThreadSafeLazyInitializer(lambda: RAGService())
_kb_service_instance = ThreadSafeLazyInitializer(lambda: KnowledgeBaseService())


def get_rag_service() -> RAGService:
    """获取 RAGService 单例"""
    return _rag_service_instance.get()


def get_knowledge_base_service() -> KnowledgeBaseService:
    """获取 KnowledgeBaseService 单例"""
    return _kb_service_instance.get()
