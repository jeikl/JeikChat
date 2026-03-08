


import httpx
import sys
from pathlib import Path

# 添加 backend 目录到路径
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from agent.tools.ToolsProtect import McpToolNode

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, START, END #状态图 开始 结束
from langgraph.prebuilt import ToolNode, tools_condition #工具节点 工具条件
from langgraph.graph.message import MessagesState #基础状态图
from langchain_core.messages import AIMessage, ToolMessage # 基础消息类型 工具消息类型
from langchain_deepseek import ChatDeepSeek # 深度求索模型
from typing import Dict, Any # 字典 任意类型






class GuardedToolNode(ToolNode):
    """
    带守卫机制的工具节点

    继承自 ToolNode，增加参数校验逻辑
    防止 LLM 生成无效的工具调用参数
    """
    async def ainvoke(self, input: Dict[str, Any], config: Dict[str, Any] = None):
        """
        异步调用工具节点

        Args:
            input: 包含 messages 的状态字典
            config: 可选配置字典

        Returns:
            包含工具响应消息的字典
        """
        print("  [DEBUG] 进入 tools 节点")

        # 提取最后一条消息
        if "messages" in input:
            last_msg = input["messages"][-1]
        else:
            last_msg = input

        # 检查是否为 AI 消息且有工具调用
        if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
            return {"messages": []}

        responses = []
        # 遍历所有工具调用
        for tc in last_msg.tool_calls:
            name = tc["name"]  # 工具名称
            args = tc.get("args", {})  # 工具参数
            tid = tc.get("id", "no-id")  # 工具调用 ID

            # 守卫机制：bing_search 工具的 query 参数校验
            if "bing" in name.lower():
                query = args.get("query", "")
                # 检查 query 有效性
                if not query or not isinstance(query, str) or not query.strip():
                    print(f"  [DEBUG] 守卫拦截：query 无效 {args}")
                    responses.append(ToolMessage(
                        content="工具调用失败：'query' 参数为空或无效。请重新生成完整参数。",
                        tool_call_id=tid,
                        name=name,
                        status="error"
                    ))
                    continue  # 跳过本次循环

            # 执行工具调用
            try:
                print(f"  [DEBUG] 执行工具 {name} with args {args}")
                tool = self.tools_by_name[name]  # 获取工具实例
                result = await tool.ainvoke(args)  # 异步调用
                responses.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tid,
                    name=name
                ))
            except httpx.RemoteProtocolError as e:
                # MCP 服务器连接异常
                print(f"  [ERROR] MCP 服务器异常关闭连接：{str(e)}")
                responses.append(ToolMessage(
                    content=(
                        f"bing_search 工具调用失败：服务器连接中断（RemoteProtocolError: {str(e)}）。\n"
                        "可能原因：参数无效、服务器临时问题或配额限制。\n"
                        "请尝试修改 query（简化或换关键词）后重新调用，或稍后重试。"
                    ),
                    tool_call_id=tid,
                    name=name,
                    status="error"
                ))
            except Exception as e:
                # 其他异常
                print(f"  [ERROR] 其他工具执行异常：{str(e)}")
                responses.append(ToolMessage(
                    content=f"工具执行失败：{str(e)}。请检查参数。",
                    tool_call_id=tid,
                    name=name,
                    status="error"
                ))

        print("  [DEBUG] tools 节点完成")
        return {"messages": responses}

