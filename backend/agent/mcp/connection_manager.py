"""
MCP 连接管理模块
按需连接 MCP 服务，管理连接生命周期
使用过滤后的 stdio 客户端解决日志污染问题
"""

import asyncio
from typing import Dict, List, Optional, Any
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel

from .models import MCPToolInfo, TransportType
from .cache_manager import get_cache_manager
from .config_loader import load_server_configs


class DynamicStdioTool:
    """
    动态 stdio 工具包装器
    每次执行时动态创建连接，避免 session 关闭问题
    """
    
    def __init__(self, name: str, description: str, service_id: str, config, args_schema=None):
        self.name = name
        self.description = description
        self.service_id = service_id
        self.config = config
        self.args_schema = args_schema
    
    async def _arun(self, **kwargs):
        """异步执行工具"""
        from .filtered_session import create_filtered_stdio_session
        from mcp.client.stdio import StdioServerParameters
        from mcp import ClientSession
        
        server_params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args,
            env=self.config.env,
        )
        
        async with create_filtered_stdio_session(server_params) as session:
            await session.initialize()
            
            # 调用工具
            result = await session.call_tool(self.name, arguments=kwargs)
            
            # 处理结果
            if result.content:
                texts = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        texts.append(content.text)
                    elif hasattr(content, 'data'):
                        texts.append(content.data)
                return "\n".join(texts) if texts else str(result.content)
            return str(result)
    
    def _run(self, **kwargs):
        """同步执行（不支持）"""
        raise NotImplementedError("This tool only supports async execution")


