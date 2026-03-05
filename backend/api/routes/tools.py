from fastapi import APIRouter
from api.response import success

router = APIRouter()


@router.get("/tools")
async def list_tools():
    """获取所有可用的Agent工具列表"""
    tools = [
        {
            "id": "web_search",
            "name": "网页搜索",
            "description": "搜索互联网获取最新信息",
            "enabled": True
        },
        {
            "id": "calculator",
            "name": "计算器",
            "description": "数学计算工具",
            "enabled": True
        }
    ]
    return success(data=tools, msg="获取成功")


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
