from app.config import configs
from app.services.chatbot.llms.open_ai_llm import OpenaiLLM
from app.utils.logger import get_logger

import os
import pandas as pd
from elasticsearch import Elasticsearch

logger = get_logger(__name__)

class DataIndex:
    def __init__(self):
        self.data_loc = configs["database_loc"]["process_data_loc"]
        self.keep = configs["columns"]["keep"]
        self.data_file_name = "process_data.csv"
        self.embed = OpenaiLLM().get_embeddings()
        os.makedirs(configs["search"]["pre_index_data_loc"],exist_ok=True)
        self.url = configs["search"]["elastic_url"]
        self.user = configs["search"]["user"]
        self.passd = configs["search"]["pass"]
    
    # dont use this function outside the class
    def _load_data(self):
        try:
            logger.info("Loading data from file.....")
            file_path = os.path.join(self.data_loc,self.data_file_name)
            if os.path.isfile(file_path):
                data = pd.read_csv(file_path)
                logger.info("Data loaded successfully.....")
                print(f"\033[92m✅ PASSED: Data Loading\033[0m")
                return data
            else:
                logger.error(f"File not found: {file_path}")
                raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error while loading data: {e}")
            print(f"\033[91m❌ FAILED: Data Load\033[0m")
            raise(e)
    
    def vectorize_data_for_search(self):
        try:
            logger.info("Vectorizing data for indexing.....")
            df = self._load_data()
            df["vector"] = df[self.keep].fillna("").apply(lambda x : self.embed.embed_query(" ".join(x.astype(str))),axis = 1)
            df.to_csv(os.path.join(configs["search"]["pre_index_data_loc"], "index_vector_data.csv"), index = False)
            logger.info("Data vectorized successfully for indexing.....")
            print(f"\033[92m✅ PASSED: Index Vector\033[0m")
        except Exception as e:
            logger.error(f"Error while vectorizing data: {e}")
            print(f"\033[91m❌ FAILED: Vector Index\033[0m")
            raise(e)
    
    async def _init_search_engine(self):
        try:
            logger.info("Connecting to Elasticsearch.....")
            es = Elasticsearch(
                hosts=self.url,
                http_auth=(self.user, self.passd),
                verify_certs=False,
                ssl_show_warn=False
            )
            
            if es.ping():
                logger.info("Connected to Elasticsearch")
                print(f"\033[92m✅ PASSED: Elasticsearch Connection\033[0m")
                return es
            else:
                logger.error("Failed to connect to Elasticsearch")
                raise ConnectionError("Failed to connect to Elasticsearch")
        except Exception as e:
            logger.error(f"Error while connecting to Elasticsearch: {e}")
            print(f"\033[91m❌ FAILED: Elasticsearch Connection\033[0m")
            raise(e)
    
    async def indexing_data(self):
        pass
    
    
    
    