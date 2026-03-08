import os
import pandas as pd
import re
import uuid
from app.config import configs
from app.utils.helper import request_data, save_json, load_json
from app.utils.logger import get_logger
from app.services.chatbot.llms.open_ai_llm import OpenaiLLM
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from langchain_qdrant import QdrantVectorStore
from langchain_classic.docstore.document import Document
from app.repositories.jupiter_boat_repository import BoatsRepository


logger = get_logger(__name__)


class JupiterVectorDataBase:

    def __init__(self):
        self.data_url_1 = configs["api"]["api_1"]
        self.data_url_2 = configs["api"]["api_2"]
        self.data_save_loc = configs["database_loc"]["raw_data_loc_jupiter"]
        self.keep_col = configs["columns"]["keep"]
        self.process_data_loc = configs["database_loc"]["process_data_loc_jupiter"]
        os.makedirs(configs["database_loc"]["raw_data_loc_jupiter"], exist_ok=True)
        os.makedirs(configs["database_loc"]["process_data_loc_jupiter"], exist_ok=True)
        self.qdrant_url = configs["vector"]["url"]
        self.collection_name = configs["vector"]["collection_name_jupiter"]
        self.embed = OpenaiLLM().get_embeddings()
    
    async def collect_data(self):
        try:
            logger.info("Collecting Data (Paginated)...")

            master_results = []

            # SOURCE 1
            base_url = self.data_url_1
            source = "custom"
            limit = 50
            page = 1

            while True:
                url = f"{base_url}?source={source}&fields=minimal&page={page}&limit={limit}"
                print(f"Fetching source1 page {page} ...")

                data = await request_data(url)

                results = data.get("data", [])
                metadata = data.get("metadata", {})

                for item in results:
                    item["_source"] = "data_url_1"

                master_results.extend(results)

                current_page = metadata.get("page", page)
                total_pages = metadata.get("totalPage", page)

                print(f"Source1 Page {current_page}/{total_pages}: {len(results)} items")

                if current_page >= total_pages:
                    break

                page += 1

            # SOURCE 2
            base_url = self.data_url_2
            page = 1
            limit = 2000

            while True:
                url = f"{base_url}?page={page}&limit={limit}&fields=minimal"
                print(f"Fetching source2 page {page} ...")

                data = await request_data(url)

                results = data.get("data", [])
                metadata = data.get("metadata", {})

                for item in results:
                    item["_source"] = "data_url_2"

                master_results.extend(results)

                current_page = metadata.get("page", page)
                total_pages = metadata.get("totalPage")

                print(f"Source2 Page {current_page}/{total_pages}: {len(results)} items")

                if not results:
                    print("No result returned, stop fetching")
                    break
                
                if total_pages is not None and current_page >= int(total_pages):
                    print("Reached last page. Stop fetching")
                    break

                page += 1

            save_json(
                json_data=master_results,
                index="all",
                folder_loc=self.data_save_loc
            )

            logger.info(f"Saved {len(master_results)} total records into one JSON file")
            print("\033[92m✅ PASSED: Collected Paginated Data\033[0m")

        except Exception as e:
            print("\033[91m❌ FAILED: Paginated Collect Data\033[0m")
            raise e
    
    async def process_data(self):
        try:
            logger.info("Processing Data.........")
            all_data_load = load_json(
                folder_loc=self.data_save_loc,
                index="all"
            )

            df = pd.DataFrame(all_data_load)

            for col in self.keep_col:
                if col not in df.columns:
                    df[col] = None
            df = df[self.keep_col]

            df = df.map(lambda x: re.sub(r'<[^>]+>', '', x) if isinstance(x, str) else x)

            # Remove rows without DocumentID
            df = df[df["DocumentID"].notna()].copy()

            # Deduplicate by DocumentID
            df = df.drop_duplicates(subset=["DocumentID"], keep="last")

            df["Link"] = df.apply(
                lambda r: f'/search-listing/{r.get("DocumentID", "")}',
                axis=1
            )

            df.to_csv(f"{self.process_data_loc}/process_data.csv", index=False)
            logger.info("Data Processed Successfully")
            print(f"\033[92m✅ PASSED: Data Processed\033[0m")

            logger.info("Replacing Data into boats.db.........")

            def extract_numeric(value):
                if value is None or value == '':
                    return None
                if isinstance(value, (int, float)):
                    return float(value)
                match = re.search(r'[\d.]+', str(value))
                if match:
                    try:
                        return float(match.group())
                    except ValueError:
                        return None
                return None

            import json
            def to_json_string(value):
                if value is None or value == '':
                    return None
                if isinstance(value, (list, dict)):
                    return json.dumps(value)
                return value

            boats_payload = []
            for _, row in df.iterrows():
                boats_payload.append({
                    "document_id": row.get("DocumentID"),
                    "source": row.get("Source"),
                    "general_description": to_json_string(row.get("GeneralBoatDescription")),
                    "additional_description": to_json_string(row.get("AdditionalDetailDescription")),
                    "make": row.get("MakeString"),
                    "model": row.get("Model"),
                    "model_year": int(row["ModelYear"]) if pd.notna(row.get("ModelYear")) and row.get("ModelYear") != "" else None,
                    "location": to_json_string(row.get("BoatLocation")),
                    "city": row.get("BoatCityNameNoCaseAlnumOnly"),
                    "price": extract_numeric(row.get("Price")),
                    "nominal_length": extract_numeric(row.get("NominalLength")),
                    "length_overall": extract_numeric(row.get("LengthOverall")),
                    "beam": extract_numeric(row.get("BeamMeasure")),
                    "engines": to_json_string(row.get("Engines")),
                    "total_engine_power": extract_numeric(row.get("TotalEnginePowerQuantity")),
                    "number_of_engines": int(row.get("NumberOfEngines")) if pd.notna(row.get("NumberOfEngines")) and row.get("NumberOfEngines") != "" else None,
                    "images": to_json_string(row.get("Images")),
                    "link": row.get("Link")
                })

            if not boats_payload:
                raise ValueError("boats_payload is empty. Aborting replacement.")

            await BoatsRepository.replace_all(boats_payload)
            logger.info(f"Replaced {len(boats_payload)} boats into boats.db")

        except Exception as e:
            print(f"\033[91m❌ FAILED: Data Process\033[0m")
            raise e
    
    
    # don't use outside the class
    def chunking_data(self):
        chunks = []
        try:
            logger.info("Chunking Data.............")
            df = pd.read_csv(f"{self.process_data_loc}/process_data.csv")
            for row in df.itertuples(index=False):
                combine = " ".join(f"{col}={value}" for col, value in zip(df.columns, row))
                chunks.append(combine)
            docs = [Document(page_content=chunk, metadata={"id": doc_id}) for chunk, doc_id in zip(chunks, df["DocumentID"])]
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
            if self.collection_name not in [c.name for c in client.get_collections().collections]:
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=3072,
                        distance=Distance.COSINE
                    )
                )
                logger.info("Collection Created Successfully")
                print(f"\033[92m✅ PASSED: Init Vector Database\033[0m")
            else:
                logger.info("Collection Already Exists")
                print(f"\033[92m✅ PASSED: Init Vector Database\033[0m")
            return client
        except Exception as e:
            print(f"\033[91m❌ FAILED: Init Vector Database\033[0m")
            raise(e)
    
    
    async def vectorize_data(self):
        try:
            logger.info("Vectorizing Data.........")
            docs = self.chunking_data()
            client = await self.init_vector_database()
            
            vector_store = QdrantVectorStore(
                client=client,
                collection_name=self.collection_name,
                embedding=self.embed
            )
            
            vector_store.add_documents(
                docs,
                ids=[
                    str(uuid.uuid5(uuid.NAMESPACE_DNS, str(doc.metadata["id"])))
                    for doc in docs
                ]
            )

            logger.info("Data Vectorized Successfully")
            print(f"\033[92m✅ PASSED: Vectorized\033[0m")
        except Exception as e:
            print(f"\033[91m❌ FAILED: Vectorize Data\033[0m")
            raise(e)


