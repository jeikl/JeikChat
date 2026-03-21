from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from api.response import success
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
import re

router = APIRouter()

# 后台任务状态存储
_mcp_update_tasks: Dict[str, Any] = {}


# ============================================================
# MCP 配置管理模型
# ============================================================

class MCPServerConfigModel(BaseModel):
    """MCP 服务器配置模型"""
    name: str
    transport: str = "stdio"
    command: Optional[str] = None
    args: List[str] = []
    env: Dict[str, str] = {}
    url: Optional[str] = None
    headers: Dict[str, str] = {}
    windows: Optional[Dict[str, Any]] = None
    linux: Optional[Dict[str, Any]] = None
    macos: Optional[Dict[str, Any]] = None
    timeout: int = 30
    enabled: bool = True


class MCPConfigModel(BaseModel):
    """MCP 完整配置模型"""
    servers: List[MCPServerConfigModel]
    settings: Dict[str, Any] = {
        "timeout": 30,
        "auto_reload": True,
        "log_level": "info"
    }
    default_selected_tools: List[str] = []


class MCPConfigResponse(BaseModel):
    """MCP 配置响应"""
    config: MCPConfigModel
    config_path: str


async def get_tool_list(force_refresh: bool = False):
    """
    获取工具列表，优先从缓存加载
    返回格式包含 mcp 标记，用于前端区分 MCP 工具和普通工具
    
    对于 MCP 工具，toolid 和 name 都使用带服务前缀的名称（如: github_fork_repository）
    
    Args:
        force_refresh: 是否强制刷新缓存，重新加载 MCP 配置
    """
    from agent.mcp.cache_manager import get_cache_manager, refresh_tool_cache
    from agent.tools import get_regular_tools

    # 如果需要强制刷新，先刷新缓存
    if force_refresh:
        await refresh_tool_cache()

    # 获取缓存实例（确保已初始化）
    cache = await get_cache_manager()

    # 获取普通工具（内置工具）
    regular_tools = get_regular_tools()
    regular_tool_names = {t.name for t in regular_tools}

    # 合并所有工具
    all_tools = []

    # 添加普通工具（mcp=0）
    for tool in regular_tools:
        all_tools.append({
            "toolid": tool.name,
            "name": tool.name,
            "description": tool.description,
            "mcp": 0,  # 0 表示普通工具
            "enabled": True
        })

    # 添加 MCP 工具（mcp=1）- 从缓存的工具信息中获取
    # 注意：从文件加载时，LangChain 工具对象为空，但工具信息是可用的
    for tool_name, tool_info in cache.all_tools.items():
        if tool_name not in regular_tool_names:
            # toolid 和 name 都使用带服务前缀的名称
            all_tools.append({
                "toolid": tool_info.name,      # 带服务前缀的名称
                "name": tool_info.name,        # 带服务前缀的名称
                "description": tool_info.description,
                "mcp": 1,  # 1 表示 MCP 工具
                "enabled": True
            })

    return all_tools


@router.get("/tools")
async def list_tools(refresh: bool = Query(False, description="是否强制刷新 MCP 缓存")):
    """
    获取所有可用的Agent工具列表
    
    - 默认使用缓存（O(1) 查询）
    - 设置 refresh=true 可强制刷新 MCP 配置并重新加载
    - 返回包含默认选中工具列表
    """
    from agent.mcp.config_loader import get_default_selected_tools
    
    tools = await get_tool_list(force_refresh=refresh)
    default_selected_tools = get_default_selected_tools()
    
    return success(data={
        "tools": tools,
        "defaultSelectedTools": default_selected_tools
    }, msg="获取成功")


@router.post("/tools/{tool_id}/enable")
async def enable_tool(tool_id: str):
    """启用工具"""
    return success(data={"tool_id": tool_id, "enabled": True}, msg="启用成功")


@router.post("/tools/{tool_id}/disable")
async def disable_tool(tool_id: str):
    """禁用工具"""
    return success(data={"tool_id": tool_id, "enabled": False}, msg="禁用成功")


@router.post("/tools/batch-set")
async def batch_set_tools(tools: list):
    """批量设置工具"""
    return success(data=tools, msg="设置成功")


@router.post("/tools/cache/refresh")
async def refresh_tools_cache():
    """刷新 MCP 工具缓存（当 MCP 服务配置变更时调用）"""
    from agent.mcp.cache_manager import refresh_tool_cache
    await refresh_tool_cache()
    return success(data=None, msg="工具缓存已刷新")


