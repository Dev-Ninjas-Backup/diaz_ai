from app.config import configs
from app.services.chatbot.llms.open_ai_llm import OpenaiLLM
from app.utils.logger import get_logger
from app.services.search_engine.index_mapping import mappings, settings

import os
import pandas as pd
from elasticsearch import Elasticsearch
from more_itertools import chunked
from elasticsearch.helpers import bulk

logger = get_logger(__name__)


class DataIndex:
    def __init__(self):
        self.data_loc = configs["database_loc"]["process_data_loc"]
        self.keep = configs["columns"]["keep"]
        self.data_file_name = "process_data.csv"
        self.embed = OpenaiLLM().get_embeddings()
        os.makedirs(configs["search"]["pre_index_data_loc"], exist_ok=True)
        self.url = configs["search"]["elastic_url"]
        self.user = configs["search"]["user"]
        self.passd = configs["search"]["pass"]
        self.index_name = configs["search"]["index_name"]

    # dont use this function outside the class
    def _load_data(self):
        try:
            logger.info("Loading data from file.....")
            file_path = os.path.join(self.data_loc, self.data_file_name)
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
            raise (e)

    def vectorize_data_for_search(self):
        try:
            logger.info("Vectorizing data for indexing.....")
            df = self._load_data()
            df["vector"] = (
                df[self.keep]
                .fillna("")
                .apply(
                    lambda x: self.embed.embed_query(" ".join(x.astype(str))), axis=1
                )
            )
            # df.to_csv(
            #     os.path.join(
            #         configs["search"]["pre_index_data_loc"], "index_vector_data.csv"
            #     ),
            #     index=False,
            # )
            df.to_pickle(
                os.path.join(
                    configs["search"]["pre_index_data_loc"], "index_vector_data.pkl"
                )
            )
            logger.info("Data vectorized successfully for indexing.....")
            print(f"\033[92m✅ PASSED: Index Vector\033[0m")
        except Exception as e:
            logger.error(f"Error while vectorizing data: {e}")
            print(f"\033[91m❌ FAILED: Vector Index\033[0m")
            raise (e)

    async def _init_search_engine(self):
        try:
            logger.info("Connecting to Elasticsearch.....")
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

    async def indexing_data(self):
        actions = []
        try:
            logger.info("Indexing data.....")
            es = await self._init_search_engine()  # init engine
            df = pd.read_pickle(  # load data
                os.path.join(
                    configs["search"]["pre_index_data_loc"], "index_vector_data.pkl"
                )
            )

            # checking index already exist or not
            if es.indices.exists(index=self.index_name):
                es.indices.delete(index=self.index_name)
                logger.info(f"Deleted existing index: {self.index_name}")

            # create index schema
            res = es.indices.create(
                index=self.index_name, mappings=mappings, settings=settings
            )
            logger.info(f"Created new index: {res}")

            # clean df if it has any nan
            df_cleaned = df.fillna("")

            # appending action
            for _, row in df_cleaned.iterrows():
                actions.append(
                    {
                        "_op_type": "index",
                        "_index": self.index_name,
                        "_id": row["DocumentID"],
                        "_source": row.to_dict(),
                    }
                )
            # Chunking and indexing
            for batch in chunked(actions, 15):
                try:
                    success, failed = bulk(es, batch, raise_on_error=False)
                    print(f"Success Indexing: {success}, Failed: {len(failed)}")
                    logger.info(f"Success Indexing: {success}, Failed: {len(failed)}")

                    if failed:
                        for error in failed:
                            logger.error(f"Error: {error}")

                except Exception as e:
                    print(f"Batch error: {e}")
                    raise (e)
            print(f"\033[92m✅ PASSED: Indexing\033[0m")
        except Exception as e:
            logger.error(f"Error while indexing data: {e}")
            print(f"\033[91m❌ FAILED: Indexing\033[0m")
            raise (e)