# import os
# import pandas as pd
# import re
# import uuid
# from app.config import configs
# from app.utils.helper import request_data, save_json, load_json
# from app.utils.logger import get_logger
# from app.services.chatbot.llms.open_ai_llm import OpenaiLLM
# from qdrant_client import QdrantClient
# from qdrant_client.models import VectorParams, Distance
# from langchain_qdrant import QdrantVectorStore
# from langchain_classic.docstore.document import Document
# from app.repositories.jupiter_boat_repository import BoatsRepository


# logger = get_logger(__name__)





# class JupiterVectorDataBase:

#     def __init__(self):
#         self.data_url_1 = configs["api"]["api_1"]
#         self.data_url_2 = configs["api"]["api_2"]
#         self.data_save_loc = configs["database_loc"]["raw_data_loc_jupiter"]
#         self.keep_col = configs["columns"]["keep"]
#         self.process_data_loc = configs["database_loc"]["process_data_loc_jupiter"]
#         os.makedirs(configs["database_loc"]["raw_data_loc_jupiter"], exist_ok=True)
#         os.makedirs(configs["database_loc"]["process_data_loc_jupiter"], exist_ok=True)
#         self.qdrant_url = configs["vector"]["url"]
#         self.collection_name = configs["vector"]["collection_name_jupiter"]
#         self.embed = OpenaiLLM().get_embeddings()
    
