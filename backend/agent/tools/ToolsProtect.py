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
        writer(f"\n\n🔍 正在构建参数中... \n\n")
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

        # 处理参数：将所有 null 值替换为适当的默认值（避免 MCP 工具验证失败）
        def replace_null_with_default(obj, parent_key=""):
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    result[k] = replace_null_with_default(v, k)
                return result
            elif isinstance(obj, list):
                return [replace_null_with_default(item, parent_key) for item in obj]
            elif obj is None:
                # 根据字段名智能选择默认值
                if parent_key in ['earliestStartTime', 'latestStartTime', 'limitedNum']:
                    return 0  # 数字类型字段默认0
                elif parent_key in ['sortReverse']:
                    return False  # 布尔类型字段默认False
                else:
                    return ""  # 字符串类型字段默认空字符串
            else:
                return obj

        tool_args = replace_null_with_default(tool_args)

        # 守卫检查
        if not tool_name:
            return {"messages": [ToolMessage(content="工具名称为空", tool_call_id=tool_id or "no-id", name="unknown", status="error")]}

        # 调用工具
        try:
            tool = self.tools_by_name[tool_name]
            tool_args_str = json.dumps(tool_args, ensure_ascii=False) if tool_args else "{}"
            writer(f"\n\n⌛ 正在调用工具: {tool.name} : {tool_args_str} \n\n")
            result = await tool.ainvoke(tool_args)

            # 确保 result 是字符串类型，并截取前500字符
            if isinstance(result, list):
                result_str = json.dumps(result, ensure_ascii=False)
            elif isinstance(result, dict):
                result_str = json.dumps(result, ensure_ascii=False)
            else:
                result_str = str(result)
            
            # 截取前500字符（仅显示给用户，不影响大模型）
            display_result = result_str
            if len(result_str) > 500:
                display_result = result_str[:500] + "..."
            
            writer(f"\n\n✅️ 调用成功: {tool_name}: {tool_args_str}: {display_result} \n\n")
            return {"messages": [ToolMessage(content=f"[完成] {tool_name}: {tool_args_str}: {result_str}", tool_call_id=tool_id or "no-id", name=tool_name)]}
        except Exception as e:
            error_msg = str(e)
            tool_args_str = json.dumps(tool_args, ensure_ascii=False) if tool_args else "{}"
            # 如果调用失败且参数为空，说明需要参数
            if not tool_args:
                writer(f"\n\n参数为空或不完整，请仔细阅读错误提示和工具参数描述 不需要的参数请填写默认参数 并完善提供有效参数: {error_msg}  | args: | {tool_args_str}\n\n")
                return {"messages": [ToolMessage(content=f"参数为空或不完整，请仔细阅读错误提示和工具参数描述 不需要的参数请填写默认参数 并完善提供有效参数: {error_msg}", tool_call_id=tool_id or "no-id", name=tool_name, status="error")]}
            # 如果调用失败但有参数，说明参数可能不对
            writer(f"\n\n❌ 调用失败: {tool_name}: {tool_args_str}: {error_msg} \n\n")
            return {"messages": [ToolMessage(content=f"[失败] {tool_name}: {tool_args_str}: {error_msg}\n\n", tool_call_id=tool_id or "no-id", name=tool_name, status="error")]}
