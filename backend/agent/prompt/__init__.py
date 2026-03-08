"""
提示词模块
"""

from functools import lru_cache
from pathlib import Path
import yaml
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# 当前文件所在目录
PROMPT_DIR = Path(__file__).parent

# TOOL_DESCRIPTIONS = {
#     "web_search": "网页搜索工具，用于获取最新信息",
#     "weather": "天气查询工具，用于获取城市天气",
#     "calculator": "计算器工具，用于数学计算",
# }


class Prompts:
    
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._load_prompts()
            Prompts._initialized = True

    def _load_prompts(self):
        # 新的路径：从 agent/prompt/prompts.yaml 加载
        prompts_file = PROMPT_DIR / "prompts.yaml"
        
        # 兼容旧路径：如果新路径不存在，尝试从 app/prompts.yaml 加载
        if not prompts_file.exists():
            old_prompts_file = Path(__file__).parent.parent.parent / "app" / "prompts.yaml"
            if old_prompts_file.exists():
                prompts_file = old_prompts_file
        
        if prompts_file.exists():
            with open(prompts_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            self.CHAT_SYSTEM_PROMPT = data.get("chat", {}).get("system", "")
            self.CHAT_WELCOME_PROMPT = data.get("chat", {}).get("welcome", "")
            self.AGENT_SYSTEM_PROMPT = data.get("agent", {}).get("system", "")
            self.RAG_SYSTEM_PROMPT = data.get("rag", {}).get("system", "")
            self.RAG_NO_CONTEXT_PROMPT = data.get("rag", {}).get("no_context", "")
        else:
            self._load_default_prompts()

    def _load_default_prompts(self):
        self.CHAT_SYSTEM_PROMPT = "你是一个专业的AI客服助手"
        self.CHAT_WELCOME_PROMPT = "欢迎使用JeikChat智能客服！"
        self.AGENT_SYSTEM_PROMPT = "你是一个智能Agent助手"
        self.RAG_SYSTEM_PROMPT = "你是一个知识库问答助手"
        self.RAG_NO_CONTEXT_PROMPT = "未找到相关信息"

    def get_chat_prompt(self) -> str:
        return self.CHAT_SYSTEM_PROMPT

    def get_welcome_prompt(self) -> str:
        return self.CHAT_WELCOME_PROMPT

    async def get_agent_prompt(self, tool_ids: List[str]) -> str:
        """异步获取Agent提示词（修复死锁问题）"""
        from agent.mcp.cache_manager import get_cache_manager
        from agent.tools import get_regular_tools
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[DEBUG-PROMPT] get_agent_prompt 开始，工具IDs={tool_ids}")
        
        # 获取普通工具（内存中的，不连接外部服务）
        regular_tools = get_regular_tools()
        
        # 异步获取缓存（使用await，不会阻塞事件循环）
        cache = await get_cache_manager()
        
        base_prompt = self.AGENT_SYSTEM_PROMPT or "你是一个智能Agent助手。"
        tools_desc = []
        
        for tid in tool_ids:
            found = False
            # 先在普通工具中查找
            for tool in regular_tools:
                if tool.name == tid:
                    tools_desc.append(f"- {tool.name}: {tool.description}")
                    found = True
                    break
            
            # 再在 MCP 缓存中查找
            if not found:
                # MCP 工具：分割前缀获取实际工具名
                # 格式: service_name_tool_name (如: bing-search_bing_search)
                actual_tool_name = tid
                if "_" in tid:
                    actual_tool_name = tid.split("_", 1)[1]
                
                tool_info = cache.get_tool_info(actual_tool_name)
                if tool_info:
                    tools_desc.append(f"- {tool_info.name}: {tool_info.description}")
        
        if tools_desc:
            tools_list = "你目前可用的工具：\n" + "\n".join(tools_desc)
            return base_prompt.replace("{tools}", tools_list)
        
        return base_prompt.replace("{tools}", "")

    def get_rag_prompt(self) -> str:
        return self.RAG_SYSTEM_PROMPT

    def get_rag_no_context_prompt(self) -> str:
        return self.RAG_NO_CONTEXT_PROMPT


def build_messages(system_prompt: str, user_content: str):

    """构建消息列表"""
    msg_list_agent = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
]
    return {"messages": msg_list_agent}



@lru_cache()
def get_prompts() -> Prompts:
    return Prompts()
