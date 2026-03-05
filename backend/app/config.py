"""
JeikChat 统一配置管理
所有配置从 .env 文件加载
"""

import os
from pathlib import Path
from typing import Any
from functools import lru_cache


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
