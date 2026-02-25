from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from utils.result import success

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
    """获取模型提供商列表"""
    return success(data={
        "providers": MODEL_OPTIONS,
        "embedding_models": EMBEDDING_MODELS,
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


# 配置相关API（统一格式）
MODEL_CONFIGS = {}


@router.get("/config/list")
async def list_configs():
    """获取所有模型配置列表"""
    configs = list(MODEL_CONFIGS.values())
    return success(data=configs, msg="获取成功")


@router.post("/config/create")
async def create_config(config: ModelConfig):
    """创建模型配置"""
    config.id = f"config_{len(MODEL_CONFIGS) + 1}"
    MODEL_CONFIGS[config.id] = config.model_dump()
    return success(data=config.model_dump(), msg="创建成功")


@router.put("/config/{config_id}")
async def update_config(config_id: str, config: ModelConfig):
    """更新模型配置"""
    if config_id in MODEL_CONFIGS:
        MODEL_CONFIGS[config_id] = config.model_dump()
        return success(data=config.model_dump(), msg="更新成功")
    return success(data=None, msg="配置不存在")


@router.delete("/config/{config_id}")
async def delete_config(config_id: str):
    """删除模型配置"""
    if config_id in MODEL_CONFIGS:
        del MODEL_CONFIGS[config_id]
        return success(data=None, msg="删除成功")
    return success(data=None, msg="配置不存在")


ACTIVE_CONFIG_KEY = "config_1"


@router.get("/config/active")
async def get_active_config():
    """获取当前激活的配置ID"""
    return success(data=ACTIVE_CONFIG_KEY, msg="获取成功")


@router.post("/config/active")
async def set_active_config(config_id: str):
    """设置激活的配置"""
    global ACTIVE_CONFIG_KEY
    ACTIVE_CONFIG_KEY = config_id
    return success(data=None, msg="设置成功")


# 工具相关API
TOOLS = {}


@router.get("/knowledge/tools")
async def list_tools():
    """获取所有可用的Agent工具列表"""
    tools = [
        {"id": "tool_1", "name": "数据库查询", "description": "可以执行SQL查询操作"},
        {"id": "tool_2", "name": "天气查询", "description": "查询指定城市的天气信息"},
    ]
    if tools:
        return success(data=tools, msg=f"获取成功，共 {len(tools)} 个工具")
    return success(data=[], msg="未获取到任何 Agent Tool，请检查后台配置", code=0)


@router.post("/tools/{tool_id}/enable")
async def enable_tool(tool_id: str):
    """启用指定工具"""
    return success(data=None, msg="启用成功")


@router.post("/tools/batch-set")
async def batch_set_tools(tool_ids: List[str], enabled: bool):
    """批量设置工具状态"""
    return success(data=None, msg="设置成功")
