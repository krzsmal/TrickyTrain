from utils import fetch_station_ids, fetch_train_connections, fetch_train_details, fetch_carriage_seat_map, fetch_train_route
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime
import concurrent.futures
import re


# Format datetime string into a compact format (YYYYMMDDHHMM)
def format_datetime_compact(datetime_str: str) -> str:
    try:
        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d%H%M")
    except ValueError:
        raise ValueError(f"Invalid datetime format: {datetime_str}")


# Extract carriage type from the train details, return a dictionary of carriage numbers with their types
def extract_carriage_type(train_info: dict) -> dict[str, str]:
    carriages = set(str(carriage) for carriage in train_info.get("klasa2"))
    carriages_types = {}
    for carriage in train_info.get("wagonySchemat"):
        if carriage in carriages:
            carriages_types[carriage] = train_info.get("wagonySchemat").get(carriage)

    return carriages_types


# Generate the Intercity train ticket booking link
def get_intercity_link(date: str, departure_station_id1: str, arrival_station_id1: str, time: str, ticket: str = "1010") -> str:
    return f"https://ebilet.intercity.pl/wyszukiwanie?dwyj={date}&swyj={departure_station_id1}&sprzy={arrival_station_id1}&polbez=1&time={time}&ticket100={ticket}"


# Parse the available seats from an SVG carriage seat map, return a dictionary of available seats with their types
def parse_available_seats(carriage_seats: str) -> dict[str, str]:
    root = ET.fromstring(carriage_seats)

    namespace = {
        "svg": "http://www.w3.org/2000/svg",
        "eic": "http://www.intercity.pl/eic"
    }

    seats = root.findall(".//svg:g", namespace) # Find all seats

    available_seats = {}
    for seat in seats:
        seat_class = seat.get("data-class") # Get the seat class
        if seat_class == "" or seat_class is None:
            continue
        seat_number = seat.find(".//svg:text", namespace).text.strip() # Get the seat number
        seat_status = seat.find(".//svg:image", namespace).get("status") # Get the seat status (0 - occupied, 1 - available)
        is_special = seat.find(".//eic:special", namespace) # Check if the seat is special (bike, quiet zone)

        if seat_class == "first class":
            continue

        if is_special is not None:
            is_special = is_special.get("ref")

        if seat_status == "1" and (is_special in [None, "1", "7"]):
            available_seats[seat_number] = "normal_seat"
            if is_special == "1":
                available_seats[seat_number] = "bike_seat"
            if is_special == "7":
                available_seats[seat_number] = "quiet_zone_seat"

    return available_seats


# Retrieves train connections between the specified departure and arrival stations for a given date and time
def get_trains(departure_station: str, arrival_station: str, input_date: str, input_time: str) -> tuple:
    # Validate input date and time
    input_datetime = datetime.strptime(f"{input_date} {input_time}", "%Y-%m-%d %H:%M")
    current_datetime = datetime.now()
    if input_datetime < current_datetime:
        input_datetime = current_datetime
    input_date = input_datetime.strftime("%Y-%m-%d")
    input_time = input_datetime.strftime("%H:%M")

    # Get station IDs for the departure and arrival stations
    departure_station_data = fetch_station_ids(departure_station)
    if departure_station_data is None:
        return {"error": "Nie znaleziono stacji odjadu w bazie danych"}, {}
    departure_station_id1, departure_station_id2 = departure_station_data
    arrival_station_data = fetch_station_ids(arrival_station)
    if arrival_station_data is None:
        return {"error": "Nie znaleziono stacji przyjazdu w bazie danych"}, {}
    arrival_station_id1, arrival_station_id2 = arrival_station_data

    # Store the station data in a dictionary
    stations = {
        "departure_station": departure_station,
        "departure_station_id1": departure_station_id1,
        "departure_station_id2": departure_station_id2,
        "arrival_station": arrival_station,
        "arrival_station_id1": arrival_station_id1,
        "arrival_station_id2": arrival_station_id2
    }

    # Fetch train connections between the departure and arrival stations and filter out trains that depart on or after the specified input time
    trains = fetch_train_connections(input_date, departure_station_id1, arrival_station_id1).get("polaczenia")
    trains = [t for t in trains if datetime.strptime(t["dataWyjazdu"], "%Y-%m-%d %H:%M:%S").time() >= datetime.strptime(input_time, "%H:%M").time()]
    if trains == []:
        return {"error": "Nie znaleziono bezpośrednich połączeń"}, stations

    result = []

    # Extract train details
    for train in trains:
        train_name = train.get("pociagi")[0].get("nazwaPociagu")
        train_number = train.get("pociagi")[0].get("nrPociagu")
        train_category = train.get("pociagi")[0].get("kategoriaPociagu")
        travel_time = train.get("pociagi")[0].get("czasJazdy")
        departure_datetime = train.get("dataWyjazdu")
        arrival_datetime = train.get("dataPrzyjazdu")

        result.append({
            "train_name": train_name,
            "train_number": train_number,
            "train_category": train_category,
            "travel_time": travel_time,
            "departure_datetime": departure_datetime,
            "arrival_datetime": arrival_datetime
        })

    return result, stations


