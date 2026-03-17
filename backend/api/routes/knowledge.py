"""
知识库 API 路由
"""

import os
import shutil
import asyncio
import json
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pathlib import Path

from services.knowledge_mapping import (
    get_knowledge_mapping_service,
    KNOWLEDGE_BASE_PATH,
    VECTOR_STORE_PATH,
    MAPPING_FILE
)
from agent.tools.RAG import (
    create_vector_store_from_files,
    get_all_collection_names,
    get_vector_store,
    retrieve_documents,
    VectorStoreManager,
    load_and_split_documents
)
from qdrant_client.models import Distance, VectorParams
from api.response import success

knowledge_service = get_knowledge_mapping_service()

router = APIRouter()


@router.get("/knowledge/list")
async def list_knowledge_bases():
    """获取所有知识库列表"""
    knowledge_bases = knowledge_service.list_knowledge_bases()
    if not knowledge_bases:
        return success(data=[], msg="未获取到知识库", code=0)
    return success(data=knowledge_bases, msg="获取成功")


@router.post("/knowledge/create")
async def create_knowledge_base(
    name: str = Form(...),
    description: Optional[str] = Form(None),
):
    """创建新的知识库（仅创建映射，不处理文件）"""
    # 检查是否已存在
    existing = knowledge_service.get_knowledge_base(name)
    if existing:
        return success(data=None, msg="知识库名称已存在", code=0)
    
    kb = knowledge_service.create_knowledge_base(
        name=name,
        description=description or "",
    )
    return success(data=kb, msg="创建成功")


@router.post("/knowledge/create-with-files")
async def create_knowledge_base_with_files(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
):
    """创建知识库并上传文件（一键创建）"""
    # 检查是否已存在
    existing = knowledge_service.get_knowledge_base(name)
    if existing:
        return success(data=None, msg="知识库名称已存在", code=0)
    
    # 保存上传的文件
    saved_files = []
    file_paths = []
    
    try:
        for file in files:
            # 保存文件到知识库目录
            file_path = KNOWLEDGE_BASE_PATH / file.filename
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            saved_files.append(str(file_path))
            file_paths.append(file.filename)
        
        # 创建向量库
        try:
            manager = create_vector_store_from_files(
                file_paths=saved_files,
                collection_name=name
            )
            manager.close()
        except Exception as e:
            # 如果向量库创建失败，删除已保存的文件
            for f in saved_files:
                try:
                    os.remove(f)
                except:
                    pass
            return success(data=None, msg=f"向量库创建失败: {str(e)}", code=0)
        
        # 创建知识库映射
        kb = knowledge_service.create_knowledge_base(
            name=name,
            description=description or "",
            files=file_paths,
        )
        
        return success(data=kb, msg="创建成功")
        
    except Exception as e:
        # 清理已保存的文件
        for f in saved_files:
            try:
                os.remove(f)
            except:
                pass
        return success(data=None, msg=f"创建失败: {str(e)}", code=0)


@router.get("/knowledge/{kb_name}")
async def get_knowledge_base(kb_name: str):
    """获取指定知识库"""
    kb = knowledge_service.get_knowledge_base(kb_name)
    if not kb:
        return success(data=None, msg="知识库不存在")
    return success(data=kb, msg="获取成功")


from pydantic import BaseModel

class UpdateKnowledgeRequest(BaseModel):
    description: Optional[str] = None

@router.put("/knowledge/{kb_name}")
async def update_knowledge_base(
    kb_name: str,
    request: UpdateKnowledgeRequest,
):
    """更新知识库信息"""
    kb = knowledge_service.update_knowledge_base(
        name=kb_name,
        description=request.description,
    )
    if not kb:
        return success(data=None, msg="知识库不存在")
    return success(data=kb, msg="更新成功")


