"""
MCP 工具模块
提供单例模式的 MCP 工具管理
"""

import asyncio
import os
import platform
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from langchain_core.tools import BaseTool

# 全局单例变量
_mcp_tools: Optional[List[BaseTool]] = None
_mcp_tools_by_service: Optional[Dict[str, List[BaseTool]]] = None
_mcp_clients: Dict[str, Any] = {}

# 异步锁，防止并发加载
_mcp_load_lock = asyncio.Lock()


@dataclass
class MCPService:
    """MCP 服务对象"""
    name: str
    transport: str
    config: Dict[str, Any]
    tools: List[BaseTool]


def _get_config_path() -> str:
    """获取 MCP 配置文件路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, "mcp.yaml")
    json_path = os.path.join(current_dir, "mcp.json")
    
    if os.path.exists(yaml_path):
        return yaml_path
    return json_path


def _load_yaml_config(config_path: str) -> Dict[str, Any]:
    """加载 YAML 配置文件"""
    try:
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        print("[MCP] 请安装 pyyaml: pip install pyyaml")
        return {}
    except Exception as e:
        print(f"[MCP] 读取 YAML 配置失败: {e}")
        return {}


def _load_json_config(config_path: str) -> Dict[str, Any]:
    """加载 JSON 配置文件"""
    import json
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[MCP] 读取 JSON 配置失败: {e}")
        return {}


def _load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载配置文件"""
    if config_path is None:
        config_path = _get_config_path()
    
    if not os.path.exists(config_path):
        print(f"[MCP] 配置文件不存在: {config_path}")
        return {}
    
    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
        return _load_yaml_config(config_path)
    else:
        return _load_json_config(config_path)


