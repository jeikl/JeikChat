from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
import os
import sys
from dotenv import load_dotenv

# 当前文件路径: backend/llm/langchain.py
current_dir = os.path.dirname(__file__)
env_path = os.path.abspath(os.path.join(current_dir, "..", "..", ".env"))
load_dotenv(dotenv_path=env_path, override=True)


def model_name(text: str):#根据模型名称解析对应的模型
    dash_index = text.find("-")
    if dash_index == -1:
        s = text
    else:
        s = text[:dash_index]
    letters = [char for char in s if char.isalpha()]
    return ''.join(letters).upper()


def create_client(llm: str, thinking: str = "auto"): #根据模型名称直接获取对应的客户端
    api_key = os.getenv(f"{model_name(llm)}_API_KEY")
    base_url = os.getenv(f"{model_name(llm)}_BASE_URL")
    
    if thinking == "false" or thinking == False:
        extra_body = {
            "enable_thinking": False,
            "thinking": {"type": "disabled"},
        }
    elif thinking == "deep":
        extra_body = {
            "enable_thinking": True,
            "thinking": {"type": "enabled"},
        }
    else:
        extra_body = {
            "enable_thinking": None,
            "thinking": {"type": "auto"},
        }
    
    return ChatDeepSeek(
        model=llm,
        api_key=api_key,
        api_base=base_url,
        temperature=0.7,
        streaming=True,
        timeout=1800,
        extra_body=extra_body,
    )






def llm_sendmsg_stream(llm: str, msg: str, thinking: str = 'auto'):
    """流式调用 - 生成器版本，返回包含推理内容和标准内容的字典"""
    client = create_client(llm, thinking)   #是否推理思考
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



if __name__ == "__main__":
    print("\n=== 测试流式 ===")
    for chunk in llm_sendmsg_stream("qwen3.5-plus", "你好"):
        print(chunk, end="", flush=True)
