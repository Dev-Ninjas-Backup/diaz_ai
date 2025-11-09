from app.services.chatbot.data_pipeline.dataflow_pipeline import VectorDataBase

import asyncio


vec = VectorDataBase()


# asyncio.run(vec.collect_data())
# vec.merge_data()
# vec.process_data()

asyncio.run(vec.vectorize_data())