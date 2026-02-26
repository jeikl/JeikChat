import os
import sys
from typing import List, Dict, Optional, Any
from uuid import uuid4
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.core.agents.chat import get_configuration
from backend.core.base.llm.llms import get_llm, qwen
from backend.core.base.promt import system_prompt
from init import get_settings
from core.services.llm_service import LLMService
from core.services.rag_service import RAGService

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
        model: Optional[str] = None,
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
                "model": model,
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
            model=model,
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

    def _build_system_prompt(self, ragcontext: str = "") -> str:
        base_prompt = system_prompt
    
        if ragcontext: 
            base_prompt += f"\n\n以下是相关的知识库内容，请参考：\n\n{ragcontext}\n\n请基于以上内容仔细查阅资料并回答用户的问题。"
        
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

    async def rename_session(self, session_id: str, title: str):
        """重命名会话"""
        if session_id in self.sessions:
            self.sessions[session_id]["title"] = title
            self.sessions[session_id]["updated_at"] = int(datetime.now().timestamp() * 1000)

    async def send_message_stream(self, content: str, session_id: str = None, model: str = None, knowledge_base_ids: List[str] = None):
        """流式发送消息"""
        if not session_id or session_id not in self.sessions:
            session_id = str(uuid4())
            self.sessions[session_id] = {
                "id": session_id,
                "title": content[:30] + "..." if len(content) > 30 else content,
                "messages": [],
                "created_at": int(datetime.now().timestamp() * 1000),
                "updated_at": int(datetime.now().timestamp() * 1000),
                "model": model,
                "knowledge_base_ids": knowledge_base_ids or [],
            }
        '''以上是历史记录'''

        user_message = {
            "role": "user",
            "content": content
        }


        config={
            "configurable": {"thread_id": str(uuid4())}}


        self.sessions[session_id]["messages"].append(user_message)

        references = []
        context = ""
        qwen0=get_llm(model)
        #qwen0.invoke(content,get_configuration(session_id) )


        if knowledge_base_ids:
            context = await self.rag_service.retrieve_context(
                knowledge_base_ids, content
            )
            if context:
                references = context.get("references", [])

        system_prompt = self._build_system_prompt(context)

        messages = [{"role": "system", "content": system_prompt}]


        print(qwen0.invoke(user_message,content,get_configuration(session_id) ))




        for msg in self.sessions[session_id]["messages"][-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        yield {"session_id": session_id}

        async for chunk in self.llm_service.generate_stream(messages=messages, model=model):
            if chunk:
                yield {"content": chunk}

        assistant_message = {
            "id": str(uuid4()),
            "role": "assistant",
            "content": "",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "references": references if references else None,
        }
        
        if references:
            yield {"references": references}

        self.sessions[session_id]["messages"].append(assistant_message)
        self.sessions[session_id]["updated_at"] = int(datetime.now().timestamp() * 1000)
