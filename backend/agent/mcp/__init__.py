"""
MCP 工具模块 - 重构版
提供按需连接的 MCP 工具管理

使用方式:
1. 启动时调用 initialize_mcp() 加载配置信息（不创建连接）
2. 使用 get_all_mcp_info() 获取所有 MCP 服务信息
3. 使用 connect_mcp_service() 按需连接指定服务
4. 使用 get_mcp_tool() 获取具体工具
"""

import asyncio
from typing import List, Optional, Dict, Any
from langchain_core.tools import BaseTool

# 导入模型
from .models import (
    MCPServerConfig,
    MCPToolInfo,
    MCPServiceInfo,
    TransportType,
)

# 导入配置加载
from .config_loader import (
    load_server_configs,
    get_server_config_dict,
    load_config,
)

# 导入缓存管理
from .cache_manager import (
    get_cache_manager,
    get_tool_cache,
    refresh_tool_cache,
)

# 导入连接管理
from .connection_manager import (
    get_connection_manager,
    load_service_tools,
    get_mcp_tool,
)


# ============== 主要 API ==============

async def initialize_mcp(warmup: bool = False):
    """
    初始化 MCP 模块
    
    Args:
        warmup: 如果为 True，则连接所有服务获取工具列表（首次启动时使用）
    
    默认仅加载配置信息，不创建实际连接
    """
    cache = await get_cache_manager()
    
    # 如果缓存为空且 warmup=True，则连接所有服务获取工具
    if warmup and len(cache.all_tools) == 0:
        print("[MCP] 缓存为空，正在连接所有服务获取工具列表...")
        await warmup_all_services()
    
    print("[MCP] 初始化完成（仅加载配置，未创建连接）")


async def warmup_all_services():
    """
    预热所有 MCP 服务
    连接所有服务获取工具列表，并更新缓存
    
    注意：这会在启动时创建所有连接，可能会增加启动时间
    建议在首次部署或缓存被清除后使用
    """
    from .config_loader import load_server_configs
    
    configs = load_server_configs()
    total_tools = 0
    connected_services = 0
    
    print(f"[MCP Warmup] 开始预热 {len(configs)} 个服务...")
    
    for cfg in configs:
        if not cfg.enabled:
            print(f"[MCP Warmup] 跳过禁用服务: {cfg.name}")
            continue
        
        try:
            tools = await connect_mcp_service(cfg.name)
            if tools:
                connected_services += 1
                total_tools += len(tools)
                print(f"[MCP Warmup] ✓ {cfg.name}: {len(tools)} 个工具")
            else:
                print(f"[MCP Warmup] ✗ {cfg.name}: 连接失败")
        except Exception as e:
            print(f"[MCP Warmup] ✗ {cfg.name}: {e}")
    
    print(f"[MCP Warmup] 完成: {connected_services}/{len(configs)} 个服务, {total_tools} 个工具")


async def get_all_mcp_info() -> Dict[str, MCPServiceInfo]:
    """
    获取所有 MCP 服务信息（不创建连接）
    
    Returns:
        {服务ID: MCPServiceInfo}
    """
    cache = await get_cache_manager()
    return cache.get_all_services()


async def get_mcp_info_by_id(service_id: str) -> Optional[MCPServiceInfo]:
    """
    获取指定 MCP 服务信息（不创建连接）
    
    Args:
        service_id: 服务ID
        
    Returns:
        MCPServiceInfo 或 None
    """
    cache = await get_cache_manager()
    return cache.get_service_info(service_id)


async def get_all_mcp_tools_info() -> Dict[str, MCPToolInfo]:
    """
    获取所有 MCP 工具信息（从缓存，不创建连接）
    
    Returns:
        {工具名: MCPToolInfo}
    """
    cache = await get_cache_manager()
    return cache.get_all_tools()


