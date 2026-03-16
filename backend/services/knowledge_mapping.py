"""
知识库映射管理服务
管理知识库名称与文件列表的映射关系，使用JSON配置文件存储
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# 知识库基础路径
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "agent" / "knowledges"
VECTOR_STORE_PATH = KNOWLEDGE_BASE_PATH / "vector_store"
MAPPING_FILE = KNOWLEDGE_BASE_PATH / "knowledge_mapping.json"


class KnowledgeMappingService:
    """知识库映射服务"""
    
    def __init__(self):
        self.mapping_file = MAPPING_FILE
        self.knowledge_base_path = KNOWLEDGE_BASE_PATH
        self.vector_store_path = VECTOR_STORE_PATH
        
        # 确保目录存在
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化映射文件
        self._ensure_mapping_file()
        
        logger.info(f"KnowledgeMappingService 初始化完成")
        logger.info(f"知识库路径: {self.knowledge_base_path}")
        logger.info(f"向量存储路径: {self.vector_store_path}")
        logger.info(f"映射文件: {self.mapping_file}")
    
    def _ensure_mapping_file(self):
        """确保映射文件存在"""
        if not self.mapping_file.exists():
            self._save_mapping({})
            logger.info(f"创建新的映射文件: {self.mapping_file}")
    
    def _load_mapping(self) -> Dict[str, Any]:
        """加载映射配置"""
        try:
            if self.mapping_file.exists():
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"加载映射文件失败: {e}")
            return {}
    
    def _save_mapping(self, mapping: Dict[str, Any]):
        """保存映射配置"""
        try:
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存映射文件失败: {e}")
    
    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """获取所有知识库列表"""
        mapping = self._load_mapping()
        result = []
        
        for name, info in mapping.items():
            result.append({
                "id": name,  # 使用知识库名称作为ID
                "name": name,
                "description": info.get("description", ""),
                "fileCount": len(info.get("files", [])),
                "status": info.get("status", "ready"),
                "createdAt": info.get("createdAt", ""),
                "updatedAt": info.get("updatedAt", ""),
                "files": info.get("files", []),
            })
        
        return result
    
    def get_knowledge_base(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定知识库"""
        mapping = self._load_mapping()
        info = mapping.get(name)
        
        if not info:
            return None
        
        return {
            "id": name,
            "name": name,
            "description": info.get("description", ""),
            "fileCount": len(info.get("files", [])),
            "status": info.get("status", "ready"),
            "createdAt": info.get("createdAt", ""),
            "updatedAt": info.get("updatedAt", ""),
            "files": info.get("files", []),
        }
    
    def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        files: List[str] = None
    ) -> Dict[str, Any]:
        """创建知识库"""
        mapping = self._load_mapping()
        
        now = datetime.now().isoformat()
        
        mapping[name] = {
            "files": files or [],
            "description": description,
            "status": "ready",
            "createdAt": now,
            "updatedAt": now,
        }
        
        self._save_mapping(mapping)
        logger.info(f"创建知识库: {name}, 文件数: {len(files or [])}")
        
        return {
            "id": name,
            "name": name,
            "description": description,
            "fileCount": len(files or []),
            "status": "ready",
            "createdAt": now,
            "updatedAt": now,
            "files": files or [],
        }
    
    def update_knowledge_base(
        self,
        name: str,
        description: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """更新知识库"""
        mapping = self._load_mapping()
        
        if name not in mapping:
            return None
        
        info = mapping[name]
        
        if description is not None:
            info["description"] = description
        
        if files is not None:
            info["files"] = files
        
        info["updatedAt"] = datetime.now().isoformat()
        
        self._save_mapping(mapping)
        logger.info(f"更新知识库: {name}")
        
        return {
            "id": name,
            "name": name,
            "description": info.get("description", ""),
            "fileCount": len(info.get("files", [])),
            "status": info.get("status", "ready"),
            "createdAt": info.get("createdAt", ""),
            "updatedAt": info.get("updatedAt", ""),
            "files": info.get("files", []),
        }
    
    def delete_knowledge_base(self, name: str) -> bool:
        """删除知识库"""
        mapping = self._load_mapping()
        
        if name not in mapping:
            return False
        
        del mapping[name]
        self._save_mapping(mapping)
        logger.info(f"删除知识库: {name}")
        
        return True
    
    def add_files_to_knowledge_base(self, name: str, file_paths: List[str]) -> bool:
        """向知识库添加文件"""
        mapping = self._load_mapping()
        
        if name not in mapping:
            return False
        
        info = mapping[name]
        existing_files = set(info.get("files", []))
        existing_files.update(file_paths)
        info["files"] = list(existing_files)
        info["updatedAt"] = datetime.now().isoformat()
        
        self._save_mapping(mapping)
        logger.info(f"向知识库 {name} 添加 {len(file_paths)} 个文件")
        
        return True
    
    def remove_file_from_knowledge_base(self, name: str, file_path: str) -> bool:
        """从知识库移除文件"""
        mapping = self._load_mapping()
        
        if name not in mapping:
            return False
        
        info = mapping[name]
        files = info.get("files", [])
        
        if file_path in files:
            files.remove(file_path)
            info["files"] = files
            info["updatedAt"] = datetime.now().isoformat()
            self._save_mapping(mapping)
            logger.info(f"从知识库 {name} 移除文件: {file_path}")
            return True
        
        return False
    
    def get_mapping(self) -> Dict[str, Any]:
        """获取完整映射关系"""
        return self._load_mapping()
    
    def get_vector_store_path(self, collection_name: str) -> Path:
        """获取向量存储路径"""
        return self.vector_store_path
    
    def update_knowledge_base_status(self, name: str, status: str) -> bool:
        """更新知识库状态"""
        mapping = self._load_mapping()
        
        if name not in mapping:
            return False
        
        mapping[name]["status"] = status
        mapping[name]["updatedAt"] = datetime.now().isoformat()
        self._save_mapping(mapping)
        logger.info(f"更新知识库 {name} 状态为: {status}")
        
        return True


# 单例实例
_knowledge_mapping_service: Optional[KnowledgeMappingService] = None


def get_knowledge_mapping_service() -> KnowledgeMappingService:
    """获取知识库映射服务单例"""
    global _knowledge_mapping_service
    if _knowledge_mapping_service is None:
        _knowledge_mapping_service = KnowledgeMappingService()
    return _knowledge_mapping_service
