"""
MCP 数据模型模块
定义 MCP 服务、工具等的 Pydantic 模型
"""

from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum


class TransportType(str, Enum):
    """MCP 传输类型"""
    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"
    WEBSOCKET = "websocket"


@dataclass
class MCPServerConfig:
    """MCP 服务器配置"""
    name: str
    transport: TransportType
    # stdio 类型配置
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    # http 类型配置
    url: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    # 平台特定配置
    windows: Optional[Dict[str, Any]] = None
    linux: Optional[Dict[str, Any]] = None
    macos: Optional[Dict[str, Any]] = None
    # 其他配置
    timeout: int = 30
    enabled: bool = True

    def to_client_config(self) -> Dict[str, Any]:
        """转换为 MultiServerMCPClient 所需的配置格式"""
        config: Dict[str, Any] = {
            "transport": self.transport.value,
        }
        
        if self.transport == TransportType.STDIO:
            if self.command:
                config["command"] = self.command
            if self.args:
                config["args"] = self.args
            if self.env:
                config["env"] = self.env
        elif self.transport in [TransportType.SSE, TransportType.STREAMABLE_HTTP]:
            if self.url:
                config["url"] = self.url
            if self.headers:
                config["headers"] = self.headers
                
        return config


@dataclass
class MCPToolInfo:
    """MCP 工具信息（不持有实际工具对象）"""
    name: str  # 带服务前缀的名称，如: github_fork_repository
    original_name: str  # 原始名称，如: fork_repository
    description: str
    service_id: str  # 所属服务ID
    service_name: str  # 所属服务名称
    args_schema: Optional[Dict[str, Any]] = None
    
    @property
    def prefixed_name(self) -> str:
        """获取带前缀的名称"""
        return self.name


@dataclass
class MCPServiceInfo:
    """MCP 服务信息（不持有连接）"""
    id: str
    name: str
    transport: TransportType
    config: MCPServerConfig
    tool_names: List[str] = field(default_factory=list)
    enabled: bool = True
    status: str = "not_connected"  # not_connected, connected, error
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "transport": self.transport.value,
            "tool_count": len(self.tool_names),
            "enabled": self.enabled,
            "status": self.status,
        }


@dataclass
class MCPCacheData:
    """MCP 缓存数据结构"""
    services: Dict[str, MCPServiceInfo] = field(default_factory=dict)
    all_tools: Dict[str, MCPToolInfo] = field(default_factory=dict)
    
    def get_tool_info(self, tool_name: str) -> Optional[MCPToolInfo]:
        """获取工具信息"""
        return self.all_tools.get(tool_name)
    
    def get_service_info(self, service_id: str) -> Optional[MCPServiceInfo]:
        """获取服务信息"""
        return self.services.get(service_id)
    
    def get_tools_by_service(self, service_id: str) -> List[MCPToolInfo]:
        """获取指定服务的所有工具信息"""
        service = self.services.get(service_id)
        if not service:
            return []
        return [
            self.all_tools[name] 
            for name in service.tool_names 
            if name in self.all_tools
        ]
