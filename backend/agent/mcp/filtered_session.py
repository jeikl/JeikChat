"""
使用过滤后的 stdio 客户端创建 MCP 会话
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters

from .filtered_stdio import filtered_stdio_client


@asynccontextmanager
async def create_filtered_stdio_session(
    server_params: StdioServerParameters,
    **session_kwargs: Any,
) -> AsyncIterator[ClientSession]:
    """
    创建使用过滤 stdio 客户端的 MCP 会话
    自动忽略非 JSON 输出（如日志）
    
    Args:
        server_params: 服务器参数
        **session_kwargs: 传递给 ClientSession 的额外参数
        
    Yields:
        已初始化的 ClientSession
    """
    async with filtered_stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream, **session_kwargs) as session:
            yield session
