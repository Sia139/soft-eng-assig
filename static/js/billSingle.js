$(document).ready(function() {
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