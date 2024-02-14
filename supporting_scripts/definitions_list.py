from fastapi import Query

# Global variables
hotelgegevens = None
last_execution_time = None
last_execution_status = None
stad = None
checkin_datum = None
checkout_datum = None
num_volwassenen = None
num_kinderen = None
max_paginas = None

def get_input_parameters(
    stad: str = Query("Maastricht", description="The city name"),
    checkin_datum: str = Query("2024-02-14", description="Check-in date"),
    num_volwassenen: int = Query(2, description="Number of adults"),
    num_kinderen: int = Query(0, description="Number of children"),
    max_paginas: int = Query(2, description="Maximum pages to scrape"),
):
    return stad, checkin_datum, num_volwassenen, num_kinderen, max_paginas