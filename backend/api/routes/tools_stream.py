"""
流式工具列表 API
按 MCP 服务分组返回工具，提供更好的用户体验
使用缓存系统，避免重复加载 MCP 服务
"""

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import json
import asyncio

router = APIRouter()


class StreamingBuffer:
    """用于管理流式输出的缓冲区"""
    def __init__(self):
        self.queue = asyncio.Queue()
        self.closed = False

    async def write(self, data: str):
        """写入数据到缓冲区"""
        if not self.closed:
            await self.queue.put(data)

    async def read(self) -> str:
        """从缓冲区读取数据"""
        if self.closed and self.queue.empty():
            return ""
        try:
            return await self.queue.get()
        except:
            return ""

    def close(self):
        """关闭缓冲区"""
        self.closed = True


async def stream_tools_generator(force_refresh: bool = False):
    """流式生成工具列表（按服务分组）- 使用缓存"""

    # 创建缓冲区
    buffer = StreamingBuffer()

    async def generate():
        """后台生成数据"""
        try:
            # 首先发送加载状态
            await buffer.write(f"data: {json.dumps({'type': 'status', 'message': '正在加载工具...'}, ensure_ascii=False)}\n\n")
            await asyncio.sleep(0.1)

            # 获取默认选中的工具
            from agent.mcp.config_loader import get_default_selected_tools
            default_selected_tools = get_default_selected_tools()

            # 获取普通工具（这些通常是立即可用的）
            from agent.tools import get_regular_tools
            regular_tools = get_regular_tools()

            await buffer.write(f"data: {json.dumps({'type': 'status', 'message': f'发现 {len(regular_tools)} 个基础工具'}, ensure_ascii=False)}\n\n")
            await asyncio.sleep(0.1)

            # 发送内置工具服务（作为一个服务组）
            if regular_tools:
                builtin_tools_data = []
                for tool in regular_tools:
                    builtin_tools_data.append({
                        'toolid': tool.name,
                        'name': tool.name,
                        'description': tool.description,
                        'mcp': 0,
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
                await buffer.write(f"data: {json.dumps(service_data, ensure_ascii=False)}\n\n")
                await asyncio.sleep(0.1)

            # 处理 MCP 工具
            await buffer.write(f"data: {json.dumps({'type': 'status', 'message': '正在加载 MCP 工具...'}, ensure_ascii=False)}\n\n")
            await asyncio.sleep(0.1)

            try:
                from agent.mcp.cache_manager import get_cache_manager
                from agent.mcp.config_loader import load_server_configs
                from agent.mcp.connection_manager import MCPConnectionManager

                cache = await get_cache_manager()

                if force_refresh:
                    await buffer.write(f"data: {json.dumps({'type': 'status', 'message': '正在刷新工具缓存...'}, ensure_ascii=False)}\n\n")

                    configs = load_server_configs()
                    enabled_configs = [cfg for cfg in configs if cfg.enabled]

                    if enabled_configs:
                        await buffer.write(f"data: {json.dumps({'type': 'status', 'message': f'发现 {len(enabled_configs)} 个 MCP 服务'}, ensure_ascii=False)}\n\n")
                        await asyncio.sleep(0.1)

                        connection_manager = MCPConnectionManager()

                        # 逐个连接服务并立即发送
                        for cfg in enabled_configs:
                            try:
                                await buffer.write(f"data: {json.dumps({'type': 'status', 'message': f'正在连接 {cfg.name}...'}, ensure_ascii=False)}\n\n")

                                # 连接服务
                                tools = await connection_manager.connect_service(cfg.name)

                                if tools is not None:
                                    service_info = cache.get_service_info(cfg.name)
                                    if service_info:
                                        tools_data = []
                                        for tool_name in service_info.tool_names:
                                            tool_info = cache.all_tools.get(tool_name)
                                            if tool_info:
                                                tools_data.append({
                                                    'toolid': tool_info.name,
                                                    'name': tool_info.name,
                                                    'description': tool_info.description,
                                                    'mcp': 1,
                                                    'enabled': True
                                                })

                                        display_name = cfg.name.replace('-', ' ').replace('_', ' ').title()

                                        service_data = {
                                            'type': 'service',
                                            'service': {
                                                'id': cfg.name,
                                                'name': display_name,
                                                'description': f'{display_name} MCP 服务',
                                                'toolCount': len(tools_data),
                                                'tools': tools_data,
                                                'source': 'mcp'
                                            }
                                        }
                                        await buffer.write(f"data: {json.dumps(service_data, ensure_ascii=False)}\n\n")
                                        await asyncio.sleep(0.05)
                                else:
                                    await buffer.write(f"data: {json.dumps({'type': 'warning', 'message': f'{cfg.name} 连接失败'}, ensure_ascii=False)}\n\n")

                            except Exception as e:
                                await buffer.write(f"data: {json.dumps({'type': 'warning', 'message': f'{cfg.name} 连接失败: {str(e)}'}, ensure_ascii=False)}\n\n")

                        await cache.save_to_file()
                        await buffer.write(f"data: {json.dumps({'type': 'status', 'message': '工具缓存已刷新'}, ensure_ascii=False)}\n\n")
                    else:
                        await buffer.write(f"data: {json.dumps({'type': 'status', 'message': '没有启用的 MCP 服务'}, ensure_ascii=False)}\n\n")
                else:
                    services = cache.get_all_services()
                    total_mcp_tools = len(cache.all_tools)

                    if services:
                        await buffer.write(f"data: {json.dumps({'type': 'status', 'message': f'发现 {len(services)} 个 MCP 服务，共 {total_mcp_tools} 个工具'}, ensure_ascii=False)}\n\n")
                        await asyncio.sleep(0.1)

                        for service_name, service_info in services.items():
                            tools_data = []
                            for tool_name in service_info.tool_names:
                                tool_info = cache.all_tools.get(tool_name)
                                if tool_info:
                                    tools_data.append({
                                        'toolid': tool_info.name,
                                        'name': tool_info.name,
                                        'description': tool_info.description,
                                        'mcp': 1,
                                        'enabled': True
                                    })

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
                            await buffer.write(f"data: {json.dumps(service_data, ensure_ascii=False)}\n\n")
                            await asyncio.sleep(0.05)
                    else:
                        await buffer.write(f"data: {json.dumps({'type': 'status', 'message': 'MCP 服务暂无可用工具'}, ensure_ascii=False)}\n\n")

            except Exception as e:
                await buffer.write(f"data: {json.dumps({'type': 'warning', 'message': f'MCP 工具加载失败: {str(e)}'}, ensure_ascii=False)}\n\n")

            # 发送完成状态
            total_services = 1 if regular_tools else 0
            total_tools = len(regular_tools)
            try:
                from agent.mcp.cache_manager import get_cache_manager
                cache = await get_cache_manager()
                services = cache.get_all_services()
                total_services += len(services)
                total_tools += len(cache.all_tools)
            except:
                pass

            await buffer.write(f"data: {json.dumps({'type': 'complete', 'total': total_tools, 'services': total_services, 'message': f'共加载 {total_services} 个服务，{total_tools} 个工具', 'defaultSelectedTools': default_selected_tools}, ensure_ascii=False)}\n\n")

        except Exception as e:
            await buffer.write(f"data: {json.dumps({'type': 'error', 'message': f'加载失败: {str(e)}'}, ensure_ascii=False)}\n\n")
        finally:
            buffer.close()

    # 启动后台生成任务
    generate_task = asyncio.create_task(generate())

    # 实时读取并返回数据
    while True:
        data = await buffer.read()
        if not data and buffer.closed:
            break
        if data:
            yield data
        else:
            await asyncio.sleep(0.01)

    # 等待生成任务完成
    try:
        await generate_task
    except:
        pass


@router.get("/tools/stream")
async def list_tools_stream(refresh: bool = Query(False, description="是否强制刷新 MCP 缓存")):
    """流式获取所有可用的Agent工具列表（按服务分组）- 使用缓存"""
    return StreamingResponse(
        stream_tools_generator(force_refresh=refresh),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked",
        }
    )
