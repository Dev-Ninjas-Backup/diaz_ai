from app.services.chatbot.data_pipeline.dataflow_pipeline import VectorDataBase
from app.services.chatbot.retriever.qdrant_retriever import Retriever
from app.services.search_engine.data_indexing_pipeline import DataIndex

import asyncio


# vec = VectorDataBase()


# asyncio.run(vec.collect_data())
# vec.merge_data()
# vec.process_data()
# asyncio.run(vec.vectorize_data())


# ret = Retriever()

# retriever = asyncio.run(ret.get_retriever())

# input_text = "Do you have any Yamaha boats?"
# docs = retriever.invoke(input_text, k=10)

# print(docs)


index = DataIndex()


asyncio.run(index.indexing_data())
