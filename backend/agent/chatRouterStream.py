"""
流式处理模块
包含Agent流
支持动态 MCP 工具连接
"""

from typing import List, Optional, Callable, AsyncGenerator, Dict, Any
from langchain.tools import tool
from langchain.agents import create_agent
import logging

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
DB_URL = "postgresql://root:anhuang520@pan.junv.top:5432/postgres?sslmode=disable"

from services.llm import create_client

# 使用 MCP Cache 系统
from agent.mcp.mcp_cache import get_tool_cache, get_tool_by_name
from agent.tools import get_regular_tools

logger = logging.getLogger(__name__)

# 普通工具缓存（内置工具）
_regular_tools_cache: Optional[Dict[str, Any]] = None


def _get_regular_tools_dict() -> Dict[str, Any]:
    """获取普通工具字典（缓存）"""
    global _regular_tools_cache
    if _regular_tools_cache is None:
        tools = get_regular_tools()
        _regular_tools_cache = {t.name: t for t in tools}
    return _regular_tools_cache


async def _get_tool_by_config(tool_config) -> Optional[Any]:
    """
    根据工具配置获取工具对象
    
    Args:
        tool_config: 工具配置对象 (ToolConfig Pydantic 模型或字典)
            {
                "toolid": "工具名",
                "mcp": 0/1,  # 0=普通工具, 1=MCP工具
                ...
            }
    
    Returns:
        工具对象，如果不存在返回 None
    """
    # 支持 Pydantic 模型和字典两种格式
    if hasattr(tool_config, 'toolid'):
        # Pydantic 模型
        toolid = tool_config.toolid
        is_mcp = getattr(tool_config, 'mcp', 0) == 1
    else:
        # 字典
        toolid = tool_config.get("toolid")
        is_mcp = tool_config.get("mcp", 0) == 1
    
    if not toolid:
        logger.warning("[ChatRouter] 工具配置缺少 toolid")
        return None
    
    if is_mcp:
        # MCP 工具：从缓存获取
        tool = await get_tool_by_name(toolid)
        if not tool:
            logger.warning(f"[ChatRouter] MCP 工具 '{toolid}' 未找到")
        return tool
    else:
        # 普通工具：从普通工具缓存获取
        regular_tools = _get_regular_tools_dict()
        tool = regular_tools.get(toolid)
        if not tool:
            logger.warning(f"[ChatRouter] 普通工具 '{toolid}' 未找到")
        return tool


async def _get_tools_by_configs(tool_configs: List[Dict[str, Any]]) -> List:
    """
    根据工具配置列表获取工具对象
    
    Args:
        tool_configs: 工具配置列表
            [
                {"toolid": "工具名1", "mcp": 0},
                {"toolid": "工具名2", "mcp": 1},
                ...
            ]
    
    Returns:
        工具对象列表
    """
    if not tool_configs:
        # 如果没有指定工具，只返回普通工具（不自动加载所有 MCP 工具）
        logger.info("[ChatRouter] 未指定工具，仅使用普通工具")
        return list(_get_regular_tools_dict().values())
    
    tools = []
    for config in tool_configs:
        tool = await _get_tool_by_config(config)
        if tool:
            tools.append(tool)
    
    return tools


# 假设其他必要的 imports 已经存在 (SystemMessage, create_client, create_agent, logger, tools 等)

async def agent_stream0(
    llm: str,
    msg,
    thinking: str,
    tool_configs: List[Dict[str, Any]],  # 改为接收工具配置列表
    history,
    should_stop: Optional[Callable[[], bool]] = None,
) -> AsyncGenerator[dict, None]:
    """
    代理流式响应 (精简版)
    支持动态 MCP 工具连接
    
    Args:
        tool_configs: 工具配置列表
            [
                {"toolid": "工具名", "mcp": 0/1},
                ...
            ]
    """
    # 根据工具配置获取工具对象
    selected_tools = await _get_tools_by_configs(tool_configs)
    
    logger.info(f"[ChatRouter] 使用 {len(selected_tools)} 个工具: {[t.name for t in selected_tools]}")
    
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpoint:
        client = create_client(llm, thinking)
        agent = create_agent(
            client,
            tools=selected_tools,
            checkpointer=checkpoint,
        )
        
        # ❌ 删除了繁杂的 current_tool_call 状态变量
        try:
            async for token, metadata in agent.astream(msg, config=history,stream_mode="messages"):
                if should_stop and should_stop():
                    break
                
                node = metadata.get("langgraph_node", "")

                # ==========================================
                # 1. 提取推理过程 (Reasoning)
                # ==========================================
                reasoning = token.additional_kwargs.get("reasoning_content")
                if reasoning:
                    yield {"reasoning": reasoning}

                # ==========================================
                # 2. 提取工具调用动作 (Tool Calls)
                # ==========================================
                # 💡 核心技巧: LangChain 的 tool_call_chunks 在流式传输时，
                # 只有工具发出的"第一帧"会包含 'name' 字段。
                # 我们利用这一点，无需任何状态变量就能实现"只提示一次工具调用"。
                for tc_chunk in getattr(token, "tool_call_chunks", []):
                    if tc_chunk.get("name"): 
                        yield {"reasoning": f"\n\n🧠 正在调用工具: {tc_chunk['name']} ...\n"}

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
                            yield {"reasoning": f"\n✅️ 调用成功 已取得数据\n"}
                        elif node == "model":
                            yield {"content": text}

        except GeneratorExit:
            raise
        except Exception as e:
            logger.error(f"Agent 流错误: {e}")
            yield {"content": f"\n\n❌ 模型调用失败: \n\n{str(e)}"}
            raise
