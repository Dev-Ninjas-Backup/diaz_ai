from sqlalchemy import select, and_
from app.db.boats_db import boats_session
from app.models.jupiter_boat import Boat

async def search_boats(
    make: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    price_min: float | None = None,
    price_max: float | None = None
):
    async with boats_session() as session:
        conditions = []

        if make:
            conditions.append(Boat.make.ilike(f"%{make}%"))
        if year_from:
            conditions.append(Boat.model_year >= year_from)
        if year_to:
            conditions.append(Boat.model_year <= year_to)
        if price_min:
            conditions.append(Boat.price >= price_min)
        if price_max:
            conditions.append(Boat.price <= price_max)

        stmt = select(Boat).where(and_(*conditions))
        result = await session.execute(stmt)
        return result.scalars().all()
