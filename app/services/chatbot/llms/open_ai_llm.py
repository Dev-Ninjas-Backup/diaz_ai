from langchain_openai import ChatOpenAI

from app.config import settings, configs
from app.utils.logger import get_logger

logger = get_logger(__name__)



class OpenaiLLM:

    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model_name = configs["openai"]["model"]
        self.temperature = configs["openai"]["temperature"]


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

