"""
JeikChat 统一配置管理
合并应用配置和启动配置，提供统一的管理接口
"""

from typing import Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
from functools import lru_cache


def get_env_file_path():
    """获取环境配置文件路径"""
    environment = os.environ.get("AICHAT_ENVIRONMENT", "dev")
    if environment == "local":
        return ".env.local"
    return ".env"


class StartConfig(BaseModel):
    """启动配置类"""
    
    # 后端配置
    backend_host: str = "::"
    backend_port: int = 8000
    
    # 前端配置
    frontend_host: str = "::"
    frontend_port: int = 5173
    
    # 开发模式
    dev_mode: bool = True
    
    # 环境模式
    environment: str = "dev"
    
    # API 文档配置
    api_docs_host: str = "localhost"
    api_docs_port: int = 8000
    
    @classmethod
    def from_env(cls) -> "StartConfig":
        """从环境变量加载配置"""
        return cls(
            backend_host=os.getenv("JEIKCHAT_BACKEND_HOST", "0.0.0.0"),
            backend_port=int(os.getenv("JEIKCHAT_BACKEND_PORT", "8000")),
            frontend_host=os.getenv("JEIKCHAT_FRONTEND_HOST", "0.0.0.0"),
            frontend_port=int(os.getenv("JEIKCHAT_FRONTEND_PORT", "5173")),
            dev_mode=os.getenv("JEIKCHAT_DEV_MODE", "true").lower() == "true",
            environment=os.getenv("JEIKCHAT_ENVIRONMENT", "dev"),
            api_docs_host=os.getenv("JEIKCHAT_API_DOCS_HOST", "localhost"),
            api_docs_port=int(os.getenv("JEIKCHAT_API_DOCS_PORT", "8000")),
        )
    
    @property
    def backend_url(self) -> str:
        """后端服务地址"""
        return f"http://{self.backend_host}:{self.backend_port}"
    
    @property
    def frontend_url(self) -> str:
        """前端服务地址"""
        return f"http://{self.frontend_host}:{self.frontend_port}"
    
    @property
    def api_docs_url(self) -> str:
        """API 文档地址"""
        return f"http://{self.api_docs_host}:{self.api_docs_port}/docs"
    
    def get_backend_command(self) -> str:
        """获取后端启动命令"""
        reload_flag = "--reload" if self.dev_mode else ""
        return f"python -m uvicorn main:app --host {self.backend_host} --port {self.backend_port} {reload_flag}"
    
    def get_frontend_command(self) -> str:
        """获取前端启动命令"""
        dev_flag = "dev" if self.dev_mode else "build"
        return f"npm run {dev_flag} -- --host {self.frontend_host} --port {self.frontend_port}"
    
    def print_config(self):
        """打印配置信息"""
        print("🚀 JeikChat 启动配置")
        print("=" * 50)
        print(f"后端服务: {self.backend_url}")
        print(f"前端服务: {self.frontend_url}")
        print(f"API 文档: {self.api_docs_url}")
        print(f"开发模式: {'是' if self.dev_mode else '否'}")
        print(f"环境模式: {self.environment}")
        print("=" * 50)


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=get_env_file_path(),
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    APP_NAME: str = "JeikChat"
    APP_VERSION: str = "3.0.0"
    
    DATABASE_URL: str = "sqlite:///./aichat.db"
    
    DEFAULT_LLM_PROVIDER: str = "openai"
    
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_DISPLAY_NAME: str = "OPENAI_MODEL"
    
    # Anthropic配置
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_DISPLAY_NAME: str = "ANTHROPIC_MODEL"
    
    # Google配置
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_BASE_URL: str = "https://generativelanguage.googleapis.com"
    GOOGLE_MODEL: str = "gemini-2.0-flash"
    GOOGLE_DISPLAY_NAME: str = "GOOGLE_MODEL"
    
    # 阿里云通义千问配置
    QWEN_API_KEY: Optional[str] = None
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com"
    QWEN_MODEL: str = "qwen-max"
    QWEN_DISPLAY_NAME: str = "QWEN_MODEL"
    
    # 字节跳动豆包配置
    DOUBAO_API_KEY: Optional[str] = None
    DOUBAO_BASE_URL: str = "https://ark.cn-beijing.volces.com"
    DOUBAO_MODEL: str = "doubao-pro"
    DOUBAO_DISPLAY_NAME: str = "DOUBAO_MODEL"
    
    # 月之暗面Kimi配置
    MOONSHOT_API_KEY: Optional[str] = None
    MOONSHOT_BASE_URL: str = "https://api.moonshot.cn"
    MOONSHOT_MODEL: str = "moonshot-v1-8k"
    MOONSHOT_DISPLAY_NAME: str = "MOONSHOT_MODEL"
    
    # 智谱AI配置
    ZHIPU_API_KEY: Optional[str] = None
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn"
    ZHIPU_MODEL: str = "glm-4-air"
    ZHIPU_DISPLAY_NAME: str = "ZHIPU_MODEL"
    
    # 百度文心一言配置
    BAIDU_API_KEY: Optional[str] = None
    BAIDU_SECRET_KEY: Optional[str] = None
    BAIDU_BASE_URL: str = "https://aip.baidubce.com"
    BAIDU_MODEL: str = "ernie-bot-4.5"
    BAIDU_DISPLAY_NAME: str = "BAIDU_MODEL"
    
    # 讯飞星火配置
    XFYUN_API_KEY: Optional[str] = None
    XFYUN_SECRET_KEY: Optional[str] = None
    XFYUN_APP_ID: Optional[str] = None
    XFYUN_BASE_URL: str = "https://spark-api-open.xf-yun.com"
    XFYUN_MODEL: str = "spark-4.5-ultra"
    XFYUN_DISPLAY_NAME: str = "XFYUN_MODEL"
    
    # Ollama本地部署配置
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2:7b"
    OLLAMA_DISPLAY_NAME: str = "OLLAMA_MODEL"
    
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_STORE_TYPE: str = "chroma"
    
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200


# 全局配置实例
start_config = StartConfig.from_env()


@lru_cache()
def get_settings() -> Settings:
    """获取应用配置（缓存）"""
    return Settings()


# 导出别名，保持向后兼容
settings = get_settings()