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

    // Time update function
    function updateTime() {
        const timeElement = document.querySelector('.time');
        if (timeElement) {
            const now = new Date();
            let hours = now.getHours();
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const ampm = hours >= 12 ? 'pm' : 'am';
            hours = hours % 12 || 12; // Convert to 12-hour format
            timeElement.textContent = `${hours}:${minutes}${ampm}`;
        }
    }

    // Update time immediately and then every minute
    updateTime();
    setInterval(updateTime, 60000);

});

// function displayReport(report, selectedMonth) {
//     // Show the report section
//     document.getElementById('reportSummary').style.display = 'block';
    
//     // Update summary cards
//     document.getElementById('selectedMonth').textContent = formatMonth(selectedMonth);
//     document.getElementById('totalRevenue').textContent = formatCurrency(report.totalRevenue);
//     document.getElementById('totalPaid').textContent = formatCurrency(report.totalPaid);
//     document.getElementById('totalPending').textContent = formatCurrency(report.totalPending);
//     document.getElementById('collectionRate').textContent = `${report.collectionRate}%`;
    
//     // Update fee type breakdown table
//     const tableBody = document.getElementById('feeTypeTable').getElementsByTagName('tbody')[0];
//     tableBody.innerHTML = ''; // Clear existing rows
    
//     report.feeTypes.forEach(fee => {
//         const row = tableBody.insertRow();
//         row.innerHTML = `
//             <td>${fee.type}</td>
//             <td>${formatCurrency(fee.total)}</td>
//             <td>${formatCurrency(fee.paid)}</td>
//             <td>${formatCurrency(fee.pending)}</td>
//             <td>${fee.collectionRate}%</td>
//         `;
//     });
// }

// function formatCurrency(amount) {
//     return new Intl.NumberFormat('en-US', {
//         style: 'currency',
//         currency: 'USD'
//     }).format(amount);
// }

// function formatMonth(monthStr) {
//     return new Date(monthStr + '-01').toLocaleDateString('en-US', {
//         year: 'numeric',
//         month: 'long'
//     });
// }
