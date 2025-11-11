from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from uuid import uuid4

from app.services.search_engine.search import SearchEngine
from app.schemas.schema import SearchModel
from app.utils.logger import get_logger


logger = get_logger(__name__)

router = APIRouter()


async def get_search_engine():
    search_engine = SearchEngine()
    search_engine.es = await search_engine._init_search_engine()
    return search_engine


@router.post("/search_boat")
async def search_boat(
    request: SearchModel, boat_search: SearchEngine = Depends(get_search_engine)
):
    try:
        logger.info("Searching boat.....")
        response = await boat_search.search_boat(
            query=request.query, k=request.k, es=boat_search.es
        )
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        logger.error(f"Error while searching boat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
