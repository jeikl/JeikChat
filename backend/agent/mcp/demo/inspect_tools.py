"""
查看 MCP 工具的详细信息
"""
import asyncio
from mcp_loader import get_mcp_tools


async def inspect_tools():
    """检查所有 MCP 工具的详细信息"""
    tools = await get_mcp_tools()
    
    print("=" * 60)
    print("MCP 工具详细信息")
    print("=" * 60)
    
    for i, tool in enumerate(tools, 1):
        print(f"\n【工具 {i}】{tool.name}")
        print("-" * 40)
        print(f"描述: {tool.description}")
        print(f"\n参数模式:")
        if hasattr(tool, 'args_schema'):
            print(f"  {tool.args_schema.schema()}")
        print()


if __name__ == "__main__":
    asyncio.run(inspect_tools())
