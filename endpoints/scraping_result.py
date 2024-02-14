import base64
import datetime
from io import BytesIO
from fastapi import APIRouter, Depends, Query, Request, FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from matplotlib import pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from datetime import datetime, timedelta
import pandas as pd
import os

from supporting_scripts import func_scraping, definitions_list
from supporting_scripts.db_connection import get_db, HotelData, Prijzen

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/scrapingresult")
async def scrapingresult(
    request: Request,
    input_params: tuple[str, str, int, int, int] = Depends(definitions_list.get_input_parameters),
):
    global last_execution_time, last_execution_status, hotelgegevens, stad, checkin_datum, checkout_datum, num_volwassenen, num_kinderen, max_paginas

    # Extract values from the tuple
    stad, checkin_datum, num_volwassenen, num_kinderen, max_paginas = input_params

    checkin_datum = datetime.strptime(checkin_datum, "%Y-%m-%d")
    checkout_datum = (checkin_datum + timedelta(days=1))
    checkin_datum = checkin_datum.strftime("%Y-%m-%d")
    checkout_datum = checkout_datum.strftime("%Y-%m-%d")
    # max_paginas = 2

    # Use the user-provided values
    stad = stad
    checkin_datum = checkin_datum
    checkout_datum = checkout_datum
    num_volwassenen = num_volwassenen
    num_kinderen = num_kinderen
    max_paginas = max_paginas

    hotelgegevens = func_scraping.scrape_booking_data(stad, checkin_datum, checkout_datum, num_volwassenen, num_kinderen, max_paginas)

    hotelgegevens['naam'] = hotelgegevens['naam'].astype(str)
    hotelgegevens['locatie'] = hotelgegevens['locatie'].astype(str)
    hotelgegevens['prijs'] = pd.to_numeric(hotelgegevens['prijs'], errors='coerce').astype(pd.Int64Dtype())
    hotelgegevens['beoordeling'] = hotelgegevens['beoordeling'].str.replace(',', '.').astype(float)

    last_execution_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Bijwerken van de uitvoeringsstatus
    if hotelgegevens.empty:
        last_execution_status = "Old data from data archive"
    else:
        last_execution_status = "Live"

    unique_locations = hotelgegevens['locatie'].unique()
    color_palette = sns.color_palette('Set1', n_colors=len(unique_locations))

    plt.figure(figsize=(8, 6))
    for i, location in enumerate(unique_locations):
        subset = hotelgegevens[hotelgegevens['locatie'] == location]
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
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plot_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")


    #Bereken gemiddelde, modus en mediaan van de prijzen
    average_price = hotelgegevens['prijs'].mean()
    modus_price = hotelgegevens['prijs'].agg(pd.Series.mode)
    modus_price = modus_price[0]
    median_price = hotelgegevens['prijs'].median()

    # Plot a bar chart for price distribution
    plt.figure(figsize=(8, 6))
    sns.histplot(hotelgegevens['prijs'], bins=40, kde=False, color="skyblue")
    plt.title("Price Distribution")
    plt.xlabel("Price")
    plt.ylabel("Number of hotels")

    # Add text annotations for average_price and median_price
    plt.axvline(x=average_price, color='red', linestyle='--', linewidth=2, label=f'Average Price: €{average_price:.2f}')
    plt.axvline(x=median_price, color='green', linestyle='--', linewidth=2, label=f'Median: €{median_price:.2f}')
    plt.axvline(x=modus_price, color='blue', linestyle='--', linewidth=2, label=f'Modus: €{modus_price:.2f}')

    plt.legend()  # Show legend with annotations

    # Save the plot to a BytesIO object
    image_stream = BytesIO()
    plt.savefig(image_stream, format="png")
    image_stream.seek(0)

    # Encode the image to base64 for embedding in HTML
    image_base64 = base64.b64encode(image_stream.read()).decode("utf-8")

    # Close the plot to release resources
    plt.close()

    return templates.TemplateResponse("result.html", {"request": request, 
                                                      "stad" : stad,
                                                      "checkin_datum": checkin_datum,
                                                      "checkout_datum": checkout_datum,
                                                      "num_volwassenen": num_volwassenen,
                                                      "num_kinderen": num_kinderen,
                                                      "max_paginas": max_paginas,
                                                      "gemiddelde_prijs": average_price,
                                                      "modus_prijs": modus_price, 
                                                      "mediaan_prijs": median_price,
                                                      "plot_base64": plot_base64,
                                                      "image_base64": image_base64,
                                                      "last_execution_time": last_execution_time,
                                                      "last_execution_status": last_execution_status})

@router.post("/save_data")
async def save_data():
    global hotelgegevens

    if hotelgegevens is not None and not hotelgegevens.empty:
        # Voeg inputparameters toe aan DataFrame
        hotelgegevens["Stad"] = stad
        hotelgegevens["Checkin_datum"] = checkin_datum
        hotelgegevens["Checkout_datum"] = checkout_datum
        hotelgegevens["Num_volwassenen"] = num_volwassenen
        hotelgegevens["Num_kinderen"] = num_kinderen

        # Voeg een datum/tijdstempelkolom toe
        hotelgegevens["Datum_tijd_stempel"] = datetime.now()

        # Specify the directory where you want to save the CSV file
        save_directory = "csv_data"  # Replace with your folder path

        # Ensure the directory exists, create it if not
        os.makedirs(save_directory, exist_ok=True)

        # Generate the full path for the CSV file
        filename = f"hotel_data_{stad}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        filepath = os.path.join(save_directory, filename)

        # Sla de gegevens op als CSV-bestand
        hotelgegevens.to_csv(filepath, index=False)

        # Stuur het CSV-bestand als download naar de gebruiker
        content = hotelgegevens.to_csv(index=False)
        response = StreamingResponse(iter([content]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    else:
        return {"message": "Geen data beschikbaar om op te slaan."}
    
@router.post("/load_data")
async def load_data(
    input_params: tuple[str, str, int, int, int] = Depends(definitions_list.get_input_parameters),
    db: Session = Depends(get_db)
):
    global hotelgegevens

    # Extract values from the tuple
    stad, checkin_datum, num_volwassenen, num_kinderen, max_paginas = input_params

    if hotelgegevens is not None and not hotelgegevens.empty:
        for _, row in hotelgegevens.iterrows():
            # Check if a matching row exists in the database
            existing_hotel = db.query(HotelData).filter_by(
                naam=row['naam'],
                checkout_datum=checkout_datum,
                checkin_datum=checkin_datum,
                num_volwassenen=num_volwassenen,
                num_kinderen=num_kinderen
            ).first()

            if existing_hotel:
                # Update the 'prijs' and 'beoordeling' of the existing row
                existing_hotel.prijs = row['prijs']
                existing_hotel.beoordeling = row['beoordeling']
                existing_hotel.last_execution_time = datetime.now()
            else:
                # Insert a new row
                db_data = HotelData(
                    stad=stad,
                    checkin_datum=checkin_datum,
                    checkout_datum=checkout_datum,
                    num_volwassenen=num_volwassenen,
                    num_kinderen=num_kinderen,
                    last_execution_time=datetime.now(),
                    naam=row['naam'],
                    locatie=row['locatie'],
                    prijs=row['prijs'],
                    beoordeling=row['beoordeling']
                )
                db.add(db_data)

        db.commit()
        return JSONResponse(content={"message": "Data successfully loaded into the database."})
    else:
        return JSONResponse(content={"message": "No data available to load into the database."})
    