class MCPConnectionManager:
    """MCP 连接管理器 - 按需连接"""
    
    def __init__(self):
        self._clients: Dict[str, Any] = {}  # 已连接的客户端
        self._tools: Dict[str, List[BaseTool]] = {}  # 已加载的工具 {service_id: [tools]}
        self._tool_specs: Dict[str, List[dict]] = {}  # 工具规格 {service_id: [tool_specs]}
        self._configs: Dict[str, Any] = {}  # 服务配置 {service_id: config}
        self._lock = asyncio.Lock()
    
    async def _connect_stdio_service(self, service_id: str, config) -> Optional[List[BaseTool]]:
        """使用过滤后的 stdio 客户端连接服务"""
        from .filtered_session import create_filtered_stdio_session
        from mcp.client.stdio import StdioServerParameters
        from mcp import ClientSession
        
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env,
        )
        
        try:
            async with create_filtered_stdio_session(server_params) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                
                if not tools_result.tools:
                    return None
                
                self._configs[service_id] = config
                self._tool_specs[service_id] = []
                
                customized_tools = []
                tool_infos = []
                
                for tool_spec in tools_result.tools:
                    original_name = tool_spec.name
                    # 工具名添加服务前缀，使用连字符格式与前端保持一致
                    prefixed_name = f"{service_id}_{original_name}"
                    enhanced_desc = f"【{service_id}】 {tool_spec.description}"
                    
                    dynamic_tool = self._create_dynamic_tool(
                        name=prefixed_name,
                        description=enhanced_desc,
                        service_id=service_id,
                        config=config,
                        tool_spec=tool_spec,
                        original_name=original_name
                    )
                    
                    customized_tools.append(dynamic_tool)
                    
                    tool_info = MCPToolInfo(
                        name=prefixed_name,
                        original_name=original_name,
                        description=enhanced_desc,
                        service_id=service_id,
                        service_name=service_id,
                    )
                    tool_infos.append(tool_info)
                    self._tool_specs[service_id].append({
                        "name": prefixed_name,
                        "original_name": original_name,
                        "description": tool_spec.description,
                    })
                
                self._tools[service_id] = customized_tools
                
                cache_manager = await get_cache_manager()
                cache_manager.update_service_tools(service_id, tool_infos)
                await cache_manager.save_to_file()
                
                print(f"[MCP] {service_id}: {len(customized_tools)} 个工具")
                return customized_tools
                
        except Exception as e:
            print(f"[MCP] {service_id} 连接失败: {e}")
            cache_manager = await get_cache_manager()
            cache_manager.update_service_status(service_id, "error", str(e))
            return None
    
    def _create_dynamic_tool(self, name: str, description: str, service_id: str, config, tool_spec, original_name: str = None):
        """创建动态工具"""
        from langchain_core.tools import StructuredTool
        from pydantic import create_model, Field
        from typing import Any
        
        # 如果没有提供原始名，使用 name
        if original_name is None:
            original_name = name
        
        # 构建参数模型
        properties = tool_spec.inputSchema.get("properties", {})
        required = set(tool_spec.inputSchema.get("required", []))
        
        fields = {}
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "string")
            param_desc = param_info.get("description", "")
            
            # 映射 JSON schema 类型到 Python 类型
            type_mapping = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "array": list,
                "object": dict,
            }
            py_type = type_mapping.get(param_type, Any)
            
            # 必需参数使用 ... 作为默认值
            if param_name in required:
                fields[param_name] = (py_type, Field(..., description=param_desc))
            else:
                fields[param_name] = (Optional[py_type], Field(default=None, description=param_desc))
        
        if fields:
            ArgsModel = create_model(f"{name}_args", **fields)
        else:
            ArgsModel = create_model(f"{name}_args", __base__=BaseModel)
        
        # 创建工具实例 - 使用原始工具名调用
        async def tool_func(**kwargs):
            return await self._execute_stdio_tool(service_id, config, original_name, kwargs)
        
        return StructuredTool(
            name=name,
            description=description,
            func=tool_func,
            args_schema=ArgsModel,
            coroutine=tool_func,
        )
    
    async def _execute_stdio_tool(self, service_id: str, config, tool_name: str, arguments: dict):
        """执行 stdio 工具"""
        from .filtered_session import create_filtered_stdio_session
        from mcp.client.stdio import StdioServerParameters
        
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env,
        )
        
        async with create_filtered_stdio_session(server_params) as session:
            await session.initialize()
            
            result = await session.call_tool(tool_name, arguments=arguments)
            
            # 处理结果
            texts = []
            for content in result.content:
                if hasattr(content, 'text'):
                    texts.append(content.text)
                elif hasattr(content, 'data'):
                    texts.append(str(content.data))
            
            return "\n".join(texts) if texts else str(result.content)
    
    async def _connect_service_standard(self, service_id: str, config) -> Optional[List[BaseTool]]:
        """使用标准方式连接服务（SSE、HTTP 等）"""
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        client_config = {service_id: config.to_client_config()}
        client = MultiServerMCPClient(client_config)
        
        try:
            tools = await asyncio.wait_for(client.get_tools(), timeout=10.0)
        except asyncio.TimeoutError:
            print(f"[MCP] {service_id} 连接超时")
            cache_manager = await get_cache_manager()
            cache_manager.update_service_status(service_id, "error", "连接超时")
            return None
        
        customized_tools = []
        tool_infos = []
        
        for tool in tools:
            original_name = tool.name
            # 工具名添加服务前缀，使用连字符格式与前端保持一致
            prefixed_name = f"{service_id}_{original_name}"
            enhanced_desc = f"【{service_id}】 {tool.description}"
            tool.name = prefixed_name
            tool.description = enhanced_desc
            
            customized_tools.append(tool)
            
            tool_info = MCPToolInfo(
                name=prefixed_name,
                original_name=original_name,
                description=enhanced_desc,
                service_id=service_id,
                service_name=service_id,
            )
            tool_infos.append(tool_info)
        
        self._clients[service_id] = client
        self._tools[service_id] = customized_tools
        
        cache_manager = await get_cache_manager()
        cache_manager.update_service_tools(service_id, tool_infos)
        await cache_manager.save_to_file()
        
        print(f"[MCP] {service_id}: {len(tools)} 个工具")
        return customized_tools
    
    async def connect_service(self, service_id: str) -> Optional[List[BaseTool]]:
        """
        连接指定 MCP 服务并获取工具
        
        Args:
            service_id: 服务ID
            
        Returns:
            工具列表，连接失败返回 None
        """
        # 检查是否已连接
        if service_id in self._tools:
            return self._tools[service_id]
        
        async with self._lock:
            # 双重检查
            if service_id in self._tools:
                return self._tools[service_id]
            
            # 获取服务配置
            configs = load_server_configs()
            config = None
            for cfg in configs:
                if cfg.name == service_id:
                    config = cfg
                    break
            
            if not config:
                print(f"[MCP Connection] 服务配置不存在: {service_id}")
                return None
            
            # 根据传输类型选择连接方式
            try:
                if config.transport == TransportType.STDIO:
                    # STDIO 模式使用过滤后的客户端
                    return await self._connect_stdio_service(service_id, config)
                else:
                    # SSE、HTTP 等使用标准客户端
                    return await self._connect_service_standard(service_id, config)
                    
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                print(f"[MCP Connection] 服务 '{service_id}' 连接失败: {e}")
                print(f"[MCP Connection] 错误详情:\n{error_detail}")
                cache_manager = await get_cache_manager()
                cache_manager.update_service_status(service_id, "error", str(e))
                return None
    
    async def get_tool(self, service_id: str, tool_name: str) -> Optional[BaseTool]:
        """
        获取指定服务的指定工具
        
        Args:
            service_id: 服务ID
            tool_name: 工具名称（带前缀或不带前缀）
            
        Returns:
            工具对象，未找到返回 None
        """
        # 确保服务已连接
        tools = await self.connect_service(service_id)
        if not tools:
            return None
        
        # 查找工具
        for tool in tools:
            if tool.name == tool_name or tool.name.endswith(f"_{tool_name}"):
                return tool
        
        return None
    
    async def get_tools_by_service(self, service_id: str) -> List[BaseTool]:
        """获取指定服务的所有工具"""
        tools = await self.connect_service(service_id)
        return tools or []
    
    async def disconnect_service(self, service_id: str):
        """断开指定服务连接"""
        if service_id in self._clients:
            client = self._clients.pop(service_id)
            try:
                if hasattr(client, 'close'):
                    await client.close()
                print(f"[MCP Connection] 服务 '{service_id}' 已断开")
            except Exception as e:
                print(f"[MCP Connection] 断开服务 '{service_id}' 时出错: {e}")
        
        self._tools.pop(service_id, None)
        
        # 更新缓存状态
        cache_manager = await get_cache_manager()
        cache_manager.update_service_status(service_id, "not_connected")
    
    async def disconnect_all(self):
        """断开所有服务连接"""
        for service_id in list(self._clients.keys()):
            await self.disconnect_service(service_id)
    
    def is_connected(self, service_id: str) -> bool:
        """检查服务是否已连接"""
        return service_id in self._tools
    
    def get_connected_services(self) -> List[str]:
        """获取已连接的服务列表"""
        return list(self._tools.keys())


# 全局连接管理器
_connection_manager: Optional[MCPConnectionManager] = None


async def get_connection_manager() -> MCPConnectionManager:
    """获取连接管理器实例"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = MCPConnectionManager()
    return _connection_manager


async def load_service_tools(service_id: str) -> List[BaseTool]:
    """加载指定服务的工具（兼容旧接口）"""
    manager = await get_connection_manager()
    tools = await manager.connect_service(service_id)
    return tools or []


async def get_mcp_tool(service_id: str, tool_name: str) -> Optional[BaseTool]:
    """获取 MCP 工具（兼容旧接口）"""
    manager = await get_connection_manager()
    return await manager.get_tool(service_id, tool_name)
