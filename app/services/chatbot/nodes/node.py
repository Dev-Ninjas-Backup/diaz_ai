from app.services.chatbot.states.state import ChatState
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChatbotNodes:

    def __init__(self, model):
        self.llm = model


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

            response = await self.llm.ainvoke(state["messages"])

            return {"messages" : [response]}

        except Exception as e:
            logger.error(f"Error invoking LLM: {e}")
            raise e





