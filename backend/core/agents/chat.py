from os import name
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from llm.langchaint import create_client

def creat_chat_agent(llm: str, system: str, configid: str, thinking: str = "auto"):
    llm_client = create_client(llm, thinking)
    chat_agent = create_agent(
        model=llm_client, 
        tools=[],
        system_prompt=system
    )
    return chat_agent



if __name__ == "__main__":
    llm = "qwen3.5-plus"
    system = "你是一个智能助手 请你根据用户的问题进行回答"
    chat_agent = creat_chat_agent(llm, system, "123", thinking="deep")

    print("=== 开始流式输出 ===\n", flush=True)
    
    reasoning_buffer = ""
    content_buffer = ""
    is_reasoning_phase = True
    
    for token, metadata in chat_agent.stream(  
        {"messages": [{"role": "user", "content": "你好呀 怎么学习英语?"}]},
        stream_mode="messages",
    ):
        # ========== 直接从 token 对象获取字段值 ==========
        reasoning = ""
        content = ""
        
        # 方法1: 从 additional_kwargs 获取 (DeepSeek)
        if hasattr(token, 'additional_kwargs') and token.additional_kwargs:
            reasoning = token.additional_kwargs.get('reasoning_content', '')
        
        # 方法2: 直接从 token 属性获取 (阿里/豆包)
        if hasattr(token, 'reasoning'):
            reasoning = getattr(token, 'reasoning', '')
        
        # 方法3: 从 content 获取
        if hasattr(token, 'content'):
            content = token.content
        
        # 显示逻辑
        if reasoning:
            reasoning_buffer += reasoning
            is_reasoning_phase = True
            print(f"\r[🤔 思考中...] {reasoning_buffer[-50:]}", end='', flush=True)
        
        if content:
            if is_reasoning_phase and reasoning_buffer:
                print("\n", flush=True)
                is_reasoning_phase = False
            
            content_buffer += content
            print(f"\r[💬 回答] {content_buffer[-50:]}", end='', flush=True)
    
    print("\n\n=== 完成 ===", flush=True)