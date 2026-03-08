from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, ToolMessage


from typing import Dict, Any
import json

class SafeMCPToolNode(ToolNode):
    """自定义节点：聚合 chunk + 拒绝空/不完整 args，让模型重试"""

    async def aexecute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get("messages", [])
        if not messages:
            return {"messages": []}

        last_msg = messages[-1]
        if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
            return {"messages": []}

        responses = []
        for tool_call in last_msg.tool_calls:
            tool_name = tool_call["name"]
            args = tool_call["args"]

            # 关键校验：如果 args 为空 dict 或缺少 query
            if not args or "query" not in args or not args.get("query"):
                error_msg = (
                    f"工具 {tool_name} 参数不完整（query 缺失或为空）。\n"
                    "请提供完整参数，例如：{{'query': '北京最新资讯', 'count': 10}}"
                )
                responses.append(ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_call.get("id", ""),
                    name=tool_name,
                    status="error"
                ))
                continue

            # 可选：尝试 json 规范化（防格式异常）
            try:
                args = json.loads(json.dumps(args))  # 深拷贝 + 基本校验
            except Exception:
                responses.append(ToolMessage(
                    content="参数格式无效（非有效 JSON），请重新生成完整参数。",
                    tool_call_id=tool_call.get("id", ""),
                    name=tool_name,
                    status="error"
                ))
                continue

            # 执行工具（MCP）
            try:
                tool = self.tools_by_name[tool_name]
                result = await tool.ainvoke(args)
                responses.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call.get("id", ""),
                    name=tool_name
                ))
            except Exception as e:
                responses.append(ToolMessage(
                    content=f"工具执行失败: {str(e)}",
                    tool_call_id=tool_call.get("id", ""),
                    name=tool_name,
                    status="error"
                ))

        return {"messages": responses}

# 在你的代码中替换默认工具节点
# 但 create_agent 内部图不易直接替换，建议切换到手动 LangGraph 构建（见方案 4）