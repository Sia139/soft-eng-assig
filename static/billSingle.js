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

    // Existing download button functionality
    document.getElementById('download-btn').addEventListener('click', function() {
        const fileUrl = 'invoice.pdf'; // Ensure this is the correct file path
        const anchor = document.createElement('a');
        anchor.href = fileUrl;
        anchor.download = 'Invoice_1003.pdf'; // Use a simple filename
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
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