"""
MCP 连接管理模块
按需连接 MCP 服务，管理连接生命周期
"""

import asyncio
from typing import Dict, List, Optional, Any
from langchain_core.tools import BaseTool

from .models import MCPToolInfo, TransportType
from .cache_manager import get_cache_manager
from .config_loader import load_server_configs


class MCPConnectionManager:
    """MCP 连接管理器 - 按需连接"""
    
    def __init__(self):
        self._clients: Dict[str, Any] = {}  # 已连接的客户端
        self._tools: Dict[str, List[BaseTool]] = {}  # 已加载的工具 {service_id: [tools]}
        self._lock = asyncio.Lock()
    
    async def connect_service(self, service_id: str) -> Optional[List[BaseTool]]:
        """
        连接指定 MCP 服务并获取工具
        
        Args:
            service_id: 服务ID
            
        Returns:
            工具列表，连接失败返回 None
        """
        # 检查是否已连接
        if service_id in self._tools:
            return self._tools[service_id]
        
        async with self._lock:
            # 双重检查
            if service_id in self._tools:
                return self._tools[service_id]
            
            # 获取服务配置
            configs = load_server_configs()
            config = None
            for cfg in configs:
                if cfg.name == service_id:
                    config = cfg
                    break
            
            if not config:
                print(f"[MCP Connection] 服务配置不存在: {service_id}")
                return None
            
            # 连接服务
            try:
                from langchain_mcp_adapters.client import MultiServerMCPClient
                
                print(f"[MCP Connection] 正在连接服务: {service_id} ({config.transport.value})")
                
                client_config = {service_id: config.to_client_config()}
                client = MultiServerMCPClient(client_config)
                
                # 获取工具
                tools = await client.get_tools()
                
                # 自定义工具名称和描述
                customized_tools = []
                tool_infos = []
                
                for tool in tools:
                    # 使用原始工具名，不添加前缀
                    # 这样LLM看到的和调用的都是原始名称
                    original_name = tool.name
                    
                    # 仅增强描述，不修改名称
                    enhanced_desc = f"【{service_id}】 {tool.description}"
                    tool.description = enhanced_desc
                    
                    customized_tools.append(tool)
                    
                    # 创建工具信息 - 使用原始名称
                    tool_info = MCPToolInfo(
                        name=original_name,  # 无前缀
                        original_name=original_name,
                        description=enhanced_desc,
                        service_id=service_id,
                        service_name=service_id,
                    )
                    tool_infos.append(tool_info)
                
                # 保存客户端和工具
                self._clients[service_id] = client
                self._tools[service_id] = customized_tools
                
                # 更新缓存
                cache_manager = await get_cache_manager()
                cache_manager.update_service_tools(service_id, tool_infos)
                await cache_manager.save_to_file()
                
                print(f"[MCP Connection] 服务 '{service_id}' 连接成功，加载 {len(tools)} 个工具")
                return customized_tools
                
            except Exception as e:
                print(f"[MCP Connection] 服务 '{service_id}' 连接失败: {e}")
                cache_manager = await get_cache_manager()
                cache_manager.update_service_status(service_id, "error", str(e))
                return None
    
    async def get_tool(self, service_id: str, tool_name: str) -> Optional[BaseTool]:
        """
        获取指定服务的指定工具
        
        Args:
            service_id: 服务ID
            tool_name: 工具名称（带前缀或不带前缀）
            
        Returns:
            工具对象，未找到返回 None
        """
        # 确保服务已连接
        tools = await self.connect_service(service_id)
        if not tools:
            return None
        
        # 查找工具
        for tool in tools:
            if tool.name == tool_name or tool.name.endswith(f"_{tool_name}"):
                return tool
        
        return None
    
    async def get_tools_by_service(self, service_id: str) -> List[BaseTool]:
        """获取指定服务的所有工具"""
        tools = await self.connect_service(service_id)
        return tools or []
    
    async def disconnect_service(self, service_id: str):
        """断开指定服务连接"""
        if service_id in self._clients:
            client = self._clients.pop(service_id)
            try:
                if hasattr(client, 'close'):
                    await client.close()
                print(f"[MCP Connection] 服务 '{service_id}' 已断开")
            except Exception as e:
                print(f"[MCP Connection] 断开服务 '{service_id}' 时出错: {e}")
        
        self._tools.pop(service_id, None)
        
        # 更新缓存状态
        cache_manager = await get_cache_manager()
        cache_manager.update_service_status(service_id, "not_connected")
    
    async def disconnect_all(self):
        """断开所有服务连接"""
        for service_id in list(self._clients.keys()):
            await self.disconnect_service(service_id)
    
    def is_connected(self, service_id: str) -> bool:
        """检查服务是否已连接"""
        return service_id in self._tools
    
    def get_connected_services(self) -> List[str]:
        """获取已连接的服务列表"""
        return list(self._tools.keys())


# 全局连接管理器
_connection_manager: Optional[MCPConnectionManager] = None


async def get_connection_manager() -> MCPConnectionManager:
    """获取连接管理器实例"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = MCPConnectionManager()
    return _connection_manager


async def load_service_tools(service_id: str) -> List[BaseTool]:
    """加载指定服务的工具（兼容旧接口）"""
    manager = await get_connection_manager()
    tools = await manager.connect_service(service_id)
    return tools or []


async def get_mcp_tool(service_id: str, tool_name: str) -> Optional[BaseTool]:
    """获取 MCP 工具（兼容旧接口）"""
    manager = await get_connection_manager()
    return await manager.get_tool(service_id, tool_name)


async def disconnect_all_mcp():
    """断开所有 MCP 连接（兼容旧接口）"""
    manager = await get_connection_manager()
    await manager.disconnect_all()
