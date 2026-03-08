"""
Chat Router with Streaming Support
"""

from anyio.lowlevel import checkpoint
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

# 使用新的 MCP 缓存管理
from agent.mcp.cache_manager import get_cache_manager
from agent.mcp.connection_manager import get_connection_manager

import logging
DB_URL="postgresql://root:anhuang520@pan.junv.top:5432/postgres?sslmode=disable"

logger = logging.getLogger(__name__)

# 缓存普通工具
_regular_tools_cache: Optional[Dict[str, Any]] = None


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


def _match_tool_name(tool_name: str, toolid: str) -> bool:
    """
    匹配工具名
    现在 toolid 和 tool_name 都是带服务前缀的名称 (如: github_fork_repository)
    """
    return tool_name == toolid


async def _load_mcp_service_and_get_tool(service_name: str, toolid: str) -> Optional[Any]:
    """加载指定 MCP 服务并获取单个工具"""
    try:
        manager = await get_connection_manager()
        return await manager.get_tool(service_name, toolid)
    except Exception as e:
        logger.error(f"[MCP] 获取工具 '{toolid}' 从服务 '{service_name}' 失败: {e}")
        return None


async def _load_mcp_service_and_get_tools(service_name: str, toolids: List[str]) -> List[Any]:
    """加载指定 MCP 服务并获取多个工具"""
    try:
        manager = await get_connection_manager()
        tools = await manager.get_tools_by_service(service_name)
        
        # 过滤指定的工具
        result = []
        for toolid in toolids:
            for tool in tools:
                if _match_tool_name(tool.name, toolid):
                    result.append(tool)
                    break
        return result
    except Exception as e:
        logger.error(f"[MCP] 获取工具从服务 '{service_name}' 失败: {e}")
        return []


async def _get_mcp_tool_by_toolid(toolid: str) -> Optional[Any]:
    """
    根据 toolid 获取 MCP 工具
    优先从已加载的服务中查找, 如果没有则按需加载对应服务
    支持两种格式:
    1. 带服务前缀的名称 (如: github_fork_repository)
    2. 原始名称 (如: fork_repository) - 会尝试匹配带前缀的名称
    """
    # 1. 首先检查已连接的服务
    manager = await get_connection_manager()
    for service_name in manager.get_connected_services():
        tool = await manager.get_tool(service_name, toolid)
        if tool:
            return tool
    
    # 2. 从缓存中查找工具信息, 确定所属服务
    cache = await get_cache_manager()
    tool_info = cache.get_tool_info(toolid)
    
    if tool_info and tool_info.service_id:
        # 知道所属服务, 直接连接该服务
        return await _load_mcp_service_and_get_tool(tool_info.service_id, toolid)
    
    # 3. 尝试通过原始名称查找 (匹配带前缀的名称)
    # 例如: fork_repository -> github_fork_repository
    for cached_tool_name in cache.get_all_tools().keys():
        if cached_tool_name.endswith(f"_{toolid}"):
            tool_info = cache.get_tool_info(cached_tool_name)
            if tool_info and tool_info.service_id:
                return await _load_mcp_service_and_get_tool(tool_info.service_id, cached_tool_name)
    
    # 4. 不知道所属服务, 遍历所有服务查找
    services = cache.get_all_services()
    for service_name in services.keys():
        # 跳过已连接的服务 (已经检查过了)
        if manager.is_connected(service_name):
            continue
        
        # 尝试连接该服务
        tool = await _load_mcp_service_and_get_tool(service_name, toolid)
        if tool:
            return tool
    
    logger.warning(f"[ChatRouter] 未找到 MCP 工具 '{toolid}'")
    return None


