"""
数据模型定义 - 使用 Pydantic 进行 API 请求/响应数据校验

本文件定义了聊天功能相关的所有数据模型：
- 请求模型：用于接收客户端发送的数据
- 响应模型：用于返回给客户端的数据
- 通用模型：如统一响应格式 ResultResponse
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Generic, TypeVar, Literal
from datetime import datetime


T = TypeVar('T')


class ResultResponse(BaseModel, Generic[T]):
    """
    统一响应格式 - 所有 API 响应都使用此格式
    - status: 状态码，1表示成功，0表示失败
    - data: 返回的数据
    - msg: 提示信息
    """
    status: int = Field(default=1, description="状态码: 1成功, 0失败")
    data: Optional[T] = Field(default=None, description="返回数据")
    msg: str = Field(default="操作成功", description="提示信息")


class MessageCreate(BaseModel):
    """
    消息创建模型 - 创建消息时使用
    - role: 消息角色 (user/assistant/system)
    - content: 消息内容
    - timestamp: 时间戳（可选）
    """
    role: str
    content: str
    timestamp: Optional[int] = None


class MessageResponse(BaseModel):
    """
    消息响应模型 - 返回消息时使用
    - id: 消息唯一标识
    - role: 消息角色
    - content: 消息内容
    - timestamp: 时间戳
    - references: 知识库引用（可选，用于 RAG）
    """
    id: str
    role: str
    content: str
    timestamp: int
    references: Optional[List[dict]] = None


class ChatSessionCreate(BaseModel):
    """
    聊天会话创建模型
    - title: 会话标题
    - model_id: 使用的模型 ID（可选）
    - knowledge_base_ids: 关联的知识库 ID 列表（可选）
    """
    title: str
    model_id: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None


class ChatSessionResponse(BaseModel):
    """
    聊天会话响应模型
    - id: 会话唯一标识
    - title: 会话标题
    - messages: 消息列表
    - created_at: 创建时间戳
    - updated_at: 更新时间戳
    - model_id: 使用的模型 ID
    - knowledge_base_ids: 关联的知识库 ID 列表
    """
    id: str
    title: str
    messages: List[MessageResponse]
    created_at: int
    updated_at: int
    model_id: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None


class SendMessageRequest(BaseModel):
    """
    发送消息请求模型
    - content: 消息内容
    - session_id: 会话 ID（可选，新会话可为空）
    - model: 模型名称（可选，如 gpt-4o、qwen3.5-plus）
    - knowledge_base_ids: 知识库 ID 列表（可选，用于 RAG）
    - reasoning: 深度思考模式（auto/true/false）
    - stream: 是否使用流式响应
    """
    content: str
    session_id: Optional[str] = None
    model: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None
    reasoning: Optional[Literal["auto", "true", "false"]] = 'auto'
    stream: bool = True


class SendMessageResponse(BaseModel):
    """
    发送消息响应模型
    - session_id: 会话 ID
    - message: 发送的消息
    """
    session_id: str
    message: MessageResponse
