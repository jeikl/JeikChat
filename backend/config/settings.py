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
        self.JEIKCHAT_DEV_MODE = os.getenv("JEIKCHAT_DEV_MODE", "true").lower() == "true"
        
        self.BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
        self.BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000") or "8000")
        self.FRONTEND_HOST = os.getenv("VITE_FRONTEND_HOST", "::")
        self.FRONTEND_PORT = int(os.getenv("VITE_FRONTEND_PORT", "5173") or "5173")
        
        self.APP_NAME = os.getenv("APP_NAME", "")
        self.APP_VERSION = os.getenv("APP_VERSION", "")
        
        # 数据库配置
        self.DB_URL = os.getenv("DB_URL", "postgresql://root:anhuang520@pan.junv.top:5432/postgres?sslmode=disable")
        
        self.VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "")
        
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "104857600") or "104857600")
        
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000") or "1000")
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200") or "200")
        
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")
        
        # 加载 YAML 配置
        self._load_yaml_config()
    
    def _load_yaml_config(self):
        """加载 app_config.yaml 配置"""
        config_path = PROJECT_ROOT / "backend" / "config" / "app_config.yaml"
        if not config_path.exists():
            # 尝试回退到旧的 app_info.yaml (如果存在)
            config_path = PROJECT_ROOT / "backend" / "config" / "app_info.yaml"
            
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                    
                # 应用信息
                if "app_info" in config:
                    self.APP_INFO = config["app_info"]
                    # 如果环境变量没设置，尝试从 yaml 覆盖 APP_NAME 等
                    if not self.APP_NAME:
                        self.APP_NAME = config["app_info"].get("name", "")
                    if not self.APP_VERSION:
                        self.APP_VERSION = config["app_info"].get("version", "")
                
                # 数据库配置 (优先使用环境变量，其次使用 YAML)
                if "database" in config and config["database"].get("url"):
                    # 只有当环境变量 DB_URL 是默认值或者未设置时，才考虑使用 YAML
                    # 这里逻辑是：DB_URL 已经在 _load_from_env 里有了默认值，
                    # 我们可以简单地覆盖它，或者让 YAML 优先级低于 .env
                    # 通常 .env 用于本地覆盖，YAML 用于默认配置。
                    # 但 Settings 类初始化时已经读了 os.getenv。
                    # 如果 os.getenv 返回的是我们硬编码的默认值，我们可能无法区分。
                    # 简单策略：如果 .env 里显式设置了（os.environ中有），就用 .env；否则用 YAML。
                    if "DB_URL" not in os.environ:
                        self.DB_URL = config["database"]["url"]
                        
                # 存储配置
                if "storage" in config:
                    self.STORAGE = config["storage"]
                else:
                    self.STORAGE = {}
                    
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        else:
            self.APP_INFO = {}
            self.STORAGE = {}
    
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
        config.backend_host = os.getenv("BACKEND_HOST", "0.0.0.0")
        config.backend_port = int(os.getenv("BACKEND_PORT", "8000") or "8000")
        config.frontend_host = os.getenv("VITE_FRONTEND_HOST", "::")
        config.frontend_port = int(os.getenv("VITE_FRONTEND_PORT", "5173") or "5173")
        config.dev_mode = os.getenv("JEIKCHAT_DEV_MODE", "true").lower() == "true"
        config.environment = os.getenv("AICHAT_ENVIRONMENT", "dev") or "dev"
        return config
    
    @property
    def backend_url(self) -> str:
        host = "localhost" if self.backend_host == "0.0.0.0" else self.backend_host
        return f"http://{host}:{self.backend_port}"
    
    @property
    def frontend_url(self) -> str:
        host = "localhost" if self.frontend_host in ["::", "0.0.0.0"] else self.frontend_host
        return f"http://{host}:{self.frontend_port}"
    
    @property
    def api_docs_url(self) -> str:
        return f"{self.backend_url}/docs"


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
        config_path = PROJECT_ROOT / "backend" / "config" / "models.yaml"
        app_config_path = PROJECT_ROOT / "backend" / "config" / "app_config.yaml"
        app_info_path = PROJECT_ROOT / "backend" / "config" / "app_info.yaml"
        
        # 兼容旧路径
        if not config_path.exists():
            old_config_path = PROJECT_ROOT / "backend" / "app" / "models_config.yaml"
            if old_config_path.exists():
                config_path = old_config_path
                
        if not config_path.exists():
            print(f"[ModelsConfig] 配置文件不存在: {config_path}")
            self._config_data = {"providers": {}, "model_mappings": {}}
        else:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    raw_config = yaml.safe_load(f)
                
                # 处理环境变量替换
                self._config_data = self._process_env_vars(raw_config)
                print(f"[ModelsConfig] 成功加载模型配置，共 {len(self._config_data.get('providers', {}))} 个提供商")
                
            except Exception as e:
                print(f"[ModelsConfig] 加载配置文件失败: {e}")
                self._config_data = {"providers": {}, "model_mappings": {}}
                
        # 加载应用信息配置 (优先使用 app_config.yaml)
        self._app_info = {}
        target_app_config_path = app_config_path if app_config_path.exists() else app_info_path
        
        if target_app_config_path.exists():
            try:
                with open(target_app_config_path, 'r', encoding='utf-8') as f:
                    app_config = yaml.safe_load(f)
                    self._app_info = app_config.get("app_info", {})
                print(f"[AppInfo] 成功加载应用信息配置: {target_app_config_path}")
            except Exception as e:
                print(f"[AppInfo] 加载应用信息配置失败: {e}")
    
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
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """获取默认的 Embedding 模型配置"""
        embeddings_config = self._config_data.get("embeddings", {})
        default_provider_key = embeddings_config.get("default_provider", "modelscope")
        providers = embeddings_config.get("providers", {})
        
        provider_info = providers.get(default_provider_key, {})
        
        # 查找默认模型
        models = provider_info.get("models", [])
        default_model = None
        if models:
            default_model = next((m.get("id") for m in models if m.get("default")), models[0].get("id"))
            
        return {
            "provider": default_provider_key,
            "api_key": provider_info.get("api_key", ""),
            "base_url": provider_info.get("base_url", ""),
            "model": default_model
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


    def get_app_info(self) -> Dict[str, Any]:
        """获取应用信息"""
        return self._app_info

# 全局模型配置管理器实例
_models_config_manager = None

def get_models_config() -> ModelsConfigManager:
    """获取模型配置管理器实例"""
    global _models_config_manager
    if _models_config_manager is None:
        _models_config_manager = ModelsConfigManager()
    return _models_config_manager
