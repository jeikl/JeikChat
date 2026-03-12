"""
Chat Router with Streaming Support
"""

# 全局 MCP 客户端和工具缓存
_mcp_client_global = None
_mcp_tools_global = []
_mcp_config_hash_global = None  # 用于检测配置是否变化

from agent.prompt import get_prompts, build_messages
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import MessagesState
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import ToolMessage, AIMessage,AIMessageChunk
from typing import Any, List, Optional, Dict, Callable, AsyncGenerator
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from services.llm import create_client
from agent.tools.ToolsProtect import McpToolNode
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


async def _get_cached_mcp_client_and_tools(selected_tool_ids: List[str] = None):
    """
    获取缓存的 MCP 客户端和工具
    使用我们自己的 connection_manager 来获取工具，支持过滤后的 stdio 连接
    
    Args:
        selected_tool_ids: 选中的工具ID列表，如果提供则只加载这些工具对应的服务
    """
    global _mcp_client_global, _mcp_tools_global, _mcp_config_hash_global

    from agent.mcp.config_loader import load_server_configs
    from agent.mcp.cache_manager import get_cache_manager
    import hashlib
    import json

    # 获取当前配置
    server_configs = load_server_configs()
    
    # 计算配置哈希（包含选中的工具）
    cache_key_data = [{"name": cfg.name, "command": cfg.command, "args": cfg.args} for cfg in server_configs]
    if selected_tool_ids:
        cache_key_data.append({"selected": sorted(selected_tool_ids)})
    config_str = json.dumps(cache_key_data, sort_keys=True)
    config_hash = hashlib.md5(config_str.encode()).hexdigest()

    # 检查缓存是否有效
    if (_mcp_client_global is not None and
        _mcp_tools_global is not None and
        _mcp_config_hash_global == config_hash):
        logger.info(f"[MCP] 使用缓存的工具 ({len(_mcp_tools_global)} 个)")
        return _mcp_client_global, _mcp_tools_global

    # 确定需要加载的服务
    services_to_load = set()
    if selected_tool_ids:
        # 根据工具名前缀确定服务
        # 工具名格式: service-name_tool_name 或 service-name_service-name_tool_name（重复前缀）
        for tool_id in selected_tool_ids:
            # 标准化工具名（处理重复前缀）
            parts = tool_id.split('_')
            if len(parts) >= 3 and parts[0] == parts[1]:
                # 移除重复前缀
                normalized_id = f"{parts[0]}_{'_'.join(parts[2:])}"
            else:
                normalized_id = tool_id
            
            for cfg in server_configs:
                if not cfg.enabled:
                    continue
                # 工具名格式为 service-name_tool_name
                if normalized_id.startswith(cfg.name + '_'):
                    services_to_load.add(cfg.name)
                    break
        logger.info(f"[MCP] 根据选中的 {len(selected_tool_ids)} 个工具，需要加载 {len(services_to_load)} 个服务: {services_to_load}")
    else:
        # 加载所有启用的服务
        services_to_load = {cfg.name for cfg in server_configs if cfg.enabled}
        logger.info(f"[MCP] 加载所有 {len(services_to_load)} 个启用的服务")

    # 从 connection_manager 获取工具
    manager = await get_connection_manager()
    all_tools = []
    
    for cfg in server_configs:
        if cfg.name not in services_to_load:
            continue
        try:
            tools = await manager.connect_service(cfg.name)
            if tools:
                all_tools.extend(tools)
        except Exception as e:
            logger.error(f"[MCP] 获取服务 '{cfg.name}' 工具失败: {e}")

    # 如果只加载选中工具对应的服务，过滤工具列表
    if selected_tool_ids:
        # 处理工具名格式：前端可能发送重复前缀的格式（如 github_github_xxx）
        # 需要标准化为单层前缀格式（如 github_xxx）
        normalized_selected_ids = set()
        for tool_id in selected_tool_ids:
            # 检查是否有重复前缀（如 github_github_xxx）
            parts = tool_id.split('_')
            if len(parts) >= 3 and parts[0] == parts[1]:
                # 移除重复前缀：github_github_xxx -> github_xxx
                normalized_id = f"{parts[0]}_{'_'.join(parts[2:])}"
                normalized_selected_ids.add(normalized_id)
            else:
                normalized_selected_ids.add(tool_id)
        
        filtered_tools = [t for t in all_tools if t.name in normalized_selected_ids]
        logger.info(f"[MCP] 加载 {len(filtered_tools)}/{len(selected_tool_ids)} 个选中工具")
        all_tools = filtered_tools
    else:
        logger.info(f"[MCP] 共加载 {len(all_tools)} 个工具")

    # 更新全局缓存
    _mcp_client_global = manager
    _mcp_tools_global = all_tools
    _mcp_config_hash_global = config_hash

    return manager, all_tools


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
 
    
    global _mcp_connection_cache
    
    logger.info(f"[DEBUG-MCP] 开始获取工具，配置数量={len(tool_configs) if tool_configs else 0}")
    
    selected_tools = []
    mcp_services_needed: Dict[str, List[str]] = {}  # service_id -> [toolids]
    regular_tools = []
    
    cache = await get_cache_manager()
    logger.info(f"[DEBUG-MCP] 缓存管理器获取成功")
    
    # 1. 按 MCP 标记分组工具
    logger.info(f"[DEBUG-MCP] 开始遍历工具配置...")
    for config in tool_configs:
        toolid = _get_toolid_from_config(config)
        is_mcp = _get_mcp_from_config(config) == 1
        
        if not toolid:
            continue
        
        if is_mcp:
            # MCP 工具：分割前缀获取服务名和工具名
            # 格式: service_name_tool_name (如: bing-search_bing_search)
            if "_" in toolid:
                parts = toolid.split("_", 1)
                service_id = parts[0]
                actual_tool_name = parts[1]  # 无前缀的工具名
                
                if service_id not in mcp_services_needed:
                    mcp_services_needed[service_id] = []
                if actual_tool_name not in mcp_services_needed[service_id]:
                    mcp_services_needed[service_id].append(actual_tool_name)
                    logger.info(f"[DEBUG-MCP] 添加MCP工具: {actual_tool_name} (来自 {toolid})")
            else:
                logger.warning(f"[ChatRouter] MCP 工具名格式错误 '{toolid}'，应为 'service_tool' 格式")
        else:
            # 普通工具
            regular_tools.append(toolid)
    
    # 2. 处理 MCP 服务连接
    logger.info(f"[DEBUG-MCP] 分组完成，MCP服务={mcp_services_needed}, 普通工具={regular_tools}")
    all_configs = load_server_configs()
    configs_to_connect = {}  # 需要新建连接的服务配置
    
    logger.info(f"[DEBUG-MCP] 开始处理MCP服务连接，需要连接的服务={list(mcp_services_needed.keys())}")
    for service_id, toolids in mcp_services_needed.items():
        logger.info(f"[DEBUG-MCP] 检查服务 {service_id} 的缓存...")
        if service_id in _mcp_connection_cache:
            # 有缓存连接，直接使用
            logger.info(f"[MCP Cache] 复用缓存连接: {service_id}")
            client = _mcp_connection_cache[service_id]
            try:
                # 从缓存的客户端获取工具
                logger.info(f"[DEBUG-MCP] 从缓存连接获取工具...")
                all_tools = await client.get_tools()
                logger.info(f"[DEBUG-MCP] 缓存连接获取到 {len(all_tools)} 个工具: {[t.name for t in all_tools]}")
                for tool in all_tools:
                    # 直接匹配（现在存储的都是无前缀的工具名）
                    is_match = tool.name in toolids
                    
                    logger.info(f"[DEBUG-MCP] 检查工具: {tool.name}, 需要的工具: {toolids}, 是否匹配: {is_match}")
                    if is_match:
                        selected_tools.append(tool)
                        logger.info(f"[DEBUG-MCP] 添加MCP工具: {tool.name}")
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
    logger.info(f"[DEBUG-MCP] 需要新建连接的服务={list(configs_to_connect.keys())}")
    if configs_to_connect:
        logger.info(f"[MCP] 新建连接: {list(configs_to_connect.keys())}")
        logger.info(f"[DEBUG-MCP] 即将创建 MultiServerMCPClient...")
        try:
            # 注意：langchain-mcp-adapters 0.1.0+ 不支持 async with
            client = MultiServerMCPClient(configs_to_connect)
            #logger.info(f"[DEBUG-MCP] MultiServerMCPClient 创建成功，即将获取工具...")
            mcp_tools = await client.get_tools()
            logger.info(f"[DEBUG-MCP] 获取到 {len(mcp_tools)} 个工具")
            
            # 缓存客户端连接
            for service_id in configs_to_connect.keys():
                _mcp_connection_cache[service_id] = client
                logger.info(f"[MCP Cache] 缓存新连接: {service_id}")
            
            # 添加需要的工具
            needed_toolids = []
            for toolids in mcp_services_needed.values():
                needed_toolids.extend(toolids)
            
            logger.info(f"[DEBUG-MCP] 获取到的工具列表: {[t.name for t in mcp_tools]}")
            for tool in mcp_tools:
                # 直接匹配（现在存储的都是无前缀的工具名）
                is_match = tool.name in needed_toolids
                
                logger.info(f"[DEBUG-MCP] 检查工具: {tool.name}, 是否匹配: {is_match}")
                if is_match:
                    selected_tools.append(tool)
                    logger.info(f"[DEBUG-MCP] 添加MCP工具: {tool.name}")
                    
        except Exception as e:
            logger.error(f"[MCP] 新建连接失败: {e}")
            logger.error(f"[DEBUG-MCP] 异常详情: {str(e)}")
    else:
        logger.info(f"[DEBUG-MCP] 没有需要新建连接的服务")
    
    # 4. 添加普通工具
    logger.info(f"[DEBUG-MCP] 开始添加普通工具，数量={len(regular_tools)}")
    regular_tools_dict = _get_regular_tools_dict()
    for toolid in regular_tools:
        if toolid in regular_tools_dict:
            selected_tools.append(regular_tools_dict[toolid])
            logger.info(f"[DEBUG-MCP] 添加普通工具: {toolid}")
    
    logger.info(f"[DEBUG-MCP] 工具获取完成，共 {len(selected_tools)} 个工具")
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
                            #yield {"reasoning": f"\n\n✅ 工具返回数据成功\n\n"}
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
                    # 确保 reasoning_content 是字符串类型
                    if isinstance(reasoning_content, list):
                        reasoning_content = "".join(str(r) for r in reasoning_content)
                    else:
                        reasoning_content = str(reasoning_content)
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
    """简化版代理流式响应"""
    
    yield {"reasoning": f"\n\n✅️ 消息发送成功: {llm}\n\n"}
    
    # 提取选中的 MCP 工具ID
    selected_mcp_ids = [_get_toolid_from_config(c) for c in (tool_configs or []) if _get_toolid_from_config(c) and _get_mcp_from_config(c) == 1]
    yield {"reasoning": f"✈️ 工具连接中...\n\n"}
    # 获取工具
    mcp_client, mcp_tools = await _get_cached_mcp_client_and_tools(selected_mcp_ids if selected_mcp_ids else None)
    regular_tools = _get_regular_tools_dict()
    local_tools = [regular_tools[tid] for tid in [_get_toolid_from_config(c) for c in (tool_configs or [])] if tid and tid in regular_tools]
    all_tools = mcp_tools + local_tools
    
    logger.info(f"[MCP] 工具: MCP={len(mcp_tools)}, 本地={len(local_tools)}, 总计={len(all_tools)}")
    yield {"reasoning": f"✅️ 工具连接成功...\n\n"}
    yield {"reasoning": f"\n\n✈️ 正在初始化大模型: {llm}\n\n"}
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpoint:
 
        model = create_client(llm, thinking)
        workflow = StateGraph(MessagesState)
 
        # 绑定工具
        llm_with_tools = model.bind_tools(all_tools) if all_tools else model

        tool_node=McpToolNode(all_tools,handle_tool_errors=True)


        
        async def call_model(state):
            """调用模型，处理流式工具调用组装"""
            response = await llm_with_tools.ainvoke(state["messages"])
            
            return {"messages": [response]}

        
        workflow.add_node("agent", call_model)
        workflow.add_edge(START, "agent")
        
        if all_tools:
            workflow.add_node("tools", tool_node)
            workflow.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge("agent", END)
        
        
        
        graph = workflow.compile(checkpointer=checkpoint)
        yield {"reasoning": f"🚀 大模型初始化成功 !\n\n"}
        yield {"reasoning": f"⌛ 正在思考中...\n\n"}
        
        try:
            last = "reasoning"
            hasContent=False
            async for chunk in graph.astream(msg, config=history, stream_mode=["messages","custom"],version="v2"):
                if should_stop and should_stop():
                    #yield {"reasoning": f"\n\n⚠️ 检测到停止信号，大模型初始化已取消\n\n"}
                    break
                chunk_type = chunk.get("type")
                if chunk_type == "custom":#自定义数据输出
                    yield {f"reasoning": chunk["data"]}

                # messages 流
                if chunk_type == "messages":
                    message, meta = chunk["data"]
                    node = meta.get("langgraph_node")

                    # if node:
                    #     print("节点:", node)

                    # AI消息
                    if isinstance(message, AIMessageChunk):
                        reasoning = message.additional_kwargs.get("reasoning_content")
                        content = message.content
                        tool_calls = message.tool_calls
                        tool_chunks = message.tool_call_chunks

                        # 确保 reasoning 和 content 是字符串类型
                        if reasoning is not None:
                            if isinstance(reasoning, list):
                                reasoning = "".join(str(r) for r in reasoning)
                            else:
                                reasoning = str(reasoning)

                        if content is not None:
                            if isinstance(content, list):
                                content = "".join(str(c) for c in content)
                            else:
                                content = str(content)

                        if reasoning:
                            #print("思考:", reasoning)
                            yield {"reasoning": reasoning}
                            last == "reasoning"

                        if content:
                            #print("回答:", content)
                            if last == "reasoning" :
                                if hasContent:
                                    yield {"content": f"\n\n{content}\n\n"}
                                else:
                                    yield {"content": content}
                                    hasContent=True
                                last = "content"
                            else:
                                yield {"content": content}
                        # #只输出有 name 的 tool_calls
                        # valid_calls = [tc for tc in tool_calls if tc.get("name")]
                        # if valid_calls:
                        #     #print("工具调用:", valid_calls)
                        #     yield {"reasoning": f"\n\n⌛ 正在调用工具: {valid_calls}\n\n"}

                        # if tool_chunks:
                        #     if tool_calls:
                        #         yield {"reasoning": f"\n\n⌛ToolCall完整信息: {tool_chunks}\n\n"}
                        #     else:
                        #          yield {"reasoning": f"\n⌛正在准备参数: {tool_chunks}\n"}   
                    # 工具消息
                    # elif isinstance(message, ToolMessage):

                    #     if message.content:
                    #         # 只显示摘要
                    #         content = message.content
                    #         if content.startswith("[完成]") or content.startswith("[失败]"):
                    #             parts = content.split(":", 1)
                    #             summary = parts[0] if len(parts) == 1 else parts[0] + ":" + parts[1][:500] + "..."
                    #         else:
                    #             summary = content[:30] + "..." if len(content) > 30 else content
                    #         # print("工具结果:", summary)
                    #         yield {"reasoning": f"\n\n✅️ 调用完成: {summary}\n\n"}
        except Exception as e:
            # 此处应有表达式：捕获异常并记录日志
            logger.error(f"[agent_stream1] 运行时异常: {e}")
            yield {"reasoning": f"\n\n❌️ 调用失败: {str(e)}\n\n"}
       



