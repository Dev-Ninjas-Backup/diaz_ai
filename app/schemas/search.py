from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pydantic import ConfigDict


# Dropdown option examples (you can expand later)
BOAT_TYPES = ["Sailboat", "Yacht", "Motorboat", "Fishing Boat", "Catamaran"]
ENGINE_COUNTS = ["01", "02", "03", "04"]
CABIN_COUNTS = ["01", "02", "03", "04", "05+"]
HEAD_COUNTS = ["01", "02", "03", "04", "05+"]


class FilterParams(BaseModel):
    """
    Filter parameters for CSV search - all optional.
    These will always show up in Swagger UI.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "boat_type": None,
                "make": None,
                "model": None,
                "build_year_min": None,
                "build_year_max": None,
                "price_min": None,
                "price_max": None,
                "length_min": None,
                "length_max": None,
                "beam_min": None,
                "beam_max": None,
                "number_of_engine": None,
                "number_of_cabin": None,
                "number_of_heads": None,
                "additional_unit": None
            }
        }
    )

    boat_type: Optional[str] = Field(
        default=None,
        description="Boat type filter",
        enum=BOAT_TYPES
    )
    make: Optional[str] = Field(default=None, description="Boat brand/manufacturer")
    model: Optional[str] = Field(default=None, description="Specific model name")
    build_year_min: Optional[int] = Field(default=None, description="Minimum build year")
    build_year_max: Optional[int] = Field(default=None, description="Maximum build year")
    price_min: Optional[float] = Field(default=None, description="Minimum price USD")
    price_max: Optional[float] = Field(default=None, description="Maximum price USD")
    length_min: Optional[float] = Field(default=None, description="Minimum length in ft")
    length_max: Optional[float] = Field(default=None, description="Maximum length in ft")
    beam_min: Optional[float] = Field(default=None, description="Minimum beam size in ft")
    beam_max: Optional[float] = Field(default=None, description="Maximum beam size in ft")
    number_of_engine: Optional[str] = Field(
        default=None,
        description="Number of engines",
        enum=ENGINE_COUNTS
    )
    number_of_cabin: Optional[str] = Field(
        default=None,
        description="Number of cabins",
        enum=CABIN_COUNTS
    )
    number_of_heads: Optional[str] = Field(
        default=None,
        description="Number of heads",
        enum=HEAD_COUNTS
    )
    additional_unit: Optional[str] = Field(
        default=None,
        description="Extra unit (e.g., Jet Ski)"
    )


class SearchRequest(BaseModel):
    """Main request model — filters always visible"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": None,
                "filters": {
                    "boat_type": None,
                    "price_max": None,
                    "make": None,
                    "model": None
                }
            }
        }
    )

    query: Optional[str] = Field(
        default=None,
        description="Optional free-text search"
    )
    filters: FilterParams = Field(
        default_factory=FilterParams,
        description="Structured filtering options"
    )


class SearchResponse(BaseModel):
    """Standard response for boat search"""

    success: bool = True
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    count: Optional[int] = None
