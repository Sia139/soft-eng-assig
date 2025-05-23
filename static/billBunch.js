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

    // Form submission
    document.querySelector('.form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        fetch('/accountant/billBunch', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            if (data.status === 'success') {
                this.reset();
            }
        })
        .catch(error => {
            alert('An error occurred while processing your request.');
        });
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

// document.addEventListener("DOMContentLoaded", function() {
//     document.getElementById('download-btn').addEventListener('click', function() {
//         const fileUrl = 'invoice.pdf'; // Ensure this is the correct file path
//         const anchor = document.createElement('a');
//         anchor.href = fileUrl;
//         anchor.download = 'Invoice_1003.pdf'; // Use a simple filename
//         document.body.appendChild(anchor);
//         anchor.click();
//         document.body.removeChild(anchor);
//     });
// });

// function clearForm() {
//     document.querySelector('.form').reset();
// }

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

// Popup message functionality
function showPopupMessage(message, type) {
    // Create popup container if it doesn't exist
    let popup = document.getElementById('popup-message');
    if (!popup) {
        popup = document.createElement('div');
        popup.id = 'popup-message';
        document.body.appendChild(popup);
    }

    // Set popup content and style based on type
    popup.textContent = message;
    popup.className = `popup-message ${type}`;
    
    // Show popup
    popup.style.display = 'block';
    
    // Hide popup after 3 seconds
    setTimeout(() => {
        popup.style.display = 'none';
    }, 3000);
}