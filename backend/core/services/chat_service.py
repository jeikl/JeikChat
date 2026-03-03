import os
import sys
from typing import List, Dict, Optional, Any, AsyncGenerator
from uuid import uuid4
from datetime import datetime
import logging

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 使用相对导入避免 backend 模块名问题
from core.agents.chat import get_configuration
from core.base.llm.llms import get_llm, qwen
from core.base.promt import system_prompt
from init import get_settings
from .llm_service import LLMService, get_llm_service, StreamChunk
from .rag_service import RAGService, get_rag_service
from .singleton import ThreadSafeLazyInitializer

logger = logging.getLogger(__name__)
settings = get_settings()


class ChatService:
    """
    聊天服务类
    处理对话逻辑、消息管理和上下文构建
    使用单例模式优化性能
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # 使用单例获取服务实例
        self._llm_service: Optional[LLMService] = None
        self._rag_service: Optional[RAGService] = None
        logger.info("ChatService 初始化完成")

    @property
    def llm_service(self) -> LLMService:
        """延迟获取 LLMService 单例"""
        if self._llm_service is None:
            self._llm_service = get_llm_service()
        return self._llm_service

    @property
    def rag_service(self) -> RAGService:
        """延迟获取 RAGService 单例"""
        if self._rag_service is None:
            self._rag_service = get_rag_service()
        return self._rag_service

    async def send_message(
        self,
        content: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        knowledge_base_ids: Optional[List[str]] = None,
        stream: bool = False,
    ) -> tuple[str, Dict[str, Any]]:
        """非流式发送消息"""
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

        system_prompt_text = self._build_system_prompt(context)

        messages = [{"role": "system", "content": system_prompt_text}]
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

    async def send_message_stream(
        self,
        content: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        knowledge_base_ids: Optional[List[str]] = None,
        should_stop: Optional[callable] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式发送消息
        
        Args:
            content: 用户消息内容
            session_id: 会话ID
            model: 模型名称
            knowledge_base_ids: 知识库ID列表
            should_stop: 停止检查函数
        """
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
            context_result = await self.rag_service.retrieve_context(
                knowledge_base_ids, content
            )
            if context_result:
                context = context_result.get("context", "")
                references = context_result.get("references", [])

        system_prompt_text = self._build_system_prompt(context)

        messages = [{"role": "system", "content": system_prompt_text}]
        for msg in self.sessions[session_id]["messages"][-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        full_content = ""
        full_reasoning = ""
        
        # 使用 LLMService 的流式生成
        async for chunk in self.llm_service.generate_stream(
            messages=messages,
            model=model,
            should_stop=should_stop,
        ):
            if chunk.error:
                yield {"error": chunk.error}
                return
            
            if chunk.content:
                full_content += chunk.content
                yield {"content": chunk.content}
            
            if chunk.reasoning:
                full_reasoning += chunk.reasoning
                yield {"reasoning": chunk.reasoning}
            
            if chunk.is_finished:
                break

        # 保存助手消息
        if full_content:
            assistant_message = {
                "id": str(uuid4()),
                "role": "assistant",
                "content": full_content,
                "timestamp": int(datetime.now().timestamp() * 1000),
                "references": references if references else None,
            }
            self.sessions[session_id]["messages"].append(assistant_message)
            self.sessions[session_id]["updated_at"] = int(datetime.now().timestamp() * 1000)

        yield {
            "sessionId": session_id,
            "done": True,
            "hasReasoning": bool(full_reasoning),
            "references": references if references else None,
        }

    def _build_system_prompt(self, ragcontext: str = "") -> str:
        """构建系统提示词"""
        base_prompt = system_prompt
    
        if ragcontext: 
            base_prompt += f"\n\n以下是相关的知识库内容，请参考：\n\n{ragcontext}\n\n请基于以上内容仔细查阅资料并回答用户的问题。"
        
        return base_prompt

    async def get_all_sessions(self) -> List[Dict[str, Any]]:
        """获取所有会话列表"""
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
        """获取指定会话"""
        return self.sessions.get(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"会话已删除: {session_id}")
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            "sessions_count": len(self.sessions),
            "total_messages": sum(len(s.get("messages", [])) for s in self.sessions.values()),
        }


# 全局单例实例
_chat_service_instance = ThreadSafeLazyInitializer(lambda: ChatService())


def get_chat_service() -> ChatService:
    """获取 ChatService 单例"""
    return _chat_service_instance.get()