async def get_mcp_tool_info(tool_name: str) -> Optional[MCPToolInfo]:
    """
    获取指定工具信息（从缓存，不创建连接）
    
    Args:
        tool_name: 工具名称（带服务前缀）
        
    Returns:
        MCPToolInfo 或 None
    """
    cache = await get_cache_manager()
    return cache.get_tool_info(tool_name)


async def connect_mcp_service(service_id: str) -> Optional[List[BaseTool]]:
    """
    连接指定 MCP 服务并获取工具
    
    Args:
        service_id: 服务ID
        
    Returns:
        工具列表，连接失败返回 None
    """
    return await load_service_tools(service_id)


async def get_mcp_tool_by_name(tool_name: str) -> Optional[BaseTool]:
    """
    根据工具名称获取工具（按需连接）
    
    支持两种格式:
    1. 带服务前缀的名称 (如: github_fork_repository)
    2. 原始名称 (如: fork_repository) - 会尝试匹配
    
    Args:
        tool_name: 工具名称
        
    Returns:
        BaseTool 或 None
    """
    cache = await get_cache_manager()
    
    # 1. 尝试直接获取工具信息
    tool_info = cache.get_tool_info(tool_name)
    
    if tool_info and tool_info.service_id:
        # 知道所属服务，直接连接
        manager = await get_connection_manager()
        return await manager.get_tool(tool_info.service_id, tool_name)
    
    # 2. 尝试通过原始名称查找带前缀的名称
    # 例如: fork_repository -> github_fork_repository
    for cached_tool_name in cache.get_all_tools().keys():
        if cached_tool_name.endswith(f"_{tool_name}"):
            tool_info = cache.get_tool_info(cached_tool_name)
            if tool_info and tool_info.service_id:
                manager = await get_connection_manager()
                return await manager.get_tool(tool_info.service_id, cached_tool_name)
    
    # 3. 不知道所属服务，遍历所有服务查找
    services = cache.get_all_services()
    for service_id in services.keys():
        manager = await get_connection_manager()
        tool = await manager.get_tool(service_id, tool_name)
        if tool:
            return tool
    
    return None


async def get_mcp_tools_by_service(service_id: str) -> List[BaseTool]:
    """
    获取指定服务的所有工具
    
    Args:
        service_id: 服务ID
        
    Returns:
        工具列表
    """
    manager = await get_connection_manager()
    return await manager.get_tools_by_service(service_id)


async def disconnect_mcp_service(service_id: str):
    """
    断开指定 MCP 服务连接
    
    Args:
        service_id: 服务ID
    """
    manager = await get_connection_manager()
    await manager.disconnect_service(service_id)


async def disconnect_all_mcp():
    """断开所有 MCP 服务连接（兼容旧接口）"""
    manager = await get_connection_manager()
    await manager.disconnect_all()


async def clear_mcp_cache():
    """清除 MCP 缓存"""
    cache = await get_cache_manager()
    await cache.clear()
    # 断开所有连接
    manager = await get_connection_manager()
    await manager.disconnect_all()


async def refresh_mcp():
    """刷新 MCP 配置和缓存"""
    await clear_mcp_cache()
    await initialize_mcp()


# ============== 兼容旧接口 ==============

_mcp_tools_cache: Optional[List[BaseTool]] = None
_mcp_tools_by_service_cache: Optional[Dict[str, List[BaseTool]]] = None


async def get_mcptools() -> List[BaseTool]:
    """
    异步获取所有 MCP 工具（按需连接所有服务）
    注意：这会连接所有服务，建议按需连接
    
    Returns:
        所有 MCP 工具列表
    """
    global _mcp_tools_cache
    
    if _mcp_tools_cache is not None:
        return _mcp_tools_cache
    
    # 获取所有服务并连接
    cache = await get_cache_manager()
    services = cache.get_all_services()
    
    all_tools = []
    for service_id in services.keys():
        tools = await connect_mcp_service(service_id)
        if tools:
            all_tools.extend(tools)
    
    _mcp_tools_cache = all_tools
    return all_tools


