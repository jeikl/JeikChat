from fastapi import APIRouter, HTTPException
from typing import List
from uuid import uuid4

from models.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    SendMessageRequest,
    SendMessageResponse,
    MessageResponse,
)
from services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/chat/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    session_id, message = await chat_service.send_message(
        content=request.content,
        session_id=request.session_id,
        model_id=request.model_id,
        knowledge_base_ids=request.knowledge_base_ids,
        stream=request.stream,
    )
    return SendMessageResponse(
        session_id=session_id,
        message=MessageResponse(**message),
    )


@router.get("/chat/history", response_model=dict)
async def get_all_sessions():
    sessions = await chat_service.get_all_sessions()
    return {"sessions": sessions}


@router.get("/chat/history/{session_id}", response_model=ChatSessionResponse)
async def get_session_history(session_id: str):
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ChatSessionResponse(**session)


@router.delete("/chat/history/{session_id}")
async def delete_session(session_id: str):
    await chat_service.delete_session(session_id)
    return {"message": "Session deleted"}


@router.delete("/chat/history")
async def clear_all_history():
    await chat_service.clear_all_sessions()
    return {"message": "All sessions cleared"}
