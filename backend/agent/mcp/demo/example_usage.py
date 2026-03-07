"""
MCP 工具使用示例 - 官方风格
使用新的单例模式导入
"""

import asyncio
import os
import sys

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from langchain.agents import create_agent
from backend.agent.mcp import get_mcptools, get_server_configs
from langchain_deepseek import ChatDeepSeek

async def example_basic():
    """基本用法示例"""
    print("=" * 50)
    print("示例: 基本用法")
    print("=" * 50)
    
    # 获取服务器配置
    configs = get_server_configs()
    print(f"\n配置: {configs}")
    
    # 获取工具（使用单例模式）
    tools = await get_mcptools()
    print(f"\n工具列表: {[t.name for t in tools]}")
    
    return tools


async def example_with_agent():
    """在 Agent 中使用 MCP 工具"""
    print("\n" + "=" * 50)
    print("示例: 在 Agent 中使用")
    print("=" * 50)
    
    
 
    # 获取 MCP 工具（使用单例模式）
    tools = await get_mcptools()
    
    if not tools:
        print("⚠️ 没有可用的 MCP 工具")
        return
    print("MCP获取222工具成功")

    # 创建 LLM
    llm = ChatDeepSeek(
        model="doubao-seed-2-0-pro-260215", 
        api_key="6246ef67-931a-4f19-9409-89b42fc04a91", 
        api_base="https://ark.cn-beijing.volces.com/api/v3"
    )
    agent=create_agent(
        llm,
        tools
    )

    messages = [
        {"role": "system", "content": "你是一个可以调用各种工具的助手"},
        {"role": "user", "content": "请帮我查一下北京的最新资讯?"}
    ]
    
    msg={"messages": messages}


    # 流式调用
    # for chunk in agent.stream(messages):
    #     print(chunk.content, end="", flush=True)

    print("M")
    async for token, metadata in agent.astream(msg, stream_mode="messages"):

        node = metadata.get("langgraph_node", "")

        # ==========================================
        # 1. 提取推理过程 (Reasoning)
        # ==========================================
        reasoning = token.additional_kwargs.get("reasoning_content")
        if reasoning:
            print(reasoning, end="", flush=True)

        # ==========================================
        # 2. 提取工具调用动作 (Tool Calls)
        # ==========================================
        # 💡 核心技巧: LangChain 的 tool_call_chunks 在流式传输时，
        # 只有工具发出的"第一帧"会包含 'name' 字段。
        # 我们利用这一点，无需任何状态变量就能实现"只提示一次工具调用"。
        for tc_chunk in getattr(token, "tool_call_chunks", []):
            if tc_chunk.get("name"): 
                print(f"\n\n🧠 正在调用工具: {tc_chunk['name']} ...\n", end="", flush=True)

        # ==========================================
        # 3. 提取常规文本与工具返回结果 (Content)
        # ==========================================
        # LangChain 默认会将生成的文本放在 token.content 中
        if token.content:
            text = token.content
            
            # 兼容某些模型 content 返回 list(dict) 的情况
            if isinstance(text, list):
                text = "".join([b.get("text", "") for b in text if isinstance(b, dict) and b.get("type") == "text"])

            if text:
                if node == "tools":
                    print(f"\n🛠️ 工具返回: {text}\n", end="", flush=True)
                elif node == "model":
                    print(text, end="", flush=True)




    # agent = create_openai_functions_agent(llm, tools, prompt)
    # agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    # # 运行 Agent
    # query = "帮我搜索一下 2026 年最新的 AI 行业趋势"
    # print(f"\n用户查询: {query}")
    
    # result = await agent_executor.ainvoke({
    #     "input": query,
    #     "chat_history": []
    # })
    
    # print(f"\nAgent 回答: {result['output']}")


async def example_direct_usage():
    """直接使用 MultiServerMCPClient（官方示例风格）"""
    print("\n" + "=" * 50)
    print("示例: 直接使用 MultiServerMCPClient")
    print("=" * 50)
    
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain.agents import create_openai_functions_agent, AgentExecutor
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    
    # 获取配置
    server_configs = get_server_configs()
    
    # 创建客户端
    client = MultiServerMCPClient(server_configs)
    
    # 获取工具
    tools = await client.get_tools()
    print(f"加载了 {len(tools)} 个工具: {[t.name for t in tools]}")
    
    # 创建 Agent（与官方示例一致）
    if os.environ.get("OPENAI_API_KEY") and tools:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个有用的助手。"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
        
        # 测试查询
        response = await agent_executor.ainvoke({
            "input": "你好，请介绍一下你自己",
            "chat_history": []
        })
        
        print(f"\n响应: {response['output'][:200]}...")


async def main():
    """运行所有示例"""
    try:
        await example_basic()
    except Exception as e:
        print(f"基本示例失败: {e}")
    
    try:
        await example_with_agent()
    except Exception as e:
        print(f"Agent 示例失败: {e}")
    
    # try:
    #     await example_direct_usage()
    # except Exception as e:
    #     print(f"直接用法示例失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
