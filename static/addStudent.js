document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.querySelector('.sidebar');
    const toggleButton = document.querySelector('.collapse-button');

    toggleButton.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed'); // Toggle collapsed state
    });

    const dropdowns = document.querySelectorAll(".dropdown");

    dropdowns.forEach((dropdown) => {
        const btn = dropdown.querySelector(".dropdown-btn");
        if (!btn) return; // Prevent errors

        btn.addEventListener("click", function (event) {
            event.stopPropagation();

            // Close other dropdowns before opening the clicked one
            dropdowns.forEach((d) => {
                if (d !== dropdown) {
                    d.classList.remove("active");
                }
            });

            // Toggle active class on clicked dropdown
            dropdown.classList.toggle("active");
        });
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function () {
        dropdowns.forEach((dropdown) => dropdown.classList.remove("active"));
    });
});

document.getElementById("calendar-btn").addEventListener("click", function () {
    const calendarInput = document.getElementById("calendar");
    calendarInput.style.display = "block"; // Temporarily display the date picker
    calendarInput.focus(); // Focus on the date picker to open it
});

// Update day, month, and year inputs when a date is selected
document.getElementById("calendar").addEventListener("change", function () {
    const selectedDate = new Date(this.value);
    const day = String(selectedDate.getDate()).padStart(2, "0");
    const month = String(selectedDate.getMonth() + 1).padStart(2, "0"); // Months are zero-based
    const year = selectedDate.getFullYear();

    document.getElementById("day").value = day;
    document.getElementById("month").value = month;
    document.getElementById("year").value = year;

    this.style.display = "none"; // Hide the date picker again
});

document.querySelector('form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission

    const day = document.getElementById('day').value;
    const month = document.getElementById('month').value;
    const year = document.getElementById('year').value;

    // Combine the day, month, and year into a single date string
    const dob = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;

    // Set the combined date to the hidden input
    document.getElementById('dob').value = dob;

    // Create FormData object from the form
    const formData = new FormData(this);

    // Send POST request
    fetch(this.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Show alert based on the response
        alert(data.message);
        
        // If successful, optionally clear the form
        if (data.status === 'success') {
            clearForm();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while submitting the form');
    });
});

function updateTime() {
    // Get the current time
    const now = new Date();
    
    // Extract hours, minutes, and am/pm
    let hours = now.getHours();
    let minutes = now.getMinutes();
    let ampm = hours >= 12 ? 'pm' : 'am';

    // Convert 24-hour time to 12-hour time
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    minutes = minutes < 10 ? '0' + minutes : minutes;

    // Format the time
    const timeString = `${hours}:${minutes} ${ampm}`;

    // Update the content of the .time element
    document.querySelector('.time').textContent = timeString;
}

function clearForm() {
    document.querySelector('.form').reset();
}

// Call the function immediately to set the time when the page loads
updateTime();

// Update the time every minute
setInterval(updateTime, 60000);

fetch(window.location.href)
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    alert("Error: " + data.error);
                });
            }
            return response.text();
        })
        .catch(error => console.error("Fetch error:", error));