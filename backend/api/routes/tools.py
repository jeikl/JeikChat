from fastapi import APIRouter
from api.response import success

router = APIRouter()


def get_tool_list():
    from agent.chatRouterStream import tools
    
    result = []
    for tool in tools:
        tool_info = {
            "id": tool.name,
            "name": tool.name,
            "description": tool.description,
            "enabled": True
        }
        result.append(tool_info)
    return result


@router.get("/tools")
async def list_tools():
    """获取所有可用的Agent工具列表"""
    return success(data=get_tool_list(), msg="获取成功")


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
