"""
流式处理模块
包含聊天流和Agent流
"""
import asyncio
from typing import List, Optional, Callable, AsyncGenerator
from langchain.tools import tool
from langchain.agents import create_agent
import logging

from services.llm import create_client
from agent.prompt import get_prompts, build_messages
from agent.tools.web import search as web_search_func
from agent.tools.werther import search as weather_search_func

logger = logging.getLogger(__name__)


@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气。"""
    return weather_search_func(city)


@tool
def web_search(query: str) -> str:
    """搜索互联网获取最新信息。"""
    return web_search_func(query)


@tool
def calculator(expression: str) -> str:
    """计算数学表达式。"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {str(e)}"


TOOL_MAP = {
    "web_search": web_search,
    "weather": get_weather,
    "calculator": calculator,
}


async def chat_stream(
    llm: str,
    msg: list,
    thinking: str = "auto",
    should_stop: Optional[Callable[[], bool]] = None
) -> AsyncGenerator[dict, None]:
    """
    纯聊天流式响应
    不使用工具
    """
    client = create_client(llm, thinking)
    
    try:
        async for chunk in client.astream(msg):
            if should_stop and should_stop():
                break
            
            result = {}
            
            if hasattr(chunk, 'content') and chunk.content:
                result["content"] = chunk.content
            
            if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
                reasoning_content = chunk.additional_kwargs.get('reasoning_content')
                if reasoning_content:
                    result["reasoning"] = reasoning_content
                result["additional_kwargs"] = chunk.additional_kwargs
            
            if result:
                yield result
                
    except GeneratorExit:
        raise
    except Exception as e:
        logger.error(f"聊天流错误: {e}")
        raise


async def agent_stream(
    llm: str,
    msg: list,
    thinking: str,
    tool_ids: List[str],
    should_stop: Optional[Callable[[], bool]] = None
) -> AsyncGenerator[dict, None]:
    """
    Agent 流式响应
    支持工具调用
    """
    prompts = get_prompts()
    
    selected_tools = [TOOL_MAP[tid] for tid in tool_ids if tid in TOOL_MAP]
    
    if not selected_tools:
        yield {"content": "未找到可用的工具"}
        return
    
    system_prompt = prompts.get_agent_prompt(tool_ids)
    
    user_input = ""
    for m in msg:
        if isinstance(m, dict):
            user_input = m.get("content", "")
        elif hasattr(m, 'content'):
            user_input = m.content
    
    logger.info(f"Agent 处理输入: {user_input[:50]}..., 工具: {tool_ids}")
    
    client = create_client(llm, thinking)
    
    agent = create_agent(
        client,
        tools=selected_tools,
        system_prompt=system_prompt,
    )
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    def run_agent():
        return agent.invoke({"messages": [{"role": "user", "content": user_input}]})
    
    result = await loop.run_in_executor(None, run_agent)
    
    messages = result.get("messages", [])
    final_message = messages[-1] if messages else None
    
    if final_message:
        output = final_message.content if hasattr(final_message, "content") else str(final_message)
        
        for char in output:
            if should_stop and should_stop():
                break
            yield {"content": char}
    
    yield {"content": "", "done": True}
