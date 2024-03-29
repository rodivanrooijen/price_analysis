from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func, select, literal_column, text, case
from sqlalchemy.sql import cast
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from datetime import date, datetime
from decimal import Decimal
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import base64
import io as BytesIO
import io

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
async def get_avg_prices_by_date(hotel: str, kamertype: str, db: Session = Depends(get_db)):
    """
    Endpoint to fetch average prices per date from the HotelData table.

    Returns:
    - A JSON response containing average prices by date.
    """

    if hotel is None or kamertype is None:
        return {"error": "Please provide both a hotel name and a room type."}
    
    avg_prices_by_date = {}

    # Extract the first word from the hotel name
    first_word = hotel.split()[0]

    # Infer number of adults and children based on room type
    if kamertype == "een_persoons_kamer":
        num_adults = 1
        num_children = 0
    elif kamertype == "twee_persoons_kamer":
        num_adults = 2
        num_children = 0
    elif kamertype == "Familiekamer":
        # Family room can have 1 or more children
        num_adults = 2  # Assuming family room has space for 2 adults
        num_children = 2  # Minimum 1 child, adjust as needed

    # Query the database to get average prices per date for the specified hotel and room type
    avg_prices = db.query(func.date(HotelData.checkin_datum), func.avg(HotelData.prijs)) \
                    .filter(HotelData.stad.like(f"{first_word}%")) \
                    .filter(HotelData.num_volwassenen == num_adults) \
                    .filter(HotelData.num_kinderen == num_children) \
                    .group_by(func.date(HotelData.checkin_datum)) \
                    .all()

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
    #adjusted_hotel_name = hotel.replace(" Hotel", "")

    # Find the index of the first space
    first_space_index = hotel.find(" ")

    # Remove everything from the first space onwards
    if first_space_index != -1:
        adjusted_hotel_name = hotel[:first_space_index]
    else:
        adjusted_hotel_name = hotel

    # Determine the number of adults based on the selected room type
    num_volwassenen = case(
        {
            kamertype == "een_persoons_kamer": 1,
            kamertype == "twee_persoons_kamer": 2,
            kamertype == "Familiekamer": 2
        },
        else_=1  # Default to 1 if room type is not recognized
    )

    num_kinderen = case(
        {
            kamertype == "een_persoons_kamer": 0,
            kamertype == "twee_persoons_kamer": 0,
            kamertype == "Familiekamer": 2
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
            HotelData.num_volwassenen == num_volwassenen,
            HotelData.num_kinderen == num_kinderen
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
            HotelData.num_volwassenen == num_volwassenen,
            HotelData.num_kinderen == num_kinderen
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




    #graphs
    # Query the database to fetch prices from the hoteldata table based on the selected date
    hotelgegevens = db.query(HotelData.prijs).filter(HotelData.checkin_datum == date).filter(HotelData.stad.like(f"{adjusted_hotel_name}%")).filter(HotelData.num_volwassenen == num_volwassenen).filter(HotelData.num_kinderen == num_kinderen).all()
    # Convert the query result to a pandas DataFrame for easier manipulation
    hotelgegevens = pd.DataFrame(hotelgegevens, columns=['prijs'])
    # Calculate average, mode, and median prices
    average_price1 = hotelgegevens['prijs'].mean()
    modus_price1 = hotelgegevens['prijs'].mode()[0]  # Mode may have multiple values, so take the first one
    median_price1 = hotelgegevens['prijs'].median()

    # Plot a bar chart for price distribution
    plt.figure(figsize=(8, 6))
    sns.histplot(hotelgegevens['prijs'], bins=40, kde=False, color="skyblue")
    plt.title("Price Distribution")
    plt.xlabel("Price")
    plt.ylabel("Number of hotels")

    # Add text annotations for average_price, median_price, and mode_price
    plt.axvline(x=average_price1, color='red', linestyle='--', linewidth=2, label=f'Average Price: €{average_price1:.2f}')
    plt.axvline(x=median_price1, color='green', linestyle='--', linewidth=2, label=f'Median: €{median_price1:.2f}')
    plt.axvline(x=modus_price1, color='blue', linestyle='--', linewidth=2, label=f'Mode: €{modus_price1:.2f}')

    plt.legend()  # Show legend with annotations

    # Save the plot to a BytesIO object
    image_stream = io.BytesIO()
    plt.savefig(image_stream, format="png")
    image_stream.seek(0)

    # Encode the image to base64 for embedding in HTML
    image_base64 = base64.b64encode(image_stream.read()).decode("utf-8")

    # Close the plot to release resources
    plt.close()

    #plot 2
    # Query the database to fetch hotel data
    hotelgegevens2 = db.query(HotelData.naam, HotelData.locatie, HotelData.prijs, HotelData.beoordeling).filter(HotelData.checkin_datum == date).filter(HotelData.stad.like(f"{adjusted_hotel_name}%")).filter(HotelData.num_volwassenen == num_volwassenen).filter(HotelData.num_kinderen == num_kinderen).all()

    # Convert the query result to a pandas DataFrame for easier manipulation
    hotelgegevens2 = pd.DataFrame(hotelgegevens2, columns=['naam', 'locatie', 'prijs', 'beoordeling'])

    # Data preprocessing
    hotelgegevens2['naam'] = hotelgegevens2['naam'].astype(str)
    hotelgegevens2['locatie'] = hotelgegevens2['locatie'].astype(str)
    hotelgegevens2['prijs'] = pd.to_numeric(hotelgegevens2['prijs'], errors='coerce').astype(pd.Int64Dtype())
    hotelgegevens2['beoordeling'] = hotelgegevens2['beoordeling'].astype(float)

    # Plotting
    unique_locations = hotelgegevens2['locatie'].unique()
    color_palette = sns.color_palette('Set1', n_colors=len(unique_locations))

    plt.figure(figsize=(8, 6))
    for i, location in enumerate(unique_locations):
        subset = hotelgegevens2[hotelgegevens2['locatie'] == location]
        scatter = plt.scatter(subset['prijs'], subset['beoordeling'], color=color_palette[i], alpha=0.7, label=location)

    plt.xlabel('Price', fontsize=12)
    plt.ylabel('Rating', fontsize=12)
    plt.title('Distribution of Prices, Ratings, and Locations of Hotels', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()

    # Save the plot to an in-memory buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plot_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Close the plot to release resources
    plt.close()
    return {
        "average_price": average_price,
        "mode_price": mode_price,
        "median_price": median_price,
        "current_price": current_price,
        "last_execution_time": last_execution_time,
        "image_base64": image_base64,
        "plot_base64": plot_base64
    }

@router.post("/update_price")
async def update_price(
    hotel: str,
    kamertype: str,
    date: str,
    new_price: float,
    db: Session = Depends(get_db)
):
    # Query the database to find the hotel price entry for the given hotel, room type, and date
    hotel_price = db.query(Prijzen).filter_by(
        hotel=hotel,
        kamertype=kamertype,
        datum=date
    ).first()

    if hotel_price is None:
        # If no entry is found, return an error
        raise HTTPException(status_code=404, detail="Hotel price entry not found")

    # Update the price with the new value
    hotel_price.prijs = new_price

    # Commit the changes to the database
    db.commit()

    # Return a success message
    return {"message": "Price updated successfully"}