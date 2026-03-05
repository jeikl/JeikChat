"""
聊天 API 路由
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import Optional, List
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from schemas.chat import SendMessageRequest
from api.response import success, sse_format, sse_done
from services.stream import get_stream_manager
from agent.chatRouterStream import chat_stream, agent_stream
from agent.prompt import get_prompts, build_messages

router = APIRouter()

stream_manager = get_stream_manager()

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


def save_message(session_id: str, role: str, content: str, reasoning: str = None):
    """保存消息到会话"""
    message = {
        "id": str(uuid.uuid4()),
        "role": role,
        "content": content,
        "timestamp": int(datetime.now().timestamp() * 1000),
    }
    if reasoning:
        message["reasoning"] = reasoning
        
    sessions[session_id]["messages"].append(message)
    sessions[session_id]["updated_at"] = int(datetime.now().timestamp() * 1000)
    return message


@router.post("/chat/send")
async def send_message(request: SendMessageRequest, http_request: Request):
    """
    发送消息 - 流式返回
    """
    logger.info(f"收到消息: content={request.content[:50]}..., thinking={request.thinking}")
    
    prompts = get_prompts()
    # logger.info(f"提示词: {system_prompt}")

    
    session_id = get_session(
        request.session_id, 
        request.content, 
        request.model, 
        request.knowledge_base_ids
    )
    
    save_message(session_id, "user", request.content)
    
    model = request.model or "qwen3.5-plus"
    thinking = request.thinking or "auto"
    tools = request.tools or []

    logger.info(f"使用模型: {model}, 思考模式: {thinking}, 工具: {tools}")
    
    task_id = str(uuid.uuid4())
    task = stream_manager.register_task(task_id, session_id)
    
    history = sessions[session_id].get("messages", [])
    
    async def stream_generator():
        full_content = ""
        full_reasoning = ""
        client_disconnected = False
        
        is_agent_mode = len(tools) > 0
        logger.info(f"模式判断: is_agent_mode={is_agent_mode}")
        if is_agent_mode:
            stream_func = agent_stream
            msg = build_messages(prompts.get_agent_prompt(tools), request.content, history)
            logger.info("使用 Agent 模式")
        else:
            stream_func = chat_stream
            msg = build_messages(prompts.get_chat_prompt(), request.content, history)
            logger.info("使用聊天流模式")
        
        try:
            if is_agent_mode:
                async for chunk in stream_func(model, msg, thinking, tools, task.is_cancelled):
                    if await http_request.is_disconnected():
                        if not client_disconnected:
                            logger.info(f"客户端断开连接，后台继续生成: task_id={task_id}")
                            client_disconnected = True
                    
                    if task.is_cancelled:
                        logger.info(f"任务被取消，停止生成: task_id={task_id}")
                        break
                    
                    thinking_flag = chunk.get("thinking", False)
                    
                    if chunk.get("reasoning"):
                        full_reasoning += chunk["reasoning"]
                        if not client_disconnected:
                            try:
                                yield sse_format({"reasoning": chunk["reasoning"]})
                            except Exception:
                                client_disconnected = True
                    
                    if chunk.get("content"):
                        full_content += chunk["content"]
                        if not client_disconnected:
                            try:
                                yield sse_format({
                                    "content": chunk["content"],
                                    "thinking": thinking_flag
                                })
                            except Exception:
                                client_disconnected = True
            else:
                async for chunk in stream_func(model, msg, thinking, task.is_cancelled):
                    if await http_request.is_disconnected():
                        if not client_disconnected:
                            logger.info(f"客户端断开连接，后台继续生成: task_id={task_id}")
                            client_disconnected = True
                    
                    if task.is_cancelled:
                        logger.info(f"任务被取消，停止生成: task_id={task_id}")
                        break
                    
                    if chunk.get("reasoning"):
                        full_reasoning += chunk["reasoning"]
                        if not client_disconnected:
                            try:
                                yield sse_format({"reasoning": chunk["reasoning"]})
                            except Exception:
                                client_disconnected = True
                    
                    if chunk.get("content"):
                        full_content += chunk["content"]
                        if not client_disconnected:
                            try:
                                yield sse_format({"content": chunk["content"]})
                            except Exception:
                                client_disconnected = True
            
            if not client_disconnected:
                yield sse_format({
                    "sessionId": session_id, 
                    "done": True, 
                    "hasReasoning": bool(full_reasoning),
                    "cancelled": task.is_cancelled
                })
                yield sse_done()
            
        except GeneratorExit:
            logger.info(f"GeneratorExit: task_id={task_id}")
        finally:
            stream_manager.unregister_task(task_id)
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/chat/sessions")
async def get_sessions():
    """获取所有会话"""
    session_list = list(sessions.values())
    return success(data=session_list)


@router.get("/chat/session/{session_id}")
async def get_session_by_id(session_id: str):
    """获取指定会话"""
    session = sessions.get(session_id)
    if not session:
        return success(data=None, msg="会话不存在")
    return success(data=session)


@router.delete("/chat/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    if session_id in sessions:
        del sessions[session_id]
        stream_manager.cancel_session_tasks(session_id)
        return success(msg="删除成功")
    return success(msg="会话不存在")


@router.post("/chat/stop/{session_id}")
async def stop_session(session_id: str):
    """停止会话任务"""
    cancelled = stream_manager.cancel_session_tasks(session_id)
    return success(data={"cancelled_tasks": cancelled}, msg="已停止")


@router.post("/chat/stop")
async def stop_all_sessions():
    """停止所有会话任务"""
    from services.stream import get_stream_manager
    manager = get_stream_manager()
    cancelled = 0
    for task_id in list(manager._tasks.keys()):
        manager.cancel_task(task_id)
        cancelled += 1
    return success(data={"cancelled_tasks": cancelled}, msg="已全部停止")
