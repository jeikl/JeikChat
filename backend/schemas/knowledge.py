from pydantic import BaseModel, Field
from typing import Optional, List


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    file_count: int = 0
    status: str = "ready"
    created_at: int
    updated_at: int


class FileUploadResponse(BaseModel):
    id: str
    name: str
    type: str
    size: int
    status: str
    created_at: int