#     async def collect_data(self):
#         try:
#             logger.info("Collecting Data (Paginated)...")

#             master_results = []  # 🔹 ONE list for everything

#             # ==============================
#             # SOURCE 1
#             # ==============================
#             base_url = self.data_url_1
#             source = "custom"
#             limit = 50
#             page = 1

#             while True:
#                 url = f"{base_url}?source={source}&fields=minimal&page={page}&limit={limit}"
#                 print(f"Fetching source1 page {page} ...")

#                 data = await request_data(url)

#                 results = data.get("data", [])
#                 metadata = data.get("metadata", {})

#                 # (optional) tag origin
#                 for item in results:
#                     item["_source"] = "data_url_1"

#                 master_results.extend(results)

#                 current_page = metadata.get("page", page)
#                 total_pages = metadata.get("totalPage", page)

#                 print(f"Source1 Page {current_page}/{total_pages}: {len(results)} items")

#                 if current_page >= total_pages:
#                     break

#                 page += 1


#             # ==============================
#             # SOURCE 2
#             # ==============================
#             base_url = self.data_url_2
#             page = 1
#             limit = 2000

#             while True:
#                 url = f"{base_url}?page={page}&limit={limit}&fields=minimal"
#                 print(f"Fetching source2 page {page} ...")

#                 data = await request_data(url)

#                 results = data.get("data", [])
#                 metadata = data.get("metadata", {})

#                 # (optional) tag origin
#                 for item in results:
#                     item["_source"] = "data_url_2"

#                 master_results.extend(results)

#                 current_page = metadata.get("page", page)
#                 total_pages = metadata.get("totalPage")

#                 print(f"Source2 Page {current_page}/{total_pages}: {len(results)} items")

#                 if not results:
#                     print("No result returnd, Stop fetching")
#                     break
                
#                 if total_pages is not None and current_page >= int(total_pages):
#                     print("Reached last page. Stop fetching")
#                     break

#                 page += 1


#             # ==============================
#             # SAVE ONCE
#             # ==============================
#             save_json(
#                 json_data=master_results,
#                 index="all",
#                 folder_loc=self.data_save_loc
#             )

#             logger.info(f"Saved {len(master_results)} total records into one JSON file")

#             # logger.info("Collecting Data (Paginated)...")

#             # base_url = self.data_url_2
#             # page = 1
#             # limit = 2000
#             # all_results = []

#             # while True:
#             #     url = f"{base_url}?page={page}&limit={limit}&fields=minimal"

#             #     print(f"Fetching page {page} ...")
#             #     data = await request_data(url)

#             #     results = data.get("data", [])
#             #     metadata = data.get("metadata", {})

#             #     all_results.extend(results)

#             #     current_page = metadata.get("page", page)
#             #     total_pages = metadata.get("totalPage", 1)
#             #     #total_pages = 2

#             #     print(f"Page {current_page}/{total_pages}: {len(results)} items")

#             #     if current_page >= total_pages:
#             #         print("Reached last page. Stopping.")
#             #         break

#             #     page += 1

#             # save_json(
#             #     json_data=all_results,
#             #     index="all",
#             #     folder_loc=self.data_save_loc
#             # )

#             print("\033[92m✅ PASSED: Collected Paginated Data\033[0m")

#         except Exception as e:
#             print("\033[91m❌ FAILED: Paginated Collect Data\033[0m")
#             raise e
    
#     async def process_data(self):
#         try:
#             logger.info("Processing Data.........")
#             all_data_load = load_json(
#                 folder_loc=self.data_save_loc,
#                 index="all"
#             )

#             # Create DataFrame
#             df = pd.DataFrame(all_data_load)

#             # Keep only desired columns, fill missing ones with None
#             for col in self.keep_col:
#                 if col not in df.columns:
#                     df[col] = None
#             df = df[self.keep_col]

#             # Clean HTML tags from all string columns
#             df = df.map(lambda x: re.sub(r'<[^>]+>', '', x) if isinstance(x, str) else x)

#             # Add link column
#             df["Link"] = df.apply(
#                 lambda r: f'/search-listing/{r.get("DocumentID", "")}',
#                 axis=1
#             )

#             # Save processed CSV
#             df.to_csv(f"{self.process_data_loc}/process_data.csv", index=False)
#             logger.info("Data Processed Successfully")
#             print(f"\033[92m✅ PASSED: Data Processed\033[0m")

#             logger.info("Upserting Data into boats.db.........")

#             # Helper function to extract numeric value from price string
#             def extract_numeric(value):
#                 """Extract numeric value from strings like '629000.00 USD'"""
#                 if value is None or value == '':
#                     return None
#                 if isinstance(value, (int, float)):
#                     return float(value)
#                 # Extract digits and decimal point from string
#                 match = re.search(r'[\d.]+', str(value))
#                 if match:
#                     try:
#                         return float(match.group())
#                     except ValueError:
#                         return None
#                 return None

