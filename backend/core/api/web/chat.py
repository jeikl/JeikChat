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
from core.services.stream_manager import get_stream_manager

router = APIRouter()

# 获取流式管理器单例
stream_manager = get_stream_manager()

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


@router.post("/chat/send")
async def send_message(request: SendMessageRequest, http_request: Request):
    """
    发送消息 - 流式返回
    支持真正的中断：当客户端断开连接时，后端会停止与大模型的通信
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
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 注册流式任务
    task = stream_manager.register_task(task_id, session_id)
    
    async def stream_generator():
        full_content = ""
        full_reasoning = ""
        has_reasoning = False
        client_disconnected = False
        
        try:
            # 使用支持取消的流式生成
            async for chunk in llm_sendmsg_stream(model, request.content, thinking, task.is_cancelled):
                # 检查客户端是否断开连接
                if await http_request.is_disconnected():
                    logger.info(f"客户端断开连接，停止生成: task_id={task_id}")
                    client_disconnected = True
                    break
                
                # 检查任务是否被取消
                if task.is_cancelled():
                    logger.info(f"任务被取消，停止生成: task_id={task_id}")
                    break
                
                # chunk 是字典，包含 content 和 reasoning
                if chunk.get("reasoning"):
                    full_reasoning += chunk["reasoning"]
                    yield sse_format({"reasoning": chunk["reasoning"]})
                
                if chunk.get("content"):
                    full_content += chunk["content"]
                    yield sse_format({"content": chunk["content"]})
            
            # 保存助手消息（只有正常完成时才保存）
            if full_content and not client_disconnected and not task.is_cancelled():
                save_message(session_id, "assistant", full_content)
                logger.info(f"消息已保存: session_id={session_id}, content_length={len(full_content)}")
            elif client_disconnected or task.is_cancelled():
                logger.info(f"生成被中断，不保存消息: task_id={task_id}")
            
            # 发送完成信号
            yield sse_format({
                "sessionId": session_id, 
                "done": True, 
                "hasReasoning": bool(full_reasoning),
                "cancelled": task.is_cancelled() or client_disconnected
            })
            yield sse_done()
            
        except GeneratorExit:
            logger.info(f"生成器被关闭: task_id={task_id}")
            # 标记任务为取消状态
            task.cancel_event.set()
        except Exception as e:
            logger.error(f"流式生成错误: {e}", exc_info=True)
            error_content = f"抱歉，发生了错误：{str(e)}"
            yield sse_format({"error": error_content})
            yield sse_done()
        finally:
            # 移除任务
            stream_manager.remove_task(task_id)
            logger.info(f"流式任务结束: task_id={task_id}")
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/chat/stop/{session_id}")
async def stop_generation(session_id: str):
    """
    停止指定会话的生成
    这会真正中断后端与大模型的通信
    """
    cancelled_count = stream_manager.cancel_session_tasks(session_id)
    logger.info(f"停止会话生成: session_id={session_id}, 取消任务数={cancelled_count}")
    
    return success(
        data={"cancelled_tasks": cancelled_count},
        msg=f"已停止 {cancelled_count} 个生成任务"
    )


@router.post("/chat/stop")
async def stop_all_generation():
    """
    停止所有活跃的生成任务
    用于紧急停止所有对话
    """
    stats = stream_manager.get_stats()
    active_count = stats.get("active_tasks", 0)
    
    # 取消所有活跃任务
    cancelled = 0
    for task_id in list(stream_manager._tasks.keys()):
        if stream_manager.cancel_task(task_id):
            cancelled += 1
    
    logger.info(f"停止所有生成任务: 活跃任务数={active_count}, 已取消={cancelled}")
    
    return success(
        data={"cancelled_tasks": cancelled},
        msg=f"已停止 {cancelled} 个生成任务"
    )


@router.get("/chat/stream-stats")
async def get_stream_stats():
    """获取流式任务统计信息（用于调试和监控）"""
    stats = stream_manager.get_stats()
    return success(data=stats, msg="获取成功")


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
    # 先停止该会话的所有生成任务
    stream_manager.cancel_session_tasks(session_id)
    
    if session_id in sessions:
        del sessions[session_id]
    return success(data=None, msg="删除成功")


@router.delete("/chat/history")
async def clear_all_history():
    """清空所有会话历史"""
    # 停止所有生成任务
    for task_id in list(stream_manager._tasks.keys()):
        stream_manager.cancel_task(task_id)
    
    sessions.clear()
    return success(data=None, msg="清空成功")


@router.put("/chat/history/{session_id}/title")
async def update_session_title(session_id: str, request: dict):
    """更新会话标题"""
    session = sessions.get(session_id)
    if not session:
        return success(data=None, msg="会话不存在")
    
    title = request.get("title")
    if title:
        session["title"] = title
        session["updated_at"] = int(datetime.now().timestamp() * 1000)
    
    return success(data=None, msg="更新成功")
