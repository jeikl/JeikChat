
import os
from langchain_core.caches import InMemoryCache
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from typing import AsyncGenerator



env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../..", ".env")
)

load_dotenv(dotenv_path=env_path, override=True)

def stream_print_sync(llm, prompt: str) -> str:
    """
    同步流式处理，返回完整内容
    """
    full_content = ""
    for chunk in llm.stream([HumanMessage(content=prompt)]):
        content = chunk.content if hasattr(chunk, 'content') else str(chunk)
        full_content += content
        print(full_content,end="",flush=true)
    return full_content



async def stream_generator_async(llm, prompt: str) -> AsyncGenerator[str, None]:
    """
    异步流式处理，异步生成器方式逐个返回内容块
    这是真正的异步流式返回，每次获得chunk时立即yield
    """
    async for chunk in llm.astream([HumanMessage(content=prompt)]):
        content = chunk.content if hasattr(chunk, 'content') else str(chunk)
        yield content



def get_llm(model: str = "qwen3.5-plus", temperature: float = 0.7, streaming: bool = True) -> ChatOpenAI:
    """
    获取 Qwen LLM 实例
    
    Args:
        model: 模型名称，默认为 "qwen3.5-plus"
        temperature: 温度参数，默认为 0.7
        streaming: 是否启用流式输出，默认为 True
    
    Returns:
        ChatOpenAI 实例
    """
    # 自动扫描所有 *_API_KEY 环境变量
    model_lower = model.lower()
    
    # 定义常用的模型前缀到环境变量前缀的映射
    prefix_mapping = {
        "qwen": ("QWEN", None),
        "gpt": ("OPENAI", "https://api.openai.com/v1"),
        "o1": ("OPENAI", "https://api.openai.com/v1"),
        "o3": ("OPENAI", "https://api.openai.com/v1"),
        "claude": ("ANTHROPIC", "https://api.anthropic.com"),
        "gemini": ("GOOGLE", "https://generativelanguage.googleapis.com/v1"),
        "moonshot": ("MOONSHOT", "https://api.moonshot.cn/v1"),
        "doubao": ("DOUBAO", "https://ark.cn-beijing.volces.com/api/v3"),
        "ollama": ("OLLAMA", "http://localhost:11434/v1"),
    }
    
    # 查找匹配的前缀
    matched_prefix = None
    for prefix, (env_prefix, default_url) in prefix_mapping.items():
        if model_lower.startswith(prefix):
            matched_prefix = (env_prefix, default_url)
            break
    
    if matched_prefix is None:
        matched_prefix = ("QWEN", None)
    
    env_prefix, default_base_url = matched_prefix
    
    # 获取对应的环境变量
    api_key = os.getenv(f"{env_prefix}_API_KEY")
    base_url = os.getenv(f"{env_prefix}_BASE_URL") or default_base_url
    
    # 特殊处理：Ollama 不需要 API Key
    if env_prefix == "OLLAMA":
        api_key = "ollama"
    
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        streaming=streaming
    )


# 为了兼容性，保留直接导出
qwen = get_llm()



