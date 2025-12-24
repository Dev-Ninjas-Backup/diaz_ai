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
        await vec.process_data()
        await vec.vectorize_data()

    async def run_jupiter():
        vec = JupiterVectorDataBase()
        await vec.collect_data()
        await vec.process_data()
        await vec.vectorize_data()

    asyncio.run(run_florida())
    logger.info("Completed Florida pipeline.")

    asyncio.run(run_jupiter())
    logger.info("Completed Jupiter pipeline.")



    