#             # Helper function to convert lists/dicts to JSON strings
#             import json
#             def to_json_string(value):
#                 """Convert lists and dicts to JSON strings, handle other types"""
#                 if value is None or value == '':
#                     return None
#                 if isinstance(value, (list, dict)):
#                     return json.dumps(value)
#                 return value

#             boats_payload = []
#             for _, row in df.iterrows():
#                 boats_payload.append({
#                     "document_id": row.get("DocumentID"),
#                     "source": row.get("Source"),
#                     "general_description": to_json_string(row.get("GeneralBoatDescription")),
#                     "additional_description": to_json_string(row.get("AdditionalDetailDescription")),
#                     "make": row.get("MakeString"),
#                     "model": row.get("Model"),
#                     "model_year": int(row["ModelYear"]) if row.get("ModelYear") else None,
#                     "location": to_json_string(row.get("BoatLocation")),
#                     "city": row.get("BoatCityNameNoCaseAlnumOnly"),
#                     "price": extract_numeric(row.get("Price")),
#                     "nominal_length": extract_numeric(row.get("NominalLength")),
#                     "length_overall": extract_numeric(row.get("LengthOverall")),
#                     "beam": extract_numeric(row.get("BeamMeasure")),
#                     "engines": to_json_string(row.get("Engines")),
#                     "total_engine_power": extract_numeric(row.get("TotalEnginePowerQuantity")),
#                     "number_of_engines": int(row.get("NumberOfEngines")) if row.get("NumberOfEngines") else None,
#                     "images": to_json_string(row.get("Images")),
#                     "link": row.get("Link")
#                 })

#             await BoatsRepository.bulk_upsert(boats_payload)
#             logger.info(f"Upserted {len(boats_payload)} boats into boats.db")

#         except Exception as e:
#             print(f"\033[91m❌ FAILED: Data Process\033[0m")
#             raise e
    
    
#     # don't use outside the class
#     def chunking_data(self):
#         chunks = []
#         try:
#             logger.info("Chunking Data.............")
#             df = pd.read_csv(f"{self.process_data_loc}/process_data.csv")
#             # Chunking data
#             for row in df.itertuples(index=False):
#                 combine = " ".join(f"{col}={value}" for col, value in zip(df.columns,row))
#                 chunks.append(combine)
#             # create docs
#             docs = [Document(page_content=chunk, metadata={"id" : doc_id}) for chunk, doc_id in zip(chunks, df["DocumentID"])]
#             logger.info("Data Chunked Successfully")
#             print(f"\033[92m✅ PASSED: Chunked\033[0m")
#             return docs
#         except Exception as e:
#             print(f"\033[91m❌ FAILED: Chunk\033[0m")
#             raise(e)
        
#     # don't use outside the class
#     async def init_vector_database(self):
#         try:
#             logger.info("Initializing Vector Database.........")
#             client = QdrantClient(url=self.qdrant_url)
#             logger.info("Vector Database Initialized Successfully")
#             # create collection
#             if self.collection_name not in [c.name for c in client.get_collections().collections]:
#                 client.create_collection(
#                     collection_name = self.collection_name,
#                     vectors_config = VectorParams(
#                         size = 3072,
#                         distance = Distance.COSINE
#                     )
#                 )
#                 logger.info("Collection Created Successfully")
#                 print(f"\033[92m✅ PASSED: Init Vector Database\033[0m")
#             else:
#                 logger.info("Collection Already Exists")
#                 print(f"\033[92m✅ PASSED: Init Vector Database\033[0m")
#             # print(client.get_collections())
#             return client
#         except Exception as e:
#             print(f"\033[91m❌ FAILED: Init Vector Database\033[0m")
#             raise(e)
    
    
#     async def vectorize_data(self):
#         try:
#             logger.info("Vectorizing Data.........")
#             docs = self.chunking_data()
#             client = await self.init_vector_database()
            
#             ## vectorize
#             vector_store = QdrantVectorStore(
#                 client = client,
#                 collection_name = self.collection_name,
#                 embedding = self.embed
#             )
            
#             vector_store.add_documents(
#                 docs,
#                 ids=[
#                     str(uuid.uuid5(uuid.NAMESPACE_DNS, str(doc.metadata["id"])))
#                     for doc in docs
#                 ]
#             )

#             # vector_store.add_documents(docs, ids=[doc.metadata["id"] for doc in docs])
#             logger.info("Data Vectorized Successfully")
#             print(f"\033[92m✅ PASSED: Vectorized\033[0m")
#         except Exception as e:
#             print(f"\033[91m❌ FAILED: Vectorize Data\033[0m")
#             raise(e)
        