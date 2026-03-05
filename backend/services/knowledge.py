"""
知识库服务
管理知识库的 CRUD 操作
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

knowledge_bases: Dict[str, Dict[str, Any]] = {}


class KnowledgeBaseService:
    """知识库服务"""
    
    def __init__(self):
        logger.info("KnowledgeBaseService 初始化完成")
    
    async def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """获取所有知识库"""
        return list(knowledge_bases.values())
    
    async def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """获取指定知识库"""
        return knowledge_bases.get(kb_id)
    
    async def create_knowledge_base(
        self,
        name: str,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建知识库"""
        kb_id = str(uuid4())
        now = int(datetime.now().timestamp() * 1000)
        
        kb = {
            "id": kb_id,
            "name": name,
            "description": description or "",
            "system_prompt": system_prompt or "",
            "file_count": 0,
            "status": "ready",
            "created_at": now,
            "updated_at": now,
        }
        
        knowledge_bases[kb_id] = kb
        logger.info(f"创建知识库: {kb_id}, name={name}")
        return kb
    
    async def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新知识库"""
        if kb_id not in knowledge_bases:
            return None
        
        kb = knowledge_bases[kb_id]
        if name is not None:
            kb["name"] = name
        if description is not None:
            kb["description"] = description
        if system_prompt is not None:
            kb["system_prompt"] = system_prompt
        
        kb["updated_at"] = int(datetime.now().timestamp() * 1000)
        
        logger.info(f"更新知识库: {kb_id}")
        return kb
    
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库"""
        if kb_id in knowledge_bases:
            del knowledge_bases[kb_id]
            logger.info(f"删除知识库: {kb_id}")
            return True
        return False


_knowledge_service: Optional[KnowledgeBaseService] = None


def get_knowledge_base_service() -> KnowledgeBaseService:
    """获取知识库服务单例"""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeBaseService()
    return _knowledge_service
