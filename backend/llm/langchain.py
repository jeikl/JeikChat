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



def llm_sendmsg(llm: str, msg: str):
    """非流式调用"""
    client = create_client(llm)
    for chunk in client.invoke(msg):
        print(chunk, end="", flush=True)


def llm_sendmsg_stream(llm: str, msg: str, thinking: str = "auto"):
    """流式调用 - 生成器版本"""
    client = create_client(llm, thinking)
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
    llm_sendmsg("qwen3.5-plus", "你好")
    print("\n=== 测试流式 ===")
    for chunk in llm_sendmsg_stream("qwen3.5-plus", "你好"):
        print(chunk, end="", flush=True)
