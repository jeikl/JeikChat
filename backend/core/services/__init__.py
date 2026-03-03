"""
服务层模块
提供各种业务服务的单例访问
"""

from .singleton import SingletonMeta, singleton, ThreadSafeLazyInitializer
from .stream_manager import StreamManager, get_stream_manager

# 延迟导入服务类，避免循环导入问题
# 使用函数获取单例实例

def get_llm_service():
    """获取 LLMService 单例"""
    from .llm_service import LLMService, get_llm_service as _get_llm_service
    return _get_llm_service()


def get_rag_service():
    """获取 RAGService 单例"""
    from .rag_service import RAGService, get_rag_service as _get_rag_service
    return _get_rag_service()


def get_chat_service():
    """获取 ChatService 单例"""
    from .chat_service import ChatService, get_chat_service as _get_chat_service
    return _get_chat_service()


__all__ = [
    # 单例工具
    'SingletonMeta',
    'singleton',
    'ThreadSafeLazyInitializer',
    
    # 流式管理
    'StreamManager',
    'get_stream_manager',
    
    # 服务获取函数
    'get_llm_service',
    'get_rag_service',
    'get_chat_service',
]
