import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import random

def scrape_booking_data(stad, checkin_datum, checkout_datum, num_volwassenen, num_kinderen, max_paginas):
    # Initialiseer een lijst om gegevens van alle pagina's op te slaan
    alle_hotelgegevens = []

    # Basis URL voor Booking.com
    basis_url = 'https://www.booking.com/searchresults.nl.html'

    # Headers voor HTTP-verzoeken // ANTI-SCRAPING MAATREGELEN
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
        'Accept-Language': 'nl-NL, nl;q=0.5'
    }

    # Loop door meerdere pagina's
    for pagina_nummer in range(1, max_paginas + 1):
        # Bereken de offset voor de huidige pagina
        offset = (pagina_nummer - 1) * 25

        # Parameters voor de URL
        params = {
            'ss': stad,
            'ssne': stad,
            'ssne_untouched': stad,
            'label': 'gen173nr-1BCAEoggI46AdIM1gEaKkBiAEBmAEcuAEXyAEM2AEB6AEBiAIBqAIDuALsqKStBsACAdICJDE1MTQyOTBmLWU3ZTMtNGQ5NS04MDI2LWQ0Yzg3YTEyOGVkOdgCBeACAQ',
            'sid': '0ce72b9818a4078dc8ab51375ff64dcc',
            'aid': '304142',
            'lang': 'nl',
            'sb': '1',
            'src_elem': 'sb',
            'src': 'searchresults',
            'checkin': checkin_datum,
            'checkout': checkout_datum,
            'group_adults': num_volwassenen,
            'no_rooms': '1',
            'group_children': num_kinderen,
            'sb_travel_purpose': 'leisure',
            'selected_currency': 'EUR',
            'offset': offset  # Stel de offset in voor paginering
        }

        # Stuur een HTTP GET-verzoek naar de Booking.com URL met de bijgewerkte parameters
        response = requests.get(basis_url, params=params, headers=headers)

        soup = BeautifulSoup(response.text, 'html.parser')
        hotels = soup.find_all('div', {'data-testid': 'property-card'})

        # Als er geen hotels zijn gevonden op de huidige pagina, stop dan de lus
        if not hotels:
            break

        # Loop door de hotel-elementen en haal de gewenste gegevens op
        for hotel in hotels:
            # Haal de hotelnaam, locatie, prijs en beoordeling op
            naam_element = hotel.find('div', {'data-testid': 'title'})
            naam = naam_element.text.strip()

            locatie_element = hotel.find('span', {'data-testid': 'address'})
            locatie = locatie_element.text.strip()

            prijs_element = hotel.find('span', {'data-testid': 'price-and-discounted-price'})
            prijs = ''.join(filter(str.isdigit, prijs_element.text.strip()))
            
            beoordeling_element = hotel.find('div', {'class': 'a3b8729ab1 d86cee9b25'})
            beoordeling = beoordeling_element.text.strip()

            # Voeg hotelgegevens toe aan alle_hotelgegevens
            alle_hotelgegevens.append({
                'naam': naam,
                'locatie': locatie,
                'prijs': prijs,
                'beoordeling': beoordeling
            })

        # Voeg een vertraging toe om anti-scraping maatregelen te omzeilen
        # Generate a random sleep time between 2 and 10 seconds
        sleep_time = random.randint(2, 5)
        time.sleep(sleep_time)

    # Maak een DataFrame van de gecombineerde gegevens van alle pagina's
    hotels_df = pd.DataFrame(alle_hotelgegevens)
    return hotels_df