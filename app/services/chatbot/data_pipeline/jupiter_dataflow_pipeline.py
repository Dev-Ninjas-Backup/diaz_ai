from app.config import configs
from app.utils.helper import request_data, save_json, load_json
from app.utils.logger import get_logger
from app.services.chatbot.llms.open_ai_llm import OpenaiLLM
import asyncio
import os
import pandas as pd
import re
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from langchain_qdrant import QdrantVectorStore
from langchain_classic.docstore.document import Document
from app.repositories.boats_repository import BoatsRepository
import pprint
import uuid

logger = get_logger(__name__)





class JupiterVectorDataBase:

    def __init__(self):
        #self.data_url_1 = configs["api"]["api_1"]
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

            base_url = self.data_url_2
            page = 1
            limit = 2000
            all_results = []

            while True:
                url = f"{base_url}?page={page}&limit={limit}&fields=minimal"

                print(f"Fetching page {page} ...")
                data = await request_data(url)

                results = data.get("data", [])
                metadata = data.get("metadata", {})

                all_results.extend(results)

                current_page = metadata.get("page", page)
                #total_pages = metadata.get("totalPage", 1)
                total_pages = 2

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
    
    async def process_data(self):
        try:
            logger.info("Processing Data.........")
            all_data_load = load_json(
                folder_loc=self.data_save_loc,
                index="all"
            )

            # Create DataFrame
            df = pd.DataFrame(all_data_load)

            # Keep only desired columns, fill missing ones with None
            for col in self.keep_col:
                if col not in df.columns:
                    df[col] = None
            df = df[self.keep_col]

            # Clean HTML tags from all string columns
            df = df.map(lambda x: re.sub(r'<[^>]+>', '', x) if isinstance(x, str) else x)

            # Add link column
            df["Link"] = df.apply(
                lambda r: f'/search-listing/{r.get("DocumentID", "")}',
                axis=1
            )

            # Save processed CSV
            df.to_csv(f"{self.process_data_loc}/process_data.csv", index=False)
            logger.info("Data Processed Successfully")
            print(f"\033[92m✅ PASSED: Data Processed\033[0m")

            logger.info("Upserting Data into boats.db.........")

            # Helper function to extract numeric value from price string
            def extract_numeric(value):
                """Extract numeric value from strings like '629000.00 USD'"""
                if value is None or value == '':
                    return None
                if isinstance(value, (int, float)):
                    return float(value)
                # Extract digits and decimal point from string
                match = re.search(r'[\d.]+', str(value))
                if match:
                    try:
                        return float(match.group())
                    except ValueError:
                        return None
                return None

            # Helper function to convert lists/dicts to JSON strings
            import json
            def to_json_string(value):
                """Convert lists and dicts to JSON strings, handle other types"""
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
                    "model_year": int(row["ModelYear"]) if row.get("ModelYear") else None,
                    "location": to_json_string(row.get("BoatLocation")),
                    "city": row.get("BoatCityNameNoCaseAlnumOnly"),
                    "price": extract_numeric(row.get("Price")),
                    "nominal_length": extract_numeric(row.get("NominalLength")),
                    "length_overall": extract_numeric(row.get("LengthOverall")),
                    "beam": extract_numeric(row.get("BeamMeasure")),
                    "engines": to_json_string(row.get("Engines")),
                    "total_engine_power": extract_numeric(row.get("TotalEnginePowerQuantity")),
                    "number_of_engines": int(row.get("NumberOfEngines")) if row.get("NumberOfEngines") else None,
                    "images": to_json_string(row.get("Images")),
                    "link": row.get("Link")
                })

            await BoatsRepository.bulk_upsert(boats_payload)
            logger.info(f"Upserted {len(boats_payload)} boats into boats.db")

        except Exception as e:
            print(f"\033[91m❌ FAILED: Data Process\033[0m")
            raise e
    
    # def process_data(self):
    #     try:
    #         logger.info("Processing Data.........")
    #         all_data_load = load_json(
    #             folder_loc=self.data_save_loc,
    #             index="all"
    #         )
            
    #         df = pd.DataFrame(all_data_load)
    #         df = df.drop(columns=[c for c in df.columns if c not in self.keep_col])
    #         # df = df.map(lambda x: re.sub(r'<[^>]+>', '', str(x)))
    #         df = df.applymap(lambda x: re.sub(r'<[^>]+>', '', x) if isinstance(x, str) else x)

    #         df["Link"] = df.apply(
    #             # lambda r: f'https://development.jupitermarinesales.com/search-listing/{r["DocumentID"]}',
    #             lambda r: f'/search-listing/{r["DocumentID"]}',
    #             axis=1
    #         )
    #         df.to_csv(f"{self.process_data_loc}/process_data.csv", index=False)
    #         logger.info("Data Processed Successfully")
    #         print(f"\033[92m✅ PASSED: Data Processed\033[0m")

    #         logger.info("Upserting Data into boats.db.........")

    #         #upsert into boats.db
    #         boats_payload= []

    #         for _, row in df.iterrows():
    #             boats_payload.append({
    #                 "document_id": row["DocumentID"],
    #                 "source": row["Source"],
    #                 "general_description": row["GeneralBoatDescription"],
    #                 "additional_description": row["AdditionalDetailDescription"],
    #                 "make": row["MakeString"],
    #                 "model": row["Model"],
    #                 "model_year": int(row["ModelYear"]) if row["ModelYear"] else None,
    #                 "location": row["BoatLocation"],
    #                 "city": row["BoatCityNameNoCaseAlnumOnly"],
    #                 "price": float(row["Price"]) if row["Price"] else None,
    #                 "nominal_length": float(row["NominalLength"]) if row["NominalLength"] else None,
    #                 "length_overall": float(row["LengthOverall"]) if row["LengthOverall"] else None,
    #                 "beam": float(row["BeamMeasure"]) if row["BeamMeasure"] else None,
    #                 "engines": row["Engines"],
    #                 "total_engine_power": float(row["TotalEnginePowerQuantity"]) if row["TotalEnginePowerQuantity"] else None,
    #                 "number_of_engines": int(row["NumberOfEngines"]) if row["NumberOfEngines"] else None,
    #                 "images": row["Images"],
    #                 "link": row["Link"]
    #             })
    #         BoatsRepository.bulk_upsert(boats_payload)

    #         logger.info(f"Upserted {len(boats_payload)} boats into boats.db")

    #     except Exception as e:
    #         print(f"\033[91m❌ FAILED: Data Process\033[0m")
    #         raise(e)
    
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
    