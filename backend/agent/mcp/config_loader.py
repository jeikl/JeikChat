"""
MCP 配置加载模块
支持从 YAML/JSON 文件加载 MCP 服务器配置
支持 stdio、sse、streamable_http 等多种传输类型
"""

import os
import platform
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .models import MCPServerConfig, TransportType


def get_config_path() -> str:
    """获取 MCP 配置文件路径"""
    current_dir = Path(__file__).parent
    yaml_path = current_dir / "mcp.yaml"
    yml_path = current_dir / "mcp.yml"
    json_path = current_dir / "mcp.json"
    
    if yaml_path.exists():
        return str(yaml_path)
    if yml_path.exists():
        return str(yml_path)
    if json_path.exists():
        return str(json_path)
    
    return str(yaml_path)  # 默认返回 yaml 路径


def _load_yaml_config(config_path: str) -> Dict[str, Any]:
    """加载 YAML 配置文件"""
    try:
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        raise ImportError("请安装 pyyaml: pip install pyyaml")
    except Exception as e:
        print(f"[MCP] 读取 YAML 配置失败: {e}")
        return {}


def _load_json_config(config_path: str) -> Dict[str, Any]:
    """加载 JSON 配置文件"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception as e:
        print(f"[MCP] 读取 JSON 配置失败: {e}")
        return {}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载配置文件"""
    if config_path is None:
        config_path = get_config_path()
    
    if not os.path.exists(config_path):
        print(f"[MCP] 配置文件不存在: {config_path}")
        return {}
    
    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
        return _load_yaml_config(config_path)
    else:
        return _load_json_config(config_path)


def _apply_platform_config(server_config: Dict[str, Any]) -> Dict[str, Any]:
    """应用平台特定配置"""
    system = platform.system()
    result = dict(server_config)
    
    # 根据平台应用特定配置
    if system == "Windows" and "windows" in server_config:
        result.update(server_config["windows"])
    elif system == "Linux" and "linux" in server_config:
        result.update(server_config["linux"])
    elif system == "Darwin" and "macos" in server_config:
        result.update(server_config["macos"])
    
    # 移除平台特定键
    for key in ["windows", "linux", "macos"]:
        result.pop(key, None)
    
    return result


def parse_server_config(server_data: Dict[str, Any]) -> MCPServerConfig:
    """解析单个服务器配置"""
    # 应用平台特定配置
    config = _apply_platform_config(server_data)
    
    # 获取传输类型
    transport_str = config.get("transport", "stdio")
    try:
        transport = TransportType(transport_str)
    except ValueError:
        print(f"[MCP] 未知的传输类型: {transport_str}，使用默认 stdio")
        transport = TransportType.STDIO
    
    # 构建 MCPServerConfig
    return MCPServerConfig(
        name=config.get("name", "unnamed"),
        transport=transport,
        command=config.get("command"),
        args=config.get("args", []),
        env=config.get("env", {}),
        url=config.get("url"),
        headers=config.get("headers", {}),
        windows=server_data.get("windows"),
        linux=server_data.get("linux"),
        macos=server_data.get("macos"),
        timeout=config.get("timeout", 30),
        enabled=config.get("enabled", True),
    )


def load_server_configs(config_path: Optional[str] = None) -> List[MCPServerConfig]:
    """
    加载所有 MCP 服务器配置
    
    Returns:
        MCPServerConfig 列表
    """
    config = load_config(config_path)
    servers_data = config.get("servers", [])
    
    # 处理新旧格式兼容
    if isinstance(servers_data, dict):
        # 旧格式：字典 {name: config}
        result = []
        for name, cfg in servers_data.items():
            if isinstance(cfg, dict):
                cfg["name"] = name
                result.append(parse_server_config(cfg))
        return result
    
    # 新格式：列表
    if isinstance(servers_data, list):
        return [
            parse_server_config(server_data)
            for server_data in servers_data
            if isinstance(server_data, dict) and server_data.get("enabled", True)
        ]
    
    return []


def get_server_config_dict(config_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    获取 MCP 服务器配置字典（用于 MultiServerMCPClient）
    
    Returns:
        {服务名: 配置字典}
    """
    configs = load_server_configs(config_path)
    return {
        cfg.name: cfg.to_client_config()
        for cfg in configs
        if cfg.enabled
    }


def get_settings(config_path: Optional[str] = None) -> Dict[str, Any]:
    """获取全局设置"""
    config = load_config(config_path)
    return config.get("settings", {
        "timeout": 30,
        "auto_reload": True,
        "log_level": "info",
    })


def get_default_selected_tools(config_path: Optional[str] = None) -> List[str]:
    """
    获取默认选中的工具列表（支持通配符模式）
    
    Returns:
        默认选中的工具ID列表（包含通配符模式，如 zhipu-web-search-sse_*）
    """
    config = load_config(config_path)
    return config.get("default_selected_tools", [])