async def agent_stream3(
        llm: str,
        msg,
        thinking: str,
        tool_configs: List,
        history,
        should_stop: Optional[Callable[[], bool]] = None,
) -> AsyncGenerator[dict, None]:

    print("\n" + "=" * 50)
    print("示例：在 Agent 中使用（修复版 LangGraph + Guarded ToolNode）")
    print("=" * 50)

    # 使用缓存的 MCP 客户端和工具
    client, tools = await _get_cached_mcp_client_and_tools()

    if not tools:
        print("⚠️ 没有可用的 MCP 工具")
        return

    print(f"MCP 获取工具成功，共 {len(tools)} 个工具")
    lient=create_client(llm)

    # 初始化 DeepSeek 模型
    # llm = ChatDeepSeek(
    #     model="qwen-plus",
    #     api_key="sk-0bcb72d37754406c80b74211c3402d5d",
    #     api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    # )

    # 将工具绑定到 LLM
    llm_with_tools = lient.bind_tools(tools)

    # 定义 Agent 节点函数
    async def call_model(state: MessagesState):
        """
        Agent 节点核心逻辑
        
        Args:
            state: MessagesState，包含历史消息
            
        Returns:
            包含 LLM 响应的状态更新
        """
        # print("  [DEBUG] 进入 agent 节点，正在调用 LLM...")
        response = await llm_with_tools.ainvoke(state["messages"])
        # print("  [DEBUG] LLM 调用完成")
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

    #准备初始对话
    messages = [
        {"role": "system", "content": """你是一个新闻助手。
        1. 搜索时优先关注结果的时间戳。
        2. 如果连续两次搜索都没有找到当日的具体新闻条目，请直接告诉用户目前网络搜索结果多为旅游资讯，并提供已找到的相关动态。
        3. 严禁陷入无限重复搜索的死循环。最多尝试 2 次不同关键词 就可以总结了。"""},
        {"role": "user", "content": "请帮我查一下北京的最新资讯？"}
    ]

    input_state = {"messages": messages}
       # """构建消息列表"""
    msg_list_agent = [
        {"role": "system", "content": history},
        {"role": "user", "content": msg}
]
    #msg = build_messages(history, msg)

    msg2= {"messages": msg_list_agent}

    print(msg2)

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
                        # 确保 reasoning 是字符串类型
                        if isinstance(reasoning, list):
                            reasoning = "".join(str(r) for r in reasoning)
                        else:
                            reasoning = str(reasoning)
                        print(f"{reasoning}", end="", flush=True)
                        yield {"reasoning": f"{reasoning}"}

                # 2. 提取正式回答内容
                if hasattr(chunk, "content") and chunk.content:
                    content = chunk.content
                    # 确保 content 是字符串类型
                    if isinstance(content, list):
                        content = "".join(str(c) for c in content)
                    else:
                        content = str(content)
                    print(content, end="", flush=True)
                    yield {"content": f"{content}"}

            # --- 情况 B: 节点状态处理 (updates) ---
            elif mode == "updates":
                for node, state in data.items():
                    if node == "agent":
                        # 检查是否有工具调用动作
                        msgs = state.get("messages", [])
                        if msgs and hasattr(msgs[-1], "tool_calls") and msgs[-1].tool_calls:
                            tool_name = msgs[-1].tool_calls[0]['name']
                            print(f"\n\n🛠️  [系统动作] 正在调用工具: {tool_name}...")
                            yield {"reasoning": f"\n\n🛠️  [系统动作] 正在调用工具: {tool_name}...\n"}

                    elif node == "tools":
                        print(f"✅ [系统动作] 工具执行完毕，获取到数据。")
                        yield {"reasoning": f"✅ [系统动作] 工具执行完毕，获取到数据。\n"}
                        #print("\n--- 正在生成最终回答 ---\n")

    except Exception as e:
        print(f"\n❌ 运行中断: {e}")
        yield {"reasoning": f"\n❌ 运行中断: {e}\n"}
        yield {"content": f"\n❌ 模型调用失败: {str(e)}\n\n建议：请尝试重新提问或创建新会话。\n"}