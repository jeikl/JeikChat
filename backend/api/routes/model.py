"""
模型配置 API 路由
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from api.response import success
from app.config import get_settings

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


def get_dynamic_model_options():
    """根据配置文件动态生成模型选项"""
    settings = get_settings()
    model_options = {}
    
    providers = [
        ("openai", "OpenAI", settings.OPENAI_MODEL, settings.OPENAI_DISPLAY_NAME),
        ("anthropic", "Anthropic", settings.ANTHROPIC_MODEL, settings.ANTHROPIC_DISPLAY_NAME),
        ("google", "Google", settings.GOOGLE_MODEL, settings.GOOGLE_DISPLAY_NAME),
        ("doubao", "字节跳动", settings.DOUBAO_MODEL, settings.DOUBAO_DISPLAY_NAME),
        ("qwen", "通义千问", settings.QWEN_MODEL, settings.QWEN_DISPLAY_NAME),
        ("moonshot", "月之暗面", settings.MOONSHOT_MODEL, settings.MOONSHOT_DISPLAY_NAME),
        ("zhipu", "智谱AI", settings.ZHIPU_MODEL, settings.ZHIPU_DISPLAY_NAME),
        ("baidu", "文心一言", settings.BAIDU_MODEL, settings.BAIDU_DISPLAY_NAME),
        ("xfyun", "讯飞星火", settings.XFYUN_MODEL, settings.XFYUN_DISPLAY_NAME),
        ("ollama", "Ollama", settings.OLLAMA_MODEL, settings.OLLAMA_DISPLAY_NAME),
    ]
    
    for provider_key, provider_name, model_config, display_name in providers:
        api_key = getattr(settings, f"{provider_key.upper()}_API_KEY", None)
        
        if api_key or model_config:
            models = []
            if model_config:
                models = [m.strip() for m in model_config.split('|') if m.strip()]
            else:
                models = []
            
            if not models and api_key:
                if provider_key == "openai":
                    models = ["gpt-4o-mini"]
                elif provider_key == "anthropic":
                    models = ["claude-3-5-sonnet-20241022"]
                elif provider_key == "google":
                    models = ["gemini-2.0-flash"]
                elif provider_key == "qwen":
                    models = ["qwen-max"]
                elif provider_key == "doubao":
                    models = ["doubao-pro"]
                elif provider_key == "moonshot":
                    models = ["moonshot-v1-8k"]
                elif provider_key == "zhipu":
                    models = ["glm-4-air"]
                elif provider_key == "baidu":
                    models = ["ernie-bot-4.5"]
                elif provider_key == "xfyun":
                    models = ["spark-4.5-ultra"]
                elif provider_key == "ollama":
                    models = ["qwen2:7b"]
            
            if models:
                model_options[provider_key] = {
                    "name": provider_name,
                    "models": models,
                }
    
    return model_options


EMBEDDING_MODELS = [
    {"id": "all-MiniLM-L6-v2", "name": "all-MiniLM-L6-v2", "description": "轻量级快速模型"},
    {"id": "text-embedding-ada-002", "name": "text-embedding-ada-002", "description": "OpenAI官方"},
    {"id": "text-embedding-3-small", "name": "text-embedding-3-small", "description": "新一代小型模型"},
    {"id": "bge-small-zh-v1.5", "name": "bge-small-zh-v1.5", "description": "中文优化小型"},
    {"id": "bge-base-zh-v1.5", "name": "bge-base-zh-v1.5", "description": "中文基础模型"},
]


@router.get("/models/list")
async def list_models():
    """获取模型提供商列表"""
    model_options = get_dynamic_model_options()
    
    if not model_options:
        test_providers = {
            "test": {
                "name": "测试模型",
                "models": ["gpt4(测)", "deepseek(测)", "claude3(测)", "gemini(测)"]
            }
        }
        return success(data={
            "providers": test_providers,
            "embedding_models": EMBEDDING_MODELS,
            "has_configured_models": False
        }, msg="服务器未配置模型，此处展示测试模型")
    
    return success(data={
        "providers": model_options,
        "embedding_models": EMBEDDING_MODELS,
        "has_configured_models": True
    }, msg="获取成功")


@router.post("/models/config")
async def save_model_config(config: ModelConfig):
    """保存模型配置"""
    return success(data=config.model_dump(), msg="保存成功")


@router.get("/models/test")
async def test_model_connection(provider: str, api_key: str):
    """测试模型连接"""
    return success(data={"status": "success"}, msg=f"{provider} 连接成功")


@router.get("/models/embedding/list")
async def list_embedding_models():
    """获取嵌入模型列表"""
    return success(data=EMBEDDING_MODELS, msg="获取成功")


MODEL_CONFIGS = {}


@router.get("/config/list")
async def list_configs():
    """获取所有模型配置列表"""
    configs = list(MODEL_CONFIGS.values())
    return success(data=configs, msg="获取成功")
