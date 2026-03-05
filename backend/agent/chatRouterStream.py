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
from agent.prompt import get_prompts
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


tools = [
    web_search,
    get_weather,
    calculator,
]


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
    代理流式响应（带深度思考效果 + 打字机效果）
    """
    prompts = get_prompts()
    
    # 提取用户输入
    user_input = ""
    for m in msg:
        if isinstance(m, dict) and "content" in m:
            user_input = m["content"]
        elif hasattr(m, "content"):
            user_input = m.content
    
    logger.info(f"Agent 处理输入: {user_input[:50]}..., 工具: {tool_ids}")
    
    # 创建客户端和代理
    client = create_client(llm, thinking)
    agent = create_agent(
        client,
        tools=tools,
        system_prompt=prompts.get_agent_prompt(tool_ids),
    )
    
    # 使用 stream_mode="updates" 获取所有步骤
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        stream_mode="updates"
    ):
        # chunk 是字典，key 是节点名，value 是该节点的输出
        for step, data in chunk.items():
            if "messages" not in data:
                continue
                
            messages = data["messages"]
            if not messages:
                continue
                
            last_msg = messages[-1]
            content_blocks = last_msg.content_blocks if hasattr(last_msg, "content_blocks") else None
            
            if not content_blocks:
                continue
            
            # 遍历内容块
            for block in content_blocks:
                block_type = block.get("type")
                
                # 工具调用
                if block_type == "tool_call":
                    tool_name = block.get("name", "unknown")
                    tool_args = block.get("args", "")
                    yield {"content": f"🧠 正在调用工具: {tool_name}({tool_args})", "thinking": True}
                
                # 文本输出 - 打字机效果
                elif block_type == "text":
                    text = block.get("text", "")
                    for char in text:
                        if should_stop and should_stop():
                            break
                        yield {"content": char, "thinking": False}
                
                # 工具结果
                elif block_type == "tool_result":
                    tool_id = block.get("tool_call_id", "")
                    content = block.get("content", "")
                    yield {"content": f"🛠️ 工具返回: {content}", "thinking": True}
    
    # 确保最终完成
    yield {"content": "", "done": True}
