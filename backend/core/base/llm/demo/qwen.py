import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

# 关键：使用相对路径向上4级（从demo到backend）
env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../..", ".env")
)
print("Debug: .env file path:", env_path)
load_dotenv(dotenv_path=env_path, override=True)




async def test_qwen(messages, isStream=True, Answering=True):
    client = AsyncOpenAI(
    # 如果没有配置环境变量，请用阿里云百炼API Key替换：api_key="sk-xxx"
        api_key=os.getenv("QWEN_API_KEY"),
        base_url=os.getenv("QWEN_BASE_URL"),
    )
    completion = await client.chat.completions.create(
        model="qwen3.5-plus",  # 您可按需更换为其它深度思考模型
        messages=messages,
        extra_body={"enable_thinking": True},
        stream=isStream
    )
    
    if isStream:
        is_answering = False # 开始时处于思考阶段，未进入回复阶段
        print("\n" + "=" * 20 + "思考过程" + "=" * 20)
        async for chunk in completion:
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                # 打印思考过程
                print(delta.reasoning_content, end="", flush=True)
            if hasattr(delta, "content") and delta.content:
                if not is_answering:
                    # 第一次有实际回复内容时，切换到回复阶段
                    print("\n" + "=" * 20 + "完整回复" + "=" * 20)
                    is_answering = True
                print(delta.content, end="", flush=True)
    else:
        # For non-streaming, just return the completion
        return completion
    
    return completion if not isStream else None


import asyncio

if __name__ == "__main__":
    print("=== 测试非流式 ===")
    result = asyncio.run(test_qwen(
        [{"role": "user", "content": "你好，请介绍一下自己"}], isStream=False
    ))
    print(result)

    print("\n=== 测试流式 ===")
    asyncio.run(test_qwen([{"role": "user", "content": "你好英语的语法有啥"}], isStream=True))