@router.get("/tools/cache/status")
async def get_tools_cache_status():
    """获取工具缓存状态"""
    from agent.mcp.cache_manager import get_cache_manager
    cache = await get_cache_manager()
    
    return success(data={
        "initialized": cache.is_initialized(),
        "total_tools": len(cache.all_tools),
        "total_services": len(cache.services),
        "services": [
            {
                "id": sid,
                "name": sinfo.name,
                "tool_count": len(sinfo.tool_names)
            }
            for sid, sinfo in cache.services.items()
        ]
    }, msg="获取成功")


# ============================================================
# MCP 配置敏感信息保护
# ============================================================

# 需要保护的字段模式（正则表达式）
SENSITIVE_PATTERNS = [
    # URL 参数中的敏感信息（按优先级排序）
    (r'(Authorization=)[^&\s]+', r'\1[protected]'),
    # secret= 相关（放在 key= 之前，避免被 key= 匹配）
    (r'(secret=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    (r'(app[_-]?secret=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    (r'(client[_-]?secret=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    # key= 相关
    (r'(api[_-]?key=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    (r'(app[_-]?key=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    (r'(access[_-]?key=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    (r'(private[_-]?key=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    # 其他敏感字段
    (r'(password=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    (r'(passwd=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    (r'(pwd=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    (r'(token=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    (r'(client[_-]?id=)[^&\s]+', r'\1[protected]', re.IGNORECASE),
    # 通用 key= 和 secret= 模式（放在最后，优先级最低）
    (r'\b(secret[=:])[^&\s]+', r'\1[protected]', re.IGNORECASE),
    (r'\b(key[=:])[^&\s]+', r'\1[protected]', re.IGNORECASE),
]

# 数据库连接字符串保护 - 保护整个连接信息
# postgresql://user:password@host:port/dbname
DB_URL_PATTERN = r'(postgresql|mysql|mongodb|redis)://([^:@]+):([^@]+)@([^/]+)(/.*)?'

# URL 路径保护 - 保护路径中的敏感部分（如 API 路径中的 token）
# https://domain.com/xxx/xxx/mcp -> https://domain.com/[protected]/[protected]/mcp
URL_PATH_PATTERN = r'(https?://[^/]+)(/[^/]+){2,}(/[^/]+)$'

def mask_sensitive_info(text: str) -> str:
    """
    将敏感信息替换为 [protected]
    
    支持的格式：
    - URL 参数: Authorization=xxx, api_key=xxx
    - 连接字符串: postgresql://user:password@host:port/db
    - 键值对: password=xxx, token=xxx
    - URL 路径: https://domain.com/secret/path/mcp
    """
    if not text or not isinstance(text, str):
        return text
    
    result = text
    
    # 保护数据库连接字符串 - 整个连接信息
    # postgresql://[protected]/dbname
    def mask_db_url(match):
        protocol = match.group(1)
        db_name = match.group(5) or ''
        return f'{protocol}://[protected]{db_name}'
    
    result = re.sub(DB_URL_PATTERN, mask_db_url, result, flags=re.IGNORECASE)
    
    # 保护 URL 路径中的敏感部分
    # https://domain.com/xxx/xxx/mcp -> https://domain.com/[protected]/[protected]/mcp
    def mask_url_path(match):
        base_url = match.group(1)
        # 保留最后一个路径段（通常是端点名称）
        last_segment = match.group(3)
        # 中间的路径段数量
        middle_segments = match.group(0).count('/') - 3  # 减去 https:// 和最后一个路径
        if middle_segments > 0:
            protected_middle = '/'.join(['[protected]'] * middle_segments)
            return f'{base_url}/{protected_middle}{last_segment}'
        return match.group(0)
    
    result = re.sub(URL_PATH_PATTERN, mask_url_path, result)
    
    # 保护其他敏感字段
    for pattern in SENSITIVE_PATTERNS:
        if len(pattern) == 3:
            result = re.sub(pattern[0], pattern[1], result, flags=pattern[2])
        else:
            result = re.sub(pattern[0], pattern[1], result)
    
    return result

def unmask_sensitive_info(new_value: str, original_value: str) -> str:
    """
    如果新值包含 [protected]，则使用原值替换
    否则使用新值
    
    用于保存配置时恢复敏感信息
    """
    if not new_value or not isinstance(new_value, str):
        return new_value
    
    if '[protected]' in new_value and original_value:
        # 将 [protected] 替换为原始值中的对应部分
        # 简单处理：如果原值存在，直接使用原值
        return original_value
    
    return new_value

def mask_server_config(server: dict) -> dict:
    """对服务器配置中的敏感信息进行脱敏处理"""
    masked = dict(server)
    
    # 保护 URL
    if masked.get("url"):
        masked["url"] = mask_sensitive_info(masked["url"])
    
    # 保护 headers 中的敏感信息
    if masked.get("headers"):
        masked["headers"] = {
            k: mask_sensitive_info(v) if isinstance(v, str) else v
            for k, v in masked["headers"].items()
        }
    
    # 保护 env 中的敏感信息
    if masked.get("env"):
        masked["env"] = {
            k: mask_sensitive_info(v) if isinstance(v, str) else v
            for k, v in masked["env"].items()
        }
    
    # 保护 args 中的敏感信息（如连接字符串）
    if masked.get("args"):
        masked["args"] = [
            mask_sensitive_info(arg) if isinstance(arg, str) else arg
            for arg in masked["args"]
        ]
    
    # 保护平台特定配置
    for platform in ["windows", "linux", "macos"]:
        if masked.get(platform):
            platform_config = dict(masked[platform])
            if platform_config.get("args"):
                platform_config["args"] = [
                    mask_sensitive_info(arg) if isinstance(arg, str) else arg
                    for arg in platform_config["args"]
                ]
            masked[platform] = platform_config
    
    return masked

def unmask_server_config(new_server: dict, original_server: dict) -> dict:
    """保存时恢复敏感信息"""
    result = dict(new_server)
    
    # 恢复 URL
    if result.get("url") and original_server.get("url"):
        result["url"] = unmask_sensitive_info(result["url"], original_server["url"])
    
    # 恢复 headers
    if result.get("headers") and original_server.get("headers"):
        result["headers"] = {
            k: unmask_sensitive_info(v, original_server["headers"].get(k, v))
            for k, v in result["headers"].items()
        }
    
    # 恢复 env
    if result.get("env") and original_server.get("env"):
        result["env"] = {
            k: unmask_sensitive_info(v, original_server["env"].get(k, v))
            for k, v in result["env"].items()
        }
    
    # 恢复 args
    if result.get("args") and original_server.get("args"):
        result["args"] = [
            unmask_sensitive_info(new_arg, orig_arg) if isinstance(new_arg, str) and isinstance(orig_arg, str) else new_arg
            for new_arg, orig_arg in zip(result["args"], original_server["args"])
        ]
        # 处理长度不一致的情况
        if len(result["args"]) < len(original_server["args"]):
            result["args"].extend(original_server["args"][len(result["args"]):])
    
    # 恢复平台特定配置
    for platform in ["windows", "linux", "macos"]:
        if result.get(platform) and original_server.get(platform):
            platform_result = dict(result[platform])
            platform_orig = original_server[platform]
            if platform_result.get("args") and platform_orig.get("args"):
                platform_result["args"] = [
                    unmask_sensitive_info(new_arg, orig_arg) if isinstance(new_arg, str) and isinstance(orig_arg, str) else new_arg
                    for new_arg, orig_arg in zip(platform_result["args"], platform_orig["args"])
                ]
            result[platform] = platform_result
    
    return result


# ============================================================
# MCP 配置管理 API
# ============================================================

@router.get("/tools/mcp/config")
async def get_mcp_config():
    """
    获取 MCP 配置文件内容
    
    返回完整的 mcp.yaml 配置，包括：
    - servers: MCP 服务器列表
    - settings: 全局设置
    - default_selected_tools: 默认选中的工具
    """
    from agent.mcp.config_loader import load_config, get_config_path, get_settings, get_default_selected_tools
    
    try:
        config_path = get_config_path()
        raw_config = load_config(config_path)
        
        # 转换服务器配置为字典格式
        servers = []
        servers_data = raw_config.get("servers", [])
        
        if isinstance(servers_data, list):
            for server in servers_data:
                if isinstance(server, dict):
                    server_dict = {
                        "name": server.get("name", ""),
                        "transport": server.get("transport", "stdio"),
                        "command": server.get("command"),
                        "args": server.get("args", []),
                        "env": server.get("env", {}),
                        "url": server.get("url"),
                        "headers": server.get("headers", {}),
                        "windows": server.get("windows"),
                        "linux": server.get("linux"),
                        "macos": server.get("macos"),
                        "timeout": server.get("timeout", 30),
                        "enabled": server.get("enabled", True)
                    }
                    # 对敏感信息进行脱敏处理
                    servers.append(mask_server_config(server_dict))
        
        return success(data={
            "config": {
                "servers": servers,
                "settings": get_settings(config_path),
                "default_selected_tools": get_default_selected_tools(config_path)
            },
            "config_path": config_path
        }, msg="获取成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取 MCP 配置失败: {str(e)}")


async def _process_mcp_servers_in_background(
    added_servers: set,
    modified_servers: set,
    new_servers: Dict[str, Any]
):
    """后台处理新增/修改的 MCP 服务器"""
    from agent.mcp.cache_manager import get_cache_manager
    from .mcp_config_updater import update_server_tools
    
    cache = await get_cache_manager()
    
    for server_name in added_servers | modified_servers:
        try:
            server_config = new_servers[server_name]
            result = await update_server_tools(server_name, server_config, cache)
            if result["status"] == "connected":
                print(f"[MCP Config] 后台连接成功: {server_name} ({result['tools_count']} 个工具)")
            elif result["status"] == "failed":
                print(f"[MCP Config] 后台连接失败: {server_name} - {result.get('error', '未知错误')}")
        except Exception as e:
            print(f"[MCP Config] 后台处理失败: {server_name} - {e}")
    
    # 保存缓存到文件
    await cache.save_to_file()
    print("[MCP Config] 后台处理完成，缓存已保存")


@router.post("/tools/mcp/config")
async def save_mcp_config(config_data: dict, background_tasks: BackgroundTasks):
    """
    保存 MCP 配置文件（智能差异化处理）
    
    - 删除的服务：立即从缓存中移除
    - 新增/修改的服务：后台异步连接（不阻塞前端）
    """
    from agent.mcp.config_loader import get_config_path, load_config
    from agent.mcp.cache_manager import get_cache_manager
    import yaml
    
    try:
        config_path = get_config_path()
        cache = await get_cache_manager()
        
        # 获取当前配置（用于对比）
        current_config = load_config(config_path)
        current_servers = {s.get("name"): s for s in current_config.get("servers", [])}
        new_servers = {s.get("name"): s for s in config_data.get("servers", [])}
        
        # 分析变更
        deleted_servers = set(current_servers.keys()) - set(new_servers.keys())
        added_servers = set(new_servers.keys()) - set(current_servers.keys())
        modified_servers = set()
        for name in set(current_servers.keys()) & set(new_servers.keys()):
            old_cfg = current_servers[name]
            new_cfg = new_servers[name]
            # 比较关键字段是否变化
            if (old_cfg.get("transport") != new_cfg.get("transport") or
                old_cfg.get("command") != new_cfg.get("command") or
                old_cfg.get("url") != new_cfg.get("url") or
                old_cfg.get("args") != new_cfg.get("args")):
                modified_servers.add(name)
        
        # 1. 立即处理删除的服务：从缓存中移除
        for server_name in deleted_servers:
            if server_name in cache.services:
                service_info = cache.services[server_name]
                for tool_name in service_info.tool_names:
                    if tool_name in cache.all_tools:
                        del cache.all_tools[tool_name]
                del cache.services[server_name]
                print(f"[MCP Config] 删除服务: {server_name}")
        
        # 2. 检查哪些服务可以直接使用缓存（已存在的）
        from .mcp_config_updater import update_server_tools
        
        results = {
            "deleted": list(deleted_servers),
            "added": [],
            "modified": list(modified_servers),
            "cached": [],
            "pending": [],  # 后台处理中的服务
            "failed": []
        }
        
        # 需要后台处理的服务
        servers_to_process_in_background = set()
        
        for server_name in added_servers | modified_servers:
            server_config = new_servers[server_name]
            # 先检查缓存
            if server_name in cache.services and len(cache.services[server_name].tool_names) > 0:
                # 缓存中存在，直接使用
                results["cached"].append(server_name)
                print(f"[MCP Config] 使用缓存: {server_name}")
            else:
                # 需要后台连接
                results["pending"].append(server_name)
                servers_to_process_in_background.add(server_name)
        
        # 3. 保存 YAML 配置文件（立即执行）
        yaml_config = {
            "servers": [],
            "settings": config_data.get("settings", {"timeout": 30, "auto_reload": True, "log_level": "info"}),
            "default_selected_tools": config_data.get("default_selected_tools", [])
        }
        
        for server in config_data.get("servers", []):
            server_dict = {
                "name": server.get("name", ""),
                "transport": server.get("transport", "stdio"),
                "enabled": server.get("enabled", True),
                "timeout": server.get("timeout", 30)
            }
            
            # 获取原始服务器配置（用于恢复敏感信息）
            original_server = current_servers.get(server.get("name", ""), {})
            
            if server.get("command"):
                server_dict["command"] = server["command"]
            if server.get("args"):
                server_dict["args"] = server["args"]
            if server.get("env"):
                server_dict["env"] = server["env"]
            if server.get("url"):
                server_dict["url"] = server["url"]
            if server.get("headers"):
                server_dict["headers"] = server["headers"]
            if server.get("windows"):
                server_dict["windows"] = server["windows"]
            if server.get("linux"):
                server_dict["linux"] = server["linux"]
            if server.get("macos"):
                server_dict["macos"] = server["macos"]
            
            # 恢复敏感信息（如果前端传来的是 [protected]，则使用原值）
            server_dict = unmask_server_config(server_dict, original_server)
            
            yaml_config["servers"].append(server_dict)
        
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        
        # 4. 保存当前缓存（包含删除和缓存命中）
        await cache.save_to_file()
        
        # 5. 后台异步处理需要连接的服务
        if servers_to_process_in_background:
            background_tasks.add_task(
                _process_mcp_servers_in_background,
                servers_to_process_in_background,
                modified_servers & servers_to_process_in_background,
                new_servers
            )
        
        # 构建提示消息
        messages = []
        if results["deleted"]:
            messages.append(f"删除 {len(results['deleted'])} 个服务")
        if results["cached"]:
            messages.append(f"使用缓存 {len(results['cached'])} 个服务")
        if results["pending"]:
            messages.append(f"后台连接 {len(results['pending'])} 个服务")
        
        msg = "，".join(messages) if messages else "配置已保存"
        
        return success(data={
            "config_path": config_path,
            "changes": results
        }, msg=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存 MCP 配置失败: {str(e)}")


@router.post("/tools/mcp/config/reload")
async def reload_mcp_config():
    """
    重新加载 MCP 配置（热重载）
    
    在不重启服务的情况下重新加载 mcp.yaml 配置
    """
    from agent.mcp.cache_manager import refresh_tool_cache
    
    try:
        await refresh_tool_cache()
        return success(data=None, msg="MCP 配置已重新加载")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载 MCP 配置失败: {str(e)}")


@router.get("/tools/mcp/validate")
async def validate_mcp_config():
    """
    验证 MCP 配置是否有效
    
    检查配置文件格式是否正确，服务器配置是否完整
    """
    from agent.mcp.config_loader import load_config, get_config_path, load_server_configs
    
    try:
        config_path = get_config_path()
        raw_config = load_config(config_path)
        
        errors = []
        warnings = []
        
        # 检查 servers 字段
        servers = raw_config.get("servers", [])
        if not servers:
            warnings.append("未配置任何 MCP 服务器")
        
        if isinstance(servers, list):
            for idx, server in enumerate(servers):
                if not isinstance(server, dict):
                    errors.append(f"服务器配置 #{idx} 格式错误")
                    continue
                
                name = server.get("name", f"#{idx}")
                transport = server.get("transport", "stdio")
                
                if not server.get("name"):
                    errors.append(f"服务器 #{idx} 缺少名称")
                
                if transport == "stdio":
                    if not server.get("command"):
                        errors.append(f"服务器 '{name}' 使用 stdio 传输但缺少 command")
                elif transport in ["sse", "streamable_http"]:
                    if not server.get("url"):
                        errors.append(f"服务器 '{name}' 使用 {transport} 传输但缺少 url")
        
        # 尝试加载验证
        try:
            load_server_configs(config_path)
        except Exception as e:
            errors.append(f"配置加载测试失败: {str(e)}")
        
        is_valid = len(errors) == 0
        
        return success(data={
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings
        }, msg="验证完成" if is_valid else "配置存在问题")
    except Exception as e:
        return success(data={
            "valid": False,
            "errors": [f"验证过程出错: {str(e)}"],
            "warnings": []
        }, msg="验证失败")
