document.addEventListener("DOMContentLoaded", function() {
    // Select all durations 
    const durations = Array.from(document.querySelectorAll(".travel_time"));

    // Function to convert format HH:MM or MM to minutes
    function timeToMinutes(time) {
        if (time.includes(":")) { 
            const [hours, minutes] = time.split(":").map(Number);
            return hours * 60 + minutes;
        }
        return Number(time);
    }

    if (durations.length > 0) {
        let minTime = Infinity;
        let maxTime = -Infinity;

        // Find the shortest and the longest travel time
        durations.forEach(cell => {
            const time = timeToMinutes(cell.textContent.trim());
            minTime = Math.min(minTime, time);
            maxTime = Math.max(maxTime, time);
        });
        
        // Highlight the shortest and the longest travel time if they are different
        if (minTime != maxTime) {
            durations.forEach(cell => {
                const time = timeToMinutes(cell.textContent.trim());
                cell.classList.remove("text-success", "text-danger", "fw-bold");
                
                if (time === minTime) {
                    cell.classList.add("text-success", "fw-bold");
                } else if (time === maxTime) {
                    cell.classList.add("text-danger", "fw-bold");
                }
            });
        }
    }

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