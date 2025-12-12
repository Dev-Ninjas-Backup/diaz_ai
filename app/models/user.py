from sqlalchemy import Column, String, DateTime, func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    date = Column(DateTime, default=func.now())
