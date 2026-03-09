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
        # print(f"  [DEBUG] 工具调用数量: {len(last_msg.tool_calls)}")
        # print(f"  [DEBUG] 可用工具: {list(self.tools_by_name.keys())}")
        # print(f"  [DEBUG] last_msg.tool_calls: {last_msg.tool_calls}")
        
        # 预处理：合并损坏的 tool_calls
        # 有些模型会生成 name 和 args 分开的 tool_calls
        merged_calls = {}
        pending_args = {}  # 存储没有 name 的 args
        
        for tc in last_msg.tool_calls:
            tid = tc.get("id", "")
            name = tc.get("name", "")
            args = tc.get("args", {})
            
            if name and tid:
                # 正常的 tool_call
                merged_calls[tid] = {"name": name, "args": args, "id": tid}
            elif name and not tid:
                # 有 name 但没有 id，创建临时 id
                temp_id = f"temp_{name}"
                merged_calls[temp_id] = {"name": name, "args": args, "id": temp_id}
            elif not name and args:
                # 有 args 但没有 name，暂时存储
                pending_args[tid] = args
        
        # 尝试将 pending_args 合并到已有的 tool_call
        for tid, args in pending_args.items():
            if tid in merged_calls:
                merged_calls[tid]["args"].update(args)
            else:
                # 找不到对应的 tool_call，尝试匹配第一个有 name 但没有 args 的
                merged = False
                for mid, mc in merged_calls.items():
                    if mc["name"] and not mc["args"]:
                        mc["args"].update(args)
                        merged = True
                        break
                
                # 如果还是没找到，创建一个带有错误信息的 tool_call
                # 这样至少能返回一个响应，不会导致模型报错
                if not merged and tid:
                    merged_calls[tid] = {
                        "name": "__error__",  # 特殊标记
                        "args": args,
                        "id": tid,
                        "error": "无法匹配到对应的工具名称"
                    }
        
        # print(f"  [DEBUG] 合并后的 tool_calls: {list(merged_calls.values())}")
        
        for tc in merged_calls.values():
            name = tc.get("name", "")
            args = tc.get("args", {})
            tid = tc.get("id", "no-id")
            error_msg = tc.get("error", "")
            # print(f"  [DEBUG] 处理工具调用: name='{name}', args={args}, tid={tid}")

            # 处理特殊错误标记
            if name == "__error__":
                # print(f"  [DEBUG] 处理合并错误: {error_msg}")
                responses.append(ToolMessage(
                    content=f"工具调用参数解析错误：{error_msg}。请重新调用工具。",
                    tool_call_id=tid,
                    name="unknown",
                    status="error"
                ))
                continue

            # 检查工具名称是否为空
            if not name:
                # print(f"  [DEBUG] 工具名称为空，返回错误")
                responses.append(ToolMessage(
                    content="工具调用失败：工具名称为空",
                    tool_call_id=tid,
                    name="unknown",
                    status="error"
                ))
                continue

            # 检查工具是否在可用列表中
            if name not in self.tools_by_name:
                # print(f"  [DEBUG] 工具 '{name}' 不在可用工具列表中: {list(self.tools_by_name.keys())}")
                responses.append(ToolMessage(
                    content=f"工具调用失败：工具 '{name}' 不可用",
                    tool_call_id=tid,
                    name=name,
                    status="error"
                ))
                continue

            # 守卫机制：bing_search 工具的 query 参数校验
            if "bing" in name.lower():
                query = args.get("query", "")
                # 检查 query 有效性
                if not query or not isinstance(query, str) or not query.strip():
                    # print(f"  [DEBUG] 守卫拦截：query 无效 {args}")
                    responses.append(ToolMessage(
                        content="工具调用失败：'query' 参数为空或无效。请重新生成完整参数。",
                        tool_call_id=tid,
                        name=name,
                        status="error"
                    ))
                    continue  # 跳过本次循环

            # 执行工具调用（带重试）
            max_retries = 2
            retry_count = 0
            last_error = None
            
            while retry_count < max_retries:
                try:
                    # print(f"  [DEBUG] 执行工具 {name} with args {args} (尝试 {retry_count + 1}/{max_retries})")
                    tool = self.tools_by_name[name]  # 获取工具实例
                    result = await tool.ainvoke(args)  # 异步调用
                    responses.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tid,
                        name=name
                    ))
                    break  # 成功，跳出重试循环
                except httpx.RemoteProtocolError as e:
                    retry_count += 1
                    last_error = e
                    print(f"  [ERROR] MCP 服务器连接异常（尝试 {retry_count}/{max_retries}）：{str(e)}")
                    if retry_count < max_retries:
                        import asyncio
                        await asyncio.sleep(1)  # 等待1秒后重试
                    else:
                        # 重试耗尽，返回错误
                        responses.append(ToolMessage(
                            content=(
                                f"bing_search 工具调用失败：服务器连接中断。\n"
                                "可能原因：网络不稳定、服务器临时问题或配额限制。\n"
                                "建议：请稍后重试或简化搜索关键词。"
                            ),
                            tool_call_id=tid,
                            name=name,
                            status="error"
                        ))
                except Exception as e:
                    # 其他异常，不重试
                    print(f"  [ERROR] 工具执行异常：{str(e)}")
                    responses.append(ToolMessage(
                        content=f"工具执行失败：{str(e)}。请检查参数。",
                        tool_call_id=tid,
                        name=name,
                        status="error"
                    ))
                    break

        #print("  [DEBUG] tools 节点完成")
        return {"messages": responses}



