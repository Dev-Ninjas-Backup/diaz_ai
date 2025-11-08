from app.config import configs
from app.utils.helper import request_data, save_json, load_json
from app.utils.logger import get_logger

import os
from types import SimpleNamespace
import pandas as pd

logger = get_logger(__name__)


class VectorDataBase:

    def __init__(self):
        self.data_url_1 = configs["api"]["api_1"]
        self.data_url_2 = configs["api"]["api_2"]
        os.makedirs(configs["database_loc"]["raw_data_loc"], exist_ok=True)
        self.data_save_loc = configs["database_loc"]["raw_data_loc"]
    
    
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
            pass
        except Exception as e:
            raise(e)
    
    
    def vectorize_data(self):
        pass
    
    
    