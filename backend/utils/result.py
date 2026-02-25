"""
统一响应结果工具
"""
from typing import Generic, TypeVar, Optional, Any
from fastapi.responses import StreamingResponse
import json

T = TypeVar('T')


def success(data: Any = None, msg: str = "操作成功", code: int = 1):
    """
    成功响应
    """
    return {
        "status": code,
        "data": data,
        "msg": msg
    }


def error(msg: str = "操作失败", data: Any = None):
    """
    失败响应
    """
    return {
        "status": 0,
        "data": data,
        "msg": msg
    }


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
