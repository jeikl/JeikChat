"""
Chat Router with Streaming Support
"""

from langgraph.graph import StateGraph, START, END #状态图 开始 结束
from langgraph.graph.message import MessagesState #基础状态图
from langgraph.prebuilt import ToolNode, tools_condition #工具节点 工具条件
from .tools.ToolsProtect import McpToolNode


from langchain_core.messages import ToolMessage,AIMessage# 确保导入
from typing import Any, List, Optional, Dict, Callable, AsyncGenerator

from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from services.llm import create_client
from langchain.agents import create_agent
from agent.tools import get_regular_tools
from agent.mcp.mcp_cache import get_tool_cache

import logging
DB_URL="postgresql://root:anhuang520@pan.junv.top:5432/postgres?sslmode=disable"

logger = logging.getLogger(__name__)

# 缓存普通工具
_regular_tools_cache: Optional[Dict[str, Any]] = None

# 缓存已加载的 MCP 服务
_loaded_mcp_services: Dict[str, List[Any]] = {}


def _get_regular_tools_dict() -> Dict[str, Any]:
    """获取普通工具字典（缓存）"""
    global _regular_tools_cache
    if _regular_tools_cache is None:
        tools = get_regular_tools()
        _regular_tools_cache = {t.name: t for t in tools}
    return _regular_tools_cache


def _get_toolid_from_config(tool_config) -> Optional[str]:
    """从配置中获取 toolid"""
    if hasattr(tool_config, 'toolid'):
        return tool_config.toolid
    elif isinstance(tool_config, dict):
        return tool_config.get("toolid")
    return None


def _get_mcp_from_config(tool_config) -> int:
    """从配置中获取 mcp 标记"""
    if hasattr(tool_config, 'mcp'):
        return getattr(tool_config, 'mcp', 0)
    elif isinstance(tool_config, dict):
        return tool_config.get("mcp", 0)
    return 0


async def _load_mcp_service_and_get_tool(service_name: str, toolid: str) -> Optional[Any]:
    """加载指定 MCP 服务并获取单个工具"""
    global _loaded_mcp_services
    
    # 检查该服务是否已加载
    if service_name in _loaded_mcp_services:
        for tool in _loaded_mcp_services[service_name]:
            if _match_tool_name(tool.name, toolid):
                return tool
        return None
    
    # 服务未加载，需要连接
    logger.info(f"[MCP] 连接服务 '{service_name}'")
    
    try:
        from agent.mcp import _load_service_tools, _get_server_configs
        
        server_configs = _get_server_configs()
        config = server_configs.get(service_name, {})
        
        tools = await _load_service_tools(service_name, config)
        _loaded_mcp_services[service_name] = tools
        
        for tool in tools:
            if _match_tool_name(tool.name, toolid):
                return tool
        
        return None
        
    except Exception as e:
        logger.error(f"[MCP] 连接服务 '{service_name}' 失败: {e}")
        return None


def _match_tool_name(tool_name: str, toolid: str) -> bool:
    """
    匹配工具名
    现在 toolid 和 tool_name 都是带服务前缀的名称 (如: github_fork_repository)
    """
    return tool_name == toolid


async def _load_mcp_service_and_get_tools(service_name: str, toolids: List[str]) -> List[Any]:
    """加载指定 MCP 服务并获取多个工具"""
    global _loaded_mcp_services
    
    # 检查该服务是否已加载
    if service_name in _loaded_mcp_services:
        tools_found = []
        for toolid in toolids:
            for tool in _loaded_mcp_services[service_name]:
                if _match_tool_name(tool.name, toolid):
                    tools_found.append(tool)
                    break
        return tools_found
    
    # 服务未加载，需要连接
    logger.info(f"[MCP] 连接服务 '{service_name}'")
    
    try:
        from agent.mcp import _load_service_tools, _get_server_configs
        
        server_configs = _get_server_configs()
        config = server_configs.get(service_name, {})
        
        all_tools = await _load_service_tools(service_name, config)
        _loaded_mcp_services[service_name] = all_tools
        
        tools_found = []
        for toolid in toolids:
            for tool in all_tools:
                if _match_tool_name(tool.name, toolid):
                    tools_found.append(tool)
                    break
        
        return tools_found
        
    except Exception as e:
        logger.error(f"[MCP] 连接服务 '{service_name}' 失败: {e}")
        return []


