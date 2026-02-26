#!/usr/bin/env python3
"""
Test script for the new streaming functions in llms.py
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..", ".env")
)
load_dotenv(dotenv_path=env_path, override=True)

# Add the backend to the path so we can import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from langchain_openai import ChatOpenAI
from llms import stream_print_sync, stream_print_async
import asyncio


def test_sync_streaming():
    print("Testing sync streaming...")
    # Create a test LLM instance
    llm = ChatOpenAI(
        model="qwen3.5-plus",
        api_key=os.getenv("QWEN_API_KEY"),
        base_url=os.getenv("QWEN_BASE_URL"),
        temperature=0.7
    )
    
    try:
        result = stream_print_sync(llm, "你好，请简单介绍一下自己")
        print(f"\nSync result length: {len(result)}")
        print(f"Sync result type: {type(result)}")
    except Exception as e:
        print(f"Sync test error: {e}")


async def test_async_streaming():
    print("\nTesting async streaming...")
    # Create a test LLM instance
    llm = ChatOpenAI(
        model="qwen3.5-plus",
        api_key=os.getenv("QWEN_API_KEY"),
        base_url=os.getenv("QWEN_BASE_URL"),
        temperature=0.7
    )
    
    try:
        result = await stream_print_async(llm, "请用一句话说明什么是人工智能")
        print(f"\nAsync result length: {len(result)}")
        print(f"Async result type: {type(result)}")
    except Exception as e:
        print(f"Async test error: {e}")


if __name__ == "__main__":
    test_sync_streaming()
    asyncio.run(test_async_streaming())