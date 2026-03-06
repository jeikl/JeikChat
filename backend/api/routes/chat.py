
"""
聊天 API 路由 (同步流式重构版)
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Generator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import iterate_in_threadpool

from langchain_core.messages import HumanMessage

from schemas.chat import SendMessageRequest
from api.response import success, sse_format, sse_done
from services.stream import get_stream_manager
from agent.chatRouterStream import agent_stream, chat_stream
from agent.prompt import get_prompts, build_messages

logger = logging.getLogger(__name__)

router = APIRouter()
stream_manager = get_stream_manager()

# 简单的内存会话存储
sessions: dict = {}

def get_or_create_session(session_id: Optional[str], content: str, model: Optional[str], knowledge_base_ids: Optional[List[str]]) -> str:
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

def append_message(session_id: str, role: str, content: str, reasoning: str = None):
    """追加消息到会话"""
    if session_id not in sessions:
        return None
        
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

def sync_generator_wrapper(
    model: str, 
    msg: list, 
    thinking: str, 
    tools: list, 
    should_stop_func: callable, 
    config: dict
) -> Generator[str, None, None]:
    """
    同步生成器包装器
    负责执行同步的 agent_stream 或 chat_stream，并处理结果
    """
    full_content = ""
    full_reasoning = ""
    
    is_agent_mode = len(tools) > 0
    
    try:
        # 选择流式函数
        if is_agent_mode:
            stream_iterator = agent_stream(model, msg, thinking, tools, should_stop=should_stop_func, history=config)
        else:
            stream_iterator = chat_stream(model, msg, thinking, should_stop=should_stop_func, history=config)
            
        # 遍历生成器
        for chunk in stream_iterator:
            # 检查是否有推理内容
            if chunk.get("reasoning"):
                reasoning_text = chunk["reasoning"]
                full_reasoning += reasoning_text
                yield sse_format({"reasoning": reasoning_text})
                
            # 检查是否有正文内容
            if chunk.get("content"):
                content_text = chunk["content"]
                full_content += content_text
                yield sse_format({"content": content_text})

        # 生成结束，返回汇总信息（通过 yield 传递给外部，虽然 SSE 格式本身只传增量，这里可以传一个特殊的 done 事件或者利用 side effect）
        # 注意：这里我们通过 yield 一个特殊的 dict 来传递最终结果给外层异步 wrapper 处理保存逻辑是不太方便的
        # 因为外层是 async for，这里是 sync generator。
        # 更好的方式是：在 yield 完所有内容后，返回最终结果，但生成器只能 return，不能 yield return value 给 for loop。
        # 所以我们这里直接 yield 最终的 done 标记前，我们可以把完整内容附带在最后一个 chunk 或者专门的一个事件里？
        # 为了简化，我们直接在这里做“保存”动作是不行的，因为 sessions 是全局变量，虽然可以访问，但最好保持函数纯粹。
        # 变通方案：yield 一个特殊的内部事件，外层捕获后处理。
        
        yield {"type": "complete", "full_content": full_content, "full_reasoning": full_reasoning}

    except Exception as e:
        logger.error(f"生成过程出错: {e}")
        yield sse_format({"content": f"\n\n[系统错误] 生成过程中断: {str(e)}"})


@router.post("/chat/send")
async def send_message(request: SendMessageRequest, http_request: Request):
    """
    发送消息 - 全新优化的流式接口
    """
    # 1. 准备基础数据
    prompts = get_prompts()
    session_id = get_or_create_session(
        request.session_id, 
        request.content, 
        request.model, 
        request.knowledge_base_ids
    )
    
    # 2. 保存用户消息
    append_message(session_id, "user", request.content)
    
    # 3. 准备参数
    model = request.model or "qwen3.5-plus"
    thinking = request.thinking or "auto"
    tools = request.tools or []
    
    # LangGraph 配置
    config = {"configurable": {"thread_id": session_id}}
    
    # 注册任务
    task_id = str(uuid.uuid4())
    task = stream_manager.register_task(task_id, session_id)
    
    logger.info(f"开始生成: session={session_id}, model={model}, tools={len(tools)}")

    # 4. 构建 Prompt 消息
    if len(tools) > 0:
        system_prompt = prompts.get_agent_prompt(tools)
        msg = build_messages(system_prompt, request.content, agent=True)
    else:
        system_prompt = prompts.get_chat_prompt()
        msg = build_messages(system_prompt, request.content, agent=False)

    # 5. 定义异步生成器适配器
    async def async_response_generator():
        client_disconnected = False
        final_content = ""
        final_reasoning = ""
        
        try:
            # 核心：使用 iterate_in_threadpool 将同步生成器转为异步迭代
            # 这样既保留了同步代码的稳定性，又不会阻塞 FastAPI 的事件循环
            
            # 创建同步生成器实例
            sync_gen = sync_generator_wrapper(
                model, msg, thinking, tools, 
                should_stop_func=task.is_cancelled, 
                config=config
            )
            
            async for item in iterate_in_threadpool(sync_gen):
                # 检查客户端连接状态
                if await http_request.is_disconnected():
                    if not client_disconnected:
                        logger.info(f"客户端断开: {task_id}")
                        client_disconnected = True
                    # 注意：这里不 break，允许后台继续生成直到完成（如果需要的话），或者也可以选择 break
                    # 为了节省资源，通常选择 break，除非需要完整的历史记录
                    # 这里我们选择 break，并在 finally 中处理
                    break
                
                # 检查任务取消状态
                if task.is_cancelled:
                    logger.info(f"任务取消: {task_id}")
                    break

                # 处理内部特殊事件
                if isinstance(item, dict) and item.get("type") == "complete":
                    final_content = item["full_content"]
                    final_reasoning = item["full_reasoning"]
                    continue
                
                # 正常 SSE 消息，直接发送
                if not client_disconnected:
                    yield item

            # 6. 生成结束后的处理
            if not client_disconnected:
                # 保存助手消息
                if final_content or final_reasoning:
                    append_message(session_id, "assistant", final_content, final_reasoning)
                
                # 发送结束标记
                yield sse_format({
                    "sessionId": session_id, 
                    "done": True, 
                    "hasReasoning": bool(final_reasoning),
                    "cancelled": task.is_cancelled
                })
                yield sse_done()
                
        except Exception as e:
            logger.error(f"流式响应异常: {e}")
            if not client_disconnected:
                 yield sse_format({"content": f"\n\n[服务异常] {str(e)}"})
                 yield sse_done()
        finally:
            stream_manager.unregister_task(task_id)

    return StreamingResponse(
        async_response_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

# 保持原有的 CRUD 接口不变
@router.get("/chat/sessions")
async def get_sessions():
    """获取所有会话"""
    return success(data=list(sessions.values()))

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
    manager = get_stream_manager()
    cancelled = 0
    for task_id in list(manager._tasks.keys()):
        manager.cancel_task(task_id)
        cancelled += 1
    return success(data={"cancelled_tasks": cancelled}, msg="已全部停止")