def _get_server_configs(config_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    获取 MCP 服务器配置（用于 MultiServerMCPClient）
    
    Returns:
        {服务名: 配置字典}
    """
    config = _load_config(config_path)
    servers = config.get("servers", [])
    
    if isinstance(servers, dict):
        # 旧格式：字典
        servers_list = []
        for name, cfg in servers.items():
            cfg['name'] = name
            servers_list.append(cfg)
        servers = servers_list
    
    is_windows = platform.system() == "Windows"
    result = {}
    
    for server in servers:
        name = server.get('name')
        if not name:
            continue
            
        # 复制配置
        processed_config = dict(server)
        processed_config.pop('name', None)
        
        # 处理平台特定配置
        if is_windows and "windows" in server:
            processed_config.update(server["windows"])
        elif not is_windows and "linux" in server:
            processed_config.update(server["linux"])
        elif not is_windows and "macos" in server:
            processed_config.update(server["macos"])
        
        # 移除平台特定键
        for key in ["windows", "linux", "macos"]:
            processed_config.pop(key, None)
        
        result[name] = processed_config
    
    return result


def _get_services_list(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    获取服务列表（新格式：列表）
    
    Returns:
        [{name, transport, config}, ...]
    """
    config = _load_config(config_path)
    servers = config.get("servers", [])
    
    if isinstance(servers, dict):
        # 旧格式转换为列表
        result = []
        for name, cfg in servers.items():
            result.append({
                'name': name,
                **cfg
            })
        return result
    
    return servers


async def _load_service_tools(service_name: str, service_config: Dict[str, Any]) -> List[BaseTool]:
    """
    加载单个服务的工具
    
    Args:
        service_name: 服务名称
        service_config: 服务配置
        
    Returns:
        该服务的工具列表
    """
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        # 创建单服务客户端
        single_config = {service_name: service_config}
        client = MultiServerMCPClient(single_config)
        
        # 获取该服务的工具
        tools = await client.get_tools()
        
        # 保存客户端以便后续清理
        _mcp_clients[service_name] = client
        
        print(f"[MCP] 服务 '{service_name}' 加载了 {len(tools)} 个工具")
        return tools
        
    except Exception as e:
        print(f"[MCP] 加载服务 '{service_name}' 失败: {e}")
        return []


async def _load_all_services() -> Dict[str, MCPService]:
    """
    加载所有 MCP 服务及其工具
    
    Returns:
        {服务名: MCPService对象}
    """
    services_list = _get_services_list()
    server_configs = _get_server_configs()
    
    if not services_list:
        print("[MCP] 没有可用的 MCP 服务器配置")
        return {}
    
    services = {}
    
    for service_info in services_list:
        name = service_info.get('name')
        if not name:
            continue
        
        transport = service_info.get('transport', 'stdio')
        config = server_configs.get(name, {})
        
        # 加载该服务的工具
        tools = await _load_service_tools(name, config)
        
        services[name] = MCPService(
            name=name,
            transport=transport,
            config=config,
            tools=tools
        )
    
    return services


async def get_mcptools_by_service() -> Dict[str, List[BaseTool]]:
    """
    按 MCP 服务分组获取工具
    每个服务单独连接，直接获取属于自己的工具
    
    Returns:
        按服务名称分组的工具字典 {服务名: [工具列表]}
    """
    global _mcp_tools_by_service
    
    if _mcp_tools_by_service is not None:
        return _mcp_tools_by_service
    
    async with _mcp_load_lock:
        if _mcp_tools_by_service is not None:
            return _mcp_tools_by_service
        
        services = await _load_all_services()
        
        _mcp_tools_by_service = {
            name: service.tools 
            for name, service in services.items()
        }
        
        return _mcp_tools_by_service


def get_mcptools_by_service_sync() -> Dict[str, List[BaseTool]]:
    """同步按服务分组获取 MCP 工具"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_mcptools_by_service())
                return future.result()
        else:
            return loop.run_until_complete(get_mcptools_by_service())
    except RuntimeError:
        return asyncio.run(get_mcptools_by_service())


async def get_mcptools() -> List[BaseTool]:
    """
    异步获取所有 MCP 工具（不分组）
    
    Returns:
        所有 MCP 工具列表
    """
    global _mcp_tools
    
    if _mcp_tools is not None:
        return _mcp_tools
    
    async with _mcp_load_lock:
        if _mcp_tools is not None:
            return _mcp_tools
        
        services = await _load_all_services()
        
        # 合并所有服务的工具
        all_tools = []
        for service in services.values():
            all_tools.extend(service.tools)
        
        _mcp_tools = all_tools
        
        print(f"[MCP] 总共加载 {len(all_tools)} 个工具")
        return all_tools


def get_mcptools_sync() -> List[BaseTool]:
    """同步获取所有 MCP 工具"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_mcptools())
                return future.result()
        else:
            return loop.run_until_complete(get_mcptools())
    except RuntimeError:
        return asyncio.run(get_mcptools())


def clear_mcptools_cache():
    """清除 MCP 工具缓存"""
    global _mcp_tools, _mcp_tools_by_service, _mcp_clients
    _mcp_tools = None
    _mcp_tools_by_service = None
    
    # 关闭所有客户端连接
    for client in _mcp_clients.values():
        try:
            if hasattr(client, 'close'):
                asyncio.create_task(client.close())
        except:
            pass
    
    _mcp_clients = {}
    print("[MCP] 工具缓存已清除")


async def reload_mcptools() -> List[BaseTool]:
    """重新加载 MCP 工具"""
    clear_mcptools_cache()
    return await get_mcptools()


async def merge_tools(*tool_lists: List[BaseTool]) -> List[BaseTool]:
    """
    异步合并多个工具列表（包含 MCP 工具）
    
    Args:
        *tool_lists: 多个工具列表
        
    Returns:
        合并后的工具列表
    """
    mcp_tools = await get_mcptools()
    
    merged = list(mcp_tools)
    
    for tools in tool_lists:
        if tools:
            merged.extend(tools)
    
    # 去重
    seen = set()
    unique_tools = []
    for tool in merged:
        if tool.name not in seen:
            seen.add(tool.name)
            unique_tools.append(tool)
    
    print(f"[MCP] 合并后共 {len(unique_tools)} 个工具")
    return unique_tools


def merge_tools_sync(*tool_lists: List[BaseTool]) -> List[BaseTool]:
    """
    同步合并多个工具列表
    
    Args:
        *tool_lists: 多个工具列表
        
    Returns:
        合并后的工具列表
    """
    mcp_tools = get_mcptools_sync()
    
    merged = list(mcp_tools)
    
    for tools in tool_lists:
        if tools:
            merged.extend(tools)
    
    # 去重
    seen = set()
    unique_tools = []
    for tool in merged:
        if tool.name not in seen:
            seen.add(tool.name)
            unique_tools.append(tool)
    
    return unique_tools


# 导出主要功能
__all__ = [
    'MCPService',                   # MCP 服务对象
    'get_mcptools',                 # 异步获取 MCP 工具
    'get_mcptools_sync',            # 同步获取 MCP 工具
    'get_mcptools_by_service',      # 异步按服务分组获取
    'get_mcptools_by_service_sync', # 同步按服务分组获取
    'merge_tools',                  # 异步合并工具
    'merge_tools_sync',             # 同步合并工具
    'clear_mcptools_cache',         # 清除缓存
    'reload_mcptools',              # 重新加载
]
