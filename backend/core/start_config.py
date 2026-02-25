"""
JeikChat 启动配置管理
统一管理前后端启动参数，支持简化的启动命令
"""

import os
from typing import Optional
from pydantic import BaseModel


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


# 全局配置实例
start_config = StartConfig.from_env()