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

    // Existing calendar functionality
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

    // New form submission functionality
    $('.form').on('submit', function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = {
            student_id: $('#student_id').val(),
            details: $('#details').val(),
            price: $('#price').val(),
            due_date: `${$('#year').val()}-${$('#month').val().padStart(2, '0')}-${$('#day').val().padStart(2, '0')}`
        };
        
        // Validate form data
        if (!formData.student_id || !formData.details || !formData.price || !formData.due_date) {
            alert('Please fill in all required fields');
            return;
        }
        
        // Submit form via AJAX
        $.ajax({
            url: '/accountant/billSingle',
            method: 'POST',
            data: formData,
            success: function(response) {
                alert(response.message);
                if (response.status === 'success') {
                    // Clear form
                    $('.form')[0].reset();
                    $('#student_id').val('');
                }
            },
            error: function(xhr) {
                const response = xhr.responseJSON;
                alert(response?.message || 'An error occurred');
            }
        });
    });
    
    // Handle cancel button
    $('.cancel-btn').on('click', function() {
        window.location.href = '/accountant/viewBilling';
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