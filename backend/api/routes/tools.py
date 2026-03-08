from fastapi import APIRouter
from api.response import success

router = APIRouter()


async def get_tool_list():
    """
    获取工具列表，优先从缓存加载
    返回格式包含 mcp 标记，用于前端区分 MCP 工具和普通工具
    
    对于 MCP 工具，toolid 和 name 都使用带服务前缀的名称（如: github_fork_repository）
    """
    from agent.mcp.cache_manager import get_cache_manager
    from agent.tools import get_regular_tools

    # 获取缓存实例（确保已初始化）
    cache = await get_cache_manager()

    # 获取普通工具（内置工具）
    regular_tools = get_regular_tools()
    regular_tool_names = {t.name for t in regular_tools}

    # 合并所有工具
    all_tools = []

    # 添加普通工具（mcp=0）
    for tool in regular_tools:
        all_tools.append({
            "toolid": tool.name,
            "name": tool.name,
            "description": tool.description,
            "mcp": 0,  # 0 表示普通工具
            "enabled": True
        })

    # 添加 MCP 工具（mcp=1）- 从缓存的工具信息中获取
    # 注意：从文件加载时，LangChain 工具对象为空，但工具信息是可用的
    for tool_name, tool_info in cache.all_tools.items():
        if tool_name not in regular_tool_names:
            # toolid 和 name 都使用带服务前缀的名称
            all_tools.append({
                "toolid": tool_info.name,      # 带服务前缀的名称
                "name": tool_info.name,        # 带服务前缀的名称
                "description": tool_info.description,
                "mcp": 1,  # 1 表示 MCP 工具
                "enabled": True
            })

    return all_tools


@router.get("/tools")
async def list_tools():
    """获取所有可用的Agent工具列表（使用缓存，O(1) 查询）"""
    return success(data=await get_tool_list(), msg="获取成功")


@router.post("/tools/{tool_id}/enable")
async def enable_tool(tool_id: str):
    """启用工具"""
    return success(data={"tool_id": tool_id, "enabled": True}, msg="启用成功")


@router.post("/tools/{tool_id}/disable")
async def disable_tool(tool_id: str):
    """禁用工具"""
    return success(data={"tool_id": tool_id, "enabled": False}, msg="禁用成功")


@router.post("/tools/batch-set")
async def batch_set_tools(tools: list):
    """批量设置工具"""
    return success(data=tools, msg="设置成功")


@router.post("/tools/cache/refresh")
async def refresh_tools_cache():
    """刷新 MCP 工具缓存（当 MCP 服务配置变更时调用）"""
    from agent.mcp.cache_manager import refresh_tool_cache
    await refresh_tool_cache()
    return success(data=None, msg="工具缓存已刷新")


@router.get("/tools/cache/status")
async def get_tools_cache_status():
    """获取工具缓存状态"""
    from agent.mcp.cache_manager import get_cache_manager
    cache = await get_cache_manager()
    
    return success(data={
        "initialized": cache.is_initialized(),
        "total_tools": len(cache.all_tools),
        "total_services": len(cache.services),
        "services": [
            {
                "id": sid,
                "name": sinfo.name,
                "tool_count": len(sinfo.tool_names)
            }
            for sid, sinfo in cache.services.items()
        ]
    }, msg="获取成功")
