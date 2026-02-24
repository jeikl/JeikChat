from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional

from services.rag_service import knowledge_service, rag_service

router = APIRouter()


@router.get("/knowledge/list")
async def list_knowledge_bases():
    knowledge_bases = await knowledge_service.list_knowledge_bases()
    return knowledge_bases


@router.post("/knowledge/create")
async def create_knowledge_base(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(None),
):
    kb = await knowledge_service.create_knowledge_base(
        name=name,
        description=description,
        system_prompt=system_prompt,
    )
    return kb


@router.get("/knowledge/{kb_id}")
async def get_knowledge_base(kb_id: str):
    kb = await knowledge_service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.put("/knowledge/{kb_id}")
async def update_knowledge_base(
    kb_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(None),
):
    kb = await knowledge_service.update_knowledge_base(
        kb_id=kb_id,
        name=name,
        description=description,
        system_prompt=system_prompt,
    )
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.delete("/knowledge/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    success = await knowledge_service.delete_knowledge_base(kb_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"message": "Knowledge base deleted"}


@router.post("/knowledge/{kb_id}/upload")
async def upload_file(
    kb_id: str,
    file: UploadFile = File(...),
):
    content = await file.read()
    
    file_info = await knowledge_service.upload_file(
        kb_id=kb_id,
        file_name=file.filename or "unknown",
        file_content=content,
    )
    
    return file_info


@router.get("/knowledge/{kb_id}/files")
async def list_files(kb_id: str):
    kb = await knowledge_service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb.get("files", [])


@router.delete("/knowledge/{kb_id}/files/{file_id}")
async def delete_file(kb_id: str, file_id: str):
    success = await knowledge_service.delete_file(kb_id, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"message": "File deleted"}


@router.get("/knowledge/{kb_id}/search")
async def search_knowledge(
    kb_id: str,
    query: str,
    top_k: int = 5,
):
    results = await rag_service.retrieve_context([kb_id], query, top_k)
    return results.get("references", [])


@router.post("/knowledge/batch-search")
async def batch_search(
    knowledge_ids: List[str],
    query: str,
    top_k: int = 5,
):
    results = await rag_service.retrieve_context(knowledge_ids, query, top_k)
    return results.get("references", [])


@router.post("/knowledge/{kb_id}/rebuild")
async def rebuild_index(kb_id: str):
    await rag_service.create_vector_store(kb_id)
    return {"message": "Index rebuild started"}
