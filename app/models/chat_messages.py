from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.db.database import Base
from datetime import datetime

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    role = Column(String)   # "user" or "assistant"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
