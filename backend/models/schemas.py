from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


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