# Clean the SVG text by removing any script tags
def clean_svg(svg_text: str) -> str:
    svg_text = re.sub(r"<script.*?</script>", "", svg_text, flags=re.DOTALL)
    return svg_text


# Fetch and parse the seat map of a specific carriage on a train, returns the carriage number, SVG seat map of carriage, and a dictionary of available seats with their types
def fetch_and_parse_seat_map(carriage_number: str, carriage_type: str, train_category: str, train_number: str, departure_datetime: str, arrival_datetime: str, departure_station_id2: str, arrival_station_id2: str) -> tuple:
    response = fetch_carriage_seat_map(train_category, train_number, carriage_number, carriage_type, departure_datetime, arrival_datetime, departure_station_id2, arrival_station_id2)
    
    svg_text = response.text
    available_seats = parse_available_seats(svg_text)

    return carriage_number, svg_text, available_seats


# Process the train data by fetching and parsing the seat maps of all carriages on the train, returns a dictionary of carriage numbers with their SVG seat maps, a dictionary of carriage numbers with their dictionary of available seats, and the total number of available seats
def process_train_data(train_category: str, train_number: str, carriages_types: dict, departure_datetime: str, arrival_datetime: str, departure_station_id2: str, arrival_station_id2: str) -> tuple:
    carrige_svgs = {}
    all_available_seats = {}

    num_carriages = len(carriages_types)

    # Fetch and parse the seat maps of all carriages concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_carriages) as executor:
        future_to_carriage = {
            executor.submit(fetch_and_parse_seat_map, carriage_number, carriage_type,
                            train_category, train_number, departure_datetime, arrival_datetime,
                            departure_station_id2, arrival_station_id2
                            ): carriage_number
            for carriage_number, carriage_type in carriages_types.items()
        }

        # Process the results
        for future in concurrent.futures.as_completed(future_to_carriage):
            carriage_number, svg_text, available_seats = future.result()

            if svg_text:
                cleaned_svg = clean_svg(svg_text)
                carrige_svgs[carriage_number] = cleaned_svg
            all_available_seats[carriage_number] = available_seats

    seat_count = sum(len(seats) for seats in all_available_seats.values())

    # Sort the dictionaries by carriage number
    all_available_seats = dict(sorted(all_available_seats.items(), key=lambda x: int(x[0])))
    carrige_svgs = dict(sorted(carrige_svgs.items(), key=lambda x: int(x[0])))

    return carrige_svgs, all_available_seats, seat_count


