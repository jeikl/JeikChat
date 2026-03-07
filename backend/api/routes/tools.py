from fastapi import APIRouter
from api.response import success

router = APIRouter()


async def get_tool_list():
    """
    获取工具列表，优先从缓存加载
    返回格式包含 mcp 标记，用于前端区分 MCP 工具和普通工具
    """
    from agent.mcp.mcp_cache import get_tool_cache, get_all_cached_tools
    from agent.tools import get_regular_tools

    # 获取缓存实例（确保已初始化）
    cache = await get_tool_cache()

    # 获取普通工具（内置工具）
    regular_tools = get_regular_tools()
    regular_tool_names = {t.name for t in regular_tools}

    # 获取 MCP 工具（从缓存）
    mcp_tools = await get_all_cached_tools()
    mcp_tool_names = {t.name for t in mcp_tools}

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

    # 添加 MCP 工具（mcp=1）
    for tool in mcp_tools:
        if tool.name not in regular_tool_names:
            all_tools.append({
                "toolid": tool.name,
                "name": tool.name,
                "description": tool.description,
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
    from agent.mcp.mcp_cache import refresh_tool_cache
    await refresh_tool_cache()
    return success(data=None, msg="工具缓存已刷新")


@router.get("/tools/cache/status")
async def get_tools_cache_status():
    """获取工具缓存状态"""
    from agent.mcp.mcp_cache import get_tool_cache
    cache = await get_tool_cache()
    
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
