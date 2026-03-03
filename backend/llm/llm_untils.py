from langchain_deepseek import ChatDeepSeek
import asyncio


client=ChatDeepSeek(
    model="doubao-seed-2-0-pro-260215",
    api_key="6246ef67-931a-4f19-9409-89b42fc04a91",
    api_base="https://ark.cn-beijing.volces.com/api/v3",
    streaming= True,
    extra_body={"thinking": {"type": "enabled"}},
)

def stream_chat(content: str):
    for chunk in client.stream(content):
        result = {}
        if chunk.content:
            result["content"] = chunk.content
            print(result.get("content"))
        if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
            reasoning_content = chunk.additional_kwargs.get('reasoning_content')
            if reasoning_content:
                result["reasoning"] = reasoning_content
                print(result.get("reasoning"))
        result["additional_kwargs"] = chunk.additional_kwargs #原始参数
   


async def stream_chat_async(content: str):
    """异步版本的流式聊天"""
    loop = asyncio.get_event_loop()
    
    def sync_stream():
        for chunk in client.stream(content):
            result = {}
            if chunk.content:
                result["content"] = chunk.content
            if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
                reasoning_content = chunk.additional_kwargs.get('reasoning_content')
                if reasoning_content:
                    result["reasoning"] = reasoning_content
            if result:
                yield result
    
    for chunk in sync_stream():
        await asyncio.sleep(0)
        yield chunk



if __name__ == "__main__":
    import asyncio
    
    async def test_async():
        print("\n=== 测试异步流式 ===")
        async for chunk in stream_chat_async("你好，AI开发如何学习"):
            if chunk.get("reasoning"):
                print(f"\n[推理]: {chunk['reasoning']}")
            if chunk.get("content"):
                print(f"[内容]: {chunk['content']}", end="", flush=True)
    
    asyncio.run(test_async())
