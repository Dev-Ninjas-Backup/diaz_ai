from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

BOATS_DB_URL = "sqlite+aiosqlite:///./boats.db"

boats_engine = create_async_engine(BOATS_DB_URL, echo=False, future=True)
boats_session = async_sessionmaker(boats_engine, expire_on_commit=False)

BoatsBase = declarative_base()
