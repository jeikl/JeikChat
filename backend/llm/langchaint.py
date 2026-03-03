from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import sys
import time
import threading
from typing import Optional, Callable
from dotenv import load_dotenv







# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

env_path = os.path.join(project_root, ".env")
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
    
    model_provider = model_name(llm)
    api_key = os.getenv(f"{model_provider}_API_KEY")
    base_url = os.getenv(f"{model_provider}_BASE_URL")
    print(f"[DEBUG] 模型: {llm}")
    print(f"[DEBUG] 提供商: {model_provider}")
    print(f"[DEBUG] API Key: {api_key[:10]}..." if api_key else "[DEBUG] API Key: None")

    
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
    
    if "gemini" in llm.lower():
        print(f"[DEBUG] 检测到 Google 模型: {llm}")
        print(f"[DEBUG] GOOGLE_API_KEY: {api_key[:20]}..." if api_key else "[DEBUG] GOOGLE_API_KEY: None")
        # 设置环境变量给 langchain 使用
        print(os.environ["GOOGLE_API_KEY"])
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        client = ChatGoogleGenerativeAI(
            model=llm,
            temperature=1.0,  # Gemini 3.0+ defaults to 1.0
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
        print(f"[DEBUG] Google 客户端创建成功，模型: {llm}")
    else:
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

async def llm_sendmsg_stream(llm: str, msg: str, thinking: str = 'auto', should_stop: Optional[Callable[[], bool]] = None):
    """
    流式发送消息到大模型
    
    Args:
        llm: 模型名称
        msg: 消息内容
        thinking: 思考模式 ('auto', 'deep', 'false')
        should_stop: 可选的停止检查函数，返回 True 时停止生成
    """
    client = create_client(llm, thinking)
    try:
        # 使用 astream 支持真正的异步流，这样在等待响应时也能响应外部事件
        async for chunk in client.astream(msg):
            # 检查是否需要停止
            if should_stop and should_stop():
                print(f"LLM 流被主动中断: model={llm}")
                break
            
            result = {}
            
            # 处理内容
            if hasattr(chunk, 'content') and chunk.content:
                result["content"] = chunk.content
            
            # 处理思考过程 (Reasoning)
            # 对于 ChatDeepSeek，通常在 additional_kwargs 中
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


async def llm_sendmsg_stream_with_cancel(llm: str, msg: str, thinking: str = 'auto', cancel_event: Optional[threading.Event] = None):
    """
    支持取消的流式发送消息
    
    Args:
        llm: 模型名称
        msg: 消息内容
        thinking: 思考模式
        cancel_event: 取消事件，当事件被设置时停止生成
    """
    def should_stop():
        return cancel_event is not None and cancel_event.is_set()
    
    async for chunk in llm_sendmsg_stream(llm, msg, thinking, should_stop):
        yield chunk
