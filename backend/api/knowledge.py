from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional

from services.rag_service import knowledge_service, rag_service
from utils.result import success

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
    success_flag = await knowledge_service.delete_knowledge_base(kb_id)
    if not success_flag:
        return success(data=None, msg="知识库不存在")
    return success(data=None, msg="删除成功")


@router.post("/knowledge/{kb_id}/upload")
async def upload_file(
    kb_id: str,
    file: UploadFile = File(...),
):
    """上传文件到知识库"""
    content = await file.read()
    
    file_info = await knowledge_service.upload_file(
        kb_id=kb_id,
        file_name=file.filename or "unknown",
        file_content=content,
    )
    
    return success(data=file_info, msg="上传成功")


@router.get("/knowledge/{kb_id}/files")
async def list_files(kb_id: str):
    """获取知识库中的文件列表"""
    kb = await knowledge_service.get_knowledge_base(kb_id)
    if not kb:
        return success(data=None, msg="知识库不存在")
    return success(data=kb.get("files", []), msg="获取成功")


@router.delete("/knowledge/{kb_id}/files/{file_id}")
async def delete_file(kb_id: str, file_id: str):
    """删除知识库中的文件"""
    success_flag = await knowledge_service.delete_file(kb_id, file_id)
    if not success_flag:
        return success(data=None, msg="文件不存在")
    return success(data=None, msg="删除成功")


@router.get("/knowledge/{kb_id}/search")
async def search_knowledge(
    kb_id: str,
    query: str,
    top_k: int = 5,
):
    """在知识库中搜索"""
    results = await rag_service.retrieve_context([kb_id], query, top_k)
    return success(data=results.get("references", []), msg="搜索成功")


@router.post("/knowledge/batch-search")
async def batch_search(
    knowledge_ids: List[str],
    query: str,
    top_k: int = 5,
):
    """批量搜索多个知识库"""
    results = await rag_service.retrieve_context(knowledge_ids, query, top_k)
    return success(data=results.get("references", []), msg="搜索成功")


@router.post("/knowledge/{kb_id}/rebuild")
async def rebuild_index(kb_id: str):
    """重建知识库索引"""
    await rag_service.create_vector_store(kb_id)
    return success(data=None, msg="重建成功")
