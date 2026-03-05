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
    msg,
    thinking: str,
    tool_ids: List[str],
    system_prompt: str = "",
    should_stop: Optional[Callable[[], bool]] = None
) -> AsyncGenerator[dict, None]:
    """
    代理流式响应
    使用 astream_events 获取详细的执行事件
    """
    logger.info(f"Agent 处理输入: {msg}..., 工具: {tool_ids}")
    
    # 过滤工具
    selected_tools = [t for t in tools if t.name in tool_ids] if tool_ids else tools
    
    # 创建客户端和代理
    client = create_client(llm, thinking)
    agent = create_agent(
        client,
        tools=selected_tools,
        system_prompt=system_prompt
    )
    
    try:
        # 输入数据处理

        input_data = {"messages": msg} if isinstance(msg, list) else msg

        # 使用 astream_events 获取异步流式事件 (v2)
        async for event in agent.astream_events(
            input_data,
            version="v2"
        ):
            if should_stop and should_stop():
                break
            
            kind = event["event"]
            
            # 1. 模型生成的 Token (正式内容)
            if kind == "on_chat_model_stream":
                # 确保是最终回答的流，而不是工具调用的流
                # 通常工具调用的流会在 on_tool_start 之前，但 event data chunk 可能包含 tool_call_chunks
                # 我们只关心 content
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    yield {"content": chunk.content}
            
            # 2. 工具开始调用 (推理过程)
            elif kind == "on_tool_start":
                # 过滤掉内部工具或链
                if event["name"] and not event["name"].startswith("_"):
                    tool_name = event["name"]
                    tool_input = event["data"].get("input")
                    # 格式化为: 🧠 正在调用工具: tool_name(args)
                    # 添加换行符确保显示格式
                    yield {"reasoning": f"\n🧠 正在调用工具: {tool_name}({tool_input})\n"}
            
            # 3. 工具调用结束 (推理过程)
            elif kind == "on_tool_end":
                if event["name"] and not event["name"].startswith("_"):
                    tool_output = event["data"].get("output")
                    # 格式化为: 🛠️ 工具返回: result
                    
                    # 尝试提取内容 (处理 ToolMessage 或 dict)
                    output_str = str(tool_output)
                    if hasattr(tool_output, "content"):
                        output_str = str(tool_output.content)
                    elif isinstance(tool_output, dict) and "content" in tool_output:
                        output_str = str(tool_output["content"])
                    
                    # 截断过长的输出
                    if len(output_str) > 500:
                        output_str = output_str[:500] + "..."
                    yield {"reasoning": f"\n🛠️ 工具返回: {output_str}\n"}

    except GeneratorExit:
        raise
    except Exception as e:
        logger.error(f"Agent 流错误: {e}")
        # 发送错误信息作为内容
        yield {"content": f"\n\n[系统错误: {str(e)}]"}
        raise



