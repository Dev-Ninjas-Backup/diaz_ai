#app.schedule_task.py
from app.services.chatbot.data_pipeline.florida_dataflow_pipeline import FloridaVectorDataBase
from app.services.chatbot.data_pipeline.jupiter_dataflow_pipeline import JupiterVectorDataBase
import asyncio
from logging import getLogger
from app.celery_app import celery




@celery.task(name="app.tasks.daily_task")
def daily_task():
    logger = getLogger(__name__)
    logger.info("Starting daily chatbot data pipeline task...")

    async def run_florida():
        vec = FloridaVectorDataBase()
        await vec.collect_data()
        vec.process_data()
        await vec.vectorize_data()

    async def run_jupiter():
        vec = JupiterVectorDataBase()
        await vec.collect_data()
        vec.process_data()
        await vec.vectorize_data()

    asyncio.run(run_florida())
    logger.info("Completed Florida pipeline.")

    asyncio.run(run_jupiter())
    logger.info("Completed Jupiter pipeline.")



    
    # ret = Retriever()

    # retriever = asyncio.run(ret.get_retriever())

    # input_text = "Do you have any Yamaha boats?"
    # docs = retriever.invoke(input_text, k=10)

    # print(docs)

    ### boat

    # index = DataIndex()

    # index.vectorize_data_for_search()   # <--- missing in your code
    # asyncio.run(index.indexing_data())
# from app.services.chatbot.retriever.qdrant_retriever import Retriever
# from app.services.search_engine.data_indexing_pipeline import DataIndex
# from app.services.search_engine.search import SearchEngine