from app.services.chatbot.data_pipeline.dataflow_pipeline import VectorDataBase

import asyncio


vec = VectorDataBase()


# asyncio.run(vec.merge_data())
vec.merge_data()