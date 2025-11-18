#app.schedule_task.py
from app.services.chatbot.data_pipeline.dataflow_pipeline import VectorDataBase
from app.services.chatbot.retriever.qdrant_retriever import Retriever
from app.services.search_engine.data_indexing_pipeline import DataIndex
from app.services.search_engine.search import SearchEngine
import asyncio
from app.celery_app import celery




@celery.task(name="app.tasks.daily_task")
def daily_task():
    print("Daily task started.")
    vec = VectorDataBase()


    asyncio.run(vec.collect_data())
    # vec.merge_data()
    vec.process_data()
    asyncio.run(vec.vectorize_data())

    print("Chatbot data pipeline completed.")

    # ret = Retriever()

    # retriever = asyncio.run(ret.get_retriever())

    # input_text = "Do you have any Yamaha boats?"
    # docs = retriever.invoke(input_text, k=10)

    # print(docs)

    ### boat

    # index = DataIndex()

    # index.vectorize_data_for_search()   # <--- missing in your code
    # asyncio.run(index.indexing_data())
