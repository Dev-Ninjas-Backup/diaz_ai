from langgraph.graph import StateGraph, START, END

from app.services.chatbot.nodes.node import ChatbotNodes
from app.services.chatbot.states.state import ChatState
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GraphBuilder:

    def __init__(self, model, checkpointer, collection_name: str=None):
        self.llm = model
        self.checkpointer = checkpointer
        self.collection_name = collection_name


    def chatbot_graph(self):
        try:
            logger.info("Building chatbot graph......")
            self.chatbot_nodes = ChatbotNodes(self.llm, collection_name=self.collection_name)

            self.workflow = StateGraph(ChatState)

            ## Add nodes
            self.workflow.add_node("chatbot", self.chatbot_nodes.invoke_chat)

            ## Add edges
            self.workflow.add_edge(START, "chatbot")
            self.workflow.add_edge("chatbot", END)

            logger.info("Chatbot graph built successfully")

            return self.workflow.compile(checkpointer=self.checkpointer)
        except Exception as e:
            logger.error(f"Error building graph: {e}")
            return None





# from langgraph.graph import StateGraph, START, END

# from app.services.chatbot.nodes.node import ChatbotNodes
# from app.services.chatbot.states.state import ChatState
# from app.utils.logger import get_logger

# logger = get_logger(__name__)


# class GraphBuilder:

#     def __init__(self, model, checkpointer):
#         self.llm = model
#         self.checkpointer = checkpointer


#     def chatbot_graph(self):
#         try:
#             logger.info("Building chatbot graph......")
#             self.chatbot_nodes = ChatbotNodes(self.llm)

#             self.workflow = StateGraph(ChatState)

#             ## Add nodes
#             self.workflow.add_node("chatbot", self.chatbot_nodes.invoke_chat)

#             ## Add edges
#             self.workflow.add_edge(START, "chatbot")
#             self.workflow.add_edge("chatbot", END)

#             logger.info("Chatbot graph built successfully")

#             return self.workflow.compile(checkpointer=self.checkpointer)
#         except Exception as e:
#             logger.error(f"Error building graph: {e}")
#             return None


