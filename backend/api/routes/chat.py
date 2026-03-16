"""
聊天 API 路由
"""

import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from schemas.chat import SendMessageRequest
from api.response import success, sse_format, sse_done
from services.stream import get_stream_manager
from agent.chatRouterStream import agent_stream1
from agent.prompt import get_prompts, build_messages

router = APIRouter()
logger = logging.getLogger(__name__)
stream_manager = get_stream_manager()
sessions = {}
uuid_to_session_map = {}


def get_session(sid: str, content: str):
    """获取或创建会话"""
    if not sid or sid not in sessions:
        sessions[sid] = {
            "id": sid,
            "title": content[:30] + "..." if len(content) > 30 else content,
            "messages": [],
            "created_at": int(datetime.now().timestamp() * 1000),
            "updated_at": int(datetime.now().timestamp() * 1000),
        }
    return sid


def save_message(sid: str, role: str, content: str, reasoning: str = None):
    """保存消息到会话"""
    msg = {"id": str(uuid.uuid4()), "role": role, "content": content,
           "timestamp": int(datetime.now().timestamp() * 1000)}
    if reasoning:
        msg["reasoning"] = reasoning
    sessions[sid]["messages"].append(msg)
    sessions[sid]["updated_at"] = int(datetime.now().timestamp() * 1000)
    return msg


@router.post("/chat/send")
async def send_message(request: SendMessageRequest, http_request: Request):
    """发送消息 - 流式返回"""
    prompts = get_prompts()
    session_id = get_session(request.session_uuid, request.content)
    session_uuid = request.session_uuid or str(uuid.uuid4())
    uuid_to_session_map[session_uuid] = session_id
    save_message(session_id, "user", request.content)

    model = request.model or "qwen3.5-flash"
    thinking = request.thinking or "auto"
    tool_configs = request.tools or []
    tool_names = [t.toolid for t in tool_configs]
    config = {"configurable": {"thread_id": session_uuid}}
    
    # 获取知识库ID列表
    knowledge_base_ids = request.knowledge_base_ids or []
    
    logger.info(f"[Chat] 模型={model}, 工具={tool_names}, 知识库={knowledge_base_ids}")
    task_id = str(uuid.uuid4())
    task = stream_manager.register_task(task_id, session_id)

    async def stream_generator():
        full_content, full_reasoning, chunk_count = "", "", 0
        disconnected = False
        
        # 构建系统提示词
        system_prompt = await prompts.get_agent_prompt(tool_names) if tool_names else prompts.get_chat_prompt()
        
        # 如果有选中的知识库，在system提示词中添加知识库信息
        if knowledge_base_ids:
            knowledge_names_str = "\n".join([f"- {kb_id}" for kb_id in knowledge_base_ids])
            knowledge_hint = f"""

你有以下知识库可供检索：
{knowledge_names_str}

当用户询问专业性问题时，请使用 retrieve_documents 工具从上述知识库中检索相关文档作为参考。
你可以通过 knowledge_base 参数指定要检索的知识库名称，例如：retrieve_documents(query="问题", knowledge_base="知识库名称")
如果不指定 knowledge_base 参数，则会检索所有知识库。"""


            system_prompt = system_prompt + knowledge_hint
            logger.info(f"[Chat] 已添加知识库提示词: {knowledge_base_ids}")
        
        msg = build_messages(system_prompt, request.content)

        try:
            logger.info(f"[Chat] 开始: {task_id}")
            async for chunk in agent_stream1(model, msg, thinking, tool_configs, config, task.is_cancelled):
                chunk_count += 1
                if await http_request.is_disconnected():
                    logger.info(f"客户端断开: {task_id}")
                    disconnected = True
                    break
                if task.is_cancelled:
                    logger.info(f"任务取消: {task_id}")
                    break

                if chunk.get("reasoning"):
                    full_reasoning += chunk["reasoning"]
                    if not disconnected:
                        yield sse_format({"reasoning": chunk["reasoning"]})

                if chunk.get("content"):
                    full_content += chunk["content"]
                    if not disconnected:
                        yield sse_format({"content": chunk["content"]})

            logger.info(f"任务流完成: {task_id}, chunks={chunk_count}")
            yield sse_format({"reasoning": "\n\n✅️思考完成\n\n"})
            if full_content or full_reasoning:
                save_message(session_id, "assistant", full_content, full_reasoning)

            if not disconnected:#发送流式完成信号
                yield sse_format({"sessionId": session_id, "sessionUuid": session_uuid,
                                  "done": True, "hasReasoning": bool(full_reasoning)})
                yield sse_done()

        except Exception as e:
            logger.error(f"[Chat] 异常: {task_id}, {e}")
        finally:
            stream_manager.unregister_task(task_id)

    return StreamingResponse(stream_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})


@router.get("/chat/sessions")
async def get_sessions():
    """获取所有会话列表"""
    return success({
        "sessions": [{"sessionUuid": k, **{kk: vv for kk, vv in v.items() if kk != "messages"}}
                     for k, v in sessions.items()]
    })


@router.get("/chat/session/{session_uuid}")
async def get_session_detail(session_uuid: str):
    """获取会话详情"""
    if session_uuid not in sessions:
        return success({"session": None, "messages": []})
    return success({"session": sessions[session_uuid], "messages": sessions[session_uuid]["messages"]})


@router.delete("/chat/session/{session_uuid}")
async def delete_session(session_uuid: str):
    """删除会话"""
    if session_uuid in sessions:
        del sessions[session_uuid]
    if session_uuid in uuid_to_session_map:
        del uuid_to_session_map[session_uuid]
    return success({"deleted": True})


@router.post("/chat/session/{session_uuid}/clear")
async def clear_session(session_uuid: str):
    """清空会话消息"""
    if session_uuid in sessions:
        sessions[session_uuid]["messages"] = []
    return success({"cleared": True})


@router.post("/chat/cancel/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    stream_manager.cancel_task(task_id)
    return success({"cancelled": True})
