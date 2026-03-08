from sqlalchemy import delete
from app.db.boats_db import boats_session
from app.models.jupiter_boat import JupiterBoat


class BoatsRepository:

    @staticmethod
    async def replace_all(boats: list[dict]):
        if not boats:
            raise ValueError("boats payload is empty; aborting replacement")

        # final safety dedupe by document_id
        deduped = {}
        for boat in boats:
            doc_id = boat.get("document_id")
            if doc_id is not None:
                deduped[doc_id] = boat

        boats = list(deduped.values())

        async with boats_session() as session:
            try:
                await session.execute(delete(JupiterBoat))
                session.add_all([JupiterBoat(**boat) for boat in boats])
                await session.commit()
                print(f"✅ Replaced all boats: {len(boats)} rows")
            except Exception as e:
                await session.rollback()
                print(f"❌ Error during full replace: {e}")
                raise


# from sqlalchemy import select
# from sqlalchemy.dialects.sqlite import insert
# from app.db.boats_db import boats_session
# from app.models.jupiter_boat import JupiterBoat


# class BoatsRepository:

#     @staticmethod
#     async def upsert_boat(data: dict):
#         async with boats_session() as session:
#             stmt = insert(JupiterBoat).values(**data)
#             stmt = stmt.on_conflict_do_update(
#                 index_elements=["document_id"],
#                 set_=data   
#             )
#             await session.execute(stmt)
#             await session.commit()
    
#     @staticmethod
#     async def bulk_upsert(boats: list[dict]):
#         """Bulk upsert boats data efficiently"""
#         if not boats:
#             return
            
#         async with boats_session() as session:
#             try:
#                 # Process in batches to avoid memory issues with large datasets
#                 batch_size = 100
#                 for i in range(0, len(boats), batch_size):
#                     batch = boats[i:i + batch_size]
                    
#                     for boat in batch:
#                         stmt = insert(JupiterBoat).values(**boat)
#                         stmt = stmt.on_conflict_do_update(
#                             index_elements=["document_id"],
#                             set_=boat
#                         )
#                         await session.execute(stmt)
                    
#                     # Commit each batch
#                     await session.commit()
#                     print(f"✅ Committed batch {i//batch_size + 1}: {len(batch)} boats")
                    
#             except Exception as e:
#                 await session.rollback()
#                 print(f"❌ Error during bulk upsert: {e}")
#                 raise