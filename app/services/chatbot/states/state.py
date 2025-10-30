from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict
from typing import Sequence, Annotated


class ChatState(TypedDict):
    messages : Annotated[Sequence[BaseMessage], add_messages]




