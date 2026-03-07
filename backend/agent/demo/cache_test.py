"""
缓存机制全面测试
多次读取测试缓存是否正常工作
"""

import asyncio
import sys
import os

# 添加后端路径到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agent import get_all_tools, clear_tools_cache


async def test_multiple_cache_reads():
    """多次读取测试缓存"""
    print("=" * 60)
    print("多次缓存读取测试")
    print("=" * 60)
    
    # 清除缓存，从头开始
    clear_tools_cache()
    
    results = []
    
    # 第一次读取 - 应该加载
    print("\n【第1次读取】应该加载...")
    tools1 = await get_all_tools()
    results.append(tools1)
    print(f"  工具数: {len(tools1)}, 对象ID: {id(tools1)}")
    
    # 第2-10次读取 - 应该从缓存获取
    for i in range(2, 11):
        print(f"\n【第{i}次读取】应该从缓存获取...")
        tools = await get_all_tools()
        results.append(tools)
        print(f"  工具数: {len(tools)}, 对象ID: {id(tools)}")
        
        # 验证是否是同一个对象
        is_same = tools is results[0]
        print(f"  与第1次是同一个对象: {is_same}")
        
        if not is_same:
            print(f"  ⚠️ 警告: 缓存可能未生效！")
    
    # 验证所有结果都是同一个对象
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)
    
    all_same = all(t is results[0] for t in results)
    print(f"\n所有读取都是同一个对象: {all_same}")
    
    if all_same:
        print("✅ 缓存机制工作正常！")
    else:
        print("❌ 缓存机制有问题！")
    
    # 显示对象ID列表
    print(f"\n对象ID列表:")
    for i, tools in enumerate(results, 1):
        print(f"  第{i}次: {id(tools)}")


async def test_cache_after_clear():
    """测试清除缓存后重新加载"""
    print("\n" + "=" * 60)
    print("清除缓存后重新加载测试")
    print("=" * 60)
    
    # 先获取一次
    print("\n【获取工具】")
    tools1 = await get_all_tools()
    id1 = id(tools1)
    print(f"  对象ID: {id1}")
    
    # 清除缓存
    print("\n【清除缓存】")
    clear_tools_cache()
    
    # 再次获取
    print("\n【重新获取】")
    tools2 = await get_all_tools()
    id2 = id(tools2)
    print(f"  对象ID: {id2}")
    
    # 验证是否是不同对象
    print(f"\n两次获取是不同对象: {id1 != id2}")
    
    if id1 != id2:
        print("✅ 清除缓存后正确重新加载！")
    else:
        print("❌ 清除缓存未生效！")


async def test_parallel_access():
    """测试并行访问缓存"""
    print("\n" + "=" * 60)
    print("并行访问缓存测试")
    print("=" * 60)
    
    # 清除缓存
    clear_tools_cache()
    
    # 同时发起多个请求
    print("\n【同时发起5个请求】")
    tasks = [get_all_tools() for _ in range(5)]
    results = await asyncio.gather(*tasks)
    
    # 验证结果
    print(f"\n获取到的对象ID:")
    for i, tools in enumerate(results, 1):
        print(f"  请求{i}: {id(tools)}")
    
    # 验证是否都是同一个对象
    all_same = all(r is results[0] for r in results)
    print(f"\n所有请求返回同一个对象: {all_same}")
    
    if all_same:
        print("✅ 并行访问缓存正常！")
    else:
        print("❌ 并行访问有问题！")


async def main():
    """运行所有测试"""
    try:
        await test_multiple_cache_reads()
    except Exception as e:
        print(f"\n❌ 多次读取测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        await test_cache_after_clear()
    except Exception as e:
        print(f"\n❌ 清除缓存测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        await test_parallel_access()
    except Exception as e:
        print(f"\n❌ 并行访问测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
