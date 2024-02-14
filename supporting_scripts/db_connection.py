
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from datetime import datetime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm.session import Session
import urllib.parse
from typing import Union
from pydantic import BaseModel

# Azure MySQL connection details
azure_host = "yc2401data.mysql.database.azure.com"
azure_username = "yc2401"
azure_password = "abcd1234ABCD!@#$"
azure_database = "hotel"

# Construct Azure connection URL
azure_connection_url = f"mysql+mysqlconnector://{azure_username}:{urllib.parse.quote_plus(azure_password)}@{azure_host}/{azure_database}"
print(azure_connection_url)
# Replace existing URL with Azure connection URL
DATABASE_URL = azure_connection_url

# Local database
#DATABASE_URL = "mysql+mysqlconnector://root:@localhost/scraping"

# Database setup using SQLite (you can replace it with your preferred database)
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class HotelData(Base):
    __tablename__ = "hotel_data"

    id = Column(Integer, primary_key=True, index=True)
    stad = Column(String(255), index=True)
    checkin_datum = Column(String(20))  # Specify the length here (adjust as needed)
    checkout_datum = Column(String(20))  # Specify the length here (adjust as needed)
    num_volwassenen = Column(Integer)
    num_kinderen = Column(Integer)
    naam = Column(String(255))  # Add columns for name, location, price, and rating
    locatie = Column(String(255))
    prijs = Column(Float)
    beoordeling = Column(Float)
    last_execution_time = Column(DateTime)

class Prijzen(Base):
    __tablename__ = "prijzen"

    id = Column(Integer, primary_key=True, index=True)
    hotel = Column(String(255), index=True)
    kamertype = Column(String(255))
    prijs = Column(Float)
    datum = Column(DateTime)


class LocationRating(Base):
    __tablename__ = "LocationRating"

    ID = Column(Integer, primary_key=True, index=True)
    Nuts2Code = Column(String(255))
    Country = Column(String(255))
    LocationName = Column(String(255))
    NumAccoms = Column(Float)
    NetOccupancyRate = Column(Float)
    ArrivalsAccommodation = Column(Float)
    ExpenditureAccomodation = Column(Float)
    ExpenditureTrip = Column(Float)
    HicpCountry = Column(Float)
    LastUpdated  = Column(DateTime, default=datetime.utcnow)


# Define the Pydantic model for request data
class LocationRatingCreate(BaseModel):
    nuts_2_code: Union[str, None] = None
    country: Union[str, None] = None
    location_name: Union[str, None] = None
    num_accoms: Union[float, None] = None
    net_ccupancy_rate: Union[float, None] = None
    arrivals_accommodation: Union[float, None] = None
    expenditure_accomodation: Union[float, None] = None
    expenditure_trip: Union[float, None] = None
    hicp_country: Union[float, None] = None
    last_updated: datetime

Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Helper function to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()