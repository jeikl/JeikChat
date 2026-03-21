"""
MCP 配置更新器
处理单个服务的工具更新逻辑
"""

from typing import Dict, Any, Optional
from agent.mcp.cache_manager import MCPCacheManager
from agent.mcp.models import MCPServiceInfo, MCPToolInfo, TransportType


async def update_server_tools(
    server_name: str,
    server_config: Dict[str, Any],
    cache: MCPCacheManager
) -> Dict[str, Any]:
    """
    更新单个服务的工具信息
    
    逻辑：
    1. 检查缓存中是否已有该服务的工具信息
    2. 如果有且配置未变，直接使用缓存
    3. 如果没有或配置已变，连接服务获取工具
    
    Returns:
        {
            "status": "cached" | "connected" | "failed",
            "tools_count": int,
            "error": str (optional)
        }
    """
    transport = server_config.get("transport", "stdio")
    
    # 检查缓存中是否已有该服务
    if server_name in cache.services:
        existing_service = cache.services[server_name]
        
        # 检查配置是否相同（简单比较关键字段）
        config_unchanged = (
            existing_service.transport.value == transport and
            len(existing_service.tool_names) > 0  # 有工具信息
        )
        
        if config_unchanged:
            # 配置未变，直接使用缓存
            print(f"[MCP Config] 服务 {server_name} 已存在缓存中，直接使用")
            return {
                "status": "cached",
                "tools_count": len(existing_service.tool_names)
            }
    
    # 需要连接服务获取工具
    try:
        tools = await _connect_and_get_tools(server_name, server_config)
        
        if tools is None:
            return {
                "status": "failed",
                "tools_count": 0,
                "error": "连接服务失败"
            }
        
        # 更新缓存
        service_info = MCPServiceInfo(
            id=server_name,
            name=server_name,
            transport=TransportType(transport),
            config=None,
            tool_names=[tool.name for tool in tools],
            enabled=server_config.get("enabled", True),
            status="connected"
        )
        
        cache.services[server_name] = service_info
        
        # 更新工具信息
        for tool in tools:
            cache.all_tools[tool.name] = tool
        
        print(f"[MCP Config] 服务 {server_name} 连接成功，获取 {len(tools)} 个工具")
        
        return {
            "status": "connected",
            "tools_count": len(tools)
        }
        
    except Exception as e:
        print(f"[MCP Config] 服务 {server_name} 连接失败: {e}")
        return {
            "status": "failed",
            "tools_count": 0,
            "error": str(e)
        }


async def _connect_and_get_tools(
    server_name: str,
    server_config: Dict[str, Any]
) -> Optional[list]:
    """
    连接 MCP 服务并获取工具列表
    直接使用配置连接，不依赖配置文件
    """
    from agent.mcp.models import MCPServerConfig, TransportType, MCPToolInfo
    from agent.mcp.filtered_session import create_filtered_stdio_session
    from mcp.client.stdio import StdioServerParameters
    from mcp import ClientSession
    
    transport_str = server_config.get("transport", "stdio")
    transport = TransportType(transport_str)
    
    # 构建 MCPServerConfig
    cfg = MCPServerConfig(
        name=server_name,
        transport=transport,
        command=server_config.get("command"),
        args=server_config.get("args", []),
        env=server_config.get("env", {}),
        url=server_config.get("url"),
        headers=server_config.get("headers", {}),
        timeout=server_config.get("timeout", 30),
        enabled=server_config.get("enabled", True)
    )
    
    try:
        if transport == TransportType.STDIO:
            # STDIO 连接
            server_params = StdioServerParameters(
                command=cfg.command,
                args=cfg.args,
                env=cfg.env,
            )
            
            async with create_filtered_stdio_session(server_params) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                
                if not tools_result.tools:
                    return []
                
                tools = []
                for tool_spec in tools_result.tools:
                    # 构建带前缀的工具名
                    prefixed_name = f"{server_name}_{tool_spec.name}"
                    
                    tool_info = MCPToolInfo(
                        name=prefixed_name,
                        original_name=tool_spec.name,
                        description=tool_spec.description or f"【{server_name}】 {tool_spec.name}",
                        service_id=server_name,
                        service_name=server_name,
                        args_schema=getattr(tool_spec, 'inputSchema', None)
                    )
                    tools.append(tool_info)
                
                return tools
        else:
            # SSE/HTTP 连接
            from agent.mcp.connection_manager import MCPConnectionManager
            connection_manager = MCPConnectionManager()
            # 对于非 STDIO，使用 connection_manager 的标准方法
            # 但先临时添加到配置中
            tools = await connection_manager._connect_service_standard(server_name, cfg)
            
            # 转换为 MCPToolInfo
            tool_infos = []
            for tool in tools:
                tool_infos.append(MCPToolInfo(
                    name=tool.name,
                    original_name=tool.name.replace(f"{server_name}_", ""),
                    description=tool.description or f"【{server_name}】 {tool.name}",
                    service_id=server_name,
                    service_name=server_name,
                    args_schema=None
                ))
            return tool_infos
            
    except Exception as e:
        print(f"[MCP Config] 连接服务 {server_name} 失败: {e}")
        import traceback
        traceback.print_exc()
        return None
