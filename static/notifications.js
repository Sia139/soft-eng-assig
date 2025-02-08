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

document.addEventListener("DOMContentLoaded", function () {
    const redDot = document.querySelector(".red-dot");
    const markReadButton = document.querySelector(".mark-read-btn");

    markReadButton.addEventListener("click", function () {
        redDot.style.display = "none"; // Hide the red dot when button is clicked
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

// Call the function immediately to set the time when the page loads
updateTime();

// Update the time every minute
setInterval(updateTime, 60000);

