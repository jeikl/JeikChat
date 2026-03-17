# -*- coding: utf-8 -*-
"""
RustFS S3 兼容对象存储 - 完整增删改查 示例（基于 boto3）


2. 直接函数调用方式（推荐在其他脚本中使用）：
    from rustfs_crud import upload, list_objects, download, delete_object, create_bucket, presigned_url

    upload("./photo.jpg", "images/vacation.jpg")               # 用默认 bucket
    upload("./photo.jpg", "images/vacation.jpg", bucket="my-bkt")
    list_objects(prefix="images/")
    presigned_url("images/vacation.jpg", expire_seconds=7200)
"""

import boto3
import asyncio
import sys
import os
from botocore.client import Config
from botocore.exceptions import ClientError
from typing import BinaryIO, Union

# 尝试导入 settings，如果失败（比如单独运行脚本时），则尝试调整路径
try:
    from backend.config.settings import get_settings
except ImportError:
    # 将项目根目录添加到 sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) # f:\code\aichat
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from backend.config.settings import get_settings
    except ImportError:
        # 如果还是失败，可能是在 backend 目录下运行
        backend_dir = os.path.dirname(os.path.dirname(current_dir)) # f:\code\aichat\backend
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from config.settings import get_settings

# 获取配置
settings = get_settings()
storage_config = getattr(settings, 'STORAGE', {})

# ==================== 配置区 (从 Settings 加载) ====================
ENDPOINT_URL     = storage_config.get("endpoint_url", "http://2xu.juns.top:9000")
DISPLAY_URL      = storage_config.get("display_url", "") # 优先使用 display_url 拼接返回链接
ACCESS_KEY       = storage_config.get("access_key", "root")
SECRET_KEY       = storage_config.get("secret_key", "anhuang520")
USE_SSL          = storage_config.get("use_ssl", False)
SIGNATURE_VERSION = storage_config.get("signature_version", "s3v4")

# 默认 bucket 名称
DEFAULT_BUCKET   = storage_config.get("bucket_name", "aiimg")
# ==============================================

# 初始化客户端（全局只创建一次）
s3_client = boto3.client(
    's3',
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(
        signature_version=SIGNATURE_VERSION,
        connect_timeout=10,
        read_timeout=60,
    ),
    verify=USE_SSL,
)


def _get_bucket(bucket: str | None = None) -> str:
    """获取最终使用的 bucket 名：优先用传入的 → 其次用默认的"""
    if bucket is not None:
        return bucket
    if not DEFAULT_BUCKET:
        raise ValueError("没有指定 bucket，且 DEFAULT_BUCKET 也没有设置")
    return DEFAULT_BUCKET


# ──────────────────────────────────────────────
#  以下是 可直接调用的函数（推荐方式）
# ──────────────────────────────────────────────

def get_public_url(object_key: str, bucket: str) -> str:
    """辅助函数：拼接直链 URL"""
    # 如果配置了 DISPLAY_URL，则优先使用它作为前缀
    if DISPLAY_URL:
        base_url = DISPLAY_URL.rstrip('/')
        # 假设 display_url 已经配置为 https://aiimg.junsk.cn
        # 如果 display_url 是 https://aiimg.junsk.cn，通常它是直接映射到 bucket 根目录或者 CDN 根
        # 这里我们需要根据实际情况判断是否拼接 bucket
        # 常见 CDN 配置：cdn.com/object_key -> bucket/object_key
        # 如果是 MinIO 别名，cdn.com/bucket/object_key -> bucket/object_key
        
        # 鉴于您的配置是 display_url: "https://aiimg.junsk.cn"
        # 且通常 aiimg 可能是 bucket 名的子域，或者就是 CDN 域名
        # 我们这里采用通用拼接方式：如果 url 中没有 bucket 名，可能需要加上
        # 但最稳妥的是直接拼接，除非 display_url 明确是 bucket 域名
        
        return f"{base_url}/{bucket}/{object_key}"
    
    # 否则使用 endpoint_url
    endpoint = ENDPOINT_URL.rstrip('/')
    return f"{endpoint}/{bucket}/{object_key}"


