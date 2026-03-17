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
        # 新的路径：从 config/prompts.yaml 加载
        prompts_file = Path(__file__).parent.parent.parent / "config" / "prompts.yaml"
        
        # 兼容旧路径
        if not prompts_file.exists():
            old_prompts_file = Path(__file__).parent / "prompts.yaml"
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
        self.RAG_SYSTEM_PROMPT = "你是一个知识库问答助手\n你有以下知识库可供检索：\n{knowledge_names_str}\n当用户询问专业性问题时，请使用 retrieve_documents 工具从上述知识库中检索相关文档作为参考。"
        self.RAG_NO_CONTEXT_PROMPT = "未找到相关信息"

    def get_chat_prompt(self) -> str:
        return self.CHAT_SYSTEM_PROMPT

    def get_welcome_prompt(self) -> str:
        return self.CHAT_WELCOME_PROMPT
        
    def get_knowledge_base_hint(self) -> str:
        return self.RAG_SYSTEM_PROMPT

    async def get_agent_prompt(self, tool_ids: List[str]) -> str:
        """异步获取Agent提示词"""
        from agent.mcp.cache_manager import get_cache_manager
        from agent.tools import get_regular_tools
        import logging
        logger = logging.getLogger(__name__)
        
        # logger.info(f"[DEBUG-PROMPT] 工具IDs={tool_ids}")
        
        regular_tools = get_regular_tools()
        cache = await get_cache_manager()
        
        base_prompt = self.AGENT_SYSTEM_PROMPT or "你是一个智能Agent助手。"
        tools_desc = []
        
        for tid in tool_ids:
            found = False
            
            # 标准化工具名（处理重复前缀如 github_github_xxx -> github_xxx）
            normalized_tid = tid
            parts = tid.split('_')
            if len(parts) >= 3 and parts[0] == parts[1]:
                normalized_tid = f"{parts[0]}_{'_'.join(parts[2:])}"
            
            # 在普通工具中查找
            for tool in regular_tools:
                if tool.name == tid or tool.name == normalized_tid:
                    tools_desc.append(f"- {tool.name}: {tool.description}")
                    found = True
                    break
            
            # 在 MCP 缓存中查找（使用原始名和标准化名）
            if not found:
                for try_tid in [tid, normalized_tid]:
                    tool_info = cache.get_tool_info(try_tid)
                    if tool_info:
                        tools_desc.append(f"- {tool_info.name}: {tool_info.description}")
                        found = True
                        break
        
        if tools_desc:
            tools_list = "你目前可用的工具：\n" + "\n".join(tools_desc)
            result = base_prompt.replace("{tools}", tools_list)
        else:
            result = base_prompt.replace("{tools}", "")
        
        # logger.info(f"[DEBUG-PROMPT] 找到工具: {len(tools_desc)}/{len(tool_ids)}")
        return result

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
