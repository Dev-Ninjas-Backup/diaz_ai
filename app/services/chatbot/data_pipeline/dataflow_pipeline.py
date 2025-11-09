from app.config import configs
from app.utils.helper import request_data, save_json, load_json
from app.utils.logger import get_logger

import os
import pandas as pd
import re
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from langchain_community.vectorstores import Qdrant
from langchain_classic.docstore.document import Document
import pprint

logger = get_logger(__name__)


class VectorDataBase:

    def __init__(self):
        self.data_url_1 = configs["api"]["api_1"]
        self.data_url_2 = configs["api"]["api_2"]
        self.data_save_loc = configs["database_loc"]["raw_data_loc"]
        self.keep_col = configs["columns"]["keep"]
        self.process_data_loc = configs["database_loc"]["process_data_loc"]
        os.makedirs(configs["database_loc"]["raw_data_loc"], exist_ok=True)
        os.makedirs(configs["database_loc"]["process_data_loc"], exist_ok=True)
        self.qdrant_url = configs["vector"]["url"]
        self.collection_name = configs["vector"]["collection_name"]
    
    
    async def collect_data(self):
        all_url = [self.data_url_1, self.data_url_2]
        
        try:  
            logger.info("Collecting Data.........")
            for i,url in enumerate(all_url):
                data = await request_data(url)
                save_json(
                    json_data=data,
                    index=i,
                    folder_loc=self.data_save_loc
                )
            logger.info("Data Saved Successfully")
        except Exception as e:
            raise(e)
           
    
    def merge_data(self):
        all_data = []
        try:
            logger.info("Merging Data.........")
            for i in range(0,2):
                data_load = load_json(
                    folder_loc=self.data_save_loc,
                    index=i
                )
                
                if "data" in data_load and "results" in data_load["data"]:
                    all_data.extend(data_load["data"]["results"])
                else:
                    all_data.extend(data_load["results"])
            
            save_json(
                json_data=all_data,
                index="all",
                folder_loc=self.data_save_loc
            )
            
            logger.info("Data Merged Successfully")
                
        except Exception as e:
            raise(e)
    
    
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
                lambda r: f'https://development.jupitermarinesales.com/search-listing/{r["DocumentID"]}',
                axis=1
            )
            df.to_csv(f"{self.process_data_loc}/process_data.csv", index=False)
            logger.info("Data Processed Successfully")
        except Exception as e:
            raise(e)
    
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
            return docs
        except Exception as e:
            raise(e)
        
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
            else:
                logger.info("Collection Already Exists")
            # print(client.get_collections())
            return client
        except Exception as e:
            raise(e)
    
    
    async def vectorize_data(self):
        try:
            docs = self.chunking_data()
            client = self.init_vector_database()
            
            ## vectorize
            
        except Exception as e:
            raise(e)