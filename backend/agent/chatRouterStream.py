
"""
流式处理模块
包含聊天流和Agent流 (同步版本)
"""

from typing import List, Optional, Callable, Generator
from langchain.tools import tool
from langchain.agents import create_agent
import logging

from services.llm import create_client
from langgraph.checkpoint.postgres import PostgresSaver
from . import checkpointer


from agent.tools.web import search as web_search_func
from agent.tools.werther import search as weather_search_func

DB_URI = "postgresql://root:anhuang520@pan.junv.top:5432/postgres?sslmode=disable"

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

def chat_stream(
    llm: str,
    msg: list,
    thinking: str = "auto",
    should_stop: Optional[Callable[[], bool]] = None,
    history: dict = None
) -> Generator[dict, None, None]:
    """
    纯聊天流式响应 (同步版本)
    不使用工具
    """
    client = create_client(llm, thinking)
    
    try:
        for chunk in client.stream(msg, config=history):
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


def agent_stream(
    llm: str,
    msg,
    thinking: str,
    tool_ids: List[str],
    should_stop: Optional[Callable[[], bool]] = None,
    history: dict = None
) -> Generator[dict, None, None]:
    """
    Agent流式响应 (同步版本)
    """
    client = create_client(llm, thinking)
    agent = create_agent(
    client,
    tools=tools,
    checkpointer=checkpointer
)

    print(history)
    try:
        # 使用同步的 stream 方法
        for token, metadata in agent.stream(msg, config=history, stream_mode="messages"):
            if should_stop and should_stop():
                break
            
            node = metadata.get("langgraph_node", "")

            # 1. 提取推理过程
            if token.additional_kwargs.get("reasoning_content"):
                yield {"reasoning": token.additional_kwargs["reasoning_content"]}

            # 2. 提取工具调用
            for tc_chunk in getattr(token, "tool_call_chunks", []):
                if tc_chunk.get("name"): 
                    yield {"reasoning": f"\n\n🧠 正在调用工具: {tc_chunk['name']} ...\n"}

            # 3. 提取内容
            if token.content:
                text = token.content
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
        logger.error(f"Agent 流错误: {e}")
        raise
