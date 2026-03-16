"""
MCP 缓存管理模块
管理 MCP 服务信息和工具信息的缓存
启动时仅加载配置，不创建实际连接
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

from .models import MCPCacheData, MCPServiceInfo, MCPToolInfo, TransportType
from .config_loader import load_server_configs


class MCPCacheManager:
    """MCP 缓存管理器"""
    
    _instance: Optional['MCPCacheManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._cache = MCPCacheData()
        self._initialized = False
        self._cache_file = Path(__file__).parent / "mcpcache.json"
        
    async def initialize(self):
        """初始化缓存（仅加载配置信息，不创建连接）"""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            # 1. 首先尝试从持久化缓存加载工具信息
            if self._cache_file.exists():
                await self._load_from_file()
            
            # 2. 从配置文件加载服务信息（不连接）
            await self._load_services_from_config()
            
            self._initialized = True
            print(f"[MCP Cache] 初始化完成: {len(self._cache.services)} 个服务, {len(self._cache.all_tools)} 个工具")
    
    async def _load_services_from_config(self):
        """从配置文件加载服务信息（不创建连接）"""
        configs = load_server_configs()
        
        for cfg in configs:
            if not cfg.enabled:
                continue
            
            # 创建服务信息（不连接）
            service_info = MCPServiceInfo(
                id=cfg.name,
                name=cfg.name,
                transport=cfg.transport,
                config=cfg,
                tool_names=[],  # 初始为空，从缓存文件或首次连接时填充
                enabled=True,
                status="not_connected",
            )
            
            # 如果缓存中已有该服务的工具信息，恢复它
            if cfg.name in self._cache.services:
                existing = self._cache.services[cfg.name]
                service_info.tool_names = existing.tool_names
            
            self._cache.services[cfg.name] = service_info
    
    async def _load_from_file(self):
        """从文件加载缓存"""
        try:
            with open(self._cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 加载服务信息
            for service_id, service_data in data.get("services", {}).items():
                self._cache.services[service_id] = MCPServiceInfo(
                    id=service_data.get("id", service_id),
                    name=service_data.get("name", service_id),
                    transport=TransportType(service_data.get("transport", "stdio")),
                    config=None,  # 从配置文件重新加载
                    tool_names=service_data.get("tool_names", []),
                    enabled=service_data.get("enabled", True),
                    status="not_connected",
                )
            
            # 加载工具信息
            for tool_name, tool_data in data.get("all_tools", {}).items():
                self._cache.all_tools[tool_name] = MCPToolInfo(
                    name=tool_data.get("name", tool_name),
                    original_name=tool_data.get("original_name", tool_name),
                    description=tool_data.get("description", ""),
                    service_id=tool_data.get("service_id", ""),
                    service_name=tool_data.get("service_name", ""),
                    args_schema=tool_data.get("args_schema"),
                )
            
            print(f"[MCP Cache] 从文件加载: {len(self._cache.services)} 个服务, {len(self._cache.all_tools)} 个工具")
            
        except Exception as e:
            print(f"[MCP Cache] 从文件加载缓存失败: {e}")
    
    async def save_to_file(self):
        """保存缓存到文件"""
        try:
            data = {
                "services": {},
                "all_tools": {},
            }
            
            # 保存服务信息
            for service_id, service in self._cache.services.items():
                data["services"][service_id] = {
                    "id": service.id,
                    "name": service.name,
                    "transport": service.transport.value,
                    "tool_names": service.tool_names,
                    "enabled": service.enabled,
                }
            
            # 保存工具信息
            for tool_name, tool in self._cache.all_tools.items():
                data["all_tools"][tool_name] = {
                    "name": tool.name,
                    "original_name": tool.original_name,
                    "description": tool.description,
                    "service_id": tool.service_id,
                    "service_name": tool.service_name,
                    "args_schema": tool.args_schema,
                }
            
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"[MCP Cache] 已保存到文件: {len(self._cache.services)} 个服务, {len(self._cache.all_tools)} 个工具")
            
        except Exception as e:
            print(f"[MCP Cache] 保存缓存到文件失败: {e}")
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    def get_all_services(self) -> Dict[str, MCPServiceInfo]:
        """获取所有服务信息"""
        return dict(self._cache.services)
    
    def get_service_info(self, service_id: str) -> Optional[MCPServiceInfo]:
        """获取指定服务信息"""
        return self._cache.get_service_info(service_id)
    
    def get_tool_info(self, tool_name: str) -> Optional[MCPToolInfo]:
        """获取工具信息"""
        return self._cache.get_tool_info(tool_name)
    
    def get_all_tools(self) -> Dict[str, MCPToolInfo]:
        """获取所有工具信息"""
        return dict(self._cache.all_tools)
    
    @property
    def all_tools(self) -> Dict[str, MCPToolInfo]:
        """获取所有工具信息（属性访问方式）"""
        return self._cache.all_tools
    
    @property
    def services(self) -> Dict[str, MCPServiceInfo]:
        """获取所有服务信息（属性访问方式）"""
        return self._cache.services
    
    def update_service_tools(self, service_id: str, tools: List[MCPToolInfo]):
        """更新服务的工具列表（连接后调用）"""
        if service_id not in self._cache.services:
            return
        
        service = self._cache.services[service_id]
        service.tool_names = [tool.name for tool in tools]
        service.status = "connected"
        
        # 更新全局工具字典
        for tool in tools:
            self._cache.all_tools[tool.name] = tool
    
    def update_service_status(self, service_id: str, status: str, error_message: Optional[str] = None):
        """更新服务状态"""
        if service_id in self._cache.services:
            self._cache.services[service_id].status = status
            self._cache.services[service_id].error_message = error_message
    
    async def clear(self):
        """清除缓存"""
        self._cache = MCPCacheData()
        self._initialized = False
        if self._cache_file.exists():
            try:
                os.remove(self._cache_file)
            except Exception as e:
                print(f"[MCP Cache] 删除缓存文件失败: {e}")
    
    async def refresh(self):
        """刷新缓存"""
        await self.clear()
        await self.initialize()


# 全局单例
_cache_manager: Optional[MCPCacheManager] = None


async def get_cache_manager() -> MCPCacheManager:
    """获取缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = MCPCacheManager()
        await _cache_manager.initialize()
    return _cache_manager


