from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "AI Customer Service"
    APP_VERSION: str = "3.0.0"
    
    DATABASE_URL: str = "sqlite:///./aichat.db"
    
    DEFAULT_LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    QWEN_API_KEY: Optional[str] = None
    DOUBAO_API_KEY: Optional[str] = None
    MOONSHOT_API_KEY: Optional[str] = None
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_STORE_TYPE: str = "chroma"
    
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
