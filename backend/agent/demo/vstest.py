"""
向量数据库测试 - Qdrant 版本（最终优化版）
"""
# ========== 抑制警告（添加在开头） ==========
import logging
import warnings
# logging.getLogger("unstructured").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*FontBBox.*")
warnings.filterwarnings("ignore", message=".*pdfminer.*")

from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
# from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import sys
from pathlib import Path

# ========== 智能导入 Embeddings ==========
try:
    from ..adapter.embedding import ModelScopeAPIEmbeddings
except (ImportError, ValueError):
    CURRENT_DIR = Path(__file__).parent.resolve()
    BACKEND_DIR = CURRENT_DIR.parent.parent.resolve()
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    from agent.adapter.embedding import ModelScopeAPIEmbeddings

# ========== 初始化 Embeddings ==========
embeddings = ModelScopeAPIEmbeddings(
    model="Qwen/Qwen3-Embedding-8B",
    api_key="ms-1722d753-a473-4a8a-bb51-8dc77bd86c24",
)

# ========== 加载和分割文档 ==========
file_paths = [
    "F:/code/aichat/backend/agent/knowledges/懂王-Ai应用开发架构师-就业班3.0-冲击月薪40k.pdf"
]

loader = UnstructuredLoader(file_paths, languages=["chi_sim", "eng"])
docs = loader.load()
print(f"📄 加载了 {len(docs)} 个文档")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    add_start_index=True
)
all_splits = text_splitter.split_documents(docs)
print(f"✂️ 分割为 {len(all_splits)} 个文档块")

# ========== Qdrant 客户端 ==========
client = QdrantClient(path="./qdrant_db")

vector_size = len(embeddings.embed_query("sample text"))
print(f"📏 向量维度：{vector_size}")

collection_name = "text_collection"

if not client.collection_exists(collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
    print(f"✅ 创建集合：{collection_name}")
else:
    print(f"ℹ️ 集合已存在：{collection_name}")

vector_store = QdrantVectorStore(
    client=client,
    collection_name=collection_name,
    embedding=embeddings,
)

# ========== 添加文档 ==========
ids = vector_store.add_documents(documents=all_splits)
print(f"✅ 成功存储 {len(ids)} 个文档")

# ========== 测试搜索 ==========
results = vector_store.similarity_search("AI开发要学啥", k=3)
print("\n🔍 搜索结果：")
for i, doc in enumerate(results):
    print(f"\n--- 结果 {i+1} ---")
    print(f"内容：{doc.page_content[:100]}...")
    print(f"页码：{doc.metadata.get('page_number', 'N/A')}")

# ========== 显式关闭客户端（避免退出异常） ==========
try:
    client.close()
except Exception:
    pass

print("\n✅ 完成！")