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
    const day = document.getElementById('day').value;
    const month = document.getElementById('month').value;
    const year = document.getElementById('year').value;

    // Combine the day, month, and year into a single date string
    const dob = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;

    // Set the combined date to the hidden input
    document.getElementById('dob').value = dob;
});