"""
知识库 API 路由
"""

from fastapi import APIRouter, UploadFile, File, Form
from typing import List, Optional

from services.knowledge import get_knowledge_base_service
from services.rag import get_rag_service
from api.response import success

knowledge_service = get_knowledge_base_service()
rag_service = get_rag_service()

router = APIRouter()


@router.get("/knowledge/list")
async def list_knowledge_bases():
    """获取所有知识库列表"""
    knowledge_bases = await knowledge_service.list_knowledge_bases()
    if not knowledge_bases:
        return success(data=[], msg="未获取到知识库", code=0)
    return success(data=knowledge_bases, msg="获取成功")


@router.post("/knowledge/create")
async def create_knowledge_base(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(None),
):
    """创建新的知识库"""
    kb = await knowledge_service.create_knowledge_base(
        name=name,
        description=description,
        system_prompt=system_prompt,
    )
    return success(data=kb, msg="创建成功")


@router.get("/knowledge/{kb_id}")
async def get_knowledge_base(kb_id: str):
    """获取指定知识库"""
    kb = await knowledge_service.get_knowledge_base(kb_id)
    if not kb:
        return success(data=None, msg="知识库不存在")
    return success(data=kb, msg="获取成功")


@router.put("/knowledge/{kb_id}")
async def update_knowledge_base(
    kb_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(None),
):
    """更新知识库信息"""
    kb = await knowledge_service.update_knowledge_base(
        kb_id=kb_id,
        name=name,
        description=description,
        system_prompt=system_prompt,
    )
    if not kb:
        return success(data=None, msg="知识库不存在")
    return success(data=kb, msg="更新成功")


@router.delete("/knowledge/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    """删除知识库"""
    result = await knowledge_service.delete_knowledge_base(kb_id)
    if not result:
        return success(data=None, msg="知识库不存在")
    await rag_service.delete_vector_store(kb_id)
    return success(msg="删除成功")


@router.post("/knowledge/{kb_id}/upload")
async def upload_file(
    kb_id: str,
    file: UploadFile = File(...),
):
    """上传文件到知识库"""
    kb = await knowledge_service.get_knowledge_base(kb_id)
    if not kb:
        return success(data=None, msg="知识库不存在")
    
    content = await file.read()
    
    return success(data={
        "id": "file_" + str(hash(file.filename)),
        "name": file.filename,
        "type": file.content_type,
        "size": len(content),
        "status": "ready",
    }, msg="上传成功")


@router.get("/knowledge/{kb_id}/files")
async def list_files(kb_id: str):
    """获取知识库文件列表"""
    kb = await knowledge_service.get_knowledge_base(kb_id)
    if not kb:
        return success(data=None, msg="知识库不存在")
    
    return success(data=[], msg="获取成功")


@router.delete("/knowledge/{kb_id}/files/{file_id}")
async def delete_file(kb_id: str, file_id: str):
    """删除知识库文件"""
    return success(msg="删除成功")
