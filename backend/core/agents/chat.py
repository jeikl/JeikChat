from langchain.agents import create_agent

from langgraph.checkpoint.memory import InMemorySaver  # [!code highlight]

def get_configuration(id: str) -> dict:
    """
    获取聊天智能体配置
    
    Args:
        id: 配置ID
    
    Returns:
        配置字典
    """
    return {
        "configurable": {
            "thread_id": id,
        }
    }
def chat_agent(model: str, context: str, system: str, configid: str) -> create_agent:
    """
    创建聊天智能体
    
    Args:
        model: 模型名称
        tools: 工具列表
        system_prompt: 系统提示
    
    Returns:
        AgentExecutor 实例
    """


    config={
        "configurable": {
            "thread_id": configid,
        }
    }
    llm = get_llm(model)
    chat = create_agent(model=llm, system_prompt=system,checkpointer=InMemorySaver())

    return chat
