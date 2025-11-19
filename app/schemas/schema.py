from pydantic import BaseModel


class ChatRequest(BaseModel):
    messages: str
    user_id: str


class ChatResponse(BaseModel):
    messages: str
    user_id: str


class HistoryModel(BaseModel):
    user_id: str


class SearchModel(BaseModel):
    query: str
    k: int = 5
