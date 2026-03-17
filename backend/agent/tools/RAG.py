"""
RAG (Retrieval-Augmented Generation) 工具模块
提供向量库初始化、文档存储和语义检索功能
"""

import logging
import warnings
import threading
from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain.tools import tool
from langgraph.config import get_stream_writer

# 抑制警告
logging.getLogger("unstructured").setLevel(logging.ERROR)
logging.getLogger("pdfminer").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*FontBBox.*")
warnings.filterwarnings("ignore", message=".*pdfminer.*")
warnings.filterwarnings("ignore", message=".*Could not get FontBBox.*")

from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# ========== Qdrant 客户端单例 ==========
_qdrant_client_instance: Optional[QdrantClient] = None
_qdrant_client_path: Optional[str] = None
_qdrant_client_lock = threading.Lock()

def get_qdrant_client(persist_directory: str) -> QdrantClient:
    """获取Qdrant客户端单例（线程安全）
    
    如果路径变化，会重新创建客户端
    """
    global _qdrant_client_instance, _qdrant_client_path
    with _qdrant_client_lock:
        # 如果路径变化或实例不存在，创建新实例
        if _qdrant_client_instance is None or _qdrant_client_path != persist_directory:
            # 关闭旧实例（如果存在）
            if _qdrant_client_instance is not None:
                try:
                    _qdrant_client_instance.close()
                except:
                    pass
            _qdrant_client_instance = QdrantClient(path=persist_directory)
            _qdrant_client_path = persist_directory
        return _qdrant_client_instance


def close_qdrant_client():
    """关闭Qdrant客户端单例（用于删除文件夹前释放文件句柄）"""
    global _qdrant_client_instance, _qdrant_client_path
    with _qdrant_client_lock:
        if _qdrant_client_instance is not None:
            try:
                _qdrant_client_instance.close()
            except:
                pass
            _qdrant_client_instance = None
            _qdrant_client_path = None



# 导入 embedding（使用绝对导入，假设从 backend 目录运行）
try:
    from agent.adapter.embedding import ModelScopeAPIEmbeddings
except ImportError:
    import sys
    BACKEND_DIR = Path(__file__).parent.parent.parent.resolve()
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    from agent.adapter.embedding import ModelScopeAPIEmbeddings


from config.settings import Settings, get_models_config
settings = Settings()
models_config = get_models_config()
embedding_config = models_config.get_embedding_config()

