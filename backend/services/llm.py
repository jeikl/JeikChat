"""
LLM 客户端服务
支持多种模型提供商的流式对话
"""

from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import sys
import time
import threading
import asyncio
from typing import Optional, Callable


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"), override=True)

from config.settings import get_models_config
from api.routes.model import get_all_enabled_models

_client_cache = {}
_cache_lock = threading.Lock()
_CACHE_TTL = float('inf')


async def _warmup_all_models():
    """预热所有模型"""
    try:
        all_models_data, _ = get_all_enabled_models()
        if not all_models_data:
            print("⚠️ 未找到模型配置，跳过预热")
            return

        # 直接提取所有模型ID
        all_models = [model["id"] for model in all_models_data]

        if not all_models:
             print("⚠️ 模型列表为空，跳过预热")
             return

        await asyncio.sleep(100)
        print(f"[MODEL] 🚀 开始预热 {len(all_models)} 个大模型客户端...")
        # 遍历每个模型的三种 thinking 状态
        for model in all_models:
            for thinking in ["auto", "deep", "false"]:
                cache_key = _get_cache_key(model, thinking)
                if cache_key in _client_cache:
                    continue
                
                # 预热单个模型
                await asyncio.to_thread(create_client, model, thinking)
                
                # 关键：每次初始化后等待 15 秒
                await asyncio.sleep(200)
        
        print(f"[MODEL]  ✨所有模型预热完成! (共 {len(all_models) * 3} 个组合)")
            
    except Exception as e:
        print(f"❌ 模型预热失败: {e}")


def _get_cache_key(llm: str, thinking: str) -> str:
    return f"{llm}:{thinking}"


def create_client(llm: str, thinking: str = "auto"):
    """
    创建LLM客户端
    根据模型ID从YAML配置中读取对应的API Key和Base URL
    """
    cache_key = _get_cache_key(llm, thinking)
    
    with _cache_lock:
        if cache_key in _client_cache:
            cached_client, cached_time = _client_cache[cache_key]
            if time.time() - cached_time < _CACHE_TTL:
                return cached_client
    
    print(f"预热中 {llm}:{thinking}")
    
    # 从YAML配置中获取模型对应的提供商信息
    models_config = get_models_config()
    provider = models_config.get_provider_by_model(llm)
    
    if not provider:
        raise ValueError(f"未找到模型 {llm} 的配置信息，请检查 models_config.yaml")
    
    api_key = provider.api_key
    base_url = provider.base_url
    
    # 如果配置中没有，尝试从环境变量获取（向后兼容）
    if not api_key:
        # 根据提供商类型获取对应的环境变量
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "doubao": "DOUBAO_API_KEY",
            "qwen": "QWEN_API_KEY",
            "moonshot": "MOONSHOT_API_KEY",
            "zhipu": "ZHIPU_API_KEY",
            "baidu": "BAIDU_API_KEY",
            "xfyun": "XFYUN_API_KEY",
        }
        env_var = env_var_map.get(provider.key)
        if env_var:
            api_key = os.getenv(env_var)
    
    if not base_url:
        env_var_map = {
            "openai": "OPENAI_BASE_URL",
            "anthropic": "ANTHROPIC_BASE_URL",
            "google": "GOOGLE_BASE_URL",
            "doubao": "DOUBAO_BASE_URL",
            "qwen": "QWEN_BASE_URL",
            "moonshot": "MOONSHOT_BASE_URL",
            "zhipu": "ZHIPU_BASE_URL",
            "baidu": "BAIDU_BASE_URL",
            "xfyun": "XFYUN_BASE_URL",
            "ollama": "OLLAMA_BASE_URL",
        }
        env_var = env_var_map.get(provider.key)
        if env_var:
            base_url = os.getenv(env_var)
    
    extra_params = {}
    if thinking == "false":
        extra_params = {
            "enable_thinking": False,
            "thinking": {"type": "disabled"},
        }
    elif thinking == "deep":
        extra_params = {
            "enable_thinking": True,
            "thinking": {"type": "enabled"},
        }
    else:
        extra_params = {
            "enable_thinking": None,
            "thinking": {"type": None},
        }
    
    if "gemini" in llm.lower():
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        client = ChatGoogleGenerativeAI(
            model=llm,
            temperature=1.0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
    # elif "qwen" in llm.lower():
    #         client = ChatTongyi(
    #         model=llm,
    #         api_key=api_key,
    #         streaming=True,
    #         extra_body=extra_params,
    #     )
    else:
        client = ChatDeepSeek(
            model=llm,
            api_key=api_key,
            api_base=base_url,
            streaming=True,
            extra_body=extra_params,
        )

    with _cache_lock:
        _client_cache[cache_key] = (client, time.time())
    print(f"✅ {llm}:{thinking}")
    return client


def clear_client_cache():
    with _cache_lock:
        _client_cache.clear()


def get_model_config(llm: str) -> Optional[dict]:
    """
    获取模型的配置信息
    
    Args:
        llm: 模型ID
        
    Returns:
        包含api_key, base_url等信息的字典，如果未找到则返回None
    """
    models_config = get_models_config()
    provider = models_config.get_provider_by_model(llm)
    
    if not provider:
        return None
    
    return {
        "provider": provider.key,
        "provider_name": provider.name,
        "api_key": provider.api_key,
        "base_url": provider.base_url,
        "secret_key": provider.secret_key,
        "app_id": provider.app_id,
    }
