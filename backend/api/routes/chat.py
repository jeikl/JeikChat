"""
聊天 API 路由
"""

import sys
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
from agent.chatRouterStream import agent_stream0,agent_stream1,agent_stream3
from agent.prompt import get_prompts, build_messages

router = APIRouter()

stream_manager = get_stream_manager()

sessions: dict = {}
uuid_to_session_map: dict = {}  # UUID 到会话 ID 的映射


def get_session(session_id: Optional[str], content: str):
    """获取或创建会话 - 不持久化会话级别的设置"""
    if not session_id or session_id not in sessions:
        sessions[session_id] = {
            "id": session_id,
            "title": content[:30] + "..." if len(content) > 30 else content,
            "messages": [],
            "created_at": int(datetime.now().timestamp() * 1000),
            "updated_at": int(datetime.now().timestamp() * 1000),
            # 不保存 model, knowledge_base_ids 到会话中
            # 这些设置由全局设置管理，每次请求时使用当前设置
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
    prompts = get_prompts()

    
    session_id = get_session(
        request.session_uuid, 
        request.content, 
    )
    
    # 记录会话UUID - 如果前端未提供，则后端生成一个
    session_uuid = request.session_uuid
    if not session_uuid:
        session_uuid = str(uuid.uuid4())
        logger.warning(f"前端未提供UUID，后端生成: {session_uuid}")
    
    # 记录 UUID 到会话 ID 的映射（用于删除功能）
    uuid_to_session_map[session_uuid] = session_id
    
    config = {
        "configurable": {
            "thread_id": session_uuid
        }
    }
    save_message(session_id, "user", request.content)
    
    model = request.model or "qwen3.5-flah"
    thinking = request.thinking or "auto"
    # tools 现在是 ToolConfig 对象列表
    tool_configs = request.tools or []
    tool_names = [t.toolid for t in tool_configs] if tool_configs else []

    if tool_names:
        logger.info(f"[Chat] 模型={model}, 工具={tool_names}")
    else:
        logger.info(f"[Chat] 模型={model}")
    
    task_id = str(uuid.uuid4())
    task = stream_manager.register_task(task_id, session_id)
    
    async def stream_generator():
        full_content = ""
        full_reasoning = ""
        client_disconnected = False
        is_agent_mode = len(tool_configs) > 0
        if is_agent_mode:
            #stream_func = agent_stream
            system_prompt = await prompts.get_agent_prompt(tool_names)
        else:
            system_prompt = prompts.get_chat_prompt()

        msg = build_messages(system_prompt, request.content)

        try:
            # 传递 tool_configs（ToolConfig 对象列表）给 agent_stream0
            async for chunk in agent_stream1(model, msg, thinking, tool_configs, config, task.is_cancelled):
            #async for chunk in example_with_agent3(model, msg, thinking, tool_configs, system_prompt, task.is_cancelled):
                if await http_request.is_disconnected():
                    if not client_disconnected:
                        logger.info(f"客户端断开连接，后台停止: task_id={task_id}")
                        break


                
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
                        except Exception as e:
                            yield sse_format({"content": f"{str(e)}"})
                            client_disconnected = True
            
            
            # 保存助手回复到会话历史
            if full_content or full_reasoning:
                save_message(session_id, "assistant", full_content, full_reasoning)
            
            if not client_disconnected:
                yield sse_format({
                    "sessionId": session_id,
                    "sessionUuid": session_uuid,
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


# UUID 到会话 ID 的映射（用于前端通过 UUID 删除会话）
uuid_to_session_map: dict = {}


@router.delete("/chat/history/{session_id}")
async def delete_session_history(session_id: str):
    """
    删除指定会话历史
    
    支持两种 ID：
    1. 前端会话 ID（如 "session-xxx"）
    2. UUID（如 "550e8400-e29b-41d4-a716-446655440000"）
    """
    # 检查是否是 UUID 格式
    try:
        uuid.UUID(session_id)
        # 如果是 UUID，查找对应的会话
        if session_id in uuid_to_session_map:
            actual_session_id = uuid_to_session_map[session_id]
            if actual_session_id in sessions:
                del sessions[actual_session_id]
                stream_manager.cancel_session_tasks(actual_session_id)
                del uuid_to_session_map[session_id]
                return success(msg="删除成功")
        return success(msg="会话不存在或已删除")
    except ValueError:
        # 不是 UUID，直接作为会话 ID 处理
        if session_id in sessions:
            del sessions[session_id]
            stream_manager.cancel_session_tasks(session_id)
            # 清理 UUID 映射
            for uuid_key, sid in list(uuid_to_session_map.items()):
                if sid == session_id:
                    del uuid_to_session_map[uuid_key]
                    break
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
