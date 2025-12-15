from pydantic import BaseModel
from typing import Optional

class BoatFilterRequest(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None

    year_from: Optional[int] = None
    year_to: Optional[int] = None

    price_min: Optional[float] = None
    price_max: Optional[float] = None

    length_min: Optional[float] = None
    length_max: Optional[float] = None

    beam_min: Optional[float] = None
    beam_max: Optional[float] = None

    number_of_engines: Optional[int] = None

    additional_unit: Optional[str] = None  # "Jet ski"
