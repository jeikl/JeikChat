"""
统一响应格式
"""

from typing import Any, Optional
import json


def success(data: Any = None, msg: str = "操作成功", code: int = 1) -> dict:
    """成功响应"""
    return {
        "status": code,
        "data": data,
        "msg": msg
    }


def error(msg: str = "操作失败", code: int = 0) -> dict:
    """错误响应"""
    return {
        "status": code,
        "data": None,
        "msg": msg
    }


def sse_format(data: dict) -> str:
    """SSE 格式数据"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def sse_done() -> str:
    """SSE 完成信号"""
    return "data: [DONE]\n\n"
