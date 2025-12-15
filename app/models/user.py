from sqlalchemy import Column, String, DateTime, func
from app.db.chat_db import ChatBase

class User(ChatBase):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    date = Column(DateTime, default=func.now())
