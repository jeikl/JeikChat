"""
向后兼容层
将旧路径的导入重定向到新模块
"""

from app.config import get_settings, Settings, get_start_config, StartConfig, load_env_file
from app.main import app

__all__ = [
    "get_settings",
    "Settings", 
    "get_start_config",
    "StartConfig",
    "load_env_file",
    "app",
]
