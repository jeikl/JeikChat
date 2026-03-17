from fastapi import APIRouter, UploadFile, File, HTTPException
from api.response import success, error
from fileUntils.RustFs import upload_stream_async
import uuid
import os

router = APIRouter()

@router.post("/file/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    通用文件上传接口
    """
    try:
        # 生成唯一文件名，防止冲突
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        # 定义存储路径 (例如: uploads/2023/10/uuid.jpg)
        # 这里简化处理，直接放在 uploads/ 下
        object_key = f"uploads/{unique_filename}"
        
        # 使用异步流式上传
        url = await upload_stream_async(file.file, object_key)
        
        if url.startswith("error:"):
            return error(msg=url)
            
        return success(data={"url": url, "filename": file.filename}, msg="上传成功")
        
    except Exception as e:
        return error(msg=f"上传异常: {str(e)}")
