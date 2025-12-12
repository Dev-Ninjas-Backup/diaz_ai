from pydantic import BaseModel
from typing import List, Optional


class JupiterChatRequest(BaseModel):
    messages: str
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None

class JupiterChatResponse(BaseModel):
    messages: str
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None

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
