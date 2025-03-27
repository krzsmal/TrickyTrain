document.addEventListener("DOMContentLoaded", function () {
    // Set the minimum date for the date input field to today
    let today = new Date().toISOString().split('T')[0];
    document.getElementById("date").setAttribute("min", today);

    // Function to set up autocomplete dropdown for station inputs
    function setupAutocomplete(inputId, dropdownId) {
        const input = document.getElementById(inputId);
        const dropdown = document.getElementById(dropdownId);

        input.addEventListener("input", function () {
            const query = input.value.trim();

            // Hide dropdown if the query is too short
            if (query.length < 3) {
                dropdown.classList.remove("show");
                return;
            }

            // Fetch the list of stations from the server
            fetch(`/stations?name=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    dropdown.innerHTML = "";

                    if (data.length != 0) {
                        data.forEach(station => {
                            const item = document.createElement("li");
                            item.innerHTML = `<a class="dropdown-item">${station}</a>`;
                            
                            // Set the input value to the selected station and hide the dropdown
                            item.addEventListener("click", () => {
                                input.value = station;
                                dropdown.classList.remove("show");
                            });
                            dropdown.appendChild(item);
                        });
                        
                        dropdown.classList.add("show");
                    }
                })
                .catch(error => console.error("Błąd pobierania stacji:", error));
        });

        // Hide dropdown when clicking outside
        document.addEventListener("click", (event) => {
            if (!input.contains(event.target) && !dropdown.contains(event.target)) {
                dropdown.classList.remove("show");
            }
        });
    }

    // Set up autocomplete
    setupAutocomplete("from", "fromDropdown");
    setupAutocomplete("to", "toDropdown");

    // Get the loading screen and all forms on the page
    const forms = document.querySelectorAll("form");
    const loadingScreen = document.getElementById("loading-screen");
    
    // Show the loading screen when a form is submitted
    for (const form of forms) {
        form.addEventListener("submit", function () {
            loadingScreen.classList.remove("d-none");
        });
    }
});

// Hide the loading screen when the page is loaded from cache
window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        document.getElementById("loading-screen").classList.add("d-none");
    }
});