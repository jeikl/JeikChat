"""
Agent 工具模块
定义和导出所有普通工具
"""

from .getNowTime import get_current_time
from .RAG import retrieve_documents

REGULAR_TOOLS = [
    get_current_time,
    retrieve_documents,
]


def get_regular_tools():
    """
    获取普通工具列表
    
    Returns:
        普通工具列表的副本
    """
    return REGULAR_TOOLS.copy()


__all__ = [
    'get_current_time',
    'REGULAR_TOOLS',
    'get_regular_tools',
]
