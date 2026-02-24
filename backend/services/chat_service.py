from typing import List, Dict, Optional, Any
from uuid import uuid4
from datetime import datetime
import json

from core.config import get_settings
from services.llm_service import LLMService
from services.rag_service import RAGService

settings = get_settings()


class ChatService:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.llm_service = LLMService()
        self.rag_service = RAGService()

    async def send_message(
        self,
        content: str,
        session_id: Optional[str] = None,
        model_id: Optional[str] = None,
        knowledge_base_ids: Optional[List[str]] = None,
        stream: bool = False,
    ) -> tuple[str, Dict[str, Any]]:
        if not session_id or session_id not in self.sessions:
            session_id = str(uuid4())
            self.sessions[session_id] = {
                "id": session_id,
                "title": content[:30] + "..." if len(content) > 30 else content,
                "messages": [],
                "created_at": int(datetime.now().timestamp() * 1000),
                "updated_at": int(datetime.now().timestamp() * 1000),
                "model_id": model_id,
                "knowledge_base_ids": knowledge_base_ids or [],
            }

        user_message = {
            "id": str(uuid4()),
            "role": "user",
            "content": content,
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
        self.sessions[session_id]["messages"].append(user_message)

        references = []
        context = ""
        
        if knowledge_base_ids:
            context = await self.rag_service.retrieve_context(
                knowledge_base_ids, content
            )
            if context:
                references = context.get("references", [])

        system_prompt = self._build_system_prompt(context)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in self.sessions[session_id]["messages"][-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        response_content = await self.llm_service.generate(
            messages=messages,
            model_id=model_id,
        )

        assistant_message = {
            "id": str(uuid4()),
            "role": "assistant",
            "content": response_content,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "references": references if references else None,
        }
        self.sessions[session_id]["messages"].append(assistant_message)
        self.sessions[session_id]["updated_at"] = int(datetime.now().timestamp() * 1000)

        return session_id, assistant_message

    def _build_system_prompt(self, context: str = "") -> str:
        base_prompt = "你是一个专业的AI客服助手，请用友好、专业的方式回答用户的问题。"
        
        if context:
            base_prompt += f"\n\n以下是相关的知识库内容，请参考：\n\n{context}\n\n请基于以上内容回答用户的问题。"
        
        return base_prompt

    async def get_all_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        for session in self.sessions.values():
            sessions.append({
                "id": session["id"],
                "title": session["title"],
                "created_at": session["created_at"],
                "updated_at": session["updated_at"],
                "message_count": len(session["messages"]),
            })
        return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)

    async def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    async def clear_all_sessions(self):
        self.sessions.clear()
