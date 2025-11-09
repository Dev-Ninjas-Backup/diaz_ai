from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import settings, configs
from app.utils.logger import get_logger

logger = get_logger(__name__)



class OpenaiLLM:

    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model_name = configs["openai"]["model"]
        self.temperature = configs["openai"]["temperature"]
        self.embedding_model = configs["openai"]["embedding_model"]


    def get_llm(self):

        try:
            logger.info("Initializing OpenAI LLM........")

            llm = ChatOpenAI(
                api_key=self.openai_api_key,
                model = self.model_name,
                temperature = self.temperature)

            return llm

        except Exception as e:
            logger.error(f"Error initializing OpenAI LLM: {e}")
            return None
        
    def get_embeddings(self):
        try:
            logger.info("Initializing OpenAI Embeddings........")

            embeddings = OpenAIEmbeddings(
                api_key=self.openai_api_key,
                model=self.embedding_model
            )

            return embeddings

        except Exception as e:
            logger.error(f"Error initializing OpenAI Embeddings: {e}")
            return None

