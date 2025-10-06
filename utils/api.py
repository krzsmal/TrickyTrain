from curl_cffi import requests
import json
    

API_BASE_URL = "https://api-gateway.intercity.pl" 
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0"
}


# Fetch train connections between two stations on a given date
def fetch_train_connections(date: str, departure_station_id1: str, arrival_station_id1: str) -> dict:
    url = f"{API_BASE_URL}/server/public/endpoint/Pociagi"

    payload = json.dumps({
        "urzadzenieNr": "956",
        "metoda": "wyszukajPolaczenia",
        "dataWyjazdu": f"{date} 00:00:00",
        "dataPrzyjazdu": f"{date} 23:59:59",
        "stacjaWyjazdu": departure_station_id1,
        "stacjaPrzyjazdu": arrival_station_id1,
        "stacjePrzez": [],
        "polaczeniaNajszybsze": 0,
        "liczbaPolaczen": 0,
        "czasNaPrzesiadkeMax": 1440,
        "liczbaPrzesiadekMax": 2,
        "polaczeniaBezposrednie": 1,
        "kategoriePociagow": [],
        "kodyPrzewoznikow": [],
        "rodzajeMiejsc": [],
        "typyMiejsc": [],
        "braille": 0,
        "czasNaPrzesiadkeMin": 3
    })

    response = requests.post(url, headers=HEADERS, data=payload, impersonate="chrome")

    if response.status_code != 200:
        raise ConnectionError(f"Żądanie API zakończone kodem {response.status_code} w fetch_train_connections")

    if "ACCESS DENIED" in response.text.upper():
        raise ConnectionError("Odmowa dostępu do API PKP Intercity w fetch_train_connections")

    try:
        return response.json()
    except json.JSONDecodeError:
        raise ValueError("Nieprawidłowa odpowiedź JSON z fetch_train_connections")


# Fetch details of a specific train
def fetch_train_details(train_category: str, train_number: str, departure_datetime: str, departure_station_id2: str, arrival_datetime: str, arrival_station_id2: str) -> dict:
    url = f"{API_BASE_URL}/grm/sklad/wbnet/{train_category}/{train_number}/{departure_datetime}/{departure_station_id2}/{arrival_datetime}/{arrival_station_id2}"
    payload = {}

    response = requests.get(url, headers=HEADERS, data=payload, impersonate="chrome")

    if response.status_code != 200:
        raise ConnectionError(f"Żądanie API zakończone kodem {response.status_code} w fetch_train_details")
    
    try:
        return response.json()
    except json.JSONDecodeError:
        raise ValueError("Nieprawidłowa odpowiedź JSON z fetch_train_details")


# Fetch the seat map of a specific carriage on a train as svg
def fetch_carriage_seat_map(train_category: str, train_number: str, carriage_number: str, carriage_type: str, departure_datetime: str, arrival_datetime: str, departure_station_id2: str, arrival_station_id2: str) -> requests.Response:
    url = f"{API_BASE_URL}/grm/wagon/svg/wbnet/{train_category}/{train_number}/{carriage_number}/{carriage_type}/{departure_datetime}/{arrival_datetime}/{departure_station_id2}/{arrival_station_id2}"
    payload = {}

    response = requests.get(url, headers=HEADERS, data=payload, impersonate="chrome")

    if response.status_code != 200:
        raise ConnectionError(f"Żądanie API zakończone kodem {response.status_code} w fetch_carriage_seat_map")

    return response


# Fetch the route of a specific train
def fetch_train_route(departure_datetime: str, departure_station_id1: str, arrival_station_id1: str, train_number: str) -> dict:
    url = f"{API_BASE_URL}/server/public/endpoint/Pociagi"

    payload = json.dumps({
        "dataWyjazdu": departure_datetime,
        "stacjaWyjazdu": departure_station_id1,
        "stacjaPrzyjazdu": arrival_station_id1,
        "numerPociagu": train_number,
        "urzadzenieNr": "956",
        "metoda": "pobierzTrasePrzejazdu"
    })

    response = requests.post(url, headers=HEADERS, data=payload, impersonate="chrome")

    if response.status_code != 200:
        raise ConnectionError(f"Żądanie API zakończone kodem {response.status_code} w fetch_train_route")

    if "ACCESS DENIED" in response.text.upper():
        raise ConnectionError("Odmowa dostępu do API PKP Intercity w fetch_train_route")

    try:
        return response.json()
    except json.JSONDecodeError:
        raise ValueError("Nieprawidłowa odpowiedź JSON z fetch_train_route")


# Fetch station ids
def fetch_station_ids(station_name: str) -> tuple[str, str]:
    url = f"https://www.intercity.pl/station/get/?q={station_name}"
    payload = {}

    response = requests.get(url, headers=HEADERS, data=payload, impersonate="chrome")

    if response.status_code != 200:
        raise ConnectionError(f"Żądanie API zakończone kodem {response.status_code} w fetch_station_ids")
    
    try:
        for station in response.json():
            if station["n"].lower() == station_name.lower():
                return (station["h"], station["e"])
        raise ValueError(f"Nie znaleziono stacji {station_name} w fetch_station_ids")
    except json.JSONDecodeError:
        raise ValueError("Nieprawidłowa odpowiedź JSON z fetch_station_ids")
    

# Fetch stations
def fetch_stations(station_name: str) -> list[str]:
    url = f"https://www.intercity.pl/station/get/?q={station_name}"
    payload = {}

    response = requests.get(url, headers=HEADERS, data=payload, impersonate="chrome")

    if response.status_code != 200:
        raise ConnectionError(f"Żądanie API zakończone kodem {response.status_code} w fetch_stations")
    
    try:
        stations = response.json()
        station_names = [station["n"] for station in stations if "dowolna" not in station["n"].lower()]
        station_names.sort(key=lambda s: (not s.lower().startswith(station_name.lower()), s))
        return station_names

    except json.JSONDecodeError:
        raise ValueError("Nieprawidłowa odpowiedź JSON z fetch_stations")