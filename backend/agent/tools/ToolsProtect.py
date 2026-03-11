from typing import Any

import json
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode
from langgraph.config import get_stream_writer  # [!code highlight]


class McpToolNode(ToolNode):
    """简化版工具节点"""

    async def ainvoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
        writer = get_stream_writer()
        last_msg = input.get("messages", [input])[-1] if isinstance(input, dict) else input

        if not isinstance(last_msg, (AIMessage, AIMessageChunk)) or not last_msg.tool_calls:
            return {"messages": []}

        # 收集 tool_call_chunks 中的参数
        args_chunks = []
        tool_name = ""
        tool_id = ""

        # 先从 tool_calls 获取 name 和 id
        for tc in last_msg.tool_calls:
            name, args, tid = tc.get("name", ""), tc.get("args", {}), tc.get("id", "")
            if name and not tool_name:
                tool_name = name
                tool_id = tid

        # 从 tool_call_chunks 拼接参数
        if hasattr(last_msg, 'tool_call_chunks') and last_msg.tool_call_chunks:
            for chunk in last_msg.tool_call_chunks:
                chunk_args = chunk.get("args", "")
                if chunk_args:
                    args_chunks.append(chunk_args)

        # 拼接完整的 args
        tool_args = {}
        if args_chunks:
            args_str = "".join(args_chunks)
            try:
                tool_args = json.loads(args_str)
            except json.JSONDecodeError:
                pass

        # 如果 tool_calls 中有完整 args，直接使用
        for tc in last_msg.tool_calls:
            args = tc.get("args", {})
            if args:
                tool_args = args
                break

        # 守卫检查
        if not tool_name:
            return {"messages": [ToolMessage(content="工具名称为空", tool_call_id=tool_id or "no-id", name="unknown", status="error")]}

        # 调用工具
        try:
            tool = self.tools_by_name[tool_name]
            writer(f"\n\n⌛ 正在调用工具: {tool.name} : {tool_args} \n\n")
            result = await tool.ainvoke(tool_args)
            writer(f"\n\n✅️ 调用成功: {tool_name}: {tool_args}: {result[:500]} \n\n")
            return {"messages": [ToolMessage(content=f"[完成] {tool_name}: {tool_args}: {result}", tool_call_id=tool_id or "no-id", name=tool_name)]}
        except Exception as e:
            error_msg = str(e)
            # 如果调用失败且参数为空，说明需要参数
            if not tool_args:
                #writer(f"\n\n⌛ 正在调用工具: {tool.name} : {tool_args} \n\n")
                return {"messages": [ToolMessage(content=f"参数为空或不完整，请提供参数: {error_msg}", tool_call_id=tool_id or "no-id", name=tool_name, status="error")]}
            # 如果调用失败但有参数，说明参数可能不对
            writer(f"\n\n❌ 调用失败: {tool_name}: {tool_args}: {error_msg} \n\n")
            return {"messages": [ToolMessage(content=f"[失败] {tool_name}: {tool_args}: {error_msg}", tool_call_id=tool_id or "no-id", name=tool_name, status="error")]}