async def get_tool_cache() -> MCPCacheManager:
    """获取工具缓存（兼容旧接口）"""
    return await get_cache_manager()


async def refresh_tool_cache(on_service_connected=None):
    """刷新工具缓存 - 连接所有 MCP 服务并获取工具
    
    Args:
        on_service_connected: 可选的回调函数，当一个服务连接成功时调用
                              参数: (service_name, tools_count)
    """
    global _cache_manager
    
    if _cache_manager is not None:
        await _cache_manager.clear()
    
    _cache_manager = None
    manager = await get_cache_manager()
    
    from .connection_manager import MCPConnectionManager
    from .config_loader import load_server_configs
    
    connection_manager = MCPConnectionManager()
    configs = load_server_configs()
    
    connected_count = 0
    failed_count = 0
    total_tools = 0
    
    for cfg in configs:
        if not cfg.enabled:
            continue
        
        try:
            tools = await connection_manager.connect_service(cfg.name)
            
            if tools is not None:
                connected_count += 1
                total_tools += len(tools)
                # 调用回调通知服务已连接
                if on_service_connected:
                    await on_service_connected(cfg.name, len(tools))
            else:
                failed_count += 1
                
        except Exception as e:
            failed_count += 1
            manager.update_service_status(cfg.name, "error", str(e))
    
    await manager.save_to_file()
    
    print(f"[MCP] 刷新完成: {connected_count} 个服务, {total_tools} 个工具")
    return manager
