from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
import os
import sys
import time
import threading
from dotenv import load_dotenv

current_dir = os.path.dirname(__file__)
env_path = os.path.abspath(os.path.join(current_dir, "..", "..", ".env"))
load_dotenv(dotenv_path=env_path, override=True)

_client_cache = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 300

def model_name(text: str):
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
    
    api_key = "6246ef67-931a-4f19-9409-89b42fc04a91"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    
    extra_parms = {}
    if thinking == "false":
        extra_parms = {
            "enable_thinking": False,
            "thinking": {"type": "disabled"},
        }
    elif thinking == "deep":
        extra_parms = {
            "enable_thinking": True,
            "thinking": {"type": "enabled"},
        }
    else:
        extra_parms = {
            "enable_thinking": None,
            "thinking": {"type": None},
        }
    
    client = ChatDeepSeek(
        model=llm,
        api_key=api_key,
        api_base=base_url,
        streaming=True,
        extra_body=extra_parms,
    )
    
    with _cache_lock:
        _client_cache[cache_key] = (client, time.time())
    
    return client

def clear_client_cache():
    with _cache_lock:
        _client_cache.clear()

def llm_sendmsg_stream(llm: str, msg: str, thinking: str = 'auto'):
    client = create_client(llm, thinking)
    try:
        for chunk in client.stream(msg):
            result = {}
            
            if chunk.content:
                result["content"] = chunk.content
            
            if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
                reasoning_content = chunk.additional_kwargs.get('reasoning_content')
                if reasoning_content:
                    result["reasoning"] = reasoning_content
                result["additional_kwargs"] = chunk.additional_kwargs
            if result:
                yield result
    except GeneratorExit:
        print("客户端断开连接，停止 LLM 流")
        raise
    except Exception as e:
        print(f"LLM 流错误: {e}")
        raise
