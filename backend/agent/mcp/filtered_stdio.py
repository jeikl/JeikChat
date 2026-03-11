"""
过滤非 JSON 输出的 MCP stdio 客户端
解决 MCP 服务器输出日志到 stdout 的问题
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import TextIO

import anyio
import anyio.lowlevel
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from anyio.streams.text import TextReceiveStream

import mcp.types as types
from mcp.client.stdio import StdioServerParameters
from mcp.shared.message import SessionMessage

logger = logging.getLogger(__name__)


async def _create_process(server: StdioServerParameters, errlog: TextIO):
    """创建子进程"""
    import sys
    from pathlib import Path
    
    # 导入必要的函数
    from mcp.client.stdio import get_default_environment
    from mcp.os.win32.utilities import create_windows_process
    
    # 获取可执行命令
    if sys.platform == "win32":
        from mcp.os.win32.utilities import get_windows_executable_command
        command = get_windows_executable_command(server.command)
    else:
        command = server.command
    
    # 创建进程
    if sys.platform == "win32":
        return await create_windows_process(
            command=command,
            args=server.args,
            env=({**get_default_environment(), **server.env} if server.env is not None else get_default_environment()),
            errlog=errlog,
            cwd=server.cwd,
        )
    else:
        return await anyio.open_process(
            [command, *server.args],
            env=({**get_default_environment(), **server.env} if server.env is not None else get_default_environment()),
            stderr=errlog,
            cwd=server.cwd,
            start_new_session=True,
        )


@asynccontextmanager
async def filtered_stdio_client(server: StdioServerParameters, errlog: TextIO = sys.stderr):
    """
    过滤非 JSON 输出的 stdio 客户端
    自动忽略无法解析为 JSON-RPC 的行（如日志输出）
    """
    read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
    read_stream_writer: MemoryObjectSendStream[SessionMessage | Exception]

    write_stream: MemoryObjectSendStream[SessionMessage]
    write_stream_reader: MemoryObjectReceiveStream[SessionMessage]

    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    try:
        # 创建进程
        process = await _create_process(server, errlog)
    except OSError:
        # Clean up streams if process creation fails
        await read_stream.aclose()
        await write_stream.aclose()
        await read_stream_writer.aclose()
        await write_stream_reader.aclose()
        raise

    async def stdout_reader():
        assert process.stdout, "Opened process is missing stdout"

        try:
            async with read_stream_writer:
                buffer = ""
                async for chunk in TextReceiveStream(
                    process.stdout,
                    encoding=server.encoding,
                    errors=server.encoding_error_handler,
                ):
                    lines = (buffer + chunk).split("\n")
                    buffer = lines.pop()

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 只处理看起来像 JSON 的行（以 { 或 [ 开头）
                        if not (line.startswith('{') or line.startswith('[')):
                            # 非 JSON 行，记录到日志但不发送错误
                            logger.debug(f"Filtered non-JSON output: {line[:100]}...")
                            continue
                        
                        try:
                            message = types.JSONRPCMessage.model_validate_json(line)
                        except Exception as exc:
                            # JSON 解析失败，记录但不中断连接
                            logger.debug(f"Failed to parse JSON: {line[:100]}... - {exc}")
                            continue

                        session_message = SessionMessage(message)
                        await read_stream_writer.send(session_message)
        except anyio.ClosedResourceError:
            await anyio.lowlevel.checkpoint()

    async def stdin_writer():
        assert process.stdin, "Opened process is missing stdin"

        try:
            async with write_stream_reader:
                async for session_message in write_stream_reader:
                    json = session_message.message.model_dump_json(by_alias=True, exclude_none=True)
                    await process.stdin.send(
                        (json + "\n").encode(
                            encoding=server.encoding,
                            errors=server.encoding_error_handler,
                        )
                    )
        except anyio.ClosedResourceError:
            await anyio.lowlevel.checkpoint()

    # 手动启动任务
    stdout_task = asyncio.create_task(stdout_reader())
    stdin_task = asyncio.create_task(stdin_writer())
    
    try:
        yield read_stream, write_stream
    finally:
        # 取消任务
        stdout_task.cancel()
        stdin_task.cancel()
        
        # 关闭流
        await write_stream.aclose()
        await write_stream_reader.aclose()
        await read_stream.aclose()
        await read_stream_writer.aclose()
        
        # 终止进程
        try:
            process.terminate()
        except Exception:
            pass
