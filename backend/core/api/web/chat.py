from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import Optional, List
import json
import uuid
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from core.api.schemas import (
    ChatSessionResponse,
    SendMessageRequest,
    SendMessageResponse,
    MessageResponse,
)
from core.api.result import success, sse_format, sse_done
from llm.langchaint import llm_sendmsg_stream, model_name

router = APIRouter()

# 内存会话存储（生产环境建议用数据库）
sessions: dict = {}


def get_session(session_id: Optional[str], content: str, model: Optional[str], knowledge_base_ids: Optional[List[str]]):
    """获取或创建会话"""
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "id": session_id,
            "title": content[:30] + "..." if len(content) > 30 else content,
            "messages": [],
            "created_at": int(datetime.now().timestamp() * 1000),
            "updated_at": int(datetime.now().timestamp() * 1000),
            "model": model,
            "knowledge_base_ids": knowledge_base_ids or [],
        }
    return session_id


def save_message(session_id: str, role: str, content: str):
    """保存消息到会话"""
    message = {
        "id": str(uuid.uuid4()),
        "role": role,
        "content": content,
        "timestamp": int(datetime.now().timestamp() * 1000),
    }
    sessions[session_id]["messages"].append(message)
    sessions[session_id]["updated_at"] = int(datetime.now().timestamp() * 1000)
    return message


def build_messages(session_id: str, new_content: str) -> List[dict]:
    """构建消息列表，包含历史上下文"""
    messages = sessions[session_id].get("messages", [])
    
    system_prompt = {
        "role": "system",
        "content": "你是一个专业的AI客服助手，请用友好、专业的方式回答用户的问题。"
    }
    
    result = [system_prompt]
    
    for msg in messages[-10:]:
        result.append({"role": msg["role"], "content": msg["content"]})
    
    return result


async def stream_llm_response(model: str, content: str):
    """在后台线程中运行同步生成器"""
    loop = asyncio.get_event_loop()
    
    def run_generator():
        gen = llm_sendmsg_stream(model, content)
        try:
            while True:
                chunk = next(gen)
                if chunk:
                    yield chunk
        except StopIteration:
            pass
    
    # 使用 to_thread 在线程池中运行
    # 但因为是生成器，我们需要用不同的方式
    gen = llm_sendmsg_stream(model, content)
    
    # 直接迭代同步生成器（ChatOpenAI 的 stream 是线程安全的）
    for chunk in gen:
        yield chunk


@router.post("/chat/send")
async def send_message(request: SendMessageRequest):
    """
    发送消息 - 流式返回
    使用 langchain.py 的 llm_sendmsg_stream 进行流式输出
    """
    logger.info(f"收到消息: content={request.content[:50]}..., thinking={request.thinking}")
    
    session_id = get_session(
        request.session_id, 
        request.content, 
        request.model, 
        request.knowledge_base_ids
    )
    
    # 保存用户消息
    user_msg = save_message(session_id, "user", request.content)
    
    # 获取模型名称，默认 qwen3.5-plus
    model = request.model or "qwen3.5-plus"
    # 获取思考模式，默认 auto
    thinking = request.thinking or "auto"
    logger.info(f"使用模型: {model}, 思考模式: {thinking}")
    
    async def stream_generator():
        full_content = ""
        full_reasoning = ""
        has_reasoning = False
        
        try:
            # 直接在事件循环中迭代（ChatOpenAI.stream 是同步的但可以在 async 中迭代）
            for chunk in llm_sendmsg_stream(model, request.content, thinking):
                # chunk 是字典，包含 content 和 reasoning
                if chunk.get("reasoning"):
                    full_reasoning += chunk["reasoning"]
                    yield sse_format({"reasoning": chunk["reasoning"]})
                
                if chunk.get("content"):
                    full_content += chunk["content"]
                    yield sse_format({"content": chunk["content"]})
            
            # 保存助手消息
            if full_content:
                save_message(session_id, "assistant", full_content)
            
            # 发送完成信号
            yield sse_format({"sessionId": session_id, "done": True, "hasReasoning": bool(full_reasoning)})
            yield sse_done()
            
        except Exception as e:
            error_content = f"抱歉，发生了错误：{str(e)}"
            yield sse_format({"error": error_content})
            yield sse_done()
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/chat/history")
async def get_all_sessions():
    """获取所有会话列表"""
    result = []
    for session in sessions.values():
        result.append({
            "id": session["id"],
            "title": session["title"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "message_count": len(session["messages"]),
        })
    result.sort(key=lambda x: x["updated_at"], reverse=True)
    return success(data={"sessions": result}, msg="获取成功")


@router.get("/chat/history/{session_id}")
async def get_session_history(session_id: str):
    """获取指定会话的历史记录"""
    session = sessions.get(session_id)
    if not session:
        return success(data=None, msg="会话不存在")
    return success(data=ChatSessionResponse(**session).model_dump(), msg="获取成功")


@router.delete("/chat/history/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    if session_id in sessions:
        del sessions[session_id]
    return success(data=None, msg="删除成功")


@router.delete("/chat/history")
async def clear_all_history():
    """清空所有会话历史"""
    sessions.clear()
    return success(data=None, msg="清空成功")


@router.put("/chat/history/{session_id}/title")
async def rename_session(session_id: str, title: str):
    """重命名会话"""
    if session_id in sessions:
        sessions[session_id]["title"] = title
        sessions[session_id]["updated_at"] = int(datetime.now().timestamp() * 1000)
    return success(data=None, msg="重命名成功")
