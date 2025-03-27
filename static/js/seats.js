// Toggles the visibility of the SVG section
function toggleSVG() {
    var section = document.getElementById("svgSection");
    section.classList.toggle("show");
}

// Toggles the visibility of the seat list associated with the clicked element
function toggleSeatList(element) {
    var seatList = element.nextElementSibling;
    seatList.classList.toggle("show");
}

document.addEventListener("DOMContentLoaded", function () {
    let selectedRow = null;
    const toggleButton = document.getElementById("toggleButton");

    // For each row in the table, add an event listener to display the available seats and the SVG section
    document.querySelectorAll(".selectable-row").forEach(row => {
        row.addEventListener("click", function () {
            const index = this.getAttribute("data-index");

            if (selectedRow === this) {
                // Deselect the row if it is already selected
                this.classList.remove("table-primary");
                selectedRow = null;
                document.getElementById("available-seats").innerHTML = "";
                document.getElementById("svgSection").innerHTML = "";
                toggleButton.style.display = "none";
            } else {
                // Select the row and display the available seats and the SVG section
                if (selectedRow) {
                    selectedRow.classList.remove("table-primary");
                }
                this.classList.add("table-primary");
                selectedRow = this;

                const availableSeatsContainer = document.getElementById("available-seats");
                availableSeatsContainer.innerHTML = "";
                const svgContainer = document.getElementById("svgSection");
                svgContainer.innerHTML = "";

                // Divide non-empty carriages into columns
                let carriages = Object.entries(seatsData[index] || {}).filter(([_, seats]) => seats && Object.keys(seats).length > 0);
                const numColumns = 4;
                let columns = Array.from({ length: numColumns }, () => []);
                carriages.forEach(([carriageNr, seats], i) => {
                    columns[i % numColumns].push({ carriageNr, seats });
                });

                const rowDiv = document.createElement("div");
                rowDiv.classList.add("row");
                
                // Create columns with seat cards
                columns.forEach(col => {
                    const colDiv = document.createElement("div");
                    colDiv.classList.add("col-12", "col-md-3");
                    col.forEach(({ carriageNr, seats }) => {
                        const seatCard = document.createElement("div");
                        seatCard.classList.add("seat-card");

                        // Group seats by type
                        let seatTypes = {};
                        for (const [seatNr, seatType] of Object.entries(seats)) {
                            if (!seatTypes[seatType]) seatTypes[seatType] = [];
                            seatTypes[seatType].push(seatNr);
                        }

                        const seatNames = {
                            "normal_seat": "Normalne",
                            "bike_seat": "Rowerowe",
                            "quiet_zone_seat": "W strefie ciszy"
                        };

                        const seatClasses = {
                            "normal_seat": "seat-normal",
                            "bike_seat": "seat-bike",
                            "quiet_zone_seat": "seat-quiet"
                        };

                        // Create a card with seats information
                        seatCard.innerHTML = `
                            <div class="seat-header">Wagon ${carriageNr}</div>
                            ${Object.entries(seatTypes).map(([type, numbers]) => `
                                <div class="seat-badge ${seatClasses[type] || 'bg-secondary'}" onclick="toggleSeatList(this)">
                                    ${seatNames[type] || type}: ${numbers.length}
                                </div>
                                <div class="seat-list fw-bold">${numbers.join(", ")}</div>
                            `).join("")}
                        `;
                        colDiv.appendChild(seatCard);
                    });
                    rowDiv.appendChild(colDiv);
                });

                availableSeatsContainer.appendChild(rowDiv);

                // Display SVGs for selected row
                for (const [carriageNr, svg] of Object.entries(svgData[index] || {})) {
                    if (carriages.some(item => item.carriageNr === carriageNr || item[0] === carriageNr)) {
                        const svgElement = document.createElement("div");
                        svgElement.classList.add("mt-5");
                        svgElement.innerHTML = `
                            <h3 class="text-center fw-bold">Wagon ${carriageNr}</h3>
                            ${svg}
                        `;
                        svgContainer.appendChild(svgElement);
                    }
                }

                toggleButton.style.display = "block";
            }
        });
    });
});