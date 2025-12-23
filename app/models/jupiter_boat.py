from sqlalchemy import Column, Integer, String, Float, Text
from app.db.boats_db import BoatsBase

class JupiterBoat(BoatsBase):
    __tablename__ = "jupiter_boats"

    document_id = Column(String, primary_key=True, index=True)

    source = Column(String)

    make = Column(String, index=True)
    model = Column(String, index=True)
    model_year = Column(Integer, index=True)

    price = Column(Float, index=True)

    nominal_length = Column(Float)
    length_overall = Column(Float)
    beam = Column(Float)

    number_of_engines = Column(Integer)
    total_engine_power = Column(Float)

    location = Column(Text)
    city = Column(String, index=True)

    general_description = Column(Text)
    additional_description = Column(Text)

    engines = Column(Text)
    images = Column(Text)

    link = Column(String)
