from app.services.chatbot.states.state import ChatState
from app.utils.logger import get_logger
from app.services.chatbot.retriever.qdrant_retriever import Retriever
from app.utils.prompts import get_prompt

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import AIMessage

logger = get_logger(__name__)


class ChatbotNodes:

    def __init__(self, model, collection_name: str=None):
        self.llm = model
        self.retriever =  Retriever()
        self.collection_name = collection_name


    async def invoke_chat(self, state : ChatState):
        """
        Invoke the LLM with the current chat state.

        Args:
            state: ChatState containing messages and context

        Returns:
            dict: Updated state with LLM response

        Raises:
            Exception: Re-raises LLM errors after logging
        """
        try:
            if not state or "messages" not in state:
                raise ValueError("Invalid state")
            #logic here
            collection_name = state.get("collection_name", self.collection_name)
            system_prompt = get_prompt(collection_name)
            prompt = ChatPromptTemplate([
                        ('system' , system_prompt),
                        MessagesPlaceholder(variable_name="chat_history"),
                        ('human', "{input}")
                    ])
            
            messages = state["messages"]
            chat_history = messages[:-1]
            last_message = messages[-1]
            current_input = last_message.content if hasattr(last_message, 'content') else str(last_message) # It checks if an object has a given attribute name.
            
            
            qa_chain = create_stuff_documents_chain(llm = self.llm, prompt=prompt)
            retriever = await Retriever(collection_name).get_retriever()

            rag_chain = create_retrieval_chain(retriever, qa_chain)
            
            response = rag_chain.invoke({
                "chat_history" : chat_history,
                "input" : current_input
            })

            # return {"messages" : [response["answer"]]}
            # ✅ CORRECT - returns an AIMessage object
            return {"messages": [AIMessage(content=response["answer"])]}

        except Exception as e:
            logger.error(f"Error invoking LLM: {e}")
            raise e









# from app.services.chatbot.states.state import ChatState
# from app.utils.logger import get_logger
# from app.services.chatbot.retriever.qdrant_retriever import Retriever
# from app.utils.prompt import SYSTEM_PROMPT

# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_classic.chains import create_retrieval_chain
# from langchain_classic.chains.combine_documents import create_stuff_documents_chain
# from langchain_core.messages import AIMessage

# logger = get_logger(__name__)


# class ChatbotNodes:

#     def __init__(self, model):
#         self.llm = model
#         self.retriever =  Retriever()


#     async def invoke_chat(self, state : ChatState):
#         """
#         Invoke the LLM with the current chat state.

#         Args:
#             state: ChatState containing messages and context

#         Returns:
#             dict: Updated state with LLM response

#         Raises:
#             Exception: Re-raises LLM errors after logging
#         """
#         try:
#             if not state or "messages" not in state:
#                 raise ValueError("Invalid state")
#             #logic here
#             prompt = ChatPromptTemplate([
#                         ('system' , SYSTEM_PROMPT),
#                         MessagesPlaceholder(variable_name="chat_history"),
#                         ('human', "{input}")
#                     ])
            
#             messages = state["messages"]
#             chat_history = messages[:-1]
#             last_message = messages[-1]
#             current_input = last_message.content if hasattr(last_message, 'content') else str(last_message) # It checks if an object has a given attribute name.
            
            
#             qa_chain = create_stuff_documents_chain(llm = self.llm, prompt=prompt)
#             rag_chain = create_retrieval_chain(await self.retriever.get_retriever(), qa_chain)
            
#             response = rag_chain.invoke({
#                 "chat_history" : chat_history,
#                 "input" : current_input
#             })

#             # return {"messages" : [response["answer"]]}
#             # ✅ CORRECT - returns an AIMessage object
#             return {"messages": [AIMessage(content=response["answer"])]}

#         except Exception as e:
#             logger.error(f"Error invoking LLM: {e}")
#             raise e





