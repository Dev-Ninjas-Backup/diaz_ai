from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)




class BotMemory:
    def __init__(self):
        self.mongo_db_uri = settings.MONGODB_URI
        self.mongo_db_name = settings.DB_NAME
        self.postgres_uri = settings.POSTGRES_URI
        self.postgres_db_name = settings.NEONDB_NAME


    async def init_memory_db(self): # main one
        try:
            logger.info("Connecting to MongoDB......")
            client = MongoClient(self.mongo_db_uri)
            checkpointer = MongoDBSaver(client=client, db_name=self.mongo_db_name)
            logger.info("Checkpointer Created")
            return checkpointer
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            return None


    def init_memory_db_pg(self):
        try:
            logger.info("Connecting to Postgres......")
            checkpointer = AsyncPostgresSaver.from_conn_string(self.postgres_uri)
            logger.info("Connected to Postgres")
            return checkpointer
        except Exception as e:
            logger.error(f"Error connecting to Postgres: {e}")
            return None








