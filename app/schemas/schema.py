from pydantic import BaseModel


class ChatRequest(BaseModel):
    messages : str
    user_id : str
    session_id : str


class ChatResponse(BaseModel):
    messages : str
    session_id : str


class HistoryModel(BaseModel):
    user_id : str
    session_id : str