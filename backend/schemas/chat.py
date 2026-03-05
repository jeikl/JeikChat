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
    reasoning: Optional[str] = None
    timestamp: int
    references: Optional[List[dict]] = None


class ChatSessionCreate(BaseModel):
    title: str
    model_id: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    messages: List[dict]
    created_at: int
    updated_at: int
    model: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None


class SendMessageRequest(BaseModel):
    content: str
    session_id: Optional[str] = None
    model: Optional[str] = None
    thinking: Optional[str] = "auto"
    knowledge_base_ids: Optional[List[str]] = None
    tools: Optional[List[str]] = None


class SendMessageResponse(BaseModel):
    task_id: str
    session_id: str