async def example_with_agent():

    print("\n" + "=" * 50)
    print("示例：在 Agent 中使用（修复版 LangGraph + Guarded ToolNode）")
    print("=" * 50)

    # 初始化 MCP 多服务器客户端
    client = MultiServerMCPClient({
        "bing-cn-mcp-server": {
            "transport": "streamable_http",  # HTTP 流式传输
            "url": "https://mcp.api-inference.modelscope.net/7fcb19ec6e704b/mcp",
        }
    })

    # 获取所有可用工具
    tools = await client.get_tools()
    if not tools:
        print("⚠️ 没有可用的 MCP 工具")
        return
    print("MCP 获取工具成功")

    # 初始化 DeepSeek 模型
    llm = ChatDeepSeek(
        model="qwen-plus",
        api_key="sk-0bcb72d37754406c80b74211c3402d5d",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # 将工具绑定到 LLM
    llm_with_tools = llm.bind_tools(tools)

    # 定义 Agent 节点函数
    async def call_model(state: MessagesState):
        """
        Agent 节点核心逻辑
        
        Args:
            state: MessagesState，包含历史消息
            
        Returns:
            包含 LLM 响应的状态更新
        """
        print("  [DEBUG] 进入 agent 节点，正在调用 LLM...")
        response = await llm_with_tools.ainvoke(state["messages"])
        print("  [DEBUG] LLM 调用完成")
        return {"messages": [response]}

    # 创建守卫工具节点  拓展tools功能 重写aiinvoke
    #tool_node = GuardedToolNode(tools)
    tool_node = McpToolNode(tools)
    # 构建 LangGraph 工作流
    #设定状态图
    workflow = StateGraph(MessagesState)

    #workflow.add_node(Node名, 对应函数或Lambda表达式)  # Agent：思考决策

    # 添加节点
    #大模型核心代理节点
    workflow.add_node("agent", call_model)  # Agent：思考决策


    #工具节点
    workflow.add_node("tools", tool_node)   # Tools：执行工具

    # 设置入口
    workflow.add_edge(START, "agent")

    # 添加条件边
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: END}  # 有工具调用 返回的字符串state为tools则映射到tools节点，否则→结束
    )

    # 添加工具回路
    workflow.add_edge("tools", "agent")  # 工具完成后回 Agent

    # 编译工作流
    graph = workflow.compile()

    # 准备初始对话
    messages = [
        {"role": "system", "content": """你是一个新闻助手。
        1. 搜索时优先关注结果的时间戳。
        2. 如果连续两次搜索都没有找到当日的具体新闻条目，请直接告诉用户目前网络搜索结果多为旅游资讯，并提供已找到的相关动态。
        3. 严禁陷入无限重复搜索的死循环。最多尝试 2 次不同关键词 就可以总结了。"""},
        {"role": "user", "content": "请帮我查一下北京的最新资讯？"}
    ]
    
    input_state = {"messages": messages}
    
    print("M")  # 标记开始
        
    
    try:
        async for mode, data in graph.astream(input_state, stream_mode=["messages", "updates"]):

            # --- 情况 A: 细粒度流处理 (messages) ---
            if mode == "messages":
                chunk, _ = data

                # 1. 提取推理内容 (Reasoning / Thinking)
                # 兼容 deepseek 等模型的思维链字段
                if hasattr(chunk, "additional_kwargs"):
                    reasoning = chunk.additional_kwargs.get("reasoning_content", "")
                    if reasoning:
                        print(f"{reasoning}", end="", flush=True)

                # 2. 提取正式回答内容
                if hasattr(chunk, "content") and chunk.content:
                    print(chunk.content, end="", flush=True)

            # --- 情况 B: 节点状态处理 (updates) ---
            elif mode == "updates":
                for node, state in data.items():
                    if node == "agent":
                        # 检查是否有工具调用动作
                        msgs = state.get("messages", [])
                        if msgs and hasattr(msgs[-1], "tool_calls") and msgs[-1].tool_calls:
                            tool_name = msgs[-1].tool_calls[0]['name']
                            print(f"\n\n🛠️  [系统动作] 正在调用工具: {tool_name}...")

                    elif node == "tools":
                        print(f"✅ [系统动作] 工具执行完毕，获取到数据。")
                        #print("\n--- 正在生成最终回答 ---\n")

    except Exception as e:
        print(f"\n❌ 运行中断: {e}")


# 程序入口
if __name__ == "__main__":
    import asyncio
    asyncio.run(example_with_agent())  # 运行异步函数
