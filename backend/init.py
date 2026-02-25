"""
JeikChat 统一配置管理
所有配置从 .env 文件加载
"""

import os
from pathlib import Path
from typing import Any
from functools import lru_cache


PROJECT_ROOT = Path(__file__).parent.parent


def get_env_file_path():
    """获取环境配置文件路径"""
    environment = os.environ.get("AICHAT_ENVIRONMENT", "dev")
    if environment == "local":
        return str(PROJECT_ROOT / ".env.local")
    return str(PROJECT_ROOT / ".env")


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
        
        # 模式配置
        self.AICHAT_ENVIRONMENT = os.getenv("AICHAT_ENVIRONMENT", "dev")
        
        # 启动配置
        self.JEIKCHAT_BACKEND_HOST = os.getenv("JEIKCHAT_BACKEND_HOST", "")
        self.JEIKCHAT_BACKEND_PORT = int(os.getenv("JEIKCHAT_BACKEND_PORT", "8000") or "8000")
        self.JEIKCHAT_FRONTEND_HOST = os.getenv("JEIKCHAT_FRONTEND_HOST", "")
        self.JEIKCHAT_FRONTEND_PORT = int(os.getenv("JEIKCHAT_FRONTEND_PORT", "5173") or "5173")
        self.JEIKCHAT_API_DOCS_HOST = os.getenv("JEIKCHAT_API_DOCS_HOST", "")
        self.JEIKCHAT_API_DOCS_PORT = int(os.getenv("JEIKCHAT_API_DOCS_PORT", "8000") or "8000")
        self.JEIKCHAT_DEV_MODE = os.getenv("JEIKCHAT_DEV_MODE", "true").lower() == "true"
        
        # 应用配置
        self.APP_NAME = os.getenv("APP_NAME", "")
        self.APP_VERSION = os.getenv("APP_VERSION", "")
        self.DATABASE_URL = os.getenv("DATABASE_URL", "")
        self.DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "")
        
        # OpenAI配置
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")
        self.OPENAI_DISPLAY_NAME = os.getenv("OPENAI_DISPLAY_NAME", "")
        
        # Anthropic配置
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "")
        self.ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "")
        self.ANTHROPIC_DISPLAY_NAME = os.getenv("ANTHROPIC_DISPLAY_NAME", "")
        
        # Google配置
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        self.GOOGLE_BASE_URL = os.getenv("GOOGLE_BASE_URL", "")
        self.GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "")
        self.GOOGLE_DISPLAY_NAME = os.getenv("GOOGLE_DISPLAY_NAME", "")
        
        # 阿里云通义千问配置
        self.QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
        self.QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "")
        self.QWEN_MODEL = os.getenv("QWEN_MODEL", "")
        self.QWEN_DISPLAY_NAME = os.getenv("QWEN_DISPLAY_NAME", "")
        
        # 字节跳动豆包配置
        self.DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
        self.DOUBAO_BASE_URL = os.getenv("DOUBAO_BASE_URL", "")
        self.DOUBAO_MODEL = os.getenv("DOUBAO_MODEL", "")
        self.DOUBAO_DISPLAY_NAME = os.getenv("DOUBAO_DISPLAY_NAME", "")
        
        # 月之暗面Kimi配置
        self.MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
        self.MOONSHOT_BASE_URL = os.getenv("MOONSHOT_BASE_URL", "")
        self.MOONSHOT_MODEL = os.getenv("MOONSHOT_MODEL", "")
        self.MOONSHOT_DISPLAY_NAME = os.getenv("MOONSHOT_DISPLAY_NAME", "")
        
        # 智谱AI配置
        self.ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
        self.ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL", "")
        self.ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "")
        self.ZHIPU_DISPLAY_NAME = os.getenv("ZHIPU_DISPLAY_NAME", "")
        
        # 百度文心一言配置
        self.BAIDU_API_KEY = os.getenv("BAIDU_API_KEY", "")
        self.BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY", "")
        self.BAIDU_BASE_URL = os.getenv("BAIDU_BASE_URL", "")
        self.BAIDU_MODEL = os.getenv("BAIDU_MODEL", "")
        self.BAIDU_DISPLAY_NAME = os.getenv("BAIDU_DISPLAY_NAME", "")
        
        # 讯飞星火配置
        self.XFYUN_API_KEY = os.getenv("XFYUN_API_KEY", "")
        self.XFYUN_SECRET_KEY = os.getenv("XFYUN_SECRET_KEY", "")
        self.XFYUN_APP_ID = os.getenv("XFYUN_APP_ID", "")
        self.XFYUN_BASE_URL = os.getenv("XFYUN_BASE_URL", "")
        self.XFYUN_MODEL = os.getenv("XFYUN_MODEL", "")
        self.XFYUN_DISPLAY_NAME = os.getenv("XFYUN_DISPLAY_NAME", "")
        
        # Ollama本地部署配置
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")
        self.OLLAMA_DISPLAY_NAME = os.getenv("OLLAMA_DISPLAY_NAME", "")
        
        # 向量数据库配置
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "")
        self.VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "")
        
        # 文件上传配置
        self.UPLOAD_DIR = os.getenv("UPLOAD_DIR", "")
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "104857600") or "104857600")
        
        # 文本分割配置
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000") or "1000")
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200") or "200")
        
        # CORS配置
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return getattr(self, key, default)
    
    def __getattr__(self, name: str) -> Any:
        """支持点号访问"""
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return None


class StartConfig:
    """启动配置类 - 从环境变量加载"""
    
    @classmethod
    def from_env(cls) -> "StartConfig":
        """从环境变量加载启动配置"""
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
    
    def get_backend_command(self) -> str:
        reload_flag = "--reload" if self.dev_mode else ""
        return f"python -m uvicorn main:app --host {self.backend_host} --port {self.backend_port} {reload_flag}"
    
    def get_frontend_command(self) -> str:
        dev_flag = "dev" if self.dev_mode else "build"
        return f"npm run {dev_flag} -- --host {self.frontend_host} --port {self.frontend_port}"
    
    def print_config(self):
        print("=" * 50)
        print(f"  🚀 JeikChat 启动配置")
        print("=" * 50)
        print(f"  环境模式: {self.environment}")
        print(f"  后端服务: {self.backend_url}")
        print(f"  前端服务: {self.frontend_url}")
        print(f"  API 文档: {self.api_docs_url}")
        print(f"  开发模式: {'是' if self.dev_mode else '否'}")
        print("=" * 50)


@lru_cache()
def get_settings() -> Settings:
    """获取应用配置（缓存）"""
    return Settings()

def reload_settings() -> Settings:
    """重新加载应用配置（清除缓存）"""
    get_settings.cache_clear()
    return get_settings()


# 全局配置实例
start_config = StartConfig.from_env()

# 导出别名
settings = get_settings()
