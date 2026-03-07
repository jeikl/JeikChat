"""
MCP 工具缓存系统
提供 O(1) 时间复杂度的工具查询和调用
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from langchain_core.tools import BaseTool
import logging

logger = logging.getLogger(__name__)

# 全局工具缓存
_tool_cache: Optional['ToolCache'] = None
_cache_lock = asyncio.Lock()

# 缓存文件路径
CACHE_FILE = os.path.join(os.path.dirname(__file__), "mcpcache.json")


@dataclass
class ToolInfo:
    """工具信息数据结构"""
    name: str           # 带服务前缀的名称 (如: github_fork_repository)
    description: str
    service_id: str
    service_name: str
    # 序列化后的工具参数schema
    args_schema: Optional[Dict[str, Any]] = None


@dataclass
class ServiceInfo:
    """MCP 服务信息"""
    name: str
    transport: str
    config: Dict[str, Any]
    tool_names: List[str]


class ToolCache:
    """
    MCP 工具缓存管理器
    
    提供：
    - O(1) 时间复杂度的工具查询
    - 工具名到 MCP 服务的快速映射
    - 持久化缓存到本地文件
    """
    
    def __init__(self):
        self.all_tools: Dict[str, ToolInfo] = {}
        self.services: Dict[str, ServiceInfo] = {}
        self._langchain_tools: Dict[str, BaseTool] = {}
        self._initialized = False
    
    def is_initialized(self) -> bool:
        """检查缓存是否已初始化"""
        return self._initialized
    
    async def initialize(self, force_reload: bool = False):
        """
        初始化工具缓存

        Args:
            force_reload: 是否强制重新加载，忽略已有缓存
        """
        if self._initialized and not force_reload:
            return

        # 尝试从文件加载缓存
        if not force_reload and self._load_from_file():
            self._initialized = True
            return  # 这里必须返回，避免继续加载服务

        # 从 MCP 服务加载
        await self._load_from_services()

        # 保存到文件
        self._save_to_file()

        self._initialized = True
    
    async def _load_from_services(self):
        """从所有 MCP 服务加载工具"""
        from agent.mcp import _get_services_list, _get_server_configs, _load_service_tools

        self.all_tools.clear()
        self.services.clear()
        self._langchain_tools.clear()

        services_list = _get_services_list()
        server_configs = _get_server_configs()

        if not services_list:
            logger.warning("[MCP] 没有可用的 MCP 服务器配置")
            return

        loaded_services = []
        failed_services = []

        for service_info in services_list:
            service_name = service_info.get('name')
            if not service_name:
                continue

            transport = service_info.get('transport', 'stdio')
            config = server_configs.get(service_name, {})

            try:
                # 加载该服务的工具
                tools = await _load_service_tools(service_name, config)

                # 保存服务信息
                self.services[service_name] = ServiceInfo(
                    name=service_name,
                    transport=transport,
                    config=config,
                    tool_names=[t.name for t in tools]
                )

                # 保存工具信息
                for tool in tools:
                    self.all_tools[tool.name] = ToolInfo(
                        name=tool.name,
                        description=tool.description or "",
                        service_id=service_name,
                        service_name=service_name,
                        args_schema=self._extract_args_schema(tool)
                    )
                    self._langchain_tools[tool.name] = tool

                loaded_services.append(f"{service_name}({len(tools)})")

            except Exception as e:
                failed_services.append(service_name)
                logger.debug(f"[MCP] 加载服务 '{service_name}' 失败: {e}")

        # 汇总输出一行日志
        if loaded_services:
            logger.info(f"[MCP] 已加载 {len(loaded_services)} 个服务: {', '.join(loaded_services)}")
        if failed_services:
            logger.warning(f"[MCP] 加载失败 {len(failed_services)} 个服务: {', '.join(failed_services)}")
    
    def _extract_args_schema(self, tool: BaseTool) -> Optional[Dict[str, Any]]:
        """提取工具的参数 schema"""
        try:
            if hasattr(tool, 'args_schema') and tool.args_schema:
                return tool.args_schema.schema()
        except Exception as e:
            logger.debug(f"[ToolCache] 提取工具 '{tool.name}' 的 schema 失败: {e}")
        return None
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """
        通过工具名获取工具信息（O(1) 时间复杂度）
        
        Args:
            tool_name: 工具名称
            
        Returns:
            ToolInfo 对象，如果不存在则返回 None
        """
        return self.all_tools.get(tool_name)
    
    def get_langchain_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取 LangChain 工具对象
        
        Args:
            tool_name: 工具名称
            
        Returns:
            BaseTool 对象，如果不存在则返回 None
        """
        return self._langchain_tools.get(tool_name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """获取所有 LangChain 工具"""
        return list(self._langchain_tools.values())
    
    def get_tools_by_service(self, service_id: str) -> List[BaseTool]:
        """
        获取指定服务的所有工具
        
        Args:
            service_id: 服务ID
            
        Returns:
            该服务的工具列表
        """
        service = self.services.get(service_id)
        if not service:
            return []
        
        tools = []
        for tool_name in service.tool_names:
            tool = self._langchain_tools.get(tool_name)
            if tool:
                tools.append(tool)
        return tools
    
    def get_service_info(self, service_id: str) -> Optional[ServiceInfo]:
        """获取服务信息"""
        return self.services.get(service_id)
    
    def get_all_services(self) -> Dict[str, ServiceInfo]:
        """获取所有服务信息"""
        return dict(self.services)
    
    def _save_to_file(self):
        """将缓存保存到本地文件"""
        try:
            data = {
                "all_tools": {
                    name: asdict(info)
                    for name, info in self.all_tools.items()
                },
                "services": {
                    name: asdict(info)
                    for name, info in self.services.items()
                }
            }

            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"[MCP] 缓存已保存: {CACHE_FILE}")
        except Exception as e:
            logger.debug(f"[MCP] 保存缓存失败: {e}")
    
    def _load_from_file(self) -> bool:
        """从本地文件加载缓存"""
        try:
            if not os.path.exists(CACHE_FILE):
                return False

            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 加载工具信息
            for name, info in data.get("all_tools", {}).items():
                self.all_tools[name] = ToolInfo(**info)

            # 加载服务信息
            for name, info in data.get("services", {}).items():
                self.services[name] = ServiceInfo(**info)

            # 重要：从文件加载时，LangChain 工具对象为空
            # 但我们需要设置 tool_names，以便后续按需加载
            logger.info(f"[MCP] 缓存加载 {len(self.all_tools)} 个工具")
            return True

        except Exception as e:
            return False
    
    async def refresh(self):
        """刷新缓存（重新从 MCP 服务加载）"""
        logger.info("[MCP] 刷新缓存...")
        self._initialized = False
        await self.initialize(force_reload=True)

    def clear(self):
        """清空缓存"""
        self.all_tools.clear()
        self.services.clear()
        self._langchain_tools.clear()
        self._initialized = False

        # 删除缓存文件
        if os.path.exists(CACHE_FILE):
            try:
                os.remove(CACHE_FILE)
            except Exception as e:
                logger.debug(f"[MCP] 删除缓存文件失败: {e}")


