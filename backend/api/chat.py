from fastapi import APIRouter, HTTPException
from typing import List, Optional
from uuid import uuid4
import json

from models.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    SendMessageRequest,
    SendMessageResponse,
    MessageResponse,
)
from services.chat_service import ChatService
from utils.result import success, sse_format, sse_done

router = APIRouter()
chat_service = ChatService()


@router.post("/chat/send")
async def send_message(request: SendMessageRequest):
    """
    发送消息
    - 非流式: 返回统一格式 {status, data, msg}
    - 流式: SSE格式，保持原样不包装
    """
    if request.stream:
        async def stream_generator():
            session_id = None
            content = ""
            
            async for chunk in chat_service.send_message_stream(
                content=request.content,
                session_id=request.session_id,
                model_id=request.model_id,
                knowledge_base_ids=request.knowledge_base_ids,
            ):
                if chunk.get("session_id") and not session_id:
                    session_id = chunk["session_id"]
                
                if chunk.get("content"):
                    content += chunk["content"]
                    yield sse_format({"sessionId": session_id, "content": chunk["content"]})
                
                if chunk.get("references"):
                    yield sse_format({"references": chunk["references"]})
            
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
    else:
        session_id, message = await chat_service.send_message(
            content=request.content,
            session_id=request.session_id,
            model_id=request.model_id,
            knowledge_base_ids=request.knowledge_base_ids,
            stream=False,
        )
        return success(
            data=SendMessageResponse(
                session_id=session_id,
                message=MessageResponse(**message),
            ).model_dump(),
            msg="发送成功"
        )


@router.get("/chat/history")
async def get_all_sessions():
    """获取所有会话列表"""
    sessions = await chat_service.get_all_sessions()
    return success(data={"sessions": sessions}, msg="获取成功")


@router.get("/chat/history/{session_id}")
async def get_session_history(session_id: str):
    """获取指定会话的历史记录"""
    session = await chat_service.get_session(session_id)
    if not session:
        return success(data=None, msg="会话不存在")
    return success(data=ChatSessionResponse(**session).model_dump(), msg="获取成功")


@router.delete("/chat/history/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    await chat_service.delete_session(session_id)
    return success(data=None, msg="删除成功")


@router.delete("/chat/history")
async def clear_all_history():
    """清空所有会话历史"""
    await chat_service.clear_all_sessions()
    return success(data=None, msg="清空成功")


@router.put("/chat/history/{session_id}/title")
async def rename_session(session_id: str, title: str):
    """重命名会话"""
    await chat_service.rename_session(session_id, title)
    return success(data=None, msg="重命名成功")
