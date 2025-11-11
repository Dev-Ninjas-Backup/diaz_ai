from app.utils.logger import get_logger
from app.services.chatbot.llms.open_ai_llm import OpenaiLLM
from app.config import configs


from elasticsearch import Elasticsearch


logger = get_logger(__name__)


class SearchEngine:
    def __init__(self):
        self.url = configs["search"]["elastic_url"]
        self.user = configs["search"]["user"]
        self.passd = configs["search"]["pass"]
        self.index_name = configs["search"]["index_name"]
        self.embed = OpenaiLLM().get_embeddings()

    async def _init_search_engine(self):
        try:
            logger.info("Connecting to Elasticsearch for search.....")
            es = Elasticsearch(
                hosts=self.url,
                http_auth=(self.user, self.passd),
                verify_certs=False,
                ssl_show_warn=False,
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
            raise (e)

    async def search_boat(self, query, k: int = 5):
        try:
            logger.info("Searching boat.....")
            es = await self._init_search_engine()
            vector_query = self.embed.embed_query(query)
            query = {
                "knn": {
                    "field": "vector",
                    "query_vector": vector_query,
                    "k": k,
                    "num_candidates": 50,
                }
            }
            res = es.search(index=self.index_name, body=query)
            logger.info("Search completed.....")
            return res["hits"]["hits"]
        except Exception as e:
            logger.error(f"Error while searching: {e}")
            raise (e)
