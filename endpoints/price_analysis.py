from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func, select, literal_column, text, case
from sqlalchemy.sql import cast
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from datetime import date, datetime
from decimal import Decimal

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

        avg_prices_by_date[formatted_date] = round(avg_price)

    return avg_prices_by_date



@router.get("/get_prices_by_date_and_type")
async def get_prices_by_date_and_type(date: str, hotel: str, kamertype: str, db: Session = Depends(get_db)):
    """
    Endpoint to fetch average, mode, and median prices for a specific date, hotel, and room type.

    Parameters:
    - date: The selected date.
    - hotel: The selected hotel.
    - kamertype: The selected room type.

    Returns:
    - A JSON response containing the average, mode, and median prices.
    """
    # Adjust the hotel name to search in the 'stad' column
    adjusted_hotel_name = hotel.replace(" Hotel", "")

    # Determine the number of adults based on the selected room type
    num_volwassenen = case(
        {
            kamertype == "een_persoons_kamer": 1,
            kamertype == "twee_persoons_kamer": 2,
            kamertype == "familiekamer": 2
        },
        else_=1  # Default to 1 if room type is not recognized
    )

    # Query to calculate average, mode, and median prices for the selected date, hotel, and room type
    query = (
        db.query(
            func.avg(HotelData.prijs).label("average_price"),
            func.count(HotelData.prijs).label("count")
        )
        .filter(
            HotelData.stad == adjusted_hotel_name,
            HotelData.checkin_datum == date,
            HotelData.num_volwassenen == num_volwassenen
        )
        .group_by(HotelData.stad, HotelData.checkin_datum, num_volwassenen)
    )

    # Execute the query
    result = query.first()

    # Extract average price from the query result
    average_price = round(result[0]) if result[0] else None



    # Query to calculate the mode
    mode_query = (
        db.query(HotelData.prijs, func.count(HotelData.prijs).label("price_count"))
        .filter(
            HotelData.stad == adjusted_hotel_name,
            HotelData.checkin_datum == date,
            HotelData.num_volwassenen == num_volwassenen
        )
        .group_by(HotelData.prijs)
        .order_by(func.count(HotelData.prijs).desc())
        .limit(1)
        .first()
    )

    mode_price = mode_query[0] if mode_query else None

    median_price = round((average_price + mode_price) / 2)

    # Fetch current price from the Prijzen table
    current_price = db.query(Prijzen.prijs).filter_by(hotel=hotel, kamertype=kamertype, datum=date).scalar()

    # Query to fetch maximum last execution time for the selected date, hotel, and room type
    last_execution_time = db.query(func.max(HotelData.last_execution_time)).filter(
        HotelData.stad == adjusted_hotel_name,
        HotelData.checkin_datum == date,
        HotelData.num_volwassenen == num_volwassenen
    ).scalar()

    # If max_execution_time is None, provide a default value
    if last_execution_time is None:
        last_execution_time = datetime.now()

    return {
        "average_price": average_price,
        "mode_price": mode_price,
        "median_price": median_price,
        "current_price": current_price,
        "last_execution_time": last_execution_time
    }