def create_bucket(bucket_name: str):
    """创建 Bucket"""
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"✔ Bucket 创建成功: {bucket_name}")
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"Bucket 已存在: {bucket_name}")
    except ClientError as e:
        print(f"创建失败: {e}")


def upload(local_path: str, object_key: str, bucket: str | None = None) -> str:
    """上传文件并返回公共访问链接（直链）"""
    bucket = _get_bucket(bucket)
    if not os.path.isfile(local_path):
        error_msg = f"本地文件不存在: {local_path}"
        print(error_msg)
        return f"error: {error_msg}"

    try:
        # 上传文件（默认 ACL=public-read 以允许公共访问，如果不允许请去掉 ExtraArgs）
        s3_client.upload_file(
            local_path, 
            bucket, 
            object_key,
            # ExtraArgs={'ACL': 'public-read'}  # 如果 bucket 策略已开放 readonly，这行可以不需要
        )
        
        # 拼接直链 URL
        public_url = get_public_url(object_key, bucket)
        
        print(f"✔ 上传成功: {local_path} → {public_url}")
        return public_url
        
    except ClientError as e:
        error_msg = f"上传失败: {e}"
        print(error_msg)
        return f"error: {error_msg}"


def upload_stream(file_obj: BinaryIO, object_key: str, bucket: str | None = None) -> str:
    """
    同步流式上传 (适合 FastAPI UploadFile.file 或任何 file-like object)
    
    Args:
        file_obj: 二进制文件流对象 (必须支持 read 方法)
        object_key: 对象存储中的路径键
        bucket: 存储桶名称
    """
    bucket = _get_bucket(bucket)
    try:
        # 使用 upload_fileobj 进行流式上传
        s3_client.upload_fileobj(file_obj, bucket, object_key)
        
        public_url = get_public_url(object_key, bucket)
        print(f"✔ 流式上传成功: {object_key} → {public_url}")
        return public_url
    except ClientError as e:
        error_msg = f"流式上传失败: {e}"
        print(error_msg)
        return f"error: {error_msg}"


async def upload_stream_async(file_obj: BinaryIO, object_key: str, bucket: str | None = None) -> str:
    """
    异步流式上传 (使用 run_in_executor 包装同步阻塞操作)
    注意：boto3 本身是同步库，真正纯异步通常推荐 aioboto3，
    但为了保持依赖简单，这里使用 asyncio.to_thread 在线程池中运行。
    
    Args:
        file_obj: 二进制文件流对象
        object_key: 对象存储中的路径键
        bucket: 存储桶名称
    """
    bucket = _get_bucket(bucket)
    
    def _sync_upload():
        s3_client.upload_fileobj(file_obj, bucket, object_key)
        
    try:
        # 在线程池中执行同步上传，避免阻塞事件循环
        await asyncio.to_thread(_sync_upload)
        
        public_url = get_public_url(object_key, bucket)
        print(f"✔ 异步流式上传成功: {object_key} → {public_url}")
        return public_url
    except Exception as e:
        error_msg = f"异步流式上传失败: {e}"
        print(error_msg)
        return f"error: {error_msg}"


def list_objects(prefix: str = "", bucket: str | None = None):
    """列出对象（支持前缀过滤）"""
    bucket = _get_bucket(bucket)
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

        print(f"\nBucket: {bucket}  中的对象（前缀: {prefix or '全部'}）：")
        found = False
        for page in page_iterator:
            for obj in page.get('Contents', []):
                found = True
                key = obj['Key']
                size = obj['Size']
                modified = obj['LastModified'].strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {key:50}  {size:>10,} bytes   {modified}")
        if not found:
            print("  （空）")
    except ClientError as e:
        print(f"列出失败: {e}")


def download(object_key: str, local_path: str, bucket: str | None = None):
    """下载文件"""
    bucket = _get_bucket(bucket)
    try:
        s3_client.download_file(bucket, object_key, local_path)
        print(f"✔ 下载成功: s3://{bucket}/{object_key} → {local_path}")
    except ClientError as e:
        print(f"下载失败: {e}")


