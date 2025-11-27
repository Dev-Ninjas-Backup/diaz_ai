from app.config import configs
from app.utils.helper import request_data, save_json, load_json
from app.utils.logger import get_logger
from app.services.chatbot.llms.open_ai_llm import OpenaiLLM

import os
import pandas as pd
import re
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from langchain_qdrant import QdrantVectorStore
from langchain_classic.docstore.document import Document
import uuid

logger = get_logger(__name__)


class FloridaVectorDataBase:

    def __init__(self):
#        self.data_url_2 = configs["api"]["api_2"]
        self.data_url_1 = configs["api"]["api_1"]
        self.data_save_loc = configs["database_loc"]["raw_data_loc_florida"]
        self.keep_col = configs["columns"]["keep"]
        self.process_data_loc = configs["database_loc"]["process_data_loc_florida"]
        os.makedirs(configs["database_loc"]["raw_data_loc_florida"], exist_ok=True)
        os.makedirs(configs["database_loc"]["process_data_loc_florida"], exist_ok=True)
        self.qdrant_url = configs["vector"]["url"]
        self.collection_name = configs["vector"]["collection_name_florida"]
        self.embed = OpenaiLLM().get_embeddings()
    
    # async def collect_data(self):
    #     try:
    #         logger.info("Collecting Data (Paginated)...")

    #         base_url = self.data_url_1
    #         source = "custom"
    #         limit = 200
    #         page=1
    #         all_results = []

    #         while True:
    #             url = f"{base_url}?source={source}&fields=minimal&page={page}&limit={limit}"

    #             print(f"Fetching page {page} ...")
    #             data = await request_data(url)

    #             results = data.get("data", [])
    #             metadata = data.get("metadata", {})

    #             all_results.extend(results)

    #             current_page = metadata.get("page", page)
    #             #total_pages = metadata.get("totalPage", 1)
    #             total_pages = 2

    #             print(f"Page {current_page}/{total_pages}: {len(results)} items")

    #             if current_page >= total_pages:
    #                 print("Reached last page. Stopping.")
    #                 break

    #             page += 1

    #         save_json(
    #             json_data=all_results,
    #             index="all",
    #             folder_loc=self.data_save_loc
    #         )

    #         print("\033[92m✅ PASSED: Collected Paginated Data\033[0m")

    #     except Exception as e:
    #         print("\033[91m❌ FAILED: Paginated Collect Data\033[0m")
    #         raise e
        
    async def collect_data(self):
        try:
            logger.info("Collecting Data (Paginated)...")

            base_url = self.data_url_1  # "https://api.floridayachttrader.com/api/boats/all"
            source = "custom"
            limit = 50
            page = 1
            all_results = []

            while True:
                url = f"{base_url}?source={source}&fields=minimal&page={page}&limit={limit}"
                print(f"Fetching page {page} ...")
                data = await request_data(url)

                results = data.get("data", [])
                metadata = data.get("metadata", {})

                all_results.extend(results)

                current_page = metadata.get("page", page)
                total_pages = metadata.get("totalPage", page)  # use real total pages

                print(f"Page {current_page}/{total_pages}: {len(results)} items")

                if current_page >= total_pages:
                    print("Reached last page. Stopping.")
                    break

                page += 1

            save_json(
                json_data=all_results,
                index="all",
                folder_loc=self.data_save_loc
            )

            print("\033[92m✅ PASSED: Collected Paginated Data\033[0m")

        except Exception as e:
            print("\033[91m❌ FAILED: Paginated Collect Data\033[0m")
            raise e

    
    def process_data(self):
        try:
            logger.info("Processing Data.........")
            all_data_load = load_json(
                folder_loc=self.data_save_loc,
                index="all"
            )
            
            df = pd.DataFrame(all_data_load)
            df = df.drop(columns=[c for c in df.columns if c not in self.keep_col])
            df = df.map(lambda x: re.sub(r'<[^>]+>', '', str(x)))
            df["Link"] = df.apply(
                # lambda r: f'https://development.jupitermarinesales.com/search-listing/{r["DocumentID"]}',
                lambda r: f'/search-listing/{r["DocumentID"]}',
                axis=1
            )
            df.to_csv(f"{self.process_data_loc}/process_data.csv", index=False)
            logger.info("Data Processed Successfully")
            print(f"\033[92m✅ PASSED: Data Processed\033[0m")
        except Exception as e:
            print(f"\033[91m❌ FAILED: Data Process\033[0m")
            raise(e)
    
    # don't use outside the class
    def chunking_data(self):
        chunks = []
        try:
            logger.info("Chunking Data.............")
            df = pd.read_csv(f"{self.process_data_loc}/process_data.csv")
            # Chunking data
            for row in df.itertuples(index=False):
                combine = " ".join(f"{col}={value}" for col, value in zip(df.columns,row))
                chunks.append(combine)
            # create docs
            docs = [Document(page_content=chunk, metadata={"id" : doc_id}) for chunk, doc_id in zip(chunks, df["DocumentID"])]
            logger.info("Data Chunked Successfully")
            print(f"\033[92m✅ PASSED: Chunked\033[0m")
            return docs
        except Exception as e:
            print(f"\033[91m❌ FAILED: Chunk\033[0m")
            raise(e)
        
    # don't use outside the class
    async def init_vector_database(self):
        try:
            logger.info("Initializing Vector Database.........")
            client = QdrantClient(url=self.qdrant_url)
            logger.info("Vector Database Initialized Successfully")
            # create collection
            if self.collection_name not in [c.name for c in client.get_collections().collections]:
                client.create_collection(
                    collection_name = self.collection_name,
                    vectors_config = VectorParams(
                        size = 3072,
                        distance = Distance.COSINE
                    )
                )
                logger.info("Collection Created Successfully")
                print(f"\033[92m✅ PASSED: Init Vector Database\033[0m")
            else:
                logger.info("Collection Already Exists")
                print(f"\033[92m✅ PASSED: Init Vector Database\033[0m")
            # print(client.get_collections())
            return client
        except Exception as e:
            print(f"\033[91m❌ FAILED: Init Vector Database\033[0m")
            raise(e)
    
    
    async def vectorize_data(self):
        try:
            logger.info("Vectorizing Data.........")
            docs = self.chunking_data()
            client = await self.init_vector_database()
            
            ## vectorize
            vector_store = QdrantVectorStore(
                client = client,
                collection_name = self.collection_name,
                embedding = self.embed
            )
            
            vector_store.add_documents(
                docs,
                ids=[
                    str(uuid.uuid5(uuid.NAMESPACE_DNS, str(doc.metadata["id"])))
                    for doc in docs
                ]
            )

            # vector_store.add_documents(docs, ids=[doc.metadata["id"] for doc in docs])
            logger.info("Data Vectorized Successfully")
            print(f"\033[92m✅ PASSED: Vectorized\033[0m")
        except Exception as e:
            print(f"\033[91m❌ FAILED: Vectorize Data\033[0m")
            raise(e)
        
        
    # async def collect_data(self):
    #     all_url = [self.data_url_1, self.data_url_2]
        
    #     try:  
    #         logger.info("Collecting Data.........")
    #         for i,url in enumerate(all_url):
    #             data = await request_data(url)
    #             save_json(
    #                 json_data=data,
    #                 index=i,
    #                 folder_loc=self.data_save_loc
    #             )
    #         logger.info("Data Saved Successfully")
    #         print(f"\033[92m✅ PASSED: Collected Data\033[0m")
    #     except Exception as e:
    #         print(f"\033[91m❌ FAILED: Collect Data\033[0m")
    #         raise(e)
           
    
    # def merge_data(self):
    #     all_data = []
    #     try:
    #         logger.info("Merging Data.........")
    #         for i in range(0,2):
    #             data_load = load_json(
    #                 folder_loc=self.data_save_loc,
    #                 index=i
    #             )
                
    #             if "data" in data_load and "results" in data_load["data"]:
    #                 all_data.extend(data_load["data"]["results"])
    #             else:
    #                 all_data.extend(data_load["results"])
            
    #         save_json(
    #             json_data=all_data,
    #             index="all",
    #             folder_loc=self.data_save_loc
    #         )
            
    #         logger.info("Data Merged Successfully")
    #         print(f"\033[92m✅ PASSED: Data Merged\033[0m")
                
    #     except Exception as e:
    #         print(f"\033[91m❌ FAILED: Data Merge\033[0m")
    #         raise(e)
    