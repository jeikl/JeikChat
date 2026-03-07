"""
Agent 模块
提供完整的工具列表（普通工具 + MCP 工具）
使用 MCP Tool Cache 系统优化性能
"""

import asyncio
from typing import List, Optional
from langchain_core.tools import BaseTool

# 全局单例变量
_all_tools: Optional[List[BaseTool]] = None
_all_tools_sync: Optional[List[BaseTool]] = None

# 异步锁，防止并发加载
_load_lock = asyncio.Lock()


async def get_all_tools() -> List[BaseTool]:
    """
    获取所有工具列表（普通工具 + MCP 工具）
    
    单例模式：首次调用时加载并合并，后续返回缓存
    MCP 工具使用 ToolCache 系统，O(1) 查询
    
    Returns:
        完整的工具列表
    """
    global _all_tools
    
    # 快速检查，避免不必要的锁竞争
    if _all_tools is not None:
        return _all_tools
    
    # 使用锁保护加载过程
    async with _load_lock:
        # 双重检查，防止其他协程已经加载完成
        if _all_tools is not None:
            return _all_tools
        
        # 1. 获取普通工具
        from agent.tools import get_regular_tools
        regular_tools = get_regular_tools()
        
        # 2. 获取 MCP 工具（使用新的缓存系统）
        from agent.mcp.mcp_cache import get_all_cached_tools
        mcp_tools = await get_all_cached_tools()
        
        # 3. 合并工具列表
        _all_tools = list(regular_tools)
        
        # 添加 MCP 工具，去重
        existing_names = {t.name for t in _all_tools}
        for tool in mcp_tools:
            if tool.name not in existing_names:
                _all_tools.append(tool)
                existing_names.add(tool.name)
    
    return _all_tools


async def get_all_tools_async() -> List[BaseTool]:
    """
    异步获取所有工具列表（在同步环境中使用）
    
    用于在已经运行的事件循环中获取工具
    MCP 工具使用 ToolCache 系统，O(1) 查询
    
    Returns:
        完整的工具列表
    """
    global _all_tools_sync
    
    if _all_tools_sync is None:
        # 1. 获取普通工具
        from agent.tools import get_regular_tools
        regular_tools = get_regular_tools()
        
        # 2. 获取 MCP 工具（使用新的缓存系统）
        from agent.mcp.mcp_cache import get_all_cached_tools
        mcp_tools = await get_all_cached_tools()
        
        # 3. 合并
        _all_tools_sync = list(regular_tools)
        
        existing_names = {t.name for t in _all_tools_sync}
        for tool in mcp_tools:
            if tool.name not in existing_names:
                _all_tools_sync.append(tool)
                existing_names.add(tool.name)
    
    return _all_tools_sync


def get_all_tools_sync() -> List[BaseTool]:
    """
    同步获取所有工具列表
    
    单例模式：首次调用时加载，后续返回缓存
    
    注意：如果在异步环境中使用，请使用 get_all_tools() 或 get_all_tools_async()
    
    Returns:
        完整的工具列表
    """
    global _all_tools_sync
    
    if _all_tools_sync is None:
        # 1. 获取普通工具
        from agent.tools import get_regular_tools
        regular_tools = get_regular_tools()
        
        # 2. 获取 MCP 工具（同步）
        from agent.mcp import get_mcptools_sync
        mcp_tools = get_mcptools_sync()
        
        # 3. 合并
        _all_tools_sync = list(regular_tools)
        
        existing_names = {t.name for t in _all_tools_sync}
        for tool in mcp_tools:
            if tool.name not in existing_names:
                _all_tools_sync.append(tool)
                existing_names.add(tool.name)
    
    return _all_tools_sync


def clear_tools_cache():
    """清除工具缓存，下次调用时重新加载"""
    global _all_tools, _all_tools_sync
    _all_tools = None
    _all_tools_sync = None
    
    # 同时清除 MCP 工具缓存
    from agent.mcp import clear_mcptools_cache
    clear_mcptools_cache()
    
    print("[Agent] 工具缓存已清除")


async def reload_all_tools() -> List[BaseTool]:
    """重新加载所有工具"""
    clear_tools_cache()
    return await get_all_tools()


def get_regular_tools():
    """
    获取普通工具列表（非 MCP）
    
    Returns:
        普通工具列表的副本
    """
    from agent.tools import get_regular_tools as _get_regular_tools
    return _get_regular_tools()


# 导出主要功能
__all__ = [
    'get_all_tools',        # 异步获取所有工具（普通 + MCP）
    'get_all_tools_sync',   # 同步获取所有工具
    'get_regular_tools',    # 获取普通工具列表
    'clear_tools_cache',    # 清除缓存
    'reload_all_tools',     # 重新加载
]
