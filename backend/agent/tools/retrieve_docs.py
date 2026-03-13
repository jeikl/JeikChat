# from functools import lru_cache
# from langchain_core.tools import tool

# # @lru_cache(maxsize=5)  # 缓存多个 collection
# def get_vs(collection_name="my_rag_collection"):
#     return Chroma(
#         persist_directory="./chroma_db",
#         embedding_function=embedding,
#         collection_name=collection_name
#     )

# @tool
# def retrieve_docs(query: str):
#     """从知识库检索相关内容"""
#     vs = get_vs()                      # 第一次调用才真正加载
#     docs = vs.similarity_search(query, k=4)
#     return "\n\n".join([f"来源: {d.metadata.get('source')}\n{d.page_content}" for d in docs])