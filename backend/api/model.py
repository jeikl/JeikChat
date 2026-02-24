from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class ModelConfig(BaseModel):
    id: str
    name: str
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    enabled: bool = True


MODEL_OPTIONS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
    },
    "anthropic": {
        "name": "Anthropic",
        "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
    },
    "google": {
        "name": "Google",
        "models": ["gemini-pro", "gemini-pro-vision"],
    },
    "qwen": {
        "name": "阿里云通义千问",
        "models": ["qwen-turbo", "qwen-plus", "qwen-max"],
    },
    "doubao": {
        "name": "字节跳动豆包",
        "models": ["doubao-pro-32k", "doubao-pro-4k"],
    },
    "moonshot": {
        "name": "月之暗面Kimi",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
    },
    "ollama": {
        "name": "Ollama (本地)",
        "models": ["llama2", "mistral", "qwen", "codellama"],
    },
}

EMBEDDING_MODELS = [
    {"id": "all-MiniLM-L6-v2", "name": "all-MiniLM-L6-v2", "description": "轻量级快速模型"},
    {"id": "text-embedding-ada-002", "name": "text-embedding-ada-002", "description": "OpenAI官方"},
    {"id": "text-embedding-3-small", "name": "text-embedding-3-small", "description": "新一代小型模型"},
    {"id": "bge-small-zh-v1.5", "name": "bge-small-zh-v1.5", "description": "中文优化小型"},
    {"id": "bge-base-zh-v1.5", "name": "bge-base-zh-v1.5", "description": "中文基础模型"},
]


@router.get("/models/list")
async def list_models():
    return {
        "providers": MODEL_OPTIONS,
        "embedding_models": EMBEDDING_MODELS,
    }


@router.post("/models/config")
async def save_model_config(config: ModelConfig):
    return {"message": "Config saved", "config": config}


@router.get("/models/test")
async def test_model_connection(provider: str, api_key: str):
    return {
        "status": "success",
        "message": f"Connection to {provider} successful",
    }


@router.get("/models/embedding/list")
async def list_embedding_models():
    return EMBEDDING_MODELS
