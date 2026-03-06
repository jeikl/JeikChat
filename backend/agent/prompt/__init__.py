"""
提示词模块
"""

from functools import lru_cache
from pathlib import Path
import yaml
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
PROJECT_ROOT = Path(__file__).parent.parent.parent

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
        prompts_file = PROJECT_ROOT / "app" / "prompts.yaml"
        
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

    def get_agent_prompt(self, tool_ids: List[str]) -> str:
        from agent.chatRouterStream import tools
        
        base_prompt = self.AGENT_SYSTEM_PROMPT or "你是一个智能Agent助手。"
        tools_desc = []
        for tid in tool_ids:
            for tool in tools:
                if tool.name == tid:
                    tools_desc.append(f"- {tool.name}: {tool.description}")
                    break
        
        if tools_desc:
            tools_list = "你目前可用的工具：\n" + "\n".join(tools_desc)
            return base_prompt.replace("{tools}", tools_list)
        
        return base_prompt.replace("{tools}", "")

    def get_rag_prompt(self) -> str:
        return self.RAG_SYSTEM_PROMPT

    def get_rag_no_context_prompt(self) -> str:
        return self.RAG_NO_CONTEXT_PROMPT


def build_messages(system_prompt: str, user_content: str, agent: bool = False):
    """构建消息列表"""

    # 初始化消息列表
    msg_list = [SystemMessage(content=system_prompt)]
    
    # if history:
    #     for msg in history[-10:]:
    #         if msg.get("role") == "user":
    #             msg_list.append(HumanMessage(content=msg.get("content", "")))
    #         elif msg.get("role") == "assistant":
    #             msg_list.append(AIMessage(content=msg.get("content", "")))
    
    msg_list.append(HumanMessage(content=user_content))
    

    if agent:
        msg_list_agent = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
    ]
        return {"messages": msg_list_agent}


        # return {"messages": msg_list}
    else:
        return msg_list


@lru_cache()
def get_prompts() -> Prompts:
    return Prompts()