async def _get_tools_by_configs(tool_configs: List) -> List:
    """
    根据工具配置列表获取工具对象 - 按需加载版本
    用于 agent_stream0（不使用 MCP 的场景）
    """
    if not tool_configs:
        return list(_get_regular_tools_dict().values())
    
  
    mcp_tools_by_service: Dict[str, List[str]] = {}
    regular_tools = []
    
    # 按服务分组
    cache = await get_cache_manager()
    
    for config in tool_configs:
        toolid = _get_toolid_from_config(config)
        is_mcp = _get_mcp_from_config(config) == 1
        
        if not toolid:
            continue
        
        if is_mcp:
            tool_info = cache.get_tool_info(toolid)
            
            # 如果直接找不到，尝试通过原始名称查找带前缀的名称
            actual_toolid = toolid
            if not tool_info:
                for cached_tool_name in cache.get_all_tools().keys():
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


# 全局 MCP 连接缓存
_mcp_connection_cache: Dict[str, Any] = {}

async def _get_mcp_tools_with_cached_connection(tool_configs: List) -> List:
    """
    获取工具列表，带 MCP 连接缓存机制
    - MCP=1: 从缓存通过 toolid 找到 MCP 服务，检查是否有连接缓存，有则复用，无则新建
    - MCP=0: 普通工具直接返回
    """
    from agent.mcp.config_loader import load_server_configs
    from langchain_mcp_adapters.client import MultiServerMCPClient
    
    global _mcp_connection_cache
    
    selected_tools = []
    mcp_services_needed: Dict[str, List[str]] = {}  # service_id -> [toolids]
    regular_tools = []
    
    cache = await get_cache_manager()
    
    # 1. 按 MCP 标记分组工具
    for config in tool_configs:
        toolid = _get_toolid_from_config(config)
        is_mcp = _get_mcp_from_config(config) == 1
        
        if not toolid:
            continue
        
        if is_mcp:
            # MCP 工具：通过缓存找到所属服务
            tool_info = cache.get_tool_info(toolid)
            
            # 如果直接找不到，尝试通过原始名称查找
            if not tool_info:
                for cached_tool_name in cache.get_all_tools().keys():
                    if cached_tool_name.endswith(f"_{toolid}"):
                        tool_info = cache.get_tool_info(cached_tool_name)
                        toolid = cached_tool_name
                        break
            
            if tool_info and tool_info.service_id:
                service_id = tool_info.service_id
                if service_id not in mcp_services_needed:
                    mcp_services_needed[service_id] = []
                if toolid not in mcp_services_needed[service_id]:
                    mcp_services_needed[service_id].append(toolid)
            else:
                logger.warning(f"[ChatRouter] 未找到 MCP 工具 '{toolid}' 的服务信息")
        else:
            # 普通工具
            regular_tools.append(toolid)
    
    # 2. 处理 MCP 服务连接
    all_configs = load_server_configs()
    configs_to_connect = {}  # 需要新建连接的服务配置
    
    for service_id, toolids in mcp_services_needed.items():
        if service_id in _mcp_connection_cache:
            # 有缓存连接，直接使用
            logger.info(f"[MCP Cache] 复用缓存连接: {service_id}")
            client = _mcp_connection_cache[service_id]
            try:
                # 从缓存的客户端获取工具
                all_tools = await client.get_tools()
                for tool in all_tools:
                    if tool.name in toolids:
                        selected_tools.append(tool)
            except Exception as e:
                logger.warning(f"[MCP Cache] 缓存连接失效: {service_id}, 错误: {e}")
                # 连接失效，从缓存中移除
                del _mcp_connection_cache[service_id]
                # 需要重新连接
                for cfg in all_configs:
                    if cfg.name == service_id:
                        configs_to_connect[service_id] = cfg.to_client_config()
                        break
        else:
            # 无缓存，需要新建连接
            for cfg in all_configs:
                if cfg.name == service_id:
                    configs_to_connect[service_id] = cfg.to_client_config()
                    break
    
    # 3. 新建需要的连接
    if configs_to_connect:
        logger.info(f"[MCP] 新建连接: {list(configs_to_connect.keys())}")
        try:
            async with MultiServerMCPClient(configs_to_connect) as client:
                mcp_tools = await client.get_tools()
                
                # 缓存客户端连接
                for service_id in configs_to_connect.keys():
                    _mcp_connection_cache[service_id] = client
                    logger.info(f"[MCP Cache] 缓存新连接: {service_id}")
                
                # 添加需要的工具
                needed_toolids = []
                for toolids in mcp_services_needed.values():
                    needed_toolids.extend(toolids)
                
                for tool in mcp_tools:
                    if tool.name in needed_toolids:
                        selected_tools.append(tool)
                    
        except Exception as e:
            logger.error(f"[MCP] 新建连接失败: {e}")
    
    # 4. 添加普通工具
    regular_tools_dict = _get_regular_tools_dict()
    for toolid in regular_tools:
        if toolid in regular_tools_dict:
            selected_tools.append(regular_tools_dict[toolid])
    
    return selected_tools





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
    
    """
    代理流式响应 - 带 MCP 连接缓存的版本
    统一处理 MCP 和普通工具，通过 mcp 字段区分
    MCP=1: 从缓存通过 toolid 找到 MCP 服务，检查连接缓存，有则复用，无则新建
    MCP=0: 普通工具直接返回
    """
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpoint:
        selected_tools = []  # 在函数开头初始化
        yield {"reasoning": f"\n\n✅️ 已选择模型: {llm}\n\n"}
        
        # 1. 基础工具加载提示
        tool_names = [_get_toolid_from_config(c) for c in (tool_configs or []) if _get_toolid_from_config(c)]
        if tool_names:
            yield {"reasoning": f"\n\n🛠️ 已选择工具: {', '.join(tool_names)}\n\n"}
            yield {"reasoning": f"⏳ 正在连接工具...\n\n"}
            # 2. 获取工具（带 MCP 连接缓存）
            selected_tools = await _get_mcp_tools_with_cached_connection(tool_configs)
            yield {"reasoning": f"✅️ 工具加载完成，共 {len(selected_tools)} 个工具\n\n"}

        # 3. 创建模型和工作流
        model = create_client(llm, thinking)
        workflow = StateGraph(MessagesState)
        if selected_tools:
            llm_with_tools = model.bind_tools(selected_tools)
            # 创建工具节点
            tool_node = McpToolNode(selected_tools)
            workflow.add_node("tools", tool_node)
        else:
            llm_with_tools=model
    

        

        async def call_model(state: MessagesState):
            response = await llm_with_tools.ainvoke(state["messages"])
            return {"messages": [response]}
        
        workflow.add_node("agent", call_model)

        workflow.add_edge(START, "agent")

        if selected_tools:
            workflow.add_edge("tools", "agent")
            workflow.add_conditional_edges(
                "agent",
                tools_condition,
                {"tools": "tools", END: END}
            )
        else:
            workflow.add_edge("agent", END)
        
        graph=workflow.compile(checkpointer=checkpoint)


        
        # 执行对话
        try:
            async for mode, data in graph.astream(msg, config=history, stream_mode=["messages", "updates"]):
                if should_stop and should_stop():
                    break
    
                # --- 情况 A: 细粒度流处理 (messages) ---
                if mode == "messages":
                    chunk, _ = data

                # 1. 提取推理内容
                if hasattr(chunk, "additional_kwargs"):
                    reasoning = chunk.additional_kwargs.get("reasoning_content", "")
                    if reasoning:
                        yield {"reasoning": f"{reasoning}"}

                # 2. 提取正式回答内容
                if hasattr(chunk, "content") and chunk.content:
                    if isinstance(chunk, ToolMessage):
                        yield {"reasoning": f"\n\n✅ 工具返回数据成功: {chunk.content[:50]}...\n"}
                        print(f"工具返回数据: {chunk.content}\n")
                    else:
                        yield {"content": chunk.content}

                # 3. 检测工具调用
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    for tc in chunk.tool_calls:
                        if tc.get("name"):
                            yield {"reasoning": f"\n\n🧠 正在调用工具: {tc['name']} ...\n"}
                            print(f"[系统动作] 正在调用工具: {tc['name']}...")

        except Exception as e:
            logger.error(f"[ChatRouter] 运行时错误: {e}")
            yield {"content": f"\n\n❌ 模型调用失败: {str(e)}\n\n建议：请尝试重新提问或创建新会话。\n"}
