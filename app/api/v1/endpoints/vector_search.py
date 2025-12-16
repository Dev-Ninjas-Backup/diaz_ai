# app/api/v1/endpoints/ai_search.py

from fastapi import APIRouter
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import NamedVector
from app.config import configs
from app.services.chatbot.llms.open_ai_llm import OpenaiLLM
from pydantic import BaseModel

class AISearchRequest(BaseModel):
    query: str
    limit: int = 10

router = APIRouter()

# ✅ Load from config
QDRANT_URL = configs["vector"]["url"]
COLLECTION_NAME = configs["vector"]["collection_name_jupiter"]

# ✅ Clients (ASYNC)
qdrant = AsyncQdrantClient(url=QDRANT_URL)
embedder = OpenaiLLM().get_embeddings()


@router.post("/search/ai/boats")
async def ai_boat_search(payload: AISearchRequest):
    """
    AI semantic search for boats.
    Returns ONLY product data (no chatbot response).
    """

    # 1️⃣ Embed query (sync is OK here)
    query_vector = embedder.embed_query(payload.query)

    # 2️⃣ Search Qdrant (ASYNC ✅) - Use query_points instead of search
    hits = await qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=payload.limit,
        with_payload=True
    )

    # 3️⃣ Build product-only response
    results = []
    for hit in hits.points:  # ⚠️ Note: results are in .points attribute
        p = hit.payload or {}

        results.append({
            "id": p.get("document_id"),
            "make": p.get("make"),
            "model": p.get("model"),
            "year": p.get("model_year"),
            "price": p.get("price"),
            "length": p.get("length_overall"),
            "beam": p.get("beam"),
            "number_of_engines": p.get("number_of_engines"),
            "images": p.get("images"),
            "link": p.get("link"),
        })

    return {
        "query": payload.query,
        "count": len(results),
        "results": results,
    }