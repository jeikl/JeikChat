from typing import Any

import httpx
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode




class McpToolNode(ToolNode):
    async def ainvoke(
        self, input: Any, config: RunnableConfig | None = None, **kwargs: Any
    ) -> Any:
        """
        异步调用工具节点

        Args:
            input: 包含 messages 的状态字典
            config: 可选配置字典

        Returns:
            包含工具响应消息的字典
        """
        #yield ("正在执行工具")

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

        #print("  [DEBUG] tools 节点完成")
        return {"messages": responses}