@router.delete("/knowledge/{kb_name}")
async def delete_knowledge_base(kb_name: str):
    """删除知识库"""
    import logging
    logger = logging.getLogger(__name__)
    
    kb = knowledge_service.get_knowledge_base(kb_name)
    if not kb:
        return success(data=None, msg="知识库不存在")
    
    errors = []
    
    # 删除关联的文件
    logger.info(f"开始删除知识库文件，知识库: {kb_name}, 文件列表: {kb.get('files', [])}")
    for file_name in kb.get("files", []):
        try:
            # 确保文件名不包含路径分隔符
            safe_file_name = os.path.basename(file_name)
            file_path = KNOWLEDGE_BASE_PATH / safe_file_name
            file_path_str = str(file_path)
            
            logger.info(f"尝试删除文件: {file_path_str}")
            logger.info(f"文件是否存在: {os.path.exists(file_path_str)}")
            logger.info(f"知识库基础路径: {KNOWLEDGE_BASE_PATH}")
            logger.info(f"文件名: {safe_file_name}")
            
            if os.path.exists(file_path_str):
                os.remove(file_path_str)
                logger.info(f"删除文件成功: {file_path_str}")
            else:
                logger.warning(f"文件不存在: {file_path_str}")
                # 尝试列出目录内容
                try:
                    files_in_dir = os.listdir(KNOWLEDGE_BASE_PATH)
                    logger.info(f"目录中的文件: {files_in_dir}")
                except Exception as list_e:
                    logger.error(f"列出目录失败: {list_e}")
        except Exception as e:
            error_msg = f"删除文件失败: {file_name}, {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # 删除向量库集合
    try:
        from agent.tools.RAG import close_qdrant_client
        import shutil
        import time
        
        vector_store_path = str(VECTOR_STORE_PATH)
        
        # 关闭Qdrant客户端以释放文件句柄
        close_qdrant_client()
        logger.info("已关闭Qdrant客户端，准备删除文件夹")
        
        # 强制垃圾回收以释放文件句柄
        import gc
        gc.collect()
        
        # 等待文件句柄完全释放
        time.sleep(2)
        
        # 删除本地存储的文件夹
        collection_folder = os.path.join(vector_store_path, kb_name)
        if os.path.exists(collection_folder):
            # 尝试多次删除
            deleted = False
            for attempt in range(5):
                try:
                    shutil.rmtree(collection_folder)
                    logger.info(f"删除向量库文件夹成功: {collection_folder} (第{attempt + 1}次尝试)")
                    deleted = True
                    break
                except Exception as folder_e:
                    if attempt < 4:
                        logger.warning(f"删除向量库文件夹失败 (第{attempt + 1}次): {collection_folder}, 等待后重试...")
                        time.sleep(1)
                    else:
                        logger.warning(f"删除向量库文件夹最终失败: {collection_folder}, {folder_e}")
                        errors.append(f"删除向量库文件夹失败: {folder_e}")
        else:
            logger.info(f"向量库文件夹不存在: {collection_folder}")
            
    except Exception as e:
        error_msg = f"删除向量库失败: {kb_name}, {e}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    # 删除映射
    result = knowledge_service.delete_knowledge_base(kb_name)
    if not result:
        return success(data=None, msg="知识库不存在")
    
    logger.info(f"知识库删除成功: {kb_name}")
    
    if errors:
        return success(msg=f"删除成功，但部分文件清理失败: {'; '.join(errors)}")
    
    return success(msg="删除成功")


@router.post("/knowledge/{kb_name}/upload")
async def upload_file(
    kb_name: str,
    file: UploadFile = File(...),
):
    """上传文件到知识库"""
    kb = knowledge_service.get_knowledge_base(kb_name)
    if not kb:
        return success(data=None, msg="知识库不存在")
    
    try:
        # 保存文件
        file_path = KNOWLEDGE_BASE_PATH / file.filename
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 添加到向量库
        try:
            manager = create_vector_store_from_files(
                file_paths=[str(file_path)],
                collection_name=kb_name
            )
            manager.close()
        except Exception as e:
            # 如果向量库创建失败，删除已保存的文件
            try:
                os.remove(file_path)
            except:
                pass
            return success(data=None, msg=f"向量库处理失败: {str(e)}", code=0)
        
        # 更新映射
        knowledge_service.add_files_to_knowledge_base(kb_name, [file.filename])
        
        return success(data={
            "id": "file_" + str(hash(file.filename)),
            "name": file.filename,
            "type": file.content_type,
            "size": len(content),
            "status": "ready",
        }, msg="上传成功")
        
    except Exception as e:
        return success(data=None, msg=f"上传失败: {str(e)}", code=0)


@router.get("/knowledge/{kb_name}/files")
async def list_files(kb_name: str):
    """获取知识库文件列表"""
    kb = knowledge_service.get_knowledge_base(kb_name)
    if not kb:
        return success(data=None, msg="知识库不存在")
    
    files = kb.get("files", [])
    file_list = []
    for f in files:
        file_path = KNOWLEDGE_BASE_PATH / f
        if os.path.exists(file_path):
            file_list.append({
                "id": "file_" + str(hash(f)),
                "name": f,
                "size": os.path.getsize(file_path),
                "status": "ready",
            })
    
    return success(data=file_list, msg="获取成功")


