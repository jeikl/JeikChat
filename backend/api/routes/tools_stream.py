"""
流式工具列表 API
按 MCP 服务分组返回工具，提供更好的用户体验
使用缓存系统，避免重复加载 MCP 服务
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
import asyncio

router = APIRouter()


async def stream_tools_generator():
    """流式生成工具列表（按服务分组）- 使用缓存"""

    # 首先发送加载状态
    yield f"data: {json.dumps({'type': 'status', 'message': '正在加载工具...'}, ensure_ascii=False)}\n\n"
    await asyncio.sleep(0.1)

    try:
        # 获取普通工具（这些通常是立即可用的）
        from agent.tools import get_regular_tools
        regular_tools = get_regular_tools()

        yield f"data: {json.dumps({'type': 'status', 'message': f'发现 {len(regular_tools)} 个基础工具'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        # 发送内置工具服务（作为一个服务组）
        if regular_tools:
            builtin_tools_data = []
            for tool in regular_tools:
                builtin_tools_data.append({
                    'toolid': tool.name,
                    'name': tool.name,
                    'description': tool.description,
                    'mcp': 0,  # 0 表示普通工具
                    'enabled': True
                })

            service_data = {
                'type': 'service',
                'service': {
                    'id': 'built-in',
                    'name': '内置工具',
                    'description': '系统内置的基础工具',
                    'toolCount': len(regular_tools),
                    'tools': builtin_tools_data,
                    'source': 'built-in'
                }
            }
            yield f"data: {json.dumps(service_data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

        # 从缓存获取 MCP 工具（O(1) 查询，不连接服务）
        yield f"data: {json.dumps({'type': 'status', 'message': '正在加载 MCP 工具...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.2)

        try:
            from agent.mcp.cache_manager import get_cache_manager
            cache = await get_cache_manager()

            # 获取所有服务和工具
            services = cache.get_all_services()
            total_mcp_tools = len(cache.all_tools)

            if services:
                yield f"data: {json.dumps({'type': 'status', 'message': f'发现 {len(services)} 个 MCP 服务，共 {total_mcp_tools} 个工具'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

                # 逐个发送 MCP 服务
                for service_name, service_info in services.items():
                    # 从缓存的 all_tools 中获取该服务的工具
                    tools_data = []
                    for tool_name in service_info.tool_names:
                        tool_info = cache.all_tools.get(tool_name)
                        if tool_info:
                            # 返回带服务前缀的 toolid，与前端期望的格式一致
                            toolid_with_prefix = f"{service_name}_{tool_info.name}"
                            tools_data.append({
                                'toolid': toolid_with_prefix,
                                'name': tool_info.name,
                                'description': tool_info.description,
                                'mcp': 1,  # 1 表示 MCP 工具
                                'enabled': True
                            })

                    # 生成友好的服务显示名称
                    display_name = service_name.replace('-', ' ').replace('_', ' ').title()

                    service_data = {
                        'type': 'service',
                        'service': {
                            'id': service_name,
                            'name': display_name,
                            'description': f'{display_name} MCP 服务',
                            'toolCount': len(tools_data),
                            'tools': tools_data,
                            'source': 'mcp'
                        }
                    }
                    yield f"data: {json.dumps(service_data, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.05)
            else:
                yield f"data: {json.dumps({'type': 'status', 'message': 'MCP 服务暂无可用工具'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'warning', 'message': f'MCP 工具加载失败: {str(e)}'}, ensure_ascii=False)}\n\n"

        # 发送完成状态
        total_services = 1 if regular_tools else 0  # 内置工具服务
        total_tools = len(regular_tools)
        try:
            from agent.mcp.cache_manager import get_cache_manager
            cache = await get_cache_manager()
            services = cache.get_all_services()
            total_services += len(services)
            total_tools += len(cache.all_tools)
        except:
            pass

        yield f"data: {json.dumps({'type': 'complete', 'total': total_tools, 'services': total_services, 'message': f'共加载 {total_services} 个服务，{total_tools} 个工具'}, ensure_ascii=False)}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': f'加载失败: {str(e)}'}, ensure_ascii=False)}\n\n"


@router.get("/tools/stream")
async def list_tools_stream():
    """流式获取所有可用的Agent工具列表（按服务分组）- 使用缓存"""
    return StreamingResponse(
        stream_tools_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
