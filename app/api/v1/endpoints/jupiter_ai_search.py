
from typing import Optional, List, Dict, Any
from app.services.jupiter_AI_search import SQLiteQueryAgent
from app.config import configs
from app.models.boat import Boat
import os

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from threading import Lock
from app.services.chat_storage_service import ChatStorageService

storage = ChatStorageService()

router = APIRouter()

# Thread-safe singleton pattern
_agent_lock = Lock()
_jupiter_sqlite_agent: Optional[SQLiteQueryAgent] = None


class SearchRequest(BaseModel):
    user_id: str = Field(..., description="User identifier for chat session")
    query: str = Field(..., description="Natural language search query")
    limit: Optional[int] = Field(10, description="Maximum number of results (default: 10, max: 100)")


class SearchResponse(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    count: int
    sql_query: Optional[str] = None


def get_sqlite_agent() -> SQLiteQueryAgent:
    """Dependency to get the initialized agent."""
    if _jupiter_sqlite_agent is None:
        raise HTTPException(
            status_code=503,
            detail="SQLite Query Agent not initialized. Server starting up."
        )
    return _jupiter_sqlite_agent


def initialize_jupiter_sqlite_agent(db_path: str, table_name: str = "boats") -> SQLiteQueryAgent:
    """Initialize the agent with thread safety."""
    global _jupiter_sqlite_agent
    
    with _agent_lock:
        if _jupiter_sqlite_agent is None:
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database file not found: {db_path}")
            
            _jupiter_sqlite_agent = SQLiteQueryAgent(db_path, table_name)
            print(f"✅ Jupiter SQLite agent initialized from: {db_path}")
    
    return _jupiter_sqlite_agent


@router.post("/query", response_model=SearchResponse)
async def search_sqlite(
    request: SearchRequest,
    agent: SQLiteQueryAgent = Depends(get_sqlite_agent)
):
    """
    Execute a natural language query on the boats database.
    
    Returns first 10 results by default.
    
    Example queries:
    - "Show me boats under $500,000"
    - "Find Freeman boats from 2024"
    - "Boats in Miami with 2 engines"
    - "Most expensive boats"
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query must be provided.")
    
    # Enforce limit constraints
    limit = request.limit or 10
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100.")
    
    #add user message to db
    await storage.save_chat_message(request.user_id, "user", request.query)
    
    result = agent.execute_query(request.query, limit=limit)

    #save query result to db
    if result["success"] and result["data"]:
        # Extract make + model only
        make_model_list = [f"{item.get('make', '')} {item.get('model', '')}".strip() for item in result["data"]]

        # Convert to a single string if needed, e.g., comma-separated
        message = f"Found {result['count']} results: " + ", ".join(make_model_list)
        
        # Save to DB
        await storage.save_chat_message(request.user_id, "assistant", message)

    return SearchResponse(**result)