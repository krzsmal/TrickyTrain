import json
from flask import Flask, Response, request, redirect, url_for, render_template
from utils import get_trains, get_seat_availability, fetch_stations
from requests.exceptions import ConnectionError
from datetime import datetime
import webbrowser
import threading
import ast


app = Flask(__name__)


# Open the default web browser with the application URL
def open_browser() -> None:
    webbrowser.open("http://127.0.0.1:5000")


# Custom Jinja2 filter for formatting datetime objects in templates
@app.template_filter('format_datetime')
def format_datetime(value: str, format: str ='%H:%M %d:%m:%Y') -> str:
    if isinstance(value, str):  
        value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")  
    return value.strftime(format)


# Custom Jinja2 filter for formatting duration in minutes to hours:minutes format
@app.template_filter('format_duration')
def format_duration(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes}"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}:{mins:02}"


# Custom Jinja2 filter for calculating duration between two datetime timestamps
@app.template_filter('calculate_duration')
def calculate_duration(departure: str, arrival: str) -> str:
    departure = datetime.strptime(departure, "%Y-%m-%d %H:%M:%S")
    arrival = datetime.strptime(arrival, "%Y-%m-%d %H:%M:%S")
    minutes = int((arrival - departure).total_seconds() // 60)
    return format_duration(minutes)


# Route for the main page
@app.route('/', methods=['GET'])
def main():
    return render_template('base.html')


# Route for the trains page
@app.route('/trains', methods=['GET', 'POST'])
def trains():
    if request.method == 'POST':
        if all(key in request.form for key in ("from", "to", "date", "time")):
            input_date = request.form["date"]
            input_time = request.form["time"]
            departure_station = request.form["from"]
            arrival_station = request.form["to"]
            try:
                data, stations = get_trains(departure_station, arrival_station, input_date, input_time)
                return render_template('trains.html', data=data, stations=stations)
            except ConnectionError as e:
                print(e)
                return render_template('trains.html', data={"error": f"Sprawdź połączenie z Internetem i spróbuj ponownie: {str(e)}"})
            except Exception as e:
                print(e)
                return render_template('trains.html', data={"error": str(e)})
    return redirect(url_for('main'))


# Route for the seats page
@app.route('/seats', methods=['GET', 'POST'])
def seats():
    if request.method == 'POST':
        if "row" in request.form and "stations" in request.form:
            train = request.form["row"]
            stations = request.form["stations"]

            # Convert string representation of dictionaries into actual Python dictionaries
            train = ast.literal_eval(train)
            stations = ast.literal_eval(stations)

            try:
                data = get_seat_availability(train, stations)
            except ConnectionError as e:
                print(e)
                return render_template('seats.html', data={"error": f"Sprawdź połączenie z Internetem i spróbuj ponownie: {str(e)}"})
            except Exception  as e:
                print(e)
                return render_template('seats.html', data={"error": str(e)})
            data["departure_datetime"] = datetime.strptime(data["departure_datetime"], "%Y-%m-%d %H:%M:%S")
            data["arrival_datetime"] = datetime.strptime(data["arrival_datetime"], "%Y-%m-%d %H:%M:%S")
            return render_template('seats.html', data=data, stations=stations)
    return redirect(url_for('main'))


# Route for the list of stations
@app.route('/stations', methods=['GET'])
def stations():

    station_list = fetch_stations(request.args.get('name'))
    response_json = json.dumps(station_list, ensure_ascii=False)
    
    return Response(response_json, content_type="application/json; charset=utf-8")


if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    app.run(debug=False)