def get_mcptools_sync() -> List[BaseTool]:
    """同步获取所有 MCP 工具"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_mcptools())
                return future.result()
        else:
            return loop.run_until_complete(get_mcptools())
    except RuntimeError:
        return asyncio.run(get_mcptools())


async def get_mcptools_by_service() -> Dict[str, List[BaseTool]]:
    """
    按 MCP 服务分组获取工具（按需连接所有服务）
    
    Returns:
        按服务名称分组的工具字典 {服务名: [工具列表]}
    """
    global _mcp_tools_by_service_cache
    
    if _mcp_tools_by_service_cache is not None:
        return _mcp_tools_by_service_cache
    
    # 获取所有服务并连接
    cache = await get_cache_manager()
    services = cache.get_all_services()
    
    result = {}
    for service_id in services.keys():
        tools = await connect_mcp_service(service_id)
        if tools:
            result[service_id] = tools
    
    _mcp_tools_by_service_cache = result
    return result


def get_mcptools_by_service_sync() -> Dict[str, List[BaseTool]]:
    """同步按服务分组获取 MCP 工具"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_mcptools_by_service())
                return future.result()
        else:
            return loop.run_until_complete(get_mcptools_by_service())
    except RuntimeError:
        return asyncio.run(get_mcptools_by_service())


def clear_mcptools_cache():
    """清除 MCP 工具缓存（兼容旧接口）"""
    global _mcp_tools_cache, _mcp_tools_by_service_cache
    _mcp_tools_cache = None
    _mcp_tools_by_service_cache = None


async def reload_mcptools() -> List[BaseTool]:
    """重新加载 MCP 工具（兼容旧接口）"""
    clear_mcptools_cache()
    await refresh_mcp()
    return await get_mcptools()


async def merge_tools(*tool_lists: List[BaseTool]) -> List[BaseTool]:
    """异步合并多个工具列表"""
    mcp_tools = await get_mcptools()
    merged = list(mcp_tools)
    
    for tools in tool_lists:
        if tools:
            merged.extend(tools)
    
    # 去重
    seen = set()
    unique_tools = []
    for tool in merged:
        if tool.name not in seen:
            seen.add(tool.name)
            unique_tools.append(tool)
    
    return unique_tools


def merge_tools_sync(*tool_lists: List[BaseTool]) -> List[BaseTool]:
    """同步合并多个工具列表"""
    mcp_tools = get_mcptools_sync()
    merged = list(mcp_tools)
    
    for tools in tool_lists:
        if tools:
            merged.extend(tools)
    
    # 去重
    seen = set()
    unique_tools = []
    for tool in merged:
        if tool.name not in seen:
            seen.add(tool.name)
            unique_tools.append(tool)
    
    return unique_tools


# 导出主要功能
__all__ = [
    # 模型类
    'MCPServerConfig',
    'MCPToolInfo',
    'MCPServiceInfo',
    'TransportType',
    
    # 配置加载
    'load_server_configs',
    'get_server_config_dict',
    'load_config',
    
    # 主要 API
    'initialize_mcp',
    'get_all_mcp_info',
    'get_mcp_info_by_id',
    'get_all_mcp_tools_info',
    'get_mcp_tool_info',
    'connect_mcp_service',
    'get_mcp_tool_by_name',
    'get_mcp_tools_by_service',
    'disconnect_mcp_service',
    'disconnect_all_mcp',
    'clear_mcp_cache',
    'refresh_mcp',
    
    # 兼容旧接口
    'get_mcptools',
    'get_mcptools_sync',
    'get_mcptools_by_service',
    'get_mcptools_by_service_sync',
    'clear_mcptools_cache',
    'reload_mcptools',
    'merge_tools',
    'merge_tools_sync',
    'get_tool_cache',
    'refresh_tool_cache',
]
