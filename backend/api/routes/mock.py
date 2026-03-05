"""
测试模式 API 路由
返回模拟数据，覆盖所有正式版API接口
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import uuid
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


MOCK_SESSIONS = [
    {
        "id": "session_test_1",
        "title": "如何创建数据库？",
        "messages": [
            {"id": "msg_1", "role": "user", "content": "如何创建数据库？", "timestamp": 1700000000000},
            {"id": "msg_2", "role": "assistant", "content": "创建数据库需要以下步骤：\n1. 安装数据库软件\n2. 启动数据库服务\n3. 创建数据库\n4. 创建表", "timestamp": 1700000001000}
        ],
        "createdAt": 1700000000000,
        "updatedAt": 1700000001000
    },
    {
        "id": "session_test_2", 
        "title": "Python入门",
        "messages": [
            {"id": "msg_3", "role": "user", "content": "Python难学吗？", "timestamp": 1699900000000},
            {"id": "msg_4", "role": "assistant", "content": "Python是一门非常适合初学者的编程语言，语法简洁易懂。", "timestamp": 1699900001000}
        ],
        "createdAt": 1699900000000,
        "updatedAt": 1699900001000
    },
    {
        "id": "session_test_3",
        "title": "关于React的问题",
        "messages": [
            {"id": "msg_5", "role": "user", "content": "React Hooks是什么？", "timestamp": 1699800000000},
            {"id": "msg_6", "role": "assistant", "content": "React Hooks是React 16.8引入的新特性，允许你在不编写class的情况下使用state和其他React特性。", "timestamp": 1699800001000}
        ],
        "createdAt": 1699800000000,
        "updatedAt": 1699800001000
    }
]

MOCK_KNOWLEDGE_BASES = [
    {"id": "kb_test_1", "name": "产品文档", "description": "产品使用文档", "fileCount": 5, "status": "ready", "createdAt": 1700000000000, "updatedAt": 1700000100000},
    {"id": "kb_test_2", "name": "常见问题", "description": "FAQ文档", "fileCount": 3, "status": "ready", "createdAt": 1700010000000, "updatedAt": 1700010100000},
    {"id": "kb_test_3", "name": "技术文档", "description": "技术开发文档", "fileCount": 8, "status": "ready", "createdAt": 1700020000000, "updatedAt": 1700020100000}
]

MOCK_PROVIDERS = {
    "openai": {"name": "OpenAI", "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]},
    "anthropic": {"name": "Anthropic", "models": ["claude-3-5-sonnet-20241022"]},
    "google": {"name": "Google", "models": ["gemini-2.0-flash", "gemini-1.5-pro"]},
    "qwen": {"name": "阿里云通义千问", "models": ["qwen3.5-plus", "qwen3-max"]},
}

MOCK_ANSWERS = {
    "hello": "你好！有什么可以帮助你的吗？",
    "hi": "你好！很高兴见到你！",
    "who": "我是JeikChat智能客服助手。",
    "help": "我可以帮你回答问题、提供技术支持等。",
    "谢谢": "不客气！",
    "再见": "再见！有问题随时找我。",
    "default": "感谢你的提问！这是一个测试模式的回复。"
}


def get_mock_answer(content: str) -> str:
    content_lower = content.lower()
    for key, answer in MOCK_ANSWERS.items():
        if key in content_lower:
            return answer
    return MOCK_ANSWERS["default"]


@router.get("/chat/history")
async def get_all_sessions():
    return {"status": 1, "data": {"sessions": MOCK_SESSIONS}, "msg": "获取成功"}


@router.get("/chat/history/{session_id}")
async def get_session_history(session_id: str):
    for session in MOCK_SESSIONS:
        if session["id"] == session_id:
            return {"status": 1, "data": session, "msg": "获取成功"}
    return {"status": 1, "data": None, "msg": "会话不存在"}


@router.post("/chat/send")
async def send_message_test(request: Request):
    body = await request.json()
    stream = body.get("stream", False)
    content = body.get("content", "")
    session_id = body.get("sessionId") or body.get("session_id") or f"session_{uuid.uuid4().hex[:8]}"
    
    mock_answer = get_mock_answer(content)
    
    if stream:
        async def generate():
            words = mock_answer.split()
            for word in words:
                yield f"data: {json.dumps({'sessionId': session_id, 'content': word + ' '})}\n\n"
                await asyncio.sleep(0.05)
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        return {
            "status": 1,
            "data": {
                "sessionId": session_id,
                "message": {
                    "id": f"msg_{uuid.uuid4().hex[:8]}",
                    "role": "assistant",
                    "content": mock_answer,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            },
            "msg": "发送成功"
        }


@router.delete("/chat/history/{session_id}")
async def delete_session_test(session_id: str):
    return {"status": 1, "data": None, "msg": "删除成功"}


@router.delete("/chat/history")
async def clear_all_sessions():
    return {"status": 1, "data": None, "msg": "清空成功"}


@router.put("/chat/history/{session_id}/title")
async def rename_session(session_id: str, request: Request):
    body = await request.json()
    new_title = body.get("title", "新会话")
    return {"status": 1, "data": {"title": new_title}, "msg": "重命名成功"}


@router.get("/knowledge/list")
async def list_knowledge_bases():
    return {"status": 1, "data": MOCK_KNOWLEDGE_BASES, "msg": "获取成功"}


@router.post("/knowledge/create")
async def create_knowledge(request: Request):
    body = await request.json()
    new_kb = {
        "id": f"kb_test_{uuid.uuid4().hex[:8]}",
        "name": body.get("name", "新知识库"),
        "description": body.get("description", ""),
        "fileCount": 0,
        "status": "ready",
        "createdAt": int(datetime.now().timestamp() * 1000),
        "updatedAt": int(datetime.now().timestamp() * 1000)
    }
    return {"status": 1, "data": new_kb, "msg": "创建成功"}


@router.get("/knowledge/{kb_id}")
async def get_knowledge(kb_id: str):
    for kb in MOCK_KNOWLEDGE_BASES:
        if kb["id"] == kb_id:
            return {"status": 1, "data": kb, "msg": "获取成功"}
    return {"status": 1, "data": None, "msg": "知识库不存在"}


@router.put("/knowledge/{kb_id}")
async def update_knowledge(kb_id: str, request: Request):
    body = await request.json()
    updated = {"id": kb_id, "updatedAt": int(datetime.now().timestamp() * 1000)}
    if "name" in body:
        updated["name"] = body["name"]
    if "description" in body:
        updated["description"] = body["description"]
    return {"status": 1, "data": updated, "msg": "更新成功"}


@router.delete("/knowledge/{kb_id}")
async def delete_knowledge(kb_id: str):
    return {"status": 1, "data": None, "msg": "删除成功"}


@router.post("/knowledge/{kb_id}/upload")
async def upload_file(kb_id: str):
    new_file = {
        "id": f"file_{uuid.uuid4().hex[:8]}",
        "name": "test_file.pdf",
        "type": "pdf",
        "size": 1024000,
        "status": "processing",
        "createdAt": int(datetime.now().timestamp() * 1000)
    }
    return {"status": 1, "data": new_file, "msg": "上传成功"}


@router.get("/knowledge/{kb_id}/files")
async def get_files(kb_id: str):
    return {"status": 1, "data": [], "msg": "获取成功"}


@router.delete("/knowledge/{kb_id}/files/{file_id}")
async def delete_file(kb_id: str, file_id: str):
    return {"status": 1, "data": None, "msg": "删除成功"}


@router.get("/models/list")
async def list_models():
    return {"status": 1, "data": {"providers": MOCK_PROVIDERS, "embedding_models": [], "has_configured_models": True}, "msg": "获取成功"}


@router.post("/models/config")
async def create_model_config(request: Request):
    body = await request.json()
    return {"status": 1, "data": {"id": f"config_{uuid.uuid4().hex[:8]}"}, "msg": "创建成功"}


@router.get("/models/test")
async def test_model(request: Request):
    return {"status": 1, "data": {"result": "模型连接成功"}, "msg": "测试成功"}


@router.get("/models/embedding/list")
async def list_embedding_models():
    return {"status": 1, "data": [], "msg": "获取成功"}


@router.get("/config/list")
async def list_configs():
    return {"status": 1, "data": [], "msg": "获取成功"}


@router.post("/config/create")
async def create_config(request: Request):
    return {"status": 1, "data": {"id": f"config_{uuid.uuid4().hex[:8]}"}, "msg": "创建成功"}


@router.put("/config/{config_id}")
async def update_config(config_id: str, request: Request):
    return {"status": 1, "data": {"id": config_id}, "msg": "更新成功"}


@router.delete("/config/{config_id}")
async def delete_config(config_id: str):
    return {"status": 1, "data": None, "msg": "删除成功"}


@router.get("/config/active")
async def get_active_config():
    return {"status": 1, "data": "config_test_1", "msg": "获取成功"}


@router.post("/config/active")
async def set_active_config(request: Request):
    return {"status": 1, "data": None, "msg": "设置成功"}
