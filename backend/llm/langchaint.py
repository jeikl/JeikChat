
from langchain_deepseek import ChatDeepSeek

from langchain_openai import ChatOpenAI
import os
import sys
from dotenv import load_dotenv

current_dir = os.path.dirname(__file__)
env_path = os.path.abspath(os.path.join(current_dir, "..", "..", ".env"))
load_dotenv(dotenv_path=env_path, override=True)

_client_cache = {}


def model_name(text: str):
    dash_index = text.find("-")
    if dash_index == -1:
        s = text
    else:
        s = text[:dash_index]
    letters = [char for char in s if char.isalpha()]
    return ''.join(letters).upper()


def create_client(llm: str, reasoning: str = 'auto'):
    cache_key = f"{llm}_{reasoning}"
    if cache_key in _client_cache:
        return _client_cache[cache_key]
    
    api_key = os.getenv(f"{model_name(llm)}_API_KEY")
    base_url = os.getenv(f"{model_name(llm)}_BASE_URL")
    
    extra_body = {}
    
    # 所有模型的深度思考参数全加进去，API 会自动忽略不认识的参数
    if reasoning == 'auto':
        extra_body = {
            'enable_thinking': None,
            'thinking': {'type': 'auto'},
            'reasoning_level': 'auto',
        }
    elif reasoning == 'true':
        extra_body = {
            'enable_thinking': True,#千问深度思考
            'thinking': {'type': 'enabled'},#豆包深度思考
            'reasoning_level': 'high',#openai深度思考等级
        }
    elif reasoning == 'false':
        extra_body = {
            'enable_thinking': False,
            'thinking': {'type': 'disabled'},
            'reasoning_level': 'none',
        }
    
    client = ChatDeepSeek(
        model=llm,
        api_key=api_key,
        api_base=base_url,
        temperature=0.7,
        streaming=True,
        timeout=1800,
        extra_body=extra_body if extra_body else None,
    )
    
    _client_cache[cache_key] = client
    return client

def llm_sendmsg(llm: str, msg: str):
    """非流式调用"""
    client = create_client(llm)

    for chunk in client.invoke(msg):
        print(chunk, end="", flush=True)


def llm_sendmsg_stream(llm: str, msg: str, reasoning: str = 'auto'):
    """流式调用 - 生成器版本，返回包含推理内容和标准内容的字典"""
    client = create_client(llm, reasoning)
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


def llm_sendmsg_stream_simple(llm: str, msg: str):
    """流式调用 - 简单版本，只返回标准内容（保持向后兼容）"""
    client = create_client(llm)
    for chunk in client.stream(msg):
        if chunk.content:
            yield chunk.content


def llm_sendmsg_stream_async(llm: str, msg: str):
    """流式调用 - 异步生成器版本"""
    client = create_client(llm)
    for chunk in client.stream(msg):
        if chunk.content:
            yield chunk.content


if __name__ == "__main__":
    print("=== 测试非流式 ===")
    #llm_sendmsg("qwen3.5-plus", "你好 怎么学习AI开发")
    print("\n=== 测试流式 ===")
    for chunk in llm_sendmsg_stream_async("doubao-seed-2-0-pro-260215", "你好 怎么学习AI开发"):
        print(chunk, end="", flush=True)