@router.delete("/knowledge/{kb_name}/files/{file_name}")
async def delete_file(kb_name: str, file_name: str):
    """删除知识库文件"""
    kb = knowledge_service.get_knowledge_base(kb_name)
    if not kb:
        return success(data=None, msg="知识库不存在")
    
    # 删除物理文件
    try:
        file_path = KNOWLEDGE_BASE_PATH / file_name
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        return success(data=None, msg=f"删除文件失败: {str(e)}", code=0)
    
    # 更新映射
    knowledge_service.remove_file_from_knowledge_base(kb_name, file_name)
    
    return success(msg="删除成功")


@router.get("/knowledge/mapping")
async def get_knowledge_mapping():
    """获取知识库映射关系"""
    mapping = knowledge_service.get_mapping()
    return success(data=mapping, msg="获取成功")


@router.post("/knowledge/retrieve")
async def retrieve_from_knowledge_bases(
    query: str = Form(...),
    knowledge_names: Optional[str] = Form(None),  # JSON字符串列表
    top_k: int = Form(5),
):
    """从知识库检索文档
    
    Args:
        query: 查询文本
        knowledge_names: 知识库名称列表（JSON字符串），不传则检索全部
        top_k: 返回结果数量
    """
    try:
        import json
        
        # 解析知识库名称列表
        if knowledge_names:
            names = json.loads(knowledge_names)
        else:
            # 获取所有知识库名称
            names = get_all_collection_names(str(VECTOR_STORE_PATH))
        
        if not names:
            return success(data=[], msg="未找到知识库")
        
        all_results = []
        
        for name in names:
            try:
                manager = get_vector_store(collection_name=name)
                results = manager.similarity_search(query=query, k=top_k)
                manager.close()
                
                for doc in results:
                    all_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "knowledgeName": name,
                    })
            except Exception as e:
                print(f"检索知识库 {name} 失败: {e}")
                continue
        
        return success(data=all_results, msg="检索成功")
        
    except Exception as e:
        return success(data=None, msg=f"检索失败: {str(e)}", code=0)


@router.post("/knowledge/batch-search")
async def batch_search(
    knowledge_ids: List[str] = Form(...),
    query: str = Form(...),
    top_k: int = Form(5),
):
    """批量搜索多个知识库"""
    try:
        all_results = []
        
        for kb_id in knowledge_ids:
            try:
                manager = get_vector_store(collection_name=kb_id)
                results = manager.similarity_search(query=query, k=top_k)
                manager.close()
                
                for doc in results:
                    all_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "knowledgeName": kb_id,
                    })
            except Exception as e:
                print(f"检索知识库 {kb_id} 失败: {e}")
                continue
        
        return success(data=all_results, msg="搜索成功")
        
    except Exception as e:
        return success(data=None, msg=f"搜索失败: {str(e)}", code=0)


# ========== 异步创建知识库（带进度）==========

# 存储正在处理的任务
_processing_tasks = {}


async def _delete_collection_folder_async(folder_path: str, max_retries: int = 5):
    """后台异步删除向量库文件夹（带重试机制）"""
    import logging
    logger = logging.getLogger(__name__)
    
    for attempt in range(max_retries):
        await asyncio.sleep(2)  # 等待文件句柄释放
        try:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                logger.info(f"后台删除向量库文件夹成功: {folder_path} (第{attempt + 1}次尝试)")
                return
            else:
                logger.info(f"向量库文件夹已不存在: {folder_path}")
                return
        except Exception as e:
            logger.warning(f"后台删除向量库文件夹失败 (第{attempt + 1}次): {folder_path}, {e}")
    
    logger.error(f"后台删除向量库文件夹最终失败: {folder_path}")


def sse_event(data: dict) -> str:
    """格式化 SSE 事件"""
    return f"data: {json.dumps(data)}\n\n"


@router.post("/knowledge/create-async")
async def create_knowledge_base_async(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
):
    """异步创建知识库，返回任务ID"""
    # 检查是否已存在
    existing = knowledge_service.get_knowledge_base(name)
    if existing:
        return success(data=None, msg="知识库名称已存在", code=0)
    
    # 生成任务ID
    import uuid
    task_id = str(uuid.uuid4())
    
    # 先保存文件
    saved_files = []
    file_paths = []
    
    try:
        for file in files:
            file_path = KNOWLEDGE_BASE_PATH / file.filename
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            saved_files.append(str(file_path))
            file_paths.append(file.filename)
    except Exception as e:
        # 清理已保存的文件
        for f in saved_files:
            try:
                os.remove(f)
            except:
                pass
        return success(data=None, msg=f"文件保存失败: {str(e)}", code=0)
    
    # 创建知识库映射（状态为处理中）
    kb = knowledge_service.create_knowledge_base(
        name=name,
        description=description or "",
        files=file_paths,
    )
    # 更新状态为处理中
    knowledge_service.update_knowledge_base_status(name, "processing")
    
    # 存储任务信息
    _processing_tasks[task_id] = {
        "name": name,
        "files": saved_files,
        "status": "processing",
        "progress": 0,
        "message": "准备处理...",
        "totalChunks": 0,
        "processedChunks": 0,
    }
    
    # 启动后台任务处理向量库
    asyncio.create_task(_process_vector_store_async(task_id, name, saved_files))
    
    return success(data={"taskId": task_id, "knowledgeBase": kb}, msg="创建任务已启动")