# Searches for seat transfers on a specific train route using binary search, returns the train data with available seats, svg seat maps, and booking links
def get_seat_transfers(stations, train_category, train_number, train_name, departure_datetime, arrival_datetime):
    start, end = stations[0], stations[-1]
    path, available_seats, svgs, links = [start], [], [], []
    
    current_station = start
    current_index = 0
    
    while current_station != end:
        left, right = current_index + 1, len(stations) - 1
        best_next = None
        best_available_seats = None
        best_carriage_svgs = None
        best_link = None

        # Perform binary search to find the next best station with available seats
        while left <= right:
            mid = (left + right) // 2
            middle_station = stations[mid]

            current_station_name = current_station["station_name"]
            middle_station_name = middle_station["station_name"]
            current_station_data = fetch_station_ids(current_station_name)
            middle_station_data = fetch_station_ids(middle_station_name)
            if current_station_data is None or middle_station_data is None:
                raise ValueError(f"Nie znaleziono stacji {current_station_name} lub {middle_station_name}")

            current_station_id2 = current_station_data[1]
            middle_station_id2 = middle_station_data[1]
            
            current_departure_datetime = current_station["departure_datatime"]
            current_departure_datetime_compact = format_datetime_compact(current_departure_datetime)
            middle_arrival_datetime_compact = format_datetime_compact(middle_station["arrival_datatime"])

            train_info = fetch_train_details(train_category, train_number, current_departure_datetime_compact, current_station_id2, middle_arrival_datetime_compact, middle_station_id2)
            
            # If the connection is not found, continue searching in the left half
            if "statusCode" in train_info and train_info["statusCode"] == 404:
                right = mid - 1
                continue
            
            carriages_types = extract_carriage_type(train_info)
            carrige_svgs, all_available_seats, seat_count = process_train_data(train_category, train_number, carriages_types, current_departure_datetime_compact, middle_arrival_datetime_compact, current_station_id2, middle_station_id2)
            
            print(f"{current_station_name} -> {middle_station_name} ({seat_count})")

            # If seats are available, update the best next station and continue searching in the right half
            if seat_count > 0:
                best_next = mid
                best_available_seats = all_available_seats
                best_carriage_svgs = carrige_svgs
                best_link = get_intercity_link(current_departure_datetime.split(" ")[0], current_station_data[0], middle_station_data[0], current_departure_datetime.split(" ")[1])
                left = mid + 1
            else:
                # If seats are not available, continue searching in the left half
                right = mid - 1

        if best_next is None:
            break

        # Update informations and move to the next station
        next_station = stations[best_next]
        path.append(next_station)
        available_seats.append(best_available_seats)
        svgs.append(best_carriage_svgs)
        links.append(best_link)
        
        current_station = next_station
        current_index = best_next

    # Check if departure station is in the the path
    success = end in path

    return {
        "train_name": train_name,
        "train_number": train_number,
        "train_category": train_category,
        "departure_datetime": departure_datetime,
        "arrival_datetime": arrival_datetime,
        "status": "seat_transfer" if success else "no_seats",
        "stations": path if success else [],
        "available_seats": available_seats if success else [],
        "carrige_svgs": svgs if success else [],
        "links": links if success else []
    }


