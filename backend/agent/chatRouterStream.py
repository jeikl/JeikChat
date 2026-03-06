"""
流式处理模块
包含聊天流和Agent流
"""

import asyncio
from typing import List, Optional, Callable, AsyncGenerator
from langchain.tools import tool
from langchain.agents import create_agent
import logging

from langchain_core.messages import SystemMessage

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





# 假设其他必要的 imports 已经存在 (SystemMessage, create_client, create_agent, logger, tools 等)

async def agent_stream0(
    llm: str,
    msg,
    thinking: str,
    tool_ids: List[str],
    should_stop: Optional[Callable[[], bool]] = None
) -> AsyncGenerator[dict, None]:
    """
    代理流式响应 (精简版)
    """
    selected_tools = [t for t in tools if t.name in tool_ids] if tool_ids else tools
    client = create_client(llm, thinking)
    print(f"发送: {msg}")


    agent = create_agent(
        client,
        tools=selected_tools,
    )

    # ❌ 删除了繁杂的 current_tool_call 状态变量
    try:
        async for token, metadata in agent.astream(msg, stream_mode="messages"):
            if should_stop and should_stop():
                break
            
            node = metadata.get("langgraph_node", "")

            # ==========================================
            # 1. 提取推理过程 (Reasoning)
            # ==========================================
            reasoning = token.additional_kwargs.get("reasoning_content")
            if reasoning:
                yield {"reasoning": reasoning}

            # ==========================================
            # 2. 提取工具调用动作 (Tool Calls)
            # ==========================================
            # 💡 核心技巧: LangChain 的 tool_call_chunks 在流式传输时，
            # 只有工具发出的“第一帧”会包含 'name' 字段。
            # 我们利用这一点，无需任何状态变量就能实现“只提示一次工具调用”。
            for tc_chunk in getattr(token, "tool_call_chunks", []):
                if tc_chunk.get("name"): 
                    yield {"reasoning": f"\n\n🧠 正在调用工具: {tc_chunk['name']} ...\n"}

            # ==========================================
            # 3. 提取常规文本与工具返回结果 (Content)
            # ==========================================
            # LangChain 默认会将生成的文本放在 token.content 中
            if token.content:
                text = token.content
                
                # 兼容某些模型 content 返回 list(dict) 的情况
                if isinstance(text, list):
                    text = "".join([b.get("text", "") for b in text if isinstance(b, dict) and b.get("type") == "text"])

                if text:
                    if node == "tools":
                        yield {"reasoning": f"\n🛠️ 工具返回: {text}\n"}
                    elif node == "model":
                        yield {"content": text}

    except GeneratorExit:
        raise
    except Exception as e:
        # logger.error(f"Agent 流错误: {e}")
        raise