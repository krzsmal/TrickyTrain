# TrickyTrain - PKP Intercity Seat Availability Checker

TrickyTrain is an application that allows you to check the seat availability on PKP Intercity trains. By entering your departure and arrival stations, along with the desired travel date and time, you can quickly search for available connections. The application presents a list of all trains operating on your chosen date, allowing you to check seat availability for each one.
If a direct seat is not available for the entire journey, TrickyTrain can find seat transfers within the same train. Once you've found a connection you're happy with, TrickyTrain provides a direct link to the official [PKP Intercity](https://ebilet.intercity.pl/) website, making it quick and easy to purchase your tickets.

## Features
*   **Find Direct Train Connections:** Find direct train connections between two stations on a given date and time.

*   **Seat Availability Check:**  Check the real-time seat availability on specific trains, providing details like seat, carriage numbers and seat types.

*   **"Tricky" Seat Transfers:**  If no single seat is available for the entire journey, TrickyTrain finds seat transfer options within the same train. Instead of missing out on a trip due to full reservations, you’ll be able to switch seats along the way, ensuring you can still reach your destination with minimal disruption.

*   **Seat Map Visualization:** Displays seat maps for carriages so you can verify which seats are actually available.

*   **API Integration & Reverse Engineering:** The application interacts with an undocumented API uncovered through reverse engineering techniques, including network analysis with DevTools and Postman. It retrieves data for real-time seat availability, train connections, station searches, and route tracking.

*   **User-friendly interface:** The application is built with Bootstrap to provide a clean and intuitive user experience.

## Demo Materials
### Direct seat

![Demo Video 1](/assets/demo1.gif)
### Seat transfer
![Demo Video 2](/assets/demo2.gif)

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/krzsmal/TrickyTrain
    cd TrickyTrain
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    (Consider using a virtual environment for dependency management.)

3.  **Run the application:**

    ```bash
    python app.py
    ```

    The application will start, and a browser window should automatically open. If not, navigate to `http://127.0.0.1:5000` in your web browser.

## Future Enhancements

*   **Improved Documentation**
*   **Support for Transfers Between Trains**
*   **Recognition of Compartment and Open-Plan Coaches**
*   **Optimization and Speed Improvement**
*   **Fixing bugs**