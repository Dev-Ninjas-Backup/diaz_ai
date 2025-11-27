from app.utils.logger import get_logger
from app.services.chatbot.llms.open_ai_llm import OpenaiLLM
from app.config import configs

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient


logger = get_logger(__name__)


class Retriever:
    
    def __init__(self, collection_name: str=None):
        self.qdrant_url = configs["vector"]["url"]
        # self.collection_name = configs["vector"]["collection_name"]
        self.collection_name = collection_name
        self.embed = OpenaiLLM().get_embeddings()
    
    
    # don't use outside the class
    async def initialize_retriever(self):
        try:
            logger.info("Initializing Qdrant client.........")
            client = QdrantClient(url=self.qdrant_url)
            if self.collection_name not in [c.name for c in client.get_collections().collections]:
                logger.info("Collection not found, creating new collection")
                return
            logger.info("Qdrant client Initialized Successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise(e)

    
    async def get_retriever(self):
        try:
            client = await self.initialize_retriever()
            vector_store = QdrantVectorStore(
                client = client,
                collection_name = self.collection_name,
                embedding = self.embed
            )
            
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 5     
                }
            )
            logger.info("Retriever Initialized Successfully")
            return retriever
        except Exception as e:
            logger.error(f"Failed to get retriever: {e}")
            raise(e)


# from app.utils.logger import get_logger
# from app.services.chatbot.llms.open_ai_llm import OpenaiLLM
# from app.config import configs

# from langchain_qdrant import QdrantVectorStore
# from qdrant_client import QdrantClient


# logger = get_logger(__name__)


# class Retriever:
    
#     def __init__(self):
#         self.qdrant_url = configs["vector"]["url"]
#         self.collection_name = configs["vector"]["collection_name"]
#         self.embed = OpenaiLLM().get_embeddings()
    
    
#     # don't use outside the class
#     async def initialize_retriever(self):
#         try:
#             logger.info("Initializing Qdrant client.........")
#             client = QdrantClient(url=self.qdrant_url)
#             if self.collection_name not in [c.name for c in client.get_collections().collections]:
#                 logger.info("Collection not found, creating new collection")
#                 return
#             logger.info("Qdrant client Initialized Successfully")
#             return client
#         except Exception as e:
#             logger.error(f"Failed to initialize Qdrant client: {e}")
#             raise(e)

    
#     async def get_retriever(self):
#         try:
#             client = await self.initialize_retriever()
#             vector_store = QdrantVectorStore(
#                 client = client,
#                 collection_name = self.collection_name,
#                 embedding = self.embed
#             )
            
#             retriever = vector_store.as_retriever(
#                 search_type="similarity",
#                 search_kwargs={
#                     "k": 5     
#                 }
#             )
#             logger.info("Retriever Initialized Successfully")
#             return retriever
#         except Exception as e:
#             logger.error(f"Failed to get retriever: {e}")
#             raise(e)
