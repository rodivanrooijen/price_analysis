from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from datetime import date, datetime

from supporting_scripts.db_connection import get_db, HotelData, Prijzen

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/price_analysis", response_class=HTMLResponse)
async def price_analysis(request: Request, db: Session = Depends(get_db)):
    # Ophalen van unieke waarden voor hotels en kamertypes uit de tabel "prijzen"
    hotels = db.query(Prijzen.hotel).distinct().all()
    kamertypes = db.query(Prijzen.kamertype).distinct().all()

    hotels = [hotel[0] for hotel in hotels]
    kamertypes = [kamertype[0] for kamertype in kamertypes]

    # Fetch prices from the database
    prices = db.query(Prijzen.hotel, Prijzen.kamertype, Prijzen.prijs, Prijzen.datum).all()

    # Organize prices by hotel and room type
    prices_by_hotel_and_room = {}
    for price in prices:
        hotel = price[0]
        kamertype = price[1]
        prijs = price[2]
        datum = price[3].strftime("%Y-%m-%d")

        if hotel not in prices_by_hotel_and_room:
            prices_by_hotel_and_room[hotel] = {}

        if kamertype not in prices_by_hotel_and_room[hotel]:
            prices_by_hotel_and_room[hotel][kamertype] = {}

        prices_by_hotel_and_room[hotel][kamertype][datum] = prijs

    return templates.TemplateResponse(
        "price_analysis.html",
        {"request": request, "hotels": hotels, "kamertypes": kamertypes, "prices_by_date": prices_by_hotel_and_room},
    )

# Define the new endpoint
@router.get("/get_prices_by_date")
async def get_prices_by_date(hotel: str, kamertype: str, db: Session = Depends(get_db)):
    """
    Endpoint to fetch prices based on the selected hotel and kamertype.

    Parameters:
    - hotel: The selected hotel from the dropdown.
    - kamertype: The selected kamertype from the dropdown.

    Returns:
    - A JSON response containing prices by date.
    """
    prices_by_date = {}

    # Query the database to get prices based on the selected hotel and kamertype
    prices = db.query(Prijzen.datum, Prijzen.prijs).filter_by(hotel=hotel, kamertype=kamertype).all()

    for date, price in prices:
        # Format the date if needed
        formatted_date = date.strftime("%Y-%m-%d")
        prices_by_date[formatted_date] = price

    return prices_by_date

# Endpoint to fetch average prices per date from the HotelData table
@router.get("/get_avg_prices_by_date")
async def get_avg_prices_by_date(db: Session = Depends(get_db)):
    """
    Endpoint to fetch average prices per date from the HotelData table.

    Returns:
    - A JSON response containing average prices by date.
    """
    avg_prices_by_date = {}

    # Query the database to get average prices per date
    avg_prices = db.query(func.date(HotelData.checkin_datum), func.avg(HotelData.prijs)).group_by(func.date(HotelData.checkin_datum)).all()

    for date_str, avg_price in avg_prices:
        # Convert string date to datetime object
        if isinstance(date_str, date):  # Check if date_str is already a date object
            formatted_date = date_str.strftime("%Y-%m-%d")
        else:
            formatted_date = datetime.strptime(date_str, "%Y-%m-%d").date().strftime("%Y-%m-%d")

        avg_prices_by_date[formatted_date] = avg_price

    return avg_prices_by_date