# ========== 单例模式：全局 Embedding 实例 ==========
class EmbeddingSingleton:
    """Embedding 单例类，确保全局只有一个 embedding 实例"""
    _instance: Optional[ModelScopeAPIEmbeddings] = None

    @classmethod
    def get_instance(
        cls,
        model: str = None,
        api_key: str = None
    ) -> ModelScopeAPIEmbeddings:
        """获取 Embedding 单例实例"""
        if cls._instance is None:
            # 优先使用传入参数，否则使用配置
            m = model or embedding_config.get("model") or "Qwen/Qwen3-Embedding-8B"
            k = api_key or embedding_config.get("api_key") or "ms-1722d753-a473-4a8a-bb51-8dc77bd86c24"
            b = embedding_config.get("base_url") or "https://api-inference.modelscope.cn/v1"
            
            cls._instance = ModelScopeAPIEmbeddings(
                model=m,
                api_key=k,
                base_url=b
            )
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置单例（用于测试或重新配置）"""
        cls._instance = None


def get_embeddings() -> ModelScopeAPIEmbeddings:
    """便捷函数：获取默认 embedding 实例"""
    return EmbeddingSingleton.get_instance()


# 默认向量库存储路径 (backend/agent/knowledges/vector_store)
DEFAULT_VECTOR_STORE_PATH = Path(__file__).parent.parent / "knowledges" / "vector_store"

# ========== 向量维度缓存 ==========
_vector_size_cache: Optional[int] = None

def get_vector_size(embeddings: ModelScopeAPIEmbeddings) -> int:
    """获取向量维度（带缓存）"""
    global _vector_size_cache
    if _vector_size_cache is None:
        sample_vector = embeddings.embed_query("sample text")
        _vector_size_cache = len(sample_vector)
    return _vector_size_cache


import os

# ========== 向量库管理类 ==========
class VectorStoreManager:
    """向量库管理器：负责创建、加载和管理 Qdrant 向量库"""

    def __init__(
        self,
        collection_name: str = "default_collection",
        persist_directory: Optional[str] = None,
        embeddings: Optional[ModelScopeAPIEmbeddings] = None
    ):
        """
        初始化向量库管理器

        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录路径
            embeddings: 自定义 embedding 实例（默认使用单例）
        """
        self.collection_name = collection_name
        # 使用默认路径或用户指定路径
        if persist_directory is None:
            # 默认每个 collection 使用独立目录
            # 修正: 不再使用 collection 子目录，直接在 vector_store 下创建知识库文件夹
            self.persist_directory = str(DEFAULT_VECTOR_STORE_PATH / collection_name)
        else:
            self.persist_directory = persist_directory
        self.embeddings = embeddings or get_embeddings()

        # 确保父目录存在
        Path(self.persist_directory).parent.mkdir(parents=True, exist_ok=True)

        # 使用单例 Qdrant 客户端（避免并发访问错误）
        self.client = get_qdrant_client(self.persist_directory)

        # 获取向量维度（使用缓存）并创建/加载集合
        self.vector_size = get_vector_size(self.embeddings)
        self._ensure_collection_exists()

        # 创建 VectorStore
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=self.embeddings,
        )

    def _ensure_collection_exists(self):
        """确保集合存在，不存在则创建"""
        try:
            # 尝试获取集合信息，如果存在则跳过创建
            self.client.get_collection(self.collection_name)
            print(f"ℹ️ 集合已存在：{self.collection_name}")
        except Exception:
            # 集合不存在，创建新集合
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ 创建集合：{self.collection_name}")

    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> List[str]:
        """
        添加文档到向量库

        Args:
            documents: 文档列表
            batch_size: 批量处理大小

        Returns:
            文档 ID 列表
        """
        all_ids = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            ids = self.vector_store.add_documents(documents=batch)
            all_ids.extend(ids)
            print(f"📤 已添加 {len(all_ids)}/{len(documents)} 个文档块")
        return all_ids

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        添加纯文本到向量库

        Args:
            texts: 文本列表
            metadatas: 元数据列表（可选）

        Returns:
            文档 ID 列表
        """
        return self.vector_store.add_texts(texts=texts, metadatas=metadatas)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        语义相似度搜索

        Args:
            query: 查询文本
            k: 返回结果数量
            filter_dict: 过滤条件（可选）

        Returns:
            相关文档列表
        """
        return self.vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4
    ) -> List[tuple[Document, float]]:
        """
        语义相似度搜索（带分数）

        Args:
            query: 查询文本
            k: 返回结果数量

        Returns:
            (文档, 相似度分数) 元组列表
        """
        return self.vector_store.similarity_search_with_score(query=query, k=k)

    def close(self):
        """关闭客户端连接（单例模式下不关闭共享客户端）"""
        # 为了避免文件锁定问题，这里可以显式关闭
        # 但在单例模式下，这意味着下一次请求需要重新创建连接
        # 这是一种权衡，为了能够删除文件，必须释放句柄
        if self.client:
            try:
                self.client.close()
                # 同时清除全局单例引用，强制下次重新创建
                global _qdrant_client_instance
                with _qdrant_client_lock:
                    if _qdrant_client_instance == self.client:
                        _qdrant_client_instance = None
            except Exception as e:
                print(f"❌ 关闭 Qdrant 客户端失败: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# ========== 文档处理函数 ==========
def load_and_split_documents(
    file_paths: List[str],
    chunk_size: int = 1500,
    chunk_overlap: int = 200,
    languages: List[str] = None
) -> List[Document]:
    """
    加载文件并分割为文档块（使用 PyPDFLoader 按页读取）

    Args:
        file_paths: 文件路径列表
        chunk_size: 分块大小（默认 1500，每页大约500-1000字符）
        chunk_overlap: 重叠大小（默认 200，减少重复）
        languages: 语言列表（默认中文+英文）

    Returns:
        分割后的文档块列表
    """
    from langchain_community.document_loaders import PyPDFLoader
    
    all_pages = []
    
    for file_path in file_paths:
        print(f"📄 正在加载：{file_path}")
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        for page_num, page in enumerate(pages, 1):
            if page.page_content and page.page_content.strip():
                # 设置 metadata
                page.metadata["page_number"] = page_num
                all_pages.append(page)
    
    print(f"✅ 提取了 {len(all_pages)} 页")
    
    if not all_pages:
        return []
    
    # 对每页内容按 chunk_size 分割
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "\n\n\n", "  ", " "],
        keep_separator=True,       # 保留分隔符
        add_start_index=True
    )
    
    all_splits = text_splitter.split_documents(all_pages)
    print(f"✂️ 分割为 {len(all_splits)} 个文档块")

    return all_splits


# ========== 便捷函数：一键创建向量库 ==========
def create_vector_store_from_files(
    file_paths: List[str],
    collection_name: str
) -> VectorStoreManager:
    """
    从文件创建向量库（一站式功能）

    Args:
        file_paths: 文件路径列表
        collection_name: 集合名称

    Returns:
        VectorStoreManager 实例
    """
    # 加载并分割文档
    splits = load_and_split_documents(file_paths)

    if not splits:
        raise ValueError("没有成功加载任何文档")

    # 创建向量库
    # 使用独立目录存储
    persist_directory = str(DEFAULT_VECTOR_STORE_PATH / collection_name)
    
    manager = VectorStoreManager(
        collection_name=collection_name,
        persist_directory=persist_directory
    )

    # 添加文档
    manager.add_documents(splits)

    return manager


# ========== 获取所有集合名称 ==========
def get_all_collection_names(persist_directory: Optional[str] = None) -> List[str]:
    """
    获取所有向量库集合名称

    Args:
        persist_directory: 持久化目录（默认使用 DEFAULT_VECTOR_STORE_PATH）

    Returns:
        集合名称列表
    """
    # 如果未指定，使用默认的 collections 根目录
    if persist_directory is None:
        base_path = DEFAULT_VECTOR_STORE_PATH
    else:
        # 如果指定了 persist_directory，检查它是单个 storage 还是 collections 根目录
        base_path = Path(persist_directory)
    
    if not base_path.exists():
        return []
    
    names = []
    # 遍历目录，查找有效的向量库（包含 storage.sqlite 的目录）
    try:
        for p in base_path.iterdir():
            if p.is_dir():
                # 检查是否存在 storage.sqlite
                # Qdrant 本地存储结构: {persist_directory}/collection/{collection_name}/storage.sqlite
                # 这里 persist_directory = p, collection_name = p.name
                storage_path = p / "collection" / p.name / "storage.sqlite"
                if storage_path.exists():
                    names.append(p.name)
    except Exception as e:
        print(f"❌ 获取集合列表失败: {e}")
        return []
        
    return names


# ========== 获取现有向量库 ==========
def get_vector_store(
    collection_name: str = "default_collection",
    persist_directory: Optional[str] = None
) -> Optional[VectorStoreManager]:
    """
    获取已存在的向量库（用于检索，不创建新集合）

    Args:
        collection_name: 集合名称
        persist_directory: 持久化目录（默认使用 DEFAULT_VECTOR_STORE_PATH）

    Returns:
        VectorStoreManager 实例，如果不存在则返回 None
    """
    if persist_directory is None:
        persist_directory = str(DEFAULT_VECTOR_STORE_PATH / collection_name)
    
    # 检查目录和 storage.sqlite 是否存在
    # Qdrant 本地存储结构: {persist_directory}/collection/{collection_name}/storage.sqlite
    storage_path = os.path.join(persist_directory, "collection", collection_name, "storage.sqlite")
    
    if not os.path.exists(persist_directory) or not os.path.exists(storage_path):
        print(f"⚠️ 向量库不存在: {persist_directory} (storage: {storage_path})")
        return None
        
    return VectorStoreManager(
        collection_name=collection_name,
        persist_directory=persist_directory
    )


# ========== 检索函数（供 LangChain Tool 使用） ==========
@tool
def retrieve_documents(query: str, knowledge_base: str = None) -> str:
    """
    根据知识库名称检索文档（返回格式化字符串，适合作为 Tool 使用）
    遇到专业性问题时需要先从此处检索文档作为参考以供回答用户问题
    
    Args:
        query: 查询文本
        knowledge_base: 知识库名称，不传则检索所有知识库
    """
    # 获取所有集合名称
    writer = get_stream_writer()
    
    # 如果指定了知识库名称，只检索该知识库
    if knowledge_base:
        collection_names = [knowledge_base]
        print(f"🔍 检索指定知识库: {knowledge_base}")
    else:
        # 获取所有集合名称
        collection_names = get_all_collection_names()
        print(f"🔍 发现 {len(collection_names)} 个知识库: {collection_names}")
    
    if not collection_names:
        return "未找到任何知识库。"
    
    all_results = []
    # 遍历集合进行查询
    for collection_name in collection_names:
        try:
            # 获取向量库并搜索
            manager = get_vector_store(collection_name=collection_name)
            
            if manager is None:
                writer(f"\n\n❌ 知识库不存在或无法访问: {collection_name}\n\n")
                continue
                
            writer( f"\n\n🔍 正在查询知识库: {collection_name}\n\n")
            results = manager.similarity_search(query=query, k=10)
        
            manager.close()
            
            if results:
                writer(f"\n\n✅️ 找到 {len(results)} 条结果\n\n")
                # 按页码排序（处理 int 或 str 类型）
                def get_page_num(doc):
                    page = doc.metadata.get('page_number', 0)
                    if isinstance(page, int):
                        return page
                    if isinstance(page, str) and page.isdigit():
                        return int(page)
                    return 0
                
                sorted_results = sorted(results, key=get_page_num)
                
                all_results.append(f"\n<知识库：{collection_name}>")
                for doc in sorted_results:
                    source = doc.metadata.get('source', '未知来源')
                    page = doc.metadata.get('page_number', '')
                    # 清理特殊字符，返回完整内容
                    content = doc.page_content.replace('\x01', '').replace('\x02', '').strip()
                    if page:
                        all_results.append(f"\n[页码：{page}]\n{content}")
                    else:
                        all_results.append(f"\n{content}")
        except Exception as e:
            writer( f" \n\n❌ 查询失败: {e} \n\n")
            # 静默失败，不阻塞其他知识库查询
            continue
    
    if not all_results:
        return "未找到相关文档。"
    
    return "\n\n---\n\n".join(all_results)


# ========== 测试代码 ==========
if __name__ == "__main__":

    test_file = r"F:/code/aichat/backend/agent/knowledges/懂王-Ai应用开发架构师-就业班3.0-冲击月薪40k.pdf"
    
    # # 先看看文档分割情况
    # print("📄 检查文档分割情况...")
    # splits = load_and_split_documents([test_file])
    # print(f"\n总共分割为 {len(splits)} 个文档块\n")
    
    # # 打印每个 chunk 的大小
    # print("各文档块内容长度：")
    # for i, doc in enumerate(splits[:10]):  # 只看前10个
    #     print(f"  chunk {i+1}: {len(doc.page_content)} 字符")
    
    # print("\n" + "="*50)
    # print("前3个文档块内容预览：")
    # print("="*50)
    # for i, doc in enumerate(splits[:3]):
    #     print(f"\n--- chunk {i+1} (共{len(doc.page_content)}字符) ---")
    #     print(doc.page_content[:500])
    
    print("="*50)
    print("创建向量库...")
    print("="*50)
    
    # 使用与 knowledge_mapping.json 一致的集合名称
    collection_name = "懂王-Ai应用开发架构师-就业班3.0-冲击月薪40k"
    
    manager = create_vector_store_from_files(
        file_paths=[test_file],
        collection_name=collection_name
    )
    print("✅ 向量库创建成功！")
    manager.close()
    
    print("\n" + "="*50)
    print("检索测试...")
    print("="*50)
    
    # 直接使用 VectorStoreManager 进行检索（避免 StructuredTool 调用问题）
    manager2 = get_vector_store(collection_name=collection_name)
    results = manager2.similarity_search(query="AI应用开发教程", k=4)
    print(f"✅ 找到 {len(results)} 条结果\n")
    for i, doc in enumerate(results, 1):
        print(f"--- 结果 {i} ---")
        #print(f"来源：{doc.metadata.get('source', '未知')}")
        #print(f"页码：{doc.metadata.get('page_number', '')}")
        print(f"内容：{doc.page_content[:300]}...\n")
    manager2.close()

    
    
    # print("=" * 60)
    # print("RAG 工具模块测试")
    # print("=" * 60)
    
    # # ========== 测试 1：获取所有集合名称 ==========
    # print("\n【测试 1】获取所有知识库集合名称")
    # print("-" * 60)
    # collections = get_all_collection_names()
    # print(f"当前共有 {len(collections)} 个知识库:")
    # for name in collections:
    #     print(f"  - {name}")
    
    # # ========== 测试 2：检索文档（Tool 方式） ==========
    # print("\n【测试 2】使用 retrieve_documents 检索")
    # print("-" * 60)
    # query = "AI应用开发学习指南"
    # print(f"查询：{query}\n")
    # result = retrieve_documents.invoke(query)
    # print(result)
    
    # # ========== 测试 3：创建新向量库（如果文件存在） ==========
    # if Path(test_file).exists():
    #     print("\n【测试 3】创建新的向量库")
    #     print("-" * 60)
    #     try:
    #         manager = create_vector_store_from_files(
    #             file_paths=[test_file],
    #             collection_name="test_collection"
    #         )
    #         print("✅ 向量库创建成功！")
    #         manager.close()
            
    #         # 验证创建成功
    #         collections = get_all_collection_names()
    #         print(f"当前共有 {len(collections)} 个知识库")
            
    #     except Exception as e:
    #         print(f"❌ 创建失败：{str(e)}")
    # else:
    #     print(f"\n【测试 3】跳过 - 测试文件不存在")
    
    # # ========== 测试 4：获取特定向量库并查询 ==========
    # print("\n【测试 4】获取特定向量库并查询")
    # print("-" * 60)
    # if collections:
    #     test_collection = collections[0]
    #     print(f"选择知识库：{test_collection}")
        
    #     try:
    #         manager = get_vector_store(collection_name=test_collection)
    #         results = manager.similarity_search("学习方法", k=2)
            
    #         print(f"\n找到 {len(results)} 个相关文档:")
    #         for i, doc in enumerate(results, 1):
    #             print(f"\n【结果 {i}】")
    #             print(f"  来源：{doc.metadata.get('source', '未知')}")
    #             print(f"  内容：{doc.page_content[:100]}...")
            
    #         manager.close()
    #         print("\n✅ 查询完成！")
    #     except Exception as e:
    #         print(f"❌ 查询失败：{str(e)}")
    # else:
    #     print("⚠️ 没有可用的知识库")
    
    # print("\n" + "=" * 60)
    # print("所有测试完成！")
    # print("=" * 60)