async def _get_mcp_tool_by_toolid(toolid: str) -> Optional[Any]:
    """
    根据 toolid 获取 MCP 工具
    优先从已加载的服务中查找, 如果没有则按需加载对应服务
    支持两种格式:
    1. 带服务前缀的名称 (如: github_fork_repository)
    2. 原始名称 (如: fork_repository) - 会尝试匹配带前缀的名称
    """
    # 1. 首先检查所有已加载的服务
    for service_name, tools in _loaded_mcp_services.items():
        for tool in tools:
            if _match_tool_name(tool.name, toolid):
                return tool
    
    # 2. 从缓存中查找工具信息, 确定所属服务
    cache = await get_tool_cache()
    tool_info = cache.get_tool_info(toolid)
    
    if tool_info and tool_info.service_id:
        # 知道所属服务, 直接加载该服务
        return await _load_mcp_service_and_get_tool(tool_info.service_id, toolid)
    
    # 3. 尝试通过原始名称查找 (匹配带前缀的名称)
    # 例如: fork_repository -> github_fork_repository
    for cached_tool_name in cache.all_tools.keys():
        if cached_tool_name.endswith(f"_{toolid}"):
            tool_info = cache.get_tool_info(cached_tool_name)
            if tool_info and tool_info.service_id:
                return await _load_mcp_service_and_get_tool(tool_info.service_id, cached_tool_name)
    
    # 4. 不知道所属服务, 从缓存中获取服务列表并遍历查找
    services = cache.get_all_services()
    
    for service_name, service_info in services.items():
        # 跳过已加载的服务 (已经检查过了)
        if service_name in _loaded_mcp_services:
            continue
        
        # 尝试加载该服务
        tool = await _load_mcp_service_and_get_tool(service_name, toolid)
        if tool:
            return tool
    
    logger.warning(f"[ChatRouter] 未找到 MCP 工具 '{toolid}'")
    return None


async def _get_tools_by_configs(tool_configs: List) -> List:
    """
    根据工具配置列表获取工具对象 - 按需加载版本
    """
    if not tool_configs:
        return list(_get_regular_tools_dict().values())
    
    selected_tools = []
    mcp_tools_by_service = {}
    regular_tools = []
    
    # 按服务分组
    for config in tool_configs:
        toolid = _get_toolid_from_config(config)
        is_mcp = _get_mcp_from_config(config) == 1
        
        if not toolid:
            continue
        
        if is_mcp:
            cache = await get_tool_cache()
            tool_info = cache.get_tool_info(toolid)
            
            # 如果直接找不到，尝试通过原始名称查找带前缀的名称
            actual_toolid = toolid
            if not tool_info:
                for cached_tool_name in cache.all_tools.keys():
                    if cached_tool_name.endswith(f"_{toolid}"):
                        tool_info = cache.get_tool_info(cached_tool_name)
                        actual_toolid = cached_tool_name
                        break
            
            if tool_info and tool_info.service_id:
                service_id = tool_info.service_id
                if service_id not in mcp_tools_by_service:
                    mcp_tools_by_service[service_id] = []
                mcp_tools_by_service[service_id].append(actual_toolid)
            else:
                # 缓存中没有, 尝试直接获取
                tool = await _get_mcp_tool_by_toolid(toolid)
                if tool:
                    selected_tools.append(tool)
        else:
            regular_tools.append(toolid)
    
    # 批量加载 MCP 服务
    for service_id, toolids in mcp_tools_by_service.items():
        tools = await _load_mcp_service_and_get_tools(service_id, toolids)
        selected_tools.extend(tools)
    
    # 加载普通工具
    regular_tools_dict = _get_regular_tools_dict()
    for toolid in regular_tools:
        if toolid in regular_tools_dict:
            selected_tools.append(regular_tools_dict[toolid])
    
    return selected_tools

@wrap_model_call
def ghost_repair_wrap(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """幽灵修复：在发送请求前瞬时对齐序列"""
    msgs = request.messages
    print("我进来了")
    pending = {}
    
    for m in msgs:
        if hasattr(m, "tool_calls") and m.tool_calls:
            for tc in m.tool_calls:
                pending[tc["id"]] = tc
        elif isinstance(m, ToolMessage):
            pending.pop(m.tool_call_id, None)
    
    if pending:
        # 有未闭合的 tool_calls，在最后追加对应的 ToolMessage
        remedy_msgs = list(msgs) + [
            ToolMessage(content="[Auto-Healed]", tool_call_id=tc_id)
            for tc_id in pending.keys()
        ]
        request = request.copy(update={"messages": remedy_msgs})
    
    return handler(request)

async def agent_stream0(
    llm: str,
    msg,
    thinking: str,
    tool_configs: List,
    history,
    should_stop: Optional[Callable[[], bool]] = None,
) -> AsyncGenerator[dict, None]:
    """代理流式响应 - 深度兼容 LangGraph 结构化消息流"""
    
    # 1. 基础工具加载提示
    tool_names = [_get_toolid_from_config(c) for c in (tool_configs or []) if _get_toolid_from_config(c)]
    if tool_names:
        yield {"reasoning": f"\n\n🛠️ 已选择工具: {', '.join(tool_names)}\n\n"}

    yield {"reasoning": f"⏳ 正在连接服务...\n\n"}
    selected_tools = await _get_tools_by_configs(tool_configs)
    yield {"reasoning": f"✅️ MCP服务连接成功...\n\n"}
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpoint:
        client = create_client(llm, thinking)
        agent = create_agent(client, tools=selected_tools, checkpointer=checkpoint) 

        # ==========================================
        # 【预检修复】处理已存在的 400 状态死锁
        # ==========================================
        try:
            from langgraph.types import StateSnapshot
            state: StateSnapshot = await agent.get_state(history)
            if state and state.values and state.values.get("messages"):
                messages = state.values["messages"]
                if messages:
                    last_msg = messages[-1]
                    # 检查最后一条消息是否是带有 tool_calls 的 assistant 消息
                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        # 检查是否有对应的 tool 响应
                        pending_tool_ids = set(tc["id"] for tc in last_msg.tool_calls)
                        
                        # 检查后续消息中是否有对应的 tool 响应
                        for msg in messages:
                            if isinstance(msg, ToolMessage):
                                pending_tool_ids.discard(msg.tool_call_id)
                        
                        # 如果有未响应的 tool_calls，添加虚拟响应
                        if pending_tool_ids:
                            remedy_msgs = [
                                ToolMessage(content="[Auto-Healed] Tool call failed or was cancelled.", tool_call_id=tc_id) 
                                for tc_id in pending_tool_ids
                            ]
                            await agent.update_state(history, {"messages": remedy_msgs})
                            logger.warning(f"[ChatRouter] 发现 {len(pending_tool_ids)} 个未闭合的工具调用，已自动修复")
                            yield {"reasoning": f"\n\n⚠️ 检测到历史记录中的工具调用错误，已自动修复。\n\n"}
        except Exception as e:
            logger.error(f"[ChatRouter] 预检修复失败: {e}")

        # # 运行时状态维护
        active_tool_calls = [] # 存储当前轮次的 {id, name}
        last_message_type = "reasoning"

        try:
            yield {"reasoning": "🔄 正在思考...\n\n"}
            
            # 使用 messages 模式流式读取
            async for token, metadata in agent.astream(msg, config=history, stream_mode="messages"):
                if should_stop and should_stop(): break
                
                node = metadata.get("langgraph_node", "")
                
                # ------------------------------------------
                # A. 提取工具调用 ID (用于状态自愈)
                # ------------------------------------------
                # 优先从 tool_call_chunks 中提取 ID
                
                if hasattr(token, "tool_call_chunks"):
                    for chunk in token.tool_call_chunks:
                        if chunk.get("id"):
                            # 如果是新 ID，加入追踪列表
                            if not any(tc["id"] == chunk["id"] for tc in active_tool_calls):
                                active_tool_calls.append({"id": chunk["id"], "name": chunk.get("name")})
                                yield {"reasoning": f"\n\n🧠 正在调用工具: {chunk.get('name') or 'unknown'} ...\n"}
                                last_message_type = "reasoning"

                # ------------------------------------------
                # B. 深度解析结构化 Content Blocks (核心修复)
                # ------------------------------------------
                blocks = []
                if isinstance(token.content, list):
                    blocks = token.content
                elif isinstance(token.content, str) and token.content:
                    # 兼容普通字符串 content
                    blocks = [{"type": "text", "text": token.content}]

                for block in blocks:
                    if not isinstance(block, dict): continue
                    
                    b_type = block.get("type")
                    
                    # 1. 处理文本块
                    if b_type == "text":
                        text = block.get("text", "")
                        if not text: continue
                        
                        if node == "tools":
                            # 工具节点的输出一般代表数据获取成功
                            yield {"reasoning": f"\n\n✅ 工具返回数据成功\n\n"}
                            active_tool_calls = [] # 成功执行，清除挂起
                            last_message_type = "reasoning"
                        else:
                            # 模型节点的普通文本输出
                            if last_message_type == "reasoning":
                                text = f"\n\n{text}"
                            yield {"content": text}
                            last_message_type = "content"
                    
                    # 2. 处理推理块 (针对某些特定模型的 reasoning 字段)
                    elif b_type == "reasoning":
                        yield {"reasoning": block.get("reasoning", "")}
                        last_message_type = "reasoning"

                # ------------------------------------------
                # C. 兜底处理 additional_kwargs 中的推理
                # ------------------------------------------
                reasoning_content = token.additional_kwargs.get("reasoning_content")
                if reasoning_content:
                    yield {"reasoning": reasoning_content}
                    last_message_type = "reasoning"

        except Exception as e:
            # 运行时自愈逻辑
            error_msg = str(e)
            logger.error(f"[ChatRouter] 运行时错误: {error_msg}")
            
            # 检查是否是 MCP 工具参数错误
            if "Invalid input" in error_msg and "Required" in error_msg:
                logger.warning(f"[ChatRouter] 工具参数错误: {error_msg}")
                # 尝试修复：发送错误信息给模型，让它重新生成
                if active_tool_calls:
                    try:
                        error_tool_msg = f"工具调用失败：参数错误。{error_msg}"
                        remedy = [ToolMessage(content=error_tool_msg, tool_call_id=tc["id"]) for tc in active_tool_calls]
                        await agent.update_state(history, {"messages": remedy})
                        yield {"reasoning": "\n\n⚠️ 工具参数错误，已自动修复。请重新提问。\n"}
                    except Exception as fix_err:
                        logger.error(f"[ChatRouter] 修复失败: {fix_err}")
                yield {"content": f"\n\n❌ 工具参数错误：大模型提供的参数不正确。请尝试重新提问或创建新会话。\n"}
            elif "tool_calls" in error_msg and "tool messages" in error_msg:
                # 对话历史损坏错误
                logger.error(f"[ChatRouter] 对话历史损坏: {error_msg}")
                yield {"content": f"\n\n❌ 对话历史错误：工具调用记录不完整。\n\n建议：点击'清空对话'按钮或创建新会话。\n"}
            elif active_tool_calls:
                try:
                    remedy = [ToolMessage(content=f"Error: {error_msg}", tool_call_id=tc["id"]) for tc in active_tool_calls]
                    await agent.update_state(history, {"messages": remedy})
                    yield {"reasoning": "\n\n⚠️ 已自动截断并修复当前中断的工具链。\n"}
                except: pass
                yield {"content": f"\n\n❌ 运行错误: {error_msg}\n\n建议：请尝试重新提问。\n"}
            else:
                yield {"content": f"\n\n❌ 运行错误: {error_msg}\n\n建议：请尝试重新提问或创建新会话。\n"}
            # 不再抛出异常，让对话可以继续
            return
                
        except Exception as e:
            # 外层异常处理
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"[ChatRouter] Agent 执行错误: {e}\n{error_detail}")
            yield {"content": f"\n\n❌ 模型调用失败: {str(e)}\n\n建议：请尝试重新提问或创建新会话。\n"}
            # 不再抛出异常
            return


async def agent_stream1(
        llm: str,
        msg,
        thinking: str,
        tool_configs: List,
        history,
        should_stop: Optional[Callable[[], bool]] = None,
) -> AsyncGenerator[dict, None]:
    """代理流式响应 - 深度兼容 LangGraph 结构化消息流"""

    # 1. 基础工具加载提示
    tool_names = [_get_toolid_from_config(c) for c in (tool_configs or []) if _get_toolid_from_config(c)]
    if tool_names:
        yield {"reasoning": f"\n\n🛠️ 已选择工具: {', '.join(tool_names)}\n\n"}

    yield {"reasoning": f"⏳ 正在连接服务...\n\n"}
    selected_tools = await _get_tools_by_configs(tool_configs)
    yield {"reasoning": f"✅️ MCP服务连接成功...\n\n"}
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpoint:
        model = create_client(llm, thinking)
        #agent = create_agent(client, checkpointer=checkpoint)
        model_with_tools=model.bind_tools(selected_tools)
        async def call_model(state: MessagesState):#ainvoke的包装类
            """
            Agent 节点核心逻辑

            Args:
                state: MessagesState，

            Returns:
                包含 LLM 响应的状态更新
            """
            #print(" 调用大模型中 .")
            response = await model_with_tools.ainvoke(state["messages"]) #执行工具
            #print("  [DEBUG] LLM 调用完成")
            return {"messages": [response]}
        mcptoolNode=McpToolNode(selected_tools)

        #工作流开始定义
        workflow=StateGraph(MessagesState)
        workflow.add_node("tools",mcptoolNode)
        workflow.add_node("agent",call_model)
        workflow.add_edge(START,"agent")
    # 添加条件边
        workflow.add_conditional_edges(
            "agent",
            tools_condition,
            {"tools": "tools", END: END}  # 有工具调用 返回的字符串state为tools则映射到tools节点，否则→结束
        )
        graph=workflow.compile(checkpointer=checkpoint)#添加记忆点

        last_message_type = "reasoning"


    try:
        # 使用新的 ["messages", "updates"] 模式进行流式读取
        # 这样可以更清晰地区分消息和节点状态更新
        async for mode, data in graph.astream(msg, config=history, stream_mode=["messages", "updates"]):
            if should_stop and should_stop():
                break

            # --- 情况 A: 处理细粒度的消息流 (mode == "messages") ---
            if mode == "messages":
                chunk, metadata = data # data 是 (chunk, metadata) 元组

                # 1. 提取推理内容 (Reasoning / Thinking)
                # 兼容 deepseek 等模型的思维链字段
                reasoning_content = chunk.additional_kwargs.get("reasoning_content", "")
                if reasoning_content:
                    yield {"reasoning": f"{reasoning_content}"}

                # 2. 提取正式回答内容
                if hasattr(chunk, "content") and chunk.content:
                    # 根据消息类型决定yield的key
                    if isinstance(chunk, ToolMessage):
                        # ToolMessage 通常是工具的返回结果，可以作为推理的一部分展示
                        yield {"reasoning": f"\n\n✅ 工具返回数据成功: {chunk.content[:50]}...\n"} # 限制长度
                        print(f"工具返回数据: {chunk.content}\n")
                    else:
                        # 普通AIMessage等，作为主要内容输出
                        yield {"content": chunk.content}

            # --- 情况 B: 处理节点状态更新流 (mode == "updates") ---
            elif mode == "updates":
                # data 是一个字典，{node_name: new_state}
                for node_name, state_snapshot in data.items():

                    if node_name == "agent":
                        # 检查 agent 节点的状态快照，看是否有待执行的工具调用
                        # 通常，工具调用信息会附加在最新的消息上
                        messages_in_state = state_snapshot.get("messages", [])
                        if messages_in_state:
                            last_msg = messages_in_state[-1]
                            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                                # 发现待执行的工具调用
                                tool_name = last_msg.tool_calls[0]['name']
                                yield {"reasoning": f"\n\n🧠 正在调用工具: {tool_name} ...\n"}
                                print(f"[系统动作] 正在调用工具: {tool_name}...")

                    elif node_name == "tools":
                        # 当 tools 节点有更新时，意味着工具执行完毕
                        yield {"reasoning": f"\n\n✅ 工具执行完毕，正在处理返回数据...\n"}
                        print(f"[系统动作] 工具执行完毕，获取到数据。")


    except Exception as e:
        yield {"content": f"\n\n❌ 模型调用失败: {str(e)}\n\n建议：请尝试重新提问或创建新会话。\n"}













        # try:
        #     yield {"reasoning": "🔄 正在思考...\n\n"}
        #
        #     # 使用 messages 模式流式读取
        #     async for token, metadata in graph.astream(msg, config=history, stream_mode="messages"):
        #         if should_stop and should_stop(): break
        #         node = metadata.get("langgraph_node", "")
        #
        #
        #         if hasattr(token, "tool_call_chunks"):
        #             for chunk in token.tool_call_chunks:
        #                 if chunk.get("id"):
        #                     if not any(tc["id"] == chunk["id"] for tc in active_tool_calls):
        #                         #active_tool_calls.append({"id": chunk["id"], "name": chunk.get("name")})
        #                         yield {"reasoning": f"\n\n🧠 正在调用工具: {chunk.get('name') or 'unknown'} ...\n"}
        #                         last_message_type = "reasoning"
        #
        #         blocks = []
        #         if isinstance(token.content, list):
        #             blocks = token.content
        #         elif isinstance(token.content, str) and token.content:
        #             # 兼容普通字符串 content
        #             blocks = [{"type": "text", "text": token.content}]
        #
        #         for block in blocks:
        #             if not isinstance(block, dict): continue
        #
        #             b_type = block.get("type")
        #
        #             # 1. 处理文本块
        #             if b_type == "text":
        #                 text = block.get("text", "")
        #                 if not text: continue
        #
        #                 if node == "tools":
        #                     # 工具节点的输出一般代表数据获取成功
        #                     yield {"reasoning": f"\n\n✅ 工具返回数据成功\n\n"}
        #                     print(f"工具返回数据:{text}\n")
        #
        #                     active_tool_calls = [] # 成功执行，清除挂起
        #                     last_message_type = "reasoning"
        #                 else:
        #                     # 模型节点的普通文本输出
        #                     if last_message_type == "reasoning":
        #                         text = f"\n\n{text}"
        #                     yield {"content": text}
        #                     last_message_type = "content"
        #
        #             # 2. 处理推理块 (针对某些特定模型的 reasoning 字段)
        #             elif b_type == "reasoning":
        #                 yield {"reasoning": block.get("reasoning", "")}
        #                 last_message_type = "reasoning"
        #
        #         # ------------------------------------------
        #         # C. 兜底处理 additional_kwargs 中的推理
        #         # ------------------------------------------
        #         reasoning_content = token.additional_kwargs.get("reasoning_content")
        #         if reasoning_content:
        #             yield {"reasoning": reasoning_content}
        #             last_message_type = "reasoning"
        #
        #
        # except Exception as e:
        #     yield {"content": f"\n\n❌ 模型调用失败: {str(e)}\n\n建议：请尝试重新提问或创建新会话。\n"}


