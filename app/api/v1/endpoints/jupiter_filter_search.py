
from fastapi import APIRouter, Query
from typing import List, Any, Optional
from app.schemas.boat_filter import BoatFilterRequest
from app.repositories.jupiter_boats_hub import BoatsHub
import json

router = APIRouter()

def convert_to_json(value: Any) -> Any:
    """Convert JSON string to Python object if needed."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value

@router.post("/boats")
async def filter_boats(filters: BoatFilterRequest, limit: Optional[int] = Query(10, ge=1)):
    """
    Fetch boats based on filters, return JSON, limited to `limit` results.
    Default limit is 10.
    """
    boats = await BoatsHub.filter_boats(filters)  # list of objects/dicts

    wanted_columns = [
        'document_id','make','model','model_year','price','location','images','link'
    ]

    results = []
    for boat in boats:
        boat_dict = boat.__dict__ if not isinstance(boat, dict) else boat
        boat_json = {}
        for k in wanted_columns:
            value = boat_dict.get(k)
            # Convert JSON string fields into dict/list
            if k in ['engines', 'location', 'images'] and isinstance(value, str):
                value = convert_to_json(value)
            boat_json[k] = value
        results.append(boat_json)

    # Apply the limit
    limited_results = results[:limit]

    return {
        "count": len(limited_results),
        "results": limited_results
    }














# from fastapi import APIRouter
# from app.schemas.boat_filter import BoatFilterRequest
# from app.repositories.jupiter_boats_hub import BoatsHub

# router = APIRouter()

# @router.post("/boats")
# async def filter_boats(filters: BoatFilterRequest):
#     boats = await BoatsHub.filter_boats(filters)

#     return {
#         "count": len(boats),
#         "results": [
#             {
#                 "id": boat.document_id,
#                 "make": boat.make,
#                 "model": boat.model,
#                 "year": boat.model_year,
#                 "price": boat.price,
#                 "length": boat.length_overall,
#                 "beam": boat.beam,
#                 "engines": boat.engines,
#                 "number_of_engines": boat.number_of_engines,
#                 "location": boat.location,
#                 "city": boat.city,
#                 "images": boat.images,
#                 "link": boat.link,
#                 "general_description": boat.general_description,
#                 "additional_description": boat.additional_description,
#             }
#             for boat in boats
#         ]
#     }
