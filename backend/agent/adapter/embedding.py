from typing import List
from langchain_core.embeddings import Embeddings
from openai import OpenAI, AsyncOpenAI

"""处理第三方embedding模型的langchain适配"""
class ModelScopeAPIEmbeddings(Embeddings):
    """ModelScope API Embeddings（支持同步+异步）"""
    
    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str = "https://api-inference.modelscope.cn/v1",
    ):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    
    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            response = self.client.embeddings.create(
                model=self.model,
                input=batch_texts,
                encoding_format="float"
            )
            all_embeddings.extend([item.embedding for item in response.data])
        
        return all_embeddings
    
    # 异步方法
    async def aembed_query(self, text: str) -> List[float]:
        response = await self.async_client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            response = await self.async_client.embeddings.create(
                model=self.model,
                input=batch_texts,
                encoding_format="float"
            )
            all_embeddings.extend([item.embedding for item in response.data])
        
        return all_embeddings