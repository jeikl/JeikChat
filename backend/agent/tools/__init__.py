"""
Agent 工具模块
定义和导出所有普通工具
"""

from .werther import get_weather
from .getNowTime import get_current_time
from .calculate import calculate

# 普通工具列表（非 MCP）
REGULAR_TOOLS = [
    #get_weather,
    get_current_time,
    #calculate,
]


def get_regular_tools():
    """
    获取普通工具列表
    
    Returns:
        普通工具列表的副本
    """
    return REGULAR_TOOLS.copy()


# 导出
__all__ = [
    'get_weather',
    'get_current_time',
    'get_current_date',
    'calculate',
    'REGULAR_TOOLS',
    'get_regular_tools',
]
