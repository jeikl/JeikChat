from pydantic import BaseModel, Field
from typing import Optional, List, Union, Dict, Any
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


class ToolConfig(BaseModel):
    """工具配置对象"""
    toolid: str  # 工具名
    mcp: int = 0  # 0=普通工具, 1=MCP工具
    name: Optional[str] = None  # 显示名称（可选）
    description: Optional[str] = None  # 描述（可选）


class SendMessageRequest(BaseModel):
    content: Union[str, List[Dict[str, Any]]]
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    model: Optional[str] = None
    thinking: Optional[str] = "auto"
    knowledge_base_ids: Optional[List[str]] = Field(default=None, alias="knowledgeBaseIds")
    # tools 改为支持新的格式：工具配置对象列表
    tools: Optional[List[ToolConfig]] = None
    session_uuid: Optional[str] = Field(default=None, alias="sessionUuid")

    class Config:
        populate_by_name = True


class SendMessageResponse(BaseModel):
    task_id: str
    session_id: str