# Retrieve the seat availability for a specific train, returns the train data with available seats, svg seat maps, and booking links
def get_seat_availability(train: dict, stations: dict) -> dict:
    # Extract train details
    train_category = train.get("train_category")
    train_number = train.get("train_number")
    train_name = train.get("train_name")
    departure_datetime = train.get("departure_datetime")
    departure_datetime_compact =  format_datetime_compact(departure_datetime)
    arrival_datetime = train.get("arrival_datetime")
    arrival_datetime_compact =  format_datetime_compact(arrival_datetime)

    # Extract departure and arrival station IDs
    departure_station_id1 = stations.get("departure_station_id1")
    departure_station_id2 = stations.get("departure_station_id2")
    arrival_station_id1 = stations.get("arrival_station_id1")
    arrival_station_id2 = stations.get("arrival_station_id2")

    # Fetch train details
    train_info = fetch_train_details(train_category, train_number, departure_datetime_compact, departure_station_id2, arrival_datetime_compact, arrival_station_id2)

    # If the train is not found, return information about the train with no seats available
    if "statusCode" in train_info and train_info["statusCode"] == 404:
        return {
            "train_name": train_name,
            "train_number": train_number,
            "train_category": train_category,
            "departure_datetime": departure_datetime,
            "arrival_datetime": arrival_datetime,
            "status": "no_seats",
            "stations": [],
            "available_seats": [],
            "carrige_svgs": [],
            "links": []
        }

    # Extract carriage types and process the train data
    carriages_types = extract_carriage_type(train_info)
    carrige_svgs, all_available_seats, seat_count = process_train_data(train_category, train_number, carriages_types, departure_datetime_compact, arrival_datetime_compact, departure_station_id2, arrival_station_id2)


    # If seats are available return the train data with available seats 
    if seat_count != 0:
        return {
            "train_name": train_name,
            "train_number": train_number,
            "train_category": train_category,
            "departure_datetime": departure_datetime,
            "arrival_datetime": arrival_datetime,
            "status": "same_seat",
            "available_seats": all_available_seats,
            "carrige_svgs": carrige_svgs,
            "links": [get_intercity_link(datetime.strptime(departure_datetime, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d"), departure_station_id1, arrival_station_id1, datetime.strptime(departure_datetime, "%Y-%m-%d %H:%M:%S").strftime("%H:%M"))]
        }

    departure_datetime_iso = datetime.strptime(departure_datetime, "%Y-%m-%d %H:%M:%S").isoformat()
    route_info = fetch_train_route(departure_datetime_iso, departure_station_id1, arrival_station_id1, train_number)

    # Extract the route information
    route = route_info.get("trasePrzejezdu").get("trasaPrzejazdu")
    if not route or len(route) == 0:
        raise ValueError(f"Brak dostępnych miejsc na przejazd ze stacji {stations['departure_station']} do stacji {stations['arrival_station']} bez zmiany miejsca. PKP Intercity nie udostępnia informacji o trasie tego pociągu.")

    stations = [
        {
            "station_name": station["nazwaStacji"],
            "station_number": station["numerStacji"],
            "arrival_datatime": (datetime.strptime(station["dataPrzyjazdu"], "%a %b %d %H:%M:%S CET %Y").strftime("%Y-%m-%d %H:%M:%S") if station.get("dataPrzyjazdu") else None),
            "departure_datatime": (datetime.strptime(station["dataWyjazdu"], "%a %b %d %H:%M:%S CET %Y").strftime("%Y-%m-%d %H:%M:%S") if station.get("dataWyjazdu") else None)
        }
        for station in route
    ]
    
    all_available_seats = []
    carrige_svgs = {}

    # Check if it is possible to depart from the departure station
    start, end = stations[0], stations[1]
    start_station = start["station_name"]
    end_station = end["station_name"]
    start_arrival_datetime = start["arrival_datatime"]
    end_arrival_datetime = end["arrival_datatime"]
    start_departure_datetime = start["departure_datatime"]
    end_departure_datetime = end["departure_datatime"]
    start_station_data = fetch_station_ids(start_station)
    end_station_data = fetch_station_ids(end_station)
    if start_station_data is None or end_station_data is None:
        raise ValueError(f"Nie znaleziono stacji {start_station} lub {end_station}")
    start_station_id2 = start_station_data[1]
    end_station_id2 = end_station_data[1]
    start_arrival_datetime_compact = format_datetime_compact(start_arrival_datetime) if start_arrival_datetime else None
    start_departure_datetime_compact = format_datetime_compact(start_departure_datetime)
    end_arrival_datetime_compact = format_datetime_compact(end_arrival_datetime)
    end_departure_datetime_compact = format_datetime_compact(end_departure_datetime)

    train_info = fetch_train_details(train_category, train_number, start_departure_datetime_compact, start_station_id2, end_arrival_datetime_compact, end_station_id2)
    
    if "statusCode" in train_info and train_info["statusCode"] == 404:
        carrige_svgs = {}
        all_available_seats = {}
        seat_count = None 
    else:
        carriages_types = extract_carriage_type(train_info)
        carrige_svgs, all_available_seats, seat_count = process_train_data(train_category, train_number, carriages_types, start_departure_datetime_compact, end_departure_datetime_compact, start_station_id2, end_station_id2)

    if seat_count == 0:
        return {
            "train_name": train_name,
            "train_number": train_number,
            "train_category": train_category,
            "departure_datetime": departure_datetime,
            "arrival_datetime": arrival_datetime,
            "status": "no_seats",
            "stations": [],
            "available_seats": [],
            "carrige_svgs": [],
            "links": []
        }

    # Try to find a seat transfers
    return get_seat_transfers(stations, train_category, train_number, train_name, departure_datetime, arrival_datetime)