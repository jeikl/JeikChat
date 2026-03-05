"""
LLM 客户端服务
支持多种模型提供商的流式对话
"""

from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import sys
import time
import threading
from typing import Optional, Callable

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"), override=True)

_client_cache = {}
_cache_lock = threading.Lock()
_CACHE_TTL = float('inf')


def model_name(text: str) -> str:
    dash_index = text.find("-")
    if dash_index == -1:
        s = text
    else:
        s = text[:dash_index]
    letters = [char for char in s if char.isalpha()]
    return ''.join(letters).upper()


def _get_cache_key(llm: str, thinking: str) -> str:
    return f"{llm}:{thinking}"


def create_client(llm: str, thinking: str = "auto"):
    cache_key = _get_cache_key(llm, thinking)
    
    with _cache_lock:
        if cache_key in _client_cache:
            cached_client, cached_time = _client_cache[cache_key]
            if time.time() - cached_time < _CACHE_TTL:
                return cached_client
    
    model_provider = model_name(llm)
    api_key = os.getenv(f"{model_provider}_API_KEY")
    base_url = os.getenv(f"{model_provider}_BASE_URL")
    
    extra_params = {}
    if thinking == "false":
        extra_params = {
            "enable_thinking": False,
            "thinking": {"type": "disabled"},
        }
    elif thinking == "deep":
        extra_params = {
            "enable_thinking": True,
            "thinking": {"type": "enabled"},
        }
    else:
        extra_params = {
            "enable_thinking": None,
            "thinking": {"type": None},
        }
    
    if "gemini" in llm.lower():
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        client = ChatGoogleGenerativeAI(
            model=llm,
            temperature=1.0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
    else:
        client = ChatDeepSeek(
            model=llm,
            api_key=api_key,
            api_base=base_url,
            streaming=True,
            extra_body=extra_params,
        )

    with _cache_lock:
        _client_cache[cache_key] = (client, time.time())
    
    return client


def clear_client_cache():
    with _cache_lock:
        _client_cache.clear()


async def llm_sendmsg_stream(
    llm: str, 
    msg, 
    thinking: str = 'auto', 
    should_stop: Optional[Callable[[], bool]] = None
):
    """
    流式发送消息到大模型
    
    Args:
        llm: 模型名称
        msg: 消息内容
        thinking: 思考模式 ('auto', 'deep', 'false')
        should_stop: 可选的停止检查函数
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
        print(f"LLM 流错误: {e}")
        raise
