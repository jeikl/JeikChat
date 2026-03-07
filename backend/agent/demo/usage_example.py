"""
Agent 模块使用示例
测试获取所有工具并输出工具名
"""

import asyncio
import sys
import os

# 添加后端路径到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agent import get_all_tools, get_all_tools_sync, clear_tools_cache
from agent.mcp import (
    get_mcptools_by_service, 
    get_mcptools_by_service_sync,
    get_mcptools,
    get_mcptools_sync,
    _get_services_list,
    MCPService
)


async def test_async_tools():
    """异步获取所有工具并输出"""
    print("=" * 60)
    print("测试: 异步获取所有工具")
    print("=" * 60)
    
    tools = await get_all_tools()
    
    print(f"\n✅ 成功获取 {len(tools)} 个工具:")
    for i, tool in enumerate(tools, 1):
        print(f"  {i}. {tool.name}")
    
    return tools


def test_sync_tools():
    """同步获取所有工具并输出"""
    print("\n" + "=" * 60)
    print("测试: 同步获取所有工具")
    print("=" * 60)
    
    tools = get_all_tools_sync()
    
    print(f"\n✅ 成功获取 {len(tools)} 个工具:")
    for i, tool in enumerate(tools, 1):
        print(f"  {i}. {tool.name}")
    
    return tools


async def test_cache():
    """测试缓存机制"""
    print("\n" + "=" * 60)
    print("测试: 缓存机制")
    print("=" * 60)
    
    # 第一次获取
    print("\n第一次获取...")
    tools1 = await get_all_tools()
    print(f"工具数量: {len(tools1)}")
    
    # 第二次获取（应该从缓存读取）
    print("\n第二次获取（从缓存）...")
    tools2 = await get_all_tools()
    print(f"工具数量: {len(tools2)}")
    print(f"是否是同一个对象: {tools1 is tools2}")
    
    # # 清除缓存
    # print("\n清除缓存...")
    # clear_tools_cache()
    
    # 第三次获取（重新加载）
    print("第三次获取（重新加载）...")
    tools3 = await get_all_tools()
    print(f"工具数量: {len(tools3)}")


async def test_grouped_tools():
    """测试按服务分组获取工具（新架构：每个服务独立连接）"""
    print("\n" + "=" * 60)
    print("测试: 按服务分组获取工具（每个服务独立连接）")
    print("=" * 60)
    
    # 1. 显示配置文件中的服务
    print("\n1. 配置文件中的服务:")
    services_list = _get_services_list()
    for service in services_list:
        name = service.get('name', 'unknown')
        transport = service.get('transport', 'stdio')
        print(f"   - {name} (transport: {transport})")
    
    # 2. 获取分组后的工具
    print("\n2. 按服务分组结果:")
    grouped = await get_mcptools_by_service()
    
    total_tools = 0
    for service_name, tools in grouped.items():
        print(f"\n   【{service_name}】 - {len(tools)} 个工具")
        for tool in tools:
            print(f"      - {tool.name}")
        total_tools += len(tools)
    
    print(f"\n   总计: {len(grouped)} 个服务，{total_tools} 个工具")
    
    # 3. 验证所有工具都已分组
    all_tools = await get_mcptools()
    if len(all_tools) == total_tools:
        print(f"\n   ✅ 所有工具都已正确分组 ({len(all_tools)} / {total_tools})")
    else:
        print(f"\n   ⚠️  工具数量不匹配: 总计 {len(all_tools)}，分组统计 {total_tools}")


def test_sync_grouped_tools():
    """同步测试按服务分组获取工具"""
    print("\n" + "=" * 60)
    print("测试: 同步按服务分组获取工具")
    print("=" * 60)
    
    grouped = get_mcptools_by_service_sync()
    
    total_tools = 0
    for service_name, tools in grouped.items():
        print(f"\n   【{service_name}】 - {len(tools)} 个工具")
        for tool in tools:
            print(f"      - {tool.name}")
        total_tools += len(tools)
    
    print(f"\n   总计: {len(grouped)} 个服务，{total_tools} 个工具")


async def test_individual_services():
    """测试单独获取每个服务的工具"""
    print("\n" + "=" * 60)
    print("测试: 单独获取每个服务的工具")
    print("=" * 60)
    
    from agent.mcp import _load_all_services
    
    services = await _load_all_services()
    
    for name, service in services.items():
        print(f"\n   服务: {name}")
        print(f"   传输方式: {service.transport}")
        print(f"   工具数量: {len(service.tools)}")
        print(f"   工具列表:")
        for tool in service.tools:
            print(f"      - {tool.name}")


async def main():
    """运行所有测试"""
    tests = [
        ("异步获取所有工具", test_async_tools),
        ("同步获取所有工具", test_sync_tools),
        ("缓存机制", test_cache),
        ("按服务分组获取工具", test_grouped_tools),
        ("同步按服务分组获取工具", test_sync_grouped_tools),
        ("单独获取每个服务的工具", test_individual_services),
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"开始测试: {test_name}")
            print(f"{'='*60}")
            
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
                
            print(f"\n✅ {test_name} 测试通过")
        except Exception as e:
            print(f"\n❌ {test_name} 测试失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
