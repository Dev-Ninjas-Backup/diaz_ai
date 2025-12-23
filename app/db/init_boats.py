import asyncio
from app.db.boats_db import boats_engine, BoatsBase
from app.models.jupiter_boat import JupiterBoat
from app.models.florida_boat import FloridaBoat


async def init_boats_db():
    async with boats_engine.begin() as conn:
        await conn.run_sync(BoatsBase.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_boats_db())
