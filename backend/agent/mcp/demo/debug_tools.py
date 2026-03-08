"""
调试脚本：检查 MCP 工具的分组情况
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from agent.mcp import (
    get_mcptools_by_service, 
    get_server_config_dict, 
    get_mcptools,
    get_all_mcp_info,
)


async def debug_tools():
    """调试工具分组"""
    print("=" * 60)
    print("MCP 工具分组调试")
    print("=" * 60)
    
    # 1. 检查配置文件（不连接）
    print("\n1. 配置文件中的服务:")
    configs = get_server_config_dict()
    for name, config in configs.items():
        print(f"   - {name}: {config.get('transport', 'stdio')}")
    
    # 2. 获取所有服务信息（不连接）
    print("\n2. 从缓存获取服务信息（不连接）:")
    services = await get_all_mcp_info()
    for service_id, service_info in services.items():
        print(f"   - {service_id}: {service_info.transport.value}, 工具数: {len(service_info.tool_names)}")
    
    # 3. 按需连接获取所有工具
    print("\n3. 按需连接获取所有工具:")
    tools = await get_mcptools()
    for tool in tools:
        print(f"   - {tool.name}")
    
    # 4. 按服务分组
    print("\n4. 按服务分组结果:")
    grouped = await get_mcptools_by_service()
    for service_name, service_tools in grouped.items():
        print(f"\n   【{service_name}】")
        for tool in service_tools:
            print(f"      - {tool.name}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(debug_tools())
