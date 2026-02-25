from typing import List, Dict, Optional, Any
import os
import json

from init import get_settings

settings = get_settings()


class LLMService:
    def __init__(self):
        self.providers = {
            "openai": self._openai_chat,
            "anthropic": self._anthropic_chat,
            "qwen": self._qwen_chat,
            "doubao": self._doubao_chat,
            "moonshot": self._moonshot_chat,
            "ollama": self._ollama_chat,
        }

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        provider = self._get_provider(model)
        
        if provider in self.providers:
            return await self.providers[provider](messages, model, **kwargs)
        
        return await self._openai_chat(messages, model, **kwargs)

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ):
        """流式生成内容"""
        provider = self._get_provider(model)
        
        if provider == "openai":
            async for chunk in self._openai_chat_stream(messages, model, **kwargs):
                yield chunk
        else:
            content = await self.generate(messages, model, **kwargs)
            for char in content:
                yield char

    def _get_provider(self, model: Optional[str]) -> str:
        if not model:
            return settings.DEFAULT_LLM_PROVIDER
        
        if "gpt" in model.lower():
            return "openai"
        elif "claude" in model.lower():
            return "anthropic"
        elif "qwen" in model.lower():
            return "qwen"
        elif "doubao" in model.lower():
            return "doubao"
        elif "moonshot" in model.lower() or "kim" in model.lower():
            return "moonshot"
        elif "llama" in model.lower() or "mistral" in model.lower():
            return "ollama"
        
        return settings.DEFAULT_LLM_PROVIDER

    async def _openai_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY"),
                base_url=settings.OPENAI_BASE_URL,
            )
            
            response = await client.chat.completions.create(
                model=model or "gpt-3.5-turbo",
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Error: {str(e)}"

    async def _openai_chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ):
        """OpenAI 流式响应"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY"),
                base_url=settings.OPENAI_BASE_URL,
            )
            
            stream = await client.chat.completions.create(
                model=model or "gpt-3.5-turbo",
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {str(e)}"

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
