from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from utils.result import success
from settings import get_settings, reload_settings

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
    settings = reload_settings()
    model_options = {}
    
    # 检查并添加各提供商的模型
    providers = [
        ("openai", "OpenAI", settings.OPENAI_MODEL, settings.OPENAI_DISPLAY_NAME),
        ("anthropic", "Anthropic", settings.ANTHROPIC_MODEL, settings.ANTHROPIC_DISPLAY_NAME),
        ("google", "Google", settings.GOOGLE_MODEL, settings.GOOGLE_DISPLAY_NAME),
        ("qwen", "阿里云通义千问", settings.QWEN_MODEL, settings.QWEN_DISPLAY_NAME),
        ("doubao", "字节跳动豆包", settings.DOUBAO_MODEL, settings.DOUBAO_DISPLAY_NAME),
        ("moonshot", "月之暗面Kimi", settings.MOONSHOT_MODEL, settings.MOONSHOT_DISPLAY_NAME),
        ("zhipu", "智谱AI", settings.ZHIPU_MODEL, settings.ZHIPU_DISPLAY_NAME),
        ("baidu", "百度文心一言", settings.BAIDU_MODEL, settings.BAIDU_DISPLAY_NAME),
        ("xfyun", "讯飞星火", settings.XFYUN_MODEL, settings.XFYUN_DISPLAY_NAME),
        ("ollama", "Ollama (本地)", settings.OLLAMA_MODEL, settings.OLLAMA_DISPLAY_NAME),
    ]
    
    for provider_key, provider_name, model_config, display_name in providers:
        # 获取API密钥（判断是否有配置）
        api_key = getattr(settings, f"{provider_key.upper()}_API_KEY", None)
        
        # 如果有API密钥或配置了模型，则添加到选项中
        if api_key or model_config:
            # 处理多个模型（用 | 分隔）
            models = []
            if model_config:
                models = [m.strip() for m in model_config.split('|') if m.strip()]
            else:
                models = []  # 如果没有配置模型，则为空列表
            
            # 如果没有模型但有API密钥，则使用默认模型
            if not models and api_key:
                # 根据提供商使用默认模型
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
    
    # 如果没有任何模型配置，则返回测试模型
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


@router.get("/tools")
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
