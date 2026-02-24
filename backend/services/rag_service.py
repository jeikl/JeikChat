from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

knowledge_bases: Dict[str, Dict[str, Any]] = {}


class RAGService:
    def __init__(self):
        self.vector_stores: Dict[str, Any] = {}

    async def retrieve_context(
        self,
        knowledge_base_ids: List[str],
        query: str,
        top_k: int = 3,
    ) -> Dict[str, Any]:
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
        pass

    async def add_documents(self, knowledge_base_id: str, documents: List[str]):
        pass

    async def delete_vector_store(self, knowledge_base_id: str):
        if knowledge_base_id in self.vector_stores:
            del self.vector_stores[knowledge_base_id]


class KnowledgeBaseService:
    def __init__(self):
        self.knowledge_bases = knowledge_bases

    async def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": kb_id,
                "name": kb.get("name"),
                "description": kb.get("description"),
                "file_count": len(kb.get("files", [])),
                "status": kb.get("status", "ready"),
                "created_at": kb.get("created_at"),
                "updated_at": kb.get("updated_at"),
                "system_prompt": kb.get("system_prompt"),
            }
            for kb_id, kb in self.knowledge_bases.items()
        ]

    async def create_knowledge_base(
        self,
        name: str,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        kb_id = str(uuid4())
        kb = {
            "id": kb_id,
            "name": name,
            "description": description,
            "files": [],
            "status": "ready",
            "created_at": int(datetime.now().timestamp() * 1000),
            "updated_at": int(datetime.now().timestamp() * 1000),
            "system_prompt": system_prompt,
        }
        self.knowledge_bases[kb_id] = kb
        return kb

    async def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        return self.knowledge_bases.get(kb_id)

    async def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if kb_id not in self.knowledge_bases:
            return None
        
        kb = self.knowledge_bases[kb_id]
        if name:
            kb["name"] = name
        if description:
            kb["description"] = description
        if system_prompt is not None:
            kb["system_prompt"] = system_prompt
        kb["updated_at"] = int(datetime.now().timestamp() * 1000)
        
        return kb

    async def delete_knowledge_base(self, kb_id: str) -> bool:
        if kb_id in self.knowledge_bases:
            del self.knowledge_bases[kb_id]
            return True
        return False

    async def upload_file(
        self,
        kb_id: str,
        file_name: str,
        file_content: bytes,
    ) -> Dict[str, Any]:
        if kb_id not in self.knowledge_bases:
            raise ValueError("Knowledge base not found")
        
        file_id = str(uuid4())
        file_info = {
            "id": file_id,
            "name": file_name,
            "size": len(file_content),
            "status": "ready",
            "created_at": int(datetime.now().timestamp() * 1000),
        }
        
        self.knowledge_bases[kb_id]["files"].append(file_info)
        self.knowledge_bases[kb_id]["updated_at"] = int(datetime.now().timestamp() * 1000)
        
        return file_info

    async def delete_file(self, kb_id: str, file_id: str) -> bool:
        if kb_id not in self.knowledge_bases:
            return False
        
        files = self.knowledge_bases[kb_id]["files"]
        self.knowledge_bases[kb_id]["files"] = [f for f in files if f["id"] != file_id]
        return True


knowledge_service = KnowledgeBaseService()
rag_service = RAGService()