def delete_object(object_key: str, bucket: str | None = None):
    """删除单个对象"""
    bucket = _get_bucket(bucket)
    try:
        s3_client.delete_object(Bucket=bucket, Key=object_key)
        print(f"✔ 删除成功: s3://{bucket}/{object_key}")
    except ClientError as e:
        print(f"删除失败: {e}")


def presigned_url(object_key: str, expire_seconds: int = 3600, bucket: str | None = None):
    """生成临时下载链接（GET）"""
    bucket = _get_bucket(bucket)
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': object_key},
            ExpiresIn=expire_seconds
        )
        print(f"临时下载链接（{expire_seconds}秒有效）：")
        print(url)
        return url  # 同时返回 url，方便其他代码使用
    except ClientError as e:
        print(f"生成链接失败: {e}")
        return None


# ──────────────────────────────────────────────
#  测试用例
# ──────────────────────────────────────────────

def run_test_cases():
    print("🚀 开始 RustFS 功能测试...")
    
    test_bucket = DEFAULT_BUCKET
    test_file_name = r"F:\code\aichat\backend\agent\knowledges\懂王-Ai应用开发架构师-就业班3.0-冲击月薪40k.pdf"
    test_object_key = "knowledges/懂王-Ai应用开发架构师-就业班3.0-冲击月薪40k.pdf"
    test_stream_key = "tests/stream_upload_test.pdf"
    download_file_name = "downloaded_test.txt"

    # 1. 创建测试文件 (这里不需要创建，直接使用真实文件)
    if not os.path.exists(test_file_name):
        print(f"❌ 本地文件不存在: {test_file_name}")
        return
    print(f"📄 准备上传文件: {test_file_name}")

    try:
        # 2. 创建 Bucket (如果不存在)
        print(f"\n--- [1/6] 检查/创建 Bucket: {test_bucket} ---")
        create_bucket(test_bucket)

        # 3. 普通文件上传
        print(f"\n--- [2/6] 普通文件上传 ---")
        url = upload(test_file_name, test_object_key, bucket=test_bucket)
        if url.startswith("http"):
            print(f"   直链地址验证: ✔ {url}")
        else:
            print(f"   直链地址验证: ❌ 失败 ({url})")

        # 4. 同步流式上传测试
        print(f"\n--- [3/6] 同步流式上传测试 ---")
        with open(test_file_name, "rb") as f:
            stream_url = upload_stream(f, test_stream_key, bucket=test_bucket)
            if stream_url.startswith("http"):
                print(f"   流式上传验证: ✔ {stream_url}")
            else:
                print(f"   流式上传验证: ❌ 失败 ({stream_url})")

        # 5. 异步流式上传测试 (需要 asyncio 运行环境)
        print(f"\n--- [4/6] 异步流式上传测试 ---")
        async def test_async_upload():
            with open(test_file_name, "rb") as f:
                async_url = await upload_stream_async(f, "tests/async_stream_test.pdf", bucket=test_bucket)
                if async_url.startswith("http"):
                    print(f"   异步流式验证: ✔ {async_url}")
                else:
                    print(f"   异步流式验证: ❌ 失败 ({async_url})")
        
        asyncio.run(test_async_upload())

        # 6. 列出文件
        print(f"\n--- [5/6] 列出文件 ---")
        list_objects(prefix="tests/", bucket=test_bucket)

        # 7. 下载文件 (验证流式上传的文件)
        print(f"\n--- [6/6] 下载验证流式文件 ---")
        if os.path.exists(download_file_name):
            os.remove(download_file_name)
        download(test_stream_key, download_file_name, bucket=test_bucket)
        
        # 验证下载内容
        if os.path.exists(download_file_name):
            size = os.path.getsize(download_file_name)
            origin_size = os.path.getsize(test_file_name)
            print(f"   下载成功，文件大小: {size} bytes (原文件: {origin_size})")
            if size == origin_size:
                print("   完整性校验: ✔ 通过")
            else:
                print("   完整性校验: ❌ 失败 (大小不一致)")
            
            # 清理下载的文件
            os.remove(download_file_name)
        else:
            print("❌ 下载文件验证失败：文件未找到")

    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
    
    finally:
        # 清理本地测试文件 (真实文件不清理)
        print("\n✨ 测试流程结束")

if __name__ == "__main__":
    run_test_cases()