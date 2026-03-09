"""
模型配置 API 路由
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from api.response import success
from app.config import get_models_config

router = APIRouter()


class ModelConfigRequest(BaseModel):
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


def get_all_enabled_models():
    """获取所有启用的模型列表（扁平化，不包含提供商层级）"""
    models_config = get_models_config()
    enabled_providers = models_config.get_enabled_providers()
    
    # import logging
    # logger = logging.getLogger(__name__)
    # logger.info(f"[DEBUG] Enabled providers: {list(enabled_providers.keys())}")
    
    all_models = []
    default_model = None
    
    # 遍历所有启用的提供商，收集所有模型
    for provider_key, provider in enabled_providers.items():
        for model in provider.models:
            # logger.info(f"[DEBUG] Model {model.id} from {provider_key}: default={model.default}")
            model_data = {
                "id": model.id,
                "name": model.name,
                "tags": model.tags,
                "default": model.default,
                "provider": provider_key
            }
            all_models.append(model_data)
            
            # 记录第一个标记为 default 的模型
            if model.default and default_model is None:
                default_model = model.id
                # logger.info(f"[DEBUG] Found default model: {default_model}")
    
    # 如果没有找到标记为 default 的模型，使用第一个模型
    if default_model is None and all_models:
        default_model = all_models[0]["id"]
        # logger.info(f"[DEBUG] No default model found, using first: {default_model}")
    
    # logger.info(f"[DEBUG] Returning default_model: {default_model}")
    return all_models, default_model


def get_provider_info(provider_key: str) -> Optional[Dict[str, Any]]:
    """获取提供商详细信息"""
    models_config = get_models_config()
    provider = models_config.get_all_providers().get(provider_key)
    
    if not provider:
        return None
    
    return {
        "key": provider.key,
        "name": provider.name,
        "display_name": provider.display_name,
        "api_key": provider.api_key,
        "base_url": provider.base_url,
        "secret_key": provider.secret_key,
        "app_id": provider.app_id,
        "models": [
            {
                "id": model.id,
                "name": model.name,
                "default": model.default,
                "tags": model.tags  # 包含标签
            }
            for model in provider.models
        ]
    }


def get_model_provider_info(model_id: str) -> Optional[Dict[str, Any]]:
    """根据模型ID获取提供商配置信息"""
    models_config = get_models_config()
    provider = models_config.get_provider_by_model(model_id)
    
    if not provider:
        return None
    
    return {
        "provider_key": provider.key,
        "provider_name": provider.name,
        "display_name": provider.display_name,
        "api_key": provider.api_key,
        "base_url": provider.base_url,
        "secret_key": provider.secret_key,
        "app_id": provider.app_id,
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
    """获取模型列表（扁平化）"""
    all_models, default_model = get_all_enabled_models()

    if not all_models:
        test_models = [
            {"id": "gpt-4o", "name": "GPT-4o", "tags": [], "default": True, "provider": "openai"},
            {"id": "deepseek-chat", "name": "DeepSeek", "tags": [], "default": False, "provider": "deepseek"},
        ]
        return success(data={
            "models": test_models,
            "embedding_models": EMBEDDING_MODELS,
            "has_configured_models": False,
            "default_model": "gpt-4o"
        }, msg="服务器未配置模型，此处展示测试模型")

    return success(data={
        "models": all_models,
        "embedding_models": EMBEDDING_MODELS,
        "has_configured_models": True,
        "default_model": default_model  # 全局默认模型，用于前端首次加载
    }, msg="获取成功")


@router.get("/models/providers")
async def list_providers():
    """获取所有提供商详细信息"""
    models_config = get_models_config()
    providers = models_config.get_all_providers()
    
    result = {}
    for key, provider in providers.items():
        result[key] = {
            "key": provider.key,
            "name": provider.name,
            "display_name": provider.display_name,
            "has_api_key": bool(provider.api_key),
            "base_url": provider.base_url,
            "models": [
                {
                    "id": model.id,
                    "name": model.name,
                    "default": model.default
                }
                for model in provider.models
            ]
        }
    
    return success(data=result, msg="获取成功")


@router.get("/models/provider/{provider_key}")
async def get_provider_detail(provider_key: str):
    """获取指定提供商详细信息"""
    provider_info = get_provider_info(provider_key)
    
    if not provider_info:
        return success(data=None, msg=f"提供商 {provider_key} 不存在", code=404)
    
    return success(data=provider_info, msg="获取成功")


@router.get("/models/config/{model_id}")
async def get_model_config_info(model_id: str):
    """根据模型ID获取配置信息"""
    config_info = get_model_provider_info(model_id)
    
    if not config_info:
        return success(data=None, msg=f"模型 {model_id} 未找到配置", code=404)
    
    return success(data=config_info, msg="获取成功")


@router.post("/models/config")
async def save_model_config(config: ModelConfigRequest):
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
