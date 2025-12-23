from fastapi import APIRouter
from app.schemas.boat_filter import BoatFilterRequest
from app.repositories.jupiter_boats_hub import BoatsHub

router = APIRouter()

@router.post("/boats")
async def filter_boats(filters: BoatFilterRequest):
    boats = await BoatsHub.filter_boats(filters)

    return {
        "count": len(boats),
        "results": [
            {
                "id": boat.document_id,
                "make": boat.make,
                "model": boat.model,
                "year": boat.model_year,
                "price": boat.price,
                "length": boat.length_overall,
                "beam": boat.beam,
                "engines": boat.engines,
                "number_of_engines": boat.number_of_engines,
                "location": boat.location,
                "city": boat.city,
                "images": boat.images,
                "link": boat.link,
                "general_description": boat.general_description,
                "additional_description": boat.additional_description,
            }
            for boat in boats
        ]
    }

