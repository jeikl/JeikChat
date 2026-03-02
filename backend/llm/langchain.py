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
    # api_key = os.getenv(f"{model_name(llm)}_API_KEY")
    # base_url = os.getenv(f"{model_name(llm)}_BASE_URL")
    api_key = "6246ef67-931a-4f19-9409-89b42fc04a91"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    extra_parms={}
    if thinking == "false":
        extra_parms = {
            "thinking": {"type": "disabled"},
        }
    elif thinking == "deep":
        extra_parms = {
            "thinking": {"type": "enabled"},
        }
    else:
        extra_parms = {
            "thinking": {"type": "auto"},
        }
    
    return ChatDeepSeek(
        model=llm,
        api_key=api_key,
        api_base=base_url,
        streaming=True,
        extra_body=extra_parms,
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
    full_content = ""
    full_reasoning = ""
    has_reasoning = False

    for chunk in llm_sendmsg_stream("doubao-seed-2-0-pro-260215", "你好", "auto"):
        full_reasoning += chunk.get("reasoning", "")
        full_content += chunk.get("content", "")
        
        if chunk.get("reasoning"):
            has_reasoning = True
            print(f"\n[推理中]: {chunk['reasoning']}")
        
        if chunk.get("content"):
            print(f"[内容]: {chunk['content']}", end="", flush=True)
    
    print("\n\n=== 完整推理过程 ===")
    print(full_reasoning if full_reasoning else "(无推理内容)")
    print("\n=== 完整答案 ===")
    print(full_content)