# ==================== 全局接口函数 ====================

async def get_tool_cache() -> ToolCache:
    """
    获取工具缓存实例（单例模式）
    
    Returns:
        ToolCache 实例
    """
    global _tool_cache
    
    if _tool_cache is None:
        async with _cache_lock:
            if _tool_cache is None:
                _tool_cache = ToolCache()
    
    # 确保已初始化
    if not _tool_cache.is_initialized():
        await _tool_cache.initialize()
    
    return _tool_cache


def get_tool_cache_sync() -> ToolCache:
    """同步获取工具缓存实例"""
    global _tool_cache
    
    if _tool_cache is None:
        _tool_cache = ToolCache()
    
    if not _tool_cache.is_initialized():
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _tool_cache.initialize())
                    future.result()
            else:
                loop.run_until_complete(_tool_cache.initialize())
        except RuntimeError:
            asyncio.run(_tool_cache.initialize())
    
    return _tool_cache


async def get_tool_by_name(tool_name: str) -> Optional[BaseTool]:
    """
    通过工具名快速获取工具（O(1) 时间复杂度）
    
    tool_name 是带服务前缀的名称（如: github_fork_repository）
    
    如果缓存中没有该工具（从文件加载时 LangChain 工具对象为空），
    则动态连接到对应 MCP 服务获取。
    
    Args:
        tool_name: 工具名称（带服务前缀）
        
    Returns:
        BaseTool 对象，如果不存在则返回 None
    """
    cache = await get_tool_cache()
    
    # 首先尝试从缓存获取
    tool = cache.get_langchain_tool(tool_name)
    if tool:
        return tool
    
    # 如果缓存中没有，检查是否有该工具的信息
    tool_info = cache.get_tool_info(tool_name)
    
    if not tool_info:
        return None
    
    # 有信息但没有 LangChain 工具对象，需要动态加载
    logger.info(f"[MCP] 动态加载工具 '{tool_name}' 从服务 '{tool_info.service_id}'")
    
    try:
        from agent.mcp import _load_service_tools, _get_server_configs
        
        server_configs = _get_server_configs()
        config = server_configs.get(tool_info.service_id, {})
        
        # 连接到服务加载工具
        tools = await _load_service_tools(tool_info.service_id, config)
        
        # 更新缓存
        for t in tools:
            cache._langchain_tools[t.name] = t
        
        # 返回请求的工具
        return cache.get_langchain_tool(tool_name)
        
    except Exception as e:
        logger.error(f"[MCP] 动态加载工具 '{tool_name}' 失败: {e}")
        return None


def get_tool_by_name_sync(tool_name: str) -> Optional[BaseTool]:
    """同步通过工具名获取工具"""
    cache = get_tool_cache_sync()
    return cache.get_langchain_tool(tool_name)


async def get_tool_info(tool_name: str) -> Optional[ToolInfo]:
    """
    获取工具详细信息
    
    Args:
        tool_name: 工具名称
        
    Returns:
        ToolInfo 对象
    """
    cache = await get_tool_cache()
    return cache.get_tool_info(tool_name)


def get_tool_info_sync(tool_name: str) -> Optional[ToolInfo]:
    """同步获取工具详细信息"""
    cache = get_tool_cache_sync()
    return cache.get_tool_info(tool_name)


async def get_all_cached_tools() -> List[BaseTool]:
    """获取所有缓存的工具"""
    cache = await get_tool_cache()
    return cache.get_all_tools()


def get_all_cached_tools_sync() -> List[BaseTool]:
    """同步获取所有缓存的工具"""
    cache = get_tool_cache_sync()
    return cache.get_all_tools()


async def refresh_tool_cache():
    """刷新工具缓存"""
    cache = await get_tool_cache()
    await cache.refresh()


def clear_tool_cache():
    """清空工具缓存"""
    global _tool_cache
    if _tool_cache:
        _tool_cache.clear()
        _tool_cache = None
