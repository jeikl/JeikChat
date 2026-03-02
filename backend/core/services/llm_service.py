from typing import List, Dict, Optional, Any, AsyncGenerator
import os
import json
import asyncio
import logging
import sys
from dataclasses import dataclass

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from init import get_settings
from .singleton import ThreadSafeLazyInitializer

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class StreamChunk:
    """流式响应块"""
    content: str = ""
    reasoning: str = ""
    is_finished: bool = False
    error: Optional[str] = None


class LLMService:
    """
    LLM 服务类
    支持多种提供商的文本生成和流式生成
    使用单例模式避免重复创建客户端实例
    """
    
    def __init__(self):
        self.providers = {
            "openai": self._openai_chat,
            "anthropic": self._anthropic_chat,
            "qwen": self._qwen_chat,
            "doubao": self._doubao_chat,
            "moonshot": self._moonshot_chat,
            "ollama": self._ollama_chat,
        }
        # 客户端缓存，避免重复创建
        self._client_cache: Dict[str, Any] = {}
        self._cache_lock = asyncio.Lock()
        
        logger.info("LLMService 初始化完成")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        """非流式生成"""
        provider = self._get_provider(model)
        
        if provider in self.providers:
            return await self.providers[provider](messages, model, **kwargs)
        
        return await self._openai_chat(messages, model, **kwargs)

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        should_stop: Optional[callable] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        流式生成内容
        
        Args:
            messages: 消息列表
            model: 模型名称
            should_stop: 停止检查函数
            **kwargs: 其他参数
        """
        provider = self._get_provider(model)
        
        if provider == "openai":
            async for chunk in self._openai_chat_stream(messages, model, should_stop, **kwargs):
                yield chunk
        else:
            # 其他提供商先完整生成再分段返回
            content = await self.generate(messages, model, **kwargs)
            for char in content:
                if should_stop and should_stop():
                    logger.info("流式生成被中断")
                    break
                yield StreamChunk(content=char)

    def _get_provider(self, model: Optional[str]) -> str:
        """根据模型名称获取提供商"""
        if not model:
            return settings.DEFAULT_LLM_PROVIDER
        
        model_lower = model.lower()
        
        if "gpt" in model_lower:
            return "openai"
        elif "claude" in model_lower:
            return "anthropic"
        elif "qwen" in model_lower:
            return "qwen"
        elif "doubao" in model_lower:
            return "doubao"
        elif "moonshot" in model_lower or "kim" in model_lower:
            return "moonshot"
        elif "llama" in model_lower or "mistral" in model_lower:
            return "ollama"
        
        return settings.DEFAULT_LLM_PROVIDER

    async def _get_openai_client(self):
        """获取或创建 OpenAI 客户端（带缓存）"""
        cache_key = "openai"
        
        if cache_key in self._client_cache:
            return self._client_cache[cache_key]
        
        async with self._cache_lock:
            if cache_key in self._client_cache:
                return self._client_cache[cache_key]
            
            try:
                from openai import AsyncOpenAI
                
                client = AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY"),
                    base_url=settings.OPENAI_BASE_URL,
                )
                self._client_cache[cache_key] = client
                logger.info("OpenAI 客户端创建成功")
                return client
            except Exception as e:
                logger.error(f"创建 OpenAI 客户端失败: {e}")
                raise

    async def _openai_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        """OpenAI 非流式聊天"""
        try:
            client = await self._get_openai_client()
            
            response = await client.chat.completions.create(
                model=model or "gpt-3.5-turbo",
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI 聊天错误: {e}")
            return f"Error: {str(e)}"

    async def _openai_chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        should_stop: Optional[callable] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        """OpenAI 流式响应"""
        try:
            client = await self._get_openai_client()
            
            stream = await client.chat.completions.create(
                model=model or "gpt-3.5-turbo",
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
                stream=True,
            )
            
            async for chunk in stream:
                # 检查是否需要停止
                if should_stop and should_stop():
                    logger.info("OpenAI 流被中断")
                    yield StreamChunk(is_finished=True)
                    break
                
                if chunk.choices[0].delta.content:
                    yield StreamChunk(content=chunk.choices[0].delta.content)
                    
        except Exception as e:
            logger.error(f"OpenAI 流式聊天错误: {e}")
            yield StreamChunk(error=str(e), is_finished=True)

    async def _anthropic_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        return "Anthropic API not configured. Please add ANTHROPIC_API_KEY to .env"

    async def _qwen_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        return "Qwen API not configured. Please add QWEN_API_KEY to .env"

    async def _doubao_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        return "Doubao API not configured. Please add DOUBAO_API_KEY to .env"

    async def _moonshot_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        return "Moonshot API not configured. Please add MOONSHOT_API_KEY to .env"

    async def _ollama_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": model or "llama2",
                        "messages": messages,
                        "stream": False,
                    },
                    timeout=60.0,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("message", {}).get("content", "")
                else:
                    return f"Ollama Error: {response.status_code}"
        except Exception as e:
            return f"Ollama not available: {str(e)}"

    def clear_cache(self):
        """清除客户端缓存"""
        self._client_cache.clear()
        logger.info("LLMService 缓存已清除")


# 全局单例实例（使用延迟初始化）
_llm_service_instance = ThreadSafeLazyInitializer(lambda: LLMService())


def get_llm_service() -> LLMService:
    """获取 LLMService 单例"""
    return _llm_service_instance.get()
