from langgraph.checkpoint.memory import MemorySaver

from app.services.chatbot.llms.open_ai_llm import OpenaiLLM
from app.services.chatbot.memory.memory import BotMemory
from app.services.chatbot.graph.graph_builder import GraphBuilder
from langchain_core.messages import HumanMessage, AIMessage


from app.utils.logger import get_logger


logger = get_logger(__name__)



class InitChat:

    def __init__(self):
        self.checkpointer = None
        self.llm = None
        self.graph = None


    async def initialize_chat(self):
        try:
            logger.info("Initializing chat........")
            self.checkpointer = MemorySaver()
            self.llm = OpenaiLLM().get_llm()
            self.graph = GraphBuilder(model=self.llm, checkpointer=self.checkpointer).chatbot_graph()
            logger.info("Chat initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing chat: {e}")
            return None


    async def chat(self, prompt : str, thread_id : str):
        try:
            logger.info(f"Chatting with prompt........")
            config = {"configurable": {"thread_id": thread_id}}
            input_data = {"messages": [HumanMessage(content=prompt)]}

            result = await self.graph.ainvoke(input_data, config)
            final_result = result["messages"][-1].content

            return final_result
        except Exception as e:
            logger.error(f"Error initializing chat: {e}")
            return None


    async def get_chat_history(self, thread_id : str):

        try:
            logger.info(f"Getting chat history for session {thread_id}")
            config = {"configurable": {"thread_id": thread_id}}
            state = await self.graph.aget_state(config)

            # if state.values:
            #     return [{"role" : "user" if isinstance(msg, HumanMessage) else "assistant", "content" : msg.content} for msg in state.values["messages"]]
            if state.values:
                history = []
                for msg in state.values["messages"]:
                    if isinstance(msg, HumanMessage):
                        role= "user"
                    elif isinstance(msg, AIMessage):
                        role= "assistant"
                    else:
                        role= msg.__class__.__name__.lower()
                    history.append({"role": role, "content": msg.content})
                return history

        except Exception as e:
            logger.error(f"Failed to get chat history for session {thread_id}: {e}")
            return None
        return []





