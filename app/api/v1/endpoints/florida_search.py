from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search import CSVQueryAgent

router = APIRouter()

# Global agent instance - initialized on startup
_agent: Optional[CSVQueryAgent] = None


def get_agent() -> CSVQueryAgent:
    """Get or initialize the CSV Query Agent."""
    global _agent
    if _agent is None:
        raise HTTPException(
            status_code=500,
            detail="CSV Query Agent not initialized. Please initialize it first."
        )
    return _agent


def initialize_florida_agent(csv_path: str = "database\process_csv_data_florida\process_data.csv"):
    """Initialize the CSV Query Agent with a CSV file."""
    global _agent
    try:
        _agent = CSVQueryAgent(csv_path)
        return _agent
    except Exception as e:
        # Raise regular exception for startup event, HTTPException is for route handlers
        raise Exception(f"Failed to initialize CSV agent: {str(e)}")


@router.post("/florida_query", response_model=SearchResponse)
async def search_csv(request: SearchRequest, agent: CSVQueryAgent = Depends(get_agent)):
    """
    Execute a natural language query on the CSV file with optional filters.
    
    Both query and filters are optional, but at least one must be provided.
    
    - **query**: Optional natural language query to search the CSV (e.g., "Show me boats under 500000")
    - **filters**: Optional filter parameters (applied FIRST before AI query):
      - boat_type: Boat type filter
      - make: Make filter
      - model: Model filter
      - build_year_min/max: Build year range
      - price_min/max: Price range
      - length_min/max: Length range in feet
      - beam_min/max: Beam size range in feet
      - number_of_engine: Number of engines
      - number_of_cabin: Number of cabins
      - number_of_heads: Number of heads
      - additional_unit: Additional unit filter
    
    Behavior:
    - If only filters provided: returns filtered results without AI query
    - If only query provided: runs AI query on full dataset
    - If both provided: applies filters first, then runs AI query on filtered results
    - Filters are prioritized and applied before the AI query runs.
    """
    try:
        # Validate that at least one of query or filters is provided
        has_query = request.query and request.query.strip()
        
        # Convert filters to dict, excluding None values
        filters_dict = request.filters.model_dump(exclude_none=True)
        has_filters = bool(filters_dict)  # Check if any filters have values
        
        if not has_query and not has_filters:
            raise HTTPException(
                status_code=400,
                detail="At least one of 'query' or 'filters' must be provided"
            )
        
        # Pass None if no filters, otherwise pass the filters dict
        result = agent.execute_query(request.query, filters=filters_dict if has_filters else None)
        return SearchResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )


