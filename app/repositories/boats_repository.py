from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from app.db.boats_db import boats_session
from app.models.boat import Boat


class BoatsRepository:

    @staticmethod
    async def upsert_boat(data: dict):
        async with boats_session() as session:
            stmt = insert(Boat).values(**data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["document_id"],
                set_=data   
            )
            await session.execute(stmt)
            await session.commit()
    
    @staticmethod
    async def bulk_upsert(boats: list[dict]):
        """Bulk upsert boats data efficiently"""
        if not boats:
            return
            
        async with boats_session() as session:
            try:
                # Process in batches to avoid memory issues with large datasets
                batch_size = 100
                for i in range(0, len(boats), batch_size):
                    batch = boats[i:i + batch_size]
                    
                    for boat in batch:
                        stmt = insert(Boat).values(**boat)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["document_id"],
                            set_=boat
                        )
                        await session.execute(stmt)
                    
                    # Commit each batch
                    await session.commit()
                    print(f"✅ Committed batch {i//batch_size + 1}: {len(batch)} boats")
                    
            except Exception as e:
                await session.rollback()
                print(f"❌ Error during bulk upsert: {e}")
                raise