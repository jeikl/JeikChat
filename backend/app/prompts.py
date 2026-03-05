"""
提示词配置文件
从 YAML 文件加载提示词
"""

from functools import lru_cache
from pathlib import Path
import yaml
from langchain.messages import HumanMessage, SystemMessage

PROJECT_ROOT = Path(__file__).parent.parent


class Prompts:
    """
    提示词配置类
    """

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
        """从 YAML 文件加载提示词"""
        prompts_file = PROJECT_ROOT / "app" / "prompts.yaml"
        
        if prompts_file.exists():
            with open(prompts_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            # 聊天相关提示词
            self.CHAT_SYSTEM_PROMPT = data.get("chat", {}).get("system", "")
            self.CHAT_WELCOME_PROMPT = data.get("chat", {}).get("welcome", "")

            # 工具相关提示词
            self.TOOL_WEB_SEARCH_PROMPT = data.get("tools", {}).get("web_search", "")
            self.TOOL_CALCULATOR_PROMPT = data.get("tools", {}).get("calculator", "")

            # Agent 提示词
            self.AGENT_SYSTEM_PROMPT = data.get("agent", {}).get("system", "")

            # RAG 提示词
            self.RAG_SYSTEM_PROMPT = data.get("rag", {}).get("system", "")
            self.RAG_NO_CONTEXT_PROMPT = data.get("rag", {}).get("no_context", "")
        else:
            # 如果文件不存在，使用默认值
            self._load_default_prompts()

    def _load_default_prompts(self):
        """加载默认提示词"""
        self.CHAT_SYSTEM_PROMPT = "你是一个专业的AI客服助手"
        self.CHAT_WELCOME_PROMPT = "欢迎使用JeikChat智能客服！"
        self.TOOL_WEB_SEARCH_PROMPT = "你是一个专业的搜索助手"
        self.TOOL_CALCULATOR_PROMPT = "你是一个数学计算助手"
        self.AGENT_SYSTEM_PROMPT = "你是一个智能Agent助手"
        self.RAG_SYSTEM_PROMPT = "你是一个知识库问答助手"
        self.RAG_NO_CONTEXT_PROMPT = "未找到相关信息"

    # ============================================================
    # 获取提示词的方法
    # ============================================================

    def get_chat_prompt(self) -> str:
        """获取聊天系统提示词"""
        return self.CHAT_SYSTEM_PROMPT

    def get_welcome_prompt(self) -> str:
        """获取欢迎提示词"""
        return self.CHAT_WELCOME_PROMPT

    def get_tool_prompt(self, tool_name: str) -> str:
        """获取指定工具的提示词"""
        tool_prompts = {
            "web_search": self.TOOL_WEB_SEARCH_PROMPT,
            "calculator": self.TOOL_CALCULATOR_PROMPT,
        }
        return tool_prompts.get(tool_name, "")

    def get_agent_prompt(self) -> str:
        """获取Agent系统提示词"""
        return self.AGENT_SYSTEM_PROMPT

    def get_rag_prompt(self) -> str:
        """获取RAG系统提示词"""
        return self.RAG_SYSTEM_PROMPT

    def get_rag_no_context_prompt(self) -> str:
        """获取RAG无上下文提示词"""
        return self.RAG_NO_CONTEXT_PROMPT
    





def create_message(systemMsg: str, userMsg: str):
    """构建消息对象"""
    messages = [
        SystemMessage(content=systemMsg),
        HumanMessage(content=userMsg)
    ]
    return messages

@lru_cache()
def get_prompts() -> Prompts:
    """获取提示词单例"""
    return Prompts()

