"""
测试模式 - 返回模拟数据
覆盖所有后端API接口，与正式版API保持一致
"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
import asyncio
import uuid
from datetime import datetime

router = APIRouter()


# ==================== 模拟数据 ====================

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

MOCK_FILES = {
    "kb_test_1": [
        {"id": "file_1", "name": "产品手册.pdf", "type": "pdf", "size": 1024000, "status": "ready", "createdAt": 1700000000000},
        {"id": "file_2", "name": "使用指南.docx", "type": "docx", "size": 512000, "status": "ready", "createdAt": 1700000100000},
        {"id": "file_3", "name": "快速入门.txt", "type": "txt", "size": 10240, "status": "ready", "createdAt": 1700000200000}
    ],
    "kb_test_2": [
        {"id": "file_4", "name": "FAQ.pdf", "type": "pdf", "size": 256000, "status": "ready", "createdAt": 1700010000000},
        {"id": "file_5", "name": "问题汇总.md", "type": "md", "size": 51200, "status": "ready", "createdAt": 1700010100000}
    ],
    "kb_test_3": [
        {"id": "file_6", "name": "API文档.pdf", "type": "pdf", "size": 2048000, "status": "ready", "createdAt": 1700020000000},
        {"id": "file_7", "name": "开发指南.docx", "type": "docx", "size": 1024000, "status": "ready", "createdAt": 1700020100000}
    ]
}

MOCK_CONFIGS = [
    {"id": "config_test_1", "name": "GPT-4", "provider": "openai", "model": "gpt-4", "apiKey": "sk-test-key", "temperature": 0.7, "maxTokens": 4096, "topP": 1, "enabled": True},
    {"id": "config_test_2", "name": "GPT-3.5", "provider": "openai", "model": "gpt-3.5-turbo", "apiKey": "sk-test-key", "temperature": 0.7, "maxTokens": 2000, "topP": 1, "enabled": True},
    {"id": "config_test_3", "name": "Claude-3", "provider": "anthropic", "model": "claude-3-opus", "apiKey": "sk-ant-test", "temperature": 0.8, "maxTokens": 4096, "topP": 1, "enabled": False}
]

MOCK_TOOLS = [
    {"id": "tool_1", "name": "数据库查询", "description": "可以执行SQL查询操作", "enabled": True},
    {"id": "tool_2", "name": "天气查询", "description": "查询指定城市的天气信息", "enabled": False},
    {"id": "tool_3", "name": "计算器", "description": "执行数学计算", "enabled": True},
    {"id": "tool_4", "name": "文件读取", "description": "读取服务器上的文件内容", "enabled": False},
    {"id": "tool_5", "name": "网页搜索", "description": "搜索互联网获取信息", "enabled": True}
]

MOCK_EMBEDDING_MODELS = [
    {"id": "emb_1", "name": "text-embedding-ada-002", "description": "OpenAI官方嵌入模型"},
    {"id": "emb_2", "name": "text-embedding-3-small", "description": "新一代小型嵌入模型"},
    {"id": "emb_3", "name": "bge-large-zh-v1.5", "description": "中文优化大型模型"},
    {"id": "emb_4", "name": "bge-small-zh-v1.5", "description": "中文优化小型模型"}
]

MOCK_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    },
    "anthropic": {
        "name": "Anthropic",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
    },
    "google": {
        "name": "Google",
        "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-pro"]
    },
    "qwen": {
        "name": "阿里云通义千问",
        "models": ["qwen3.5-plus", "qwen3-max", "qwen-turbo"]
    }
}

MOCK_ANSWERS = {
    "hello": "你好！有什么可以帮助你的吗？",
    "hi": "你好！很高兴见到你！",
    "who": "我是JeikChat智能客服助手，可以帮助你解答问题和提供信息。",
    "help": "我可以帮你：\n1. 回答各种问题\n2. 提供技术支持\n3. 查询产品信息\n4. 编写代码\n5. 等等...",
    "谢谢": "不客气！很高兴能帮到你。",
    "再见": "再见！有问题随时找我。",
    "default": "感谢你的提问！这是一个测试模式的回复。在真实模式下，我会调用LLM来生成更有意义的回答。"
}


def get_mock_answer(content: str) -> str:
    """根据内容返回模拟回答"""
    content_lower = content.lower()
    for key, answer in MOCK_ANSWERS.items():
        if key in content_lower:
            return answer
    return MOCK_ANSWERS["default"]


# ==================== 聊天 API ====================
# 注意：此处不应添加 /api 前缀，因为 router 已在主应用中挂载到 /api 路径

@router.get("/chat/history")
async def get_all_sessions():
    """获取所有会话列表"""
    return {"status": 1, "data": {"sessions": MOCK_SESSIONS}, "msg": "获取成功"}


@router.get("/chat/history/{session_id}")
async def get_session_history(session_id: str):
    """获取指定会话"""
    for session in MOCK_SESSIONS:
        if session["id"] == session_id:
            return {"status": 1, "data": session, "msg": "获取成功"}
    return {"status": 1, "data": None, "msg": "会话不存在"}


@router.post("/chat/send")
async def send_message_test(request: Request):
    """发送消息"""
    import json
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 测试模式: send_message_test 被调用")
    
    body = await request.json()
    logger.info(f"🧪 接收到的请求体: {body}")
    
    stream = body.get("stream", False)
    content = body.get("content", "")
    session_id = body.get("sessionId") or body.get("session_id") or f"session_{uuid.uuid4().hex[:8]}"
    model_id = body.get("modelId") or body.get("model_id")
    knowledge_base_ids = body.get("knowledgeBaseIds") or body.get("knowledge_base_ids") or []
    
    logger.info(f"🧪 content: {content}")
    
    mock_answer = get_mock_answer(content)
    logger.info(f"🧪 mock_answer: {mock_answer}")
    
    if stream:
        async def generate():
            words = mock_answer.split()
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'sessionId': session_id, 'content': word + ' '})}\n\n"
                await asyncio.sleep(0.05)
            yield f"data: {json.dumps({'references': [{'knowledgeId': 'kb_test_1', 'knowledgeName': '产品文档', 'content': '...', 'similarity': 0.92}]})}\n\n"
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
    """删除指定会话"""
    return {"status": 1, "data": None, "msg": "删除成功"}


@router.delete("/chat/history")
async def clear_all_sessions():
    """清空所有会话"""
    return {"status": 1, "data": None, "msg": "清空成功"}


@router.put("/chat/history/{session_id}/title")
async def rename_session(session_id: str, request: Request):
    """重命名会话"""
    import json
    body = await request.json()
    new_title = body.get("title", "新会话")
    return {"status": 1, "data": {"title": new_title}, "msg": "重命名成功"}


# ==================== 知识库 API ====================

@router.get("/knowledge/list")
async def list_knowledge_bases():
    """获取知识库列表"""
    return {"status": 1, "data": MOCK_KNOWLEDGE_BASES, "msg": "获取成功"}


@router.post("/knowledge/create")
async def create_knowledge(request: Request):
    """创建知识库"""
    import json
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
    """获取指定知识库"""
    for kb in MOCK_KNOWLEDGE_BASES:
        if kb["id"] == kb_id:
            return {"status": 1, "data": kb, "msg": "获取成功"}
    return {"status": 1, "data": None, "msg": "知识库不存在"}


@router.put("/knowledge/{kb_id}")
async def update_knowledge(kb_id: str, request: Request):
    """更新知识库"""
    import json
    body = await request.json()
    updated = {
        "id": kb_id, 
        "updatedAt": int(datetime.now().timestamp() * 1000)
    }
    if "name" in body:
        updated["name"] = body["name"]
    if "description" in body:
        updated["description"] = body["description"]
    return {"status": 1, "data": updated, "msg": "更新成功"}


@router.delete("/knowledge/{kb_id}")
async def delete_knowledge(kb_id: str):
    """删除知识库"""
    return {"status": 1, "data": None, "msg": "删除成功"}


@router.post("/knowledge/{kb_id}/upload")
async def upload_file(kb_id: str):
    """上传文件到知识库"""
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
    """获取知识库文件列表"""
    files = MOCK_FILES.get(kb_id, [])
    return {"status": 1, "data": files, "msg": "获取成功"}


@router.delete("/knowledge/{kb_id}/files/{file_id}")
async def delete_file(kb_id: str, file_id: str):
    """删除知识库文件"""
    return {"status": 1, "data": None, "msg": "删除成功"}


@router.get("/knowledge/{kb_id}/search")
async def search_knowledge(kb_id: str, query: str = "", topK: int = 5):
    """知识库内搜索"""
    results = [
        {"content": f"关于'{query}'的搜索结果1，这是相关的内容摘要...", "metadata": {"file": "文档1.pdf", "page": 1}, "score": 0.95},
        {"content": f"关于'{query}'的搜索结果2，另一个相关的内容...", "metadata": {"file": "文档2.pdf", "page": 5}, "score": 0.88},
        {"content": f"关于'{query}'的搜索结果3，更多相关信息...", "metadata": {"file": "文档3.docx", "page": 10}, "score": 0.82}
    ]
    return {"status": 1, "data": results, "msg": "搜索成功"}


@router.post("/knowledge/batch-search")
async def batch_search(request: Request):
    """批量搜索多个知识库"""
    import json
    body = await request.json()
    query = body.get("query", "")
    results = [
        {"content": f"在产品文档中关于'{query}'的搜索结果...", "metadata": {"knowledgeId": "kb_test_1", "knowledgeName": "产品文档", "file": "文档.pdf"}, "score": 0.92},
        {"content": f"在常见问题中关于'{query}'的搜索结果...", "metadata": {"knowledgeId": "kb_test_2", "knowledgeName": "常见问题", "file": "FAQ.pdf"}, "score": 0.85},
        {"content": f"在技术文档中关于'{query}'的搜索结果...", "metadata": {"knowledgeId": "kb_test_3", "knowledgeName": "技术文档", "file": "API文档.pdf"}, "score": 0.78}
    ]
    return {"status": 1, "data": results, "msg": "搜索成功"}


@router.post("/knowledge/{kb_id}/rebuild")
async def rebuild_index(kb_id: str):
    """重建知识库索引"""
    return {"status": 1, "data": None, "msg": "重建成功"}


# ==================== Agent Tools API ====================

@router.get("/tools")
async def list_tools():
    """获取所有可用的Agent工具列表"""
    if MOCK_TOOLS:
        return {"status": 1, "data": MOCK_TOOLS, "msg": f"获取成功，共 {len(MOCK_TOOLS)} 个工具"}
    return {"status": 0, "data": [], "msg": "未获取到任何 Agent Tool，请检查后台配置"}


@router.post("/tools/{tool_id}/enable")
async def enable_tool(tool_id: str):
    """启用指定工具"""
    return {"status": 1, "data": None, "msg": "启用成功"}


@router.post("/tools/{tool_id}/disable")
async def disable_tool(tool_id: str):
    """禁用指定工具"""
    return {"status": 1, "data": None, "msg": "禁用成功"}


@router.post("/tools/batch-set")
async def batch_set_tools(request: Request):
    """批量设置工具状态"""
    return {"status": 1, "data": None, "msg": "设置成功"}


# ==================== 模型配置 API ====================

@router.get("/models/list")
async def list_models():
    """获取LLM模型列表"""
    return {
        "status": 1, 
        "data": {
            "providers": MOCK_PROVIDERS,
            "embedding_models": MOCK_EMBEDDING_MODELS,
            "has_configured_models": True
        }, 
        "msg": "获取成功"
    }


@router.post("/models/config")
async def create_model_config(request: Request):
    """创建模型配置"""
    import json
    body = await request.json()
    new_config = {
        "id": f"config_{uuid.uuid4().hex[:8]}",
        "name": body.get("name", "新模型"),
        "provider": body.get("provider", "openai"),
        "model": body.get("model", "gpt-4"),
        "apiKey": body.get("apiKey", ""),
        "temperature": body.get("temperature", 0.7),
        "maxTokens": body.get("maxTokens", 4096),
        "topP": body.get("topP", 1),
        "enabled": True
    }
    return {"status": 1, "data": new_config, "msg": "创建成功"}


@router.get("/models/test")
async def test_model(request: Request):
    """测试模型连接"""
    return {"status": 1, "data": {"result": "模型连接成功", "response": "Hello! I'm working!"}, "msg": "测试成功"}


@router.get("/models/embedding/list")
async def list_embedding_models():
    """获取嵌入模型列表"""
    return {"status": 1, "data": MOCK_EMBEDDING_MODELS, "msg": "获取成功"}


# ==================== 配置管理 API ====================

@router.get("/config/list")
async def list_configs():
    """获取模型配置列表"""
    return {"status": 1, "data": MOCK_CONFIGS, "msg": "获取成功"}


@router.post("/config/create")
async def create_config(request: Request):
    """创建模型配置"""
    import json
    body = await request.json()
    new_config = {
        "id": f"config_{uuid.uuid4().hex[:8]}",
        "name": body.get("name", "新配置"),
        "provider": body.get("provider", "openai"),
        "model": body.get("model", "gpt-4"),
        "apiKey": body.get("apiKey", ""),
        "temperature": body.get("temperature", 0.7),
        "maxTokens": body.get("maxTokens", 4096),
        "topP": body.get("topP", 1),
        "enabled": True
    }
    return {"status": 1, "data": new_config, "msg": "创建成功"}


@router.put("/config/{config_id}")
async def update_config(config_id: str, request: Request):
    """更新模型配置"""
    import json
    body = await request.json()
    updated = {"id": config_id}
    if "name" in body:
        updated["name"] = body["name"]
    if "temperature" in body:
        updated["temperature"] = body["temperature"]
    if "maxTokens" in body:
        updated["maxTokens"] = body["maxTokens"]
    if "topP" in body:
        updated["topP"] = body["topP"]
    if "enabled" in body:
        updated["enabled"] = body["enabled"]
    return {"status": 1, "data": updated, "msg": "更新成功"}


@router.delete("/config/{config_id}")
async def delete_config(config_id: str):
    """删除模型配置"""
    return {"status": 1, "data": None, "msg": "删除成功"}


@router.get("/config/active")
async def get_active_config():
    """获取当前激活的配置"""
    return {"status": 1, "data": "config_test_1", "msg": "获取成功"}


@router.post("/config/active")
async def set_active_config(request: Request):
    """设置激活的配置"""
    import json
    body = await request.json()
    config_id = body.get("id", "")
    return {"status": 1, "data": None, "msg": "设置成功"}
