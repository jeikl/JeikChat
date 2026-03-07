"""
调试脚本：检查 MCP 工具的分组情况
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from agent.mcp import get_mcptools_by_service, _get_server_configs, get_mcptools


async def debug_tools():
    """调试工具分组"""
    print("=" * 60)
    print("MCP 工具分组调试")
    print("=" * 60)
    
    # 1. 检查配置文件
    print("\n1. 配置文件中的服务:")
    configs = _get_server_configs()
    for name, config in configs.items():
        print(f"   - {name}: {config.get('transport', 'stdio')}")
    
    # 2. 获取所有工具
    print("\n2. 获取到的所有工具:")
    tools = await get_mcptools()
    for tool in tools:
        print(f"   - {tool.name}")
    
    # 3. 按服务分组
    print("\n3. 按服务分组结果:")
    grouped = await get_mcptools_by_service()
    for service_name, service_tools in grouped.items():
        print(f"\n   【{service_name}】")
        for tool in service_tools:
            print(f"      - {tool.name}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(debug_tools())
