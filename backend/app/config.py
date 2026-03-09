"""
JeikChat 统一配置管理
所有配置从 .env 文件加载
"""

import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from functools import lru_cache
from dataclasses import dataclass, field


PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_env_file_path():
    """获取环境配置文件路径"""
    environment = os.environ.get("AICHAT_ENVIRONMENT", "dev")
    if environment == "local":
        return str(PROJECT_ROOT / ".env.local")
    return str(PROJECT_ROOT / ".env")


def _init_env():
    """模块初始化时加载环境变量"""
    from dotenv import load_dotenv
    env_file = get_env_file_path()
    if os.path.exists(env_file):
        load_dotenv(env_file)

_init_env()


def load_env_file():
    """加载环境变量文件"""
    env_file = get_env_file_path()
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)


class Settings:
    """配置类 - 所有配置从环境变量/.env文件加载"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_from_env()
            Settings._initialized = True
    
    def _load_from_env(self):
        """从环境变量加载所有配置"""
        load_env_file()
        
        self.AICHAT_ENVIRONMENT = os.getenv("AICHAT_ENVIRONMENT", "dev")
        
        self.JEIKCHAT_BACKEND_HOST = os.getenv("JEIKCHAT_BACKEND_HOST", "")
        self.JEIKCHAT_BACKEND_PORT = int(os.getenv("JEIKCHAT_BACKEND_PORT", "8000") or "8000")
        self.JEIKCHAT_FRONTEND_HOST = os.getenv("JEIKCHAT_FRONTEND_HOST", "")
        self.JEIKCHAT_FRONTEND_PORT = int(os.getenv("JEIKCHAT_FRONTEND_PORT", "5173") or "5173")
        self.JEIKCHAT_API_DOCS_HOST = os.getenv("JEIKCHAT_API_DOCS_HOST", "")
        self.JEIKCHAT_API_DOCS_PORT = int(os.getenv("JEIKCHAT_API_DOCS_PORT", "8000") or "8000")
        self.JEIKCHAT_DEV_MODE = os.getenv("JEIKCHAT_DEV_MODE", "true").lower() == "true"
        
        self.APP_NAME = os.getenv("APP_NAME", "")
        self.APP_VERSION = os.getenv("APP_VERSION", "")
        self.DATABASE_URL = os.getenv("DATABASE_URL", "")
        self.DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "")
        
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")
        self.OPENAI_DISPLAY_NAME = os.getenv("OPENAI_DISPLAY_NAME", "")
        
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "")
        self.ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "")
        self.ANTHROPIC_DISPLAY_NAME = os.getenv("ANTHROPIC_DISPLAY_NAME", "")
        
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        self.GOOGLE_BASE_URL = os.getenv("GOOGLE_BASE_URL", "")
        self.GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "")
        self.GOOGLE_DISPLAY_NAME = os.getenv("GOOGLE_DISPLAY_NAME", "")
        
        self.QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
        self.QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "")
        self.QWEN_MODEL = os.getenv("QWEN_MODEL", "")
        self.QWEN_DISPLAY_NAME = os.getenv("QWEN_DISPLAY_NAME", "")
        
        self.DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
        self.DOUBAO_BASE_URL = os.getenv("DOUBAO_BASE_URL", "")
        self.DOUBAO_MODEL = os.getenv("DOUBAO_MODEL", "")
        self.DOUBAO_DISPLAY_NAME = os.getenv("DOUBAO_DISPLAY_NAME", "")
        
        self.MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
        self.MOONSHOT_BASE_URL = os.getenv("MOONSHOT_BASE_URL", "")
        self.MOONSHOT_MODEL = os.getenv("MOONSHOT_MODEL", "")
        self.MOONSHOT_DISPLAY_NAME = os.getenv("MOONSHOT_DISPLAY_NAME", "")
        
        self.ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
        self.ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL", "")
        self.ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "")
        self.ZHIPU_DISPLAY_NAME = os.getenv("ZHIPU_DISPLAY_NAME", "")
        
        self.BAIDU_API_KEY = os.getenv("BAIDU_API_KEY", "")
        self.BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY", "")
        self.BAIDU_BASE_URL = os.getenv("BAIDU_BASE_URL", "")
        self.BAIDU_MODEL = os.getenv("BAIDU_MODEL", "")
        self.BAIDU_DISPLAY_NAME = os.getenv("BAIDU_DISPLAY_NAME", "")
        
        self.XFYUN_API_KEY = os.getenv("XFYUN_API_KEY", "")
        self.XFYUN_SECRET_KEY = os.getenv("XFYUN_SECRET_KEY", "")
        self.XFYUN_APP_ID = os.getenv("XFYUN_APP_ID", "")
        self.XFYUN_BASE_URL = os.getenv("XFYUN_BASE_URL", "")
        self.XFYUN_MODEL = os.getenv("XFYUN_MODEL", "")
        self.XFYUN_DISPLAY_NAME = os.getenv("XFYUN_DISPLAY_NAME", "")
        
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")
        self.OLLAMA_DISPLAY_NAME = os.getenv("OLLAMA_DISPLAY_NAME", "")
        
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "")
        self.VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "")
        
        self.UPLOAD_DIR = os.getenv("UPLOAD_DIR", "")
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "104857600") or "104857600")
        
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000") or "1000")
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200") or "200")
        
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")
    
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)
    
    def __getattr__(self, name: str) -> Any:
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return None


class StartConfig:
    """启动配置类"""
    
    @classmethod
    def from_env(cls) -> "StartConfig":
        load_env_file()
        
        config = cls()
        config.backend_host = os.getenv("JEIKCHAT_BACKEND_HOST", "::") or "::"
        config.backend_port = int(os.getenv("JEIKCHAT_BACKEND_PORT", "8000") or "8000")
        config.frontend_host = os.getenv("VITE_FRONTEND_HOST") or os.getenv("JEIKCHAT_FRONTEND_HOST", "::") or "::"
        config.frontend_port = int(os.getenv("VITE_FRONTEND_PORT") or os.getenv("JEIKCHAT_FRONTEND_PORT", "5173") or "5173")
        config.dev_mode = os.getenv("JEIKCHAT_DEV_MODE", "true").lower() == "true"
        config.environment = os.getenv("AICHAT_ENVIRONMENT", "dev") or "dev"
        config.api_docs_host = os.getenv("JEIKCHAT_API_DOCS_HOST", "::") or "::"
        config.api_docs_port = int(os.getenv("JEIKCHAT_API_DOCS_PORT", "8000") or "8000")
        return config
    
    @property
    def backend_url(self) -> str:
        return f"http://{self.backend_host}:{self.backend_port}"
    
    @property
    def frontend_url(self) -> str:
        return f"http://{self.frontend_host}:{self.frontend_port}"
    
    @property
    def api_docs_url(self) -> str:
        return f"http://{self.api_docs_host}:{self.api_docs_port}/docs"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def get_start_config() -> StartConfig:
    return StartConfig.from_env()


# ==================== 模型配置管理 ====================

@dataclass
class ModelConfig:
    """单个模型配置"""
    id: str
    provider: str
    tags: List[str] = field(default_factory=list)
    default: bool = False
    enabled: bool = True
    
    @property
    def name(self) -> str:
        """返回模型ID作为名称"""
        return self.id


@dataclass
class ProviderConfig:
    """提供商配置"""
    key: str
    name: str
    api_key: str = ""
    base_url: str = ""
    display_name: str = ""
    secret_key: str = ""
    app_id: str = ""
    enabled: bool = True
    models: List[ModelConfig] = field(default_factory=list)


class ModelsConfigManager:
    """模型配置管理器 - 从YAML文件加载配置"""
    
    _instance = None
    _initialized = False
    _config_data = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_config()
            ModelsConfigManager._initialized = True
    
    def _load_config(self):
        """加载YAML配置文件"""
        config_path = PROJECT_ROOT / "backend" / "app" / "models_config.yaml"
        
        if not config_path.exists():
            print(f"[ModelsConfig] 配置文件不存在: {config_path}")
            self._config_data = {"providers": {}, "model_mappings": {}}
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)
            
            # 处理环境变量替换
            self._config_data = self._process_env_vars(raw_config)
            print(f"[ModelsConfig] 成功加载模型配置，共 {len(self._config_data.get('providers', {}))} 个提供商")
            
        except Exception as e:
            print(f"[ModelsConfig] 加载配置文件失败: {e}")
            self._config_data = {"providers": {}, "model_mappings": {}}
    
    def _process_env_vars(self, config: Dict) -> Dict:
        """处理配置中的环境变量引用"""
        env_pattern = re.compile(r'\$\{([^}]+)\}')
        
        def replace_env_vars(value):
            if isinstance(value, str):
                def replace_match(match):
                    env_expr = match.group(1)
                    # 处理默认值语法: ${VAR:-default}
                    if ':-' in env_expr:
                        var_name, default = env_expr.split(':-', 1)
                        return os.getenv(var_name, default)
                    return os.getenv(env_expr, '')
                return env_pattern.sub(replace_match, value)
            elif isinstance(value, dict):
                return {k: replace_env_vars(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_env_vars(item) for item in value]
            return value
        
        return replace_env_vars(config)
    
    def get_provider_by_model(self, model_id: str) -> Optional[ProviderConfig]:
        """根据模型ID获取提供商配置"""
        providers = self._config_data.get("providers", {})
        model_mappings = self._config_data.get("model_mappings", {})
        
        # 1. 直接匹配模型ID
        for provider_key, provider_data in providers.items():
            for model in provider_data.get("models", []):
                if model.get("id") == model_id:
                    return self._build_provider_config(provider_key, provider_data)
        
        # 2. 通过映射表查找
        for mapping_key, provider_key in model_mappings.items():
            if mapping_key.lower() in model_id.lower():
                provider_data = providers.get(provider_key)
                if provider_data:
                    return self._build_provider_config(provider_key, provider_data)
        
        # 3. 根据模型名称前缀推断
        provider_key = self._infer_provider_from_model(model_id)
        if provider_key and provider_key in providers:
            return self._build_provider_config(provider_key, providers[provider_key])
        
        return None
    
    def _infer_provider_from_model(self, model_id: str) -> Optional[str]:
        """从模型ID推断提供商"""
        model_lower = model_id.lower()
        
        # 根据模型名称特征推断
        if "gpt" in model_lower or model_lower.startswith("text-"):
            return "openai"
        elif "claude" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower:
            return "google"
        elif "deepseek" in model_lower or "doubao" in model_lower or "seed" in model_lower:
            return "doubao"
        elif "qwen" in model_lower:
            return "qwen"
        elif "moonshot" in model_lower:
            return "moonshot"
        elif "glm" in model_lower:
            return "zhipu"
        elif "ernie" in model_lower:
            return "baidu"
        elif "spark" in model_lower:
            return "xfyun"
        
        return None
    
    def _build_provider_config(self, key: str, data: Dict) -> ProviderConfig:
        """构建提供商配置对象"""
        # 提供商级别的enable，默认为True
        provider_enabled = data.get("enable", True)
        
        # 如果提供商被禁用，则所有模型都不启用
        if not provider_enabled:
            models = []
        else:
            # 只包含启用的模型
            raw_models = [
                m for m in data.get("models", [])
                if m.get("enable", True)  # 只包含启用的模型
            ]
            
            # 处理default逻辑：只有明确标记为default的模型才是默认模型
            # 不再自动将第一个模型设为默认
            models = []
            
            for m in raw_models:
                is_default = m.get("default", False) and not any(
                    model.default for model in models
                )
                
                models.append(ModelConfig(
                    id=m["id"],
                    provider=key,
                    default=is_default,
                    enabled=True,  # 已经过滤过enable了
                    tags=m.get("tags", [])  # 读取标签字段
                ))
        
        return ProviderConfig(
            key=key,
            name=data.get("name", key),
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", ""),
            display_name=data.get("display_name", data.get("name", key)),
            secret_key=data.get("secret_key", ""),
            app_id=data.get("app_id", ""),
            enabled=provider_enabled,
            models=models
        )
    
    def get_all_providers(self) -> Dict[str, ProviderConfig]:
        """获取所有提供商配置（包括禁用的）"""
        providers = self._config_data.get("providers", {})
        return {
            key: self._build_provider_config(key, data)
            for key, data in providers.items()
        }
    
    def get_enabled_providers(self) -> Dict[str, ProviderConfig]:
        """获取已启用的提供商（enable=true且有API Key）"""
        all_providers = self.get_all_providers()
        return {
            key: provider for key, provider in all_providers.items()
            if provider.enabled and provider.api_key
        }
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """获取单个模型配置（只返回启用的模型）"""
        provider = self.get_provider_by_model(model_id)
        # 确保提供商是启用的
        if provider and provider.enabled:
            for model in provider.models:
                if model.id == model_id and model.enabled:
                    return model
        return None
    
    def is_model_enabled(self, model_id: str) -> bool:
        """检查模型是否启用"""
        model = self.get_model_config(model_id)
        return model is not None
    
    def reload(self):
        """重新加载配置"""
        self._load_config()


# 全局模型配置管理器实例
_models_config_manager = None

def get_models_config() -> ModelsConfigManager:
    """获取模型配置管理器实例"""
    global _models_config_manager
    if _models_config_manager is None:
        _models_config_manager = ModelsConfigManager()
    return _models_config_manager
