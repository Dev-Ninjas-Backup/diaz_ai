import os
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Any, Dict
from app.config import configs
from pydantic import BaseModel, Field
from threading import Lock
from app.services.AI_search_engine import SQLiteQueryAgent

router = APIRouter()

# Thread-safe singleton pattern
_agent_lock = Lock()
_florida_sqlite_agent: Optional[SQLiteQueryAgent] = None


class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")
    limit: Optional[int] = Field(10, description="Maximum number of results (default: 10, max: 100)")

class SearchResponse(BaseModel):
    counts: int
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    # success: bool
    # data: Optional[List[Dict[str, Any]]] = None
    # error: Optional[str] = None
    # count: int
    # sql_query: Optional[str] = None


def get_sqlite_agent() -> SQLiteQueryAgent:
    """Dependency to get the initialized agent."""
    if _florida_sqlite_agent is None:
        raise HTTPException(
            status_code=503,
            detail="SQLite Query Agent not initialized. Server starting up."
        )
    return _florida_sqlite_agent

def initialize_florida_sqlite_agent(db_path: str, table_name: str = "florida_boats") -> SQLiteQueryAgent:
    """Initialize the agent with thread safety."""
    global _florida_sqlite_agent
    
    with _agent_lock:
        if _florida_sqlite_agent is None:
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database file not found: {db_path}")
            
            _florida_sqlite_agent = SQLiteQueryAgent(db_path, table_name)
            print(f"✅ Florida SQLite agent initialized from: {db_path}")
    
    return _florida_sqlite_agent


@router.post("/florida_query", response_model=SearchResponse)
async def search_sqlite(request: SearchRequest, agent: SQLiteQueryAgent = Depends(get_sqlite_agent)):
    """
    Execute a natural language query on the SQLite database.
    """
    table_name = "florida_boats"
    result = agent.execute_query(table_name, request.query, limit=request.limit)
    
    return SearchResponse(**result)   