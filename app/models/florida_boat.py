from sqlalchemy import Column, Integer, String, Float
from app.db.boats_db import BoatsBase


class FloridaBoat(BoatsBase):
    __tablename__ = "florida_boats"


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

    location = Column(String, index=True)
    city = Column(String, index=True)

    general_description = Column(String)
    additional_description = Column(String)

    engines= Column(String)
    images = Column(String)

    link = Column(String)