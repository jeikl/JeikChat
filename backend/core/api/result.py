"""
统一响应结果函数

使用 schemas.py 中定义的 ResultResponse 类
"""

from core.api.schemas import ResultResponse
import json


def success(data=None, msg: str = "操作成功", code: int = 1):
    """
    成功响应
    返回 ResultResponse 实例
    """
    return ResultResponse(status=code, data=data, msg=msg)


def error(msg: str = "操作失败", data=None):
    """
    失败响应
    返回 ResultResponse 实例（status=0 表示失败）
    """
    return ResultResponse(status=0, data=data, msg=msg)


def sse_format(data: dict) -> str:
    """
    SSE流式响应格式化
    用于AI对话流式输出，保持原格式不包装RESTful
    """
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def sse_done() -> str:
    """
    SSE流式响应结束标记
    """
    return "data: [DONE]\n\n"
