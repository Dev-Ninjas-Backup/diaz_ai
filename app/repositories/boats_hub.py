from sqlalchemy import select, and_
from app.models.boat import Boat
from app.db.boats_db import boats_session

class BoatsHub:

    @staticmethod
    async def filter_boats(filters):
        async with boats_session() as session:
            conditions = []

            if filters.make:
                conditions.append(Boat.make.ilike(f"%{filters.make}%"))

            if filters.model:
                conditions.append(Boat.model.ilike(f"%{filters.model}%"))

            if filters.year_from:
                conditions.append(Boat.model_year >= filters.year_from)

            if filters.year_to:
                conditions.append(Boat.model_year <= filters.year_to)

            if filters.price_min:
                conditions.append(Boat.price >= filters.price_min)

            if filters.price_max:
                conditions.append(Boat.price <= filters.price_max)

            if filters.length_min:
                conditions.append(Boat.length_overall >= filters.length_min)

            if filters.length_max:
                conditions.append(Boat.length_overall <= filters.length_max)

            if filters.beam_min:
                conditions.append(Boat.beam >= filters.beam_min)

            if filters.beam_max:
                conditions.append(Boat.beam <= filters.beam_max)

            if filters.number_of_engines:
                conditions.append(Boat.number_of_engines == filters.number_of_engines)

            if filters.additional_unit:
                conditions.append(
                    Boat.additional_description.ilike(
                        f"%{filters.additional_unit}%"
                    )
                )

            query = select(Boat)

            if conditions:
                query = query.where(and_(*conditions))

            result = await session.execute(query)
            return result.scalars().all()
