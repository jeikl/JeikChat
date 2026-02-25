from pydantic import BaseModel, Field
from typing import Optional, List, Generic, TypeVar
from datetime import datetime


T = TypeVar('T')


class ResultResponse(BaseModel, Generic[T]):
    status: int = Field(default=1, description="状态码: 1成功, 0失败")
    data: Optional[T] = Field(default=None, description="返回数据")
    msg: str = Field(default="操作成功", description="提示信息")


class MessageCreate(BaseModel):
    role: str
    content: str
    timestamp: Optional[int] = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: int
    references: Optional[List[dict]] = None


class ChatSessionCreate(BaseModel):
    title: str
    model_id: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    messages: List[MessageResponse]
    created_at: int
    updated_at: int
    model_id: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None


class SendMessageRequest(BaseModel):
    content: str
    session_id: Optional[str] = None
    model_id: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None
    stream: bool = False


class SendMessageResponse(BaseModel):
    session_id: str
    message: MessageResponse