async def _process_vector_store_async(task_id: str, name: str, file_paths: List[str]):
    """后台异步处理向量库创建"""
    try:
        _processing_tasks[task_id]["status"] = "processing"
        _processing_tasks[task_id]["message"] = "正在加载文档..."
        _processing_tasks[task_id]["progress"] = 10
        
        from agent.tools.RAG import VectorStoreManager, load_and_split_documents
        
        # 加载和分割文档（在线程池中执行，避免阻塞）
        _processing_tasks[task_id]["message"] = "正在提取文档内容..."
        _processing_tasks[task_id]["progress"] = 20
        
        # 使用线程池执行同步操作
        loop = asyncio.get_event_loop()
        splits = await loop.run_in_executor(None, load_and_split_documents, file_paths)
        total_chunks = len(splits)
        
        _processing_tasks[task_id]["message"] = f"提取完成，共 {total_chunks} 个文档块"
        _processing_tasks[task_id]["progress"] = 30
        _processing_tasks[task_id]["totalChunks"] = total_chunks
        _processing_tasks[task_id]["processedChunks"] = 0
        
        # 创建向量库（分批处理以支持进度）
        manager = VectorStoreManager(collection_name=name)
        
        # 检查集合是否存在
        try:
            manager.client.get_collection(name)
            manager.client.delete_collection(name)
        except:
            pass
        
        # 重新创建集合（使用正确的向量维度）
        manager.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=manager.vector_size, distance=Distance.COSINE)
        )
        
        # 分批添加文档
        batch_size = 50
        for i in range(0, total_chunks, batch_size):
            batch = splits[i:i+batch_size]
            # 在线程池中执行同步操作
            await loop.run_in_executor(None, manager.vector_store.add_documents, batch)
            
            processed = min(i + batch_size, total_chunks)
            progress = 30 + int((processed / total_chunks) * 70)
            
            _processing_tasks[task_id]["progress"] = progress
            _processing_tasks[task_id]["processedChunks"] = processed
            _processing_tasks[task_id]["message"] = f"已添加 {processed}/{total_chunks} 个文档块"
            
            # 让出控制权，允许其他任务运行
            await asyncio.sleep(0.1)
        
        manager.close()
        
        # 更新状态为完成
        knowledge_service.update_knowledge_base_status(name, "ready")
        _processing_tasks[task_id]["status"] = "completed"
        _processing_tasks[task_id]["progress"] = 100
        _processing_tasks[task_id]["message"] = "创建完成"
        
    except Exception as e:
        # 更新状态为失败
        knowledge_service.update_knowledge_base_status(name, "error")
        _processing_tasks[task_id]["status"] = "error"
        _processing_tasks[task_id]["message"] = f"创建失败: {str(e)}"
        print(f"异步创建知识库失败: {e}")


@router.get("/knowledge/create-progress/{task_id}")
async def get_create_progress(task_id: str):
    """获取创建进度（SSE 流）"""
    async def event_generator():
        while True:
            if task_id not in _processing_tasks:
                yield sse_event({"type": "error", "message": "任务不存在"})
                break
            
            task = _processing_tasks[task_id]
            
            yield sse_event({
                "type": "progress",
                "taskId": task_id,
                "status": task["status"],
                "progress": task["progress"],
                "message": task["message"],
                "totalChunks": task.get("totalChunks", 0),
                "processedChunks": task.get("processedChunks", 0),
            })
            
            # 如果任务完成或失败，结束流
            if task["status"] in ["completed", "error"]:
                # 清理任务
                if task_id in _processing_tasks:
                    del _processing_tasks[task_id]
                break
            
            # 等待一段时间后继续
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.get("/knowledge/task-status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态（非流式）"""
    if task_id not in _processing_tasks:
        return success(data=None, msg="任务不存在", code=0)
    
    task = _processing_tasks[task_id]
    return success(data={
        "taskId": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "message": task["message"],
        "totalChunks": task.get("totalChunks", 0),
        "processedChunks": task.get("processedChunks", 0),
    }, msg="获取成功")
