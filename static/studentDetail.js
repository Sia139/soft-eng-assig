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

function sortTable(n) {
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.getElementById("myTable2");
    switching = true;
    dir = "asc"; // Set the sorting direction to ascending by default.

    // Reset all sort indicators in headers.
    const headers = table.getElementsByTagName("TH");
    for (let header of headers) {
        const span = header.querySelector(".sort");
        if (span) {
            span.innerHTML = ""; // Clear any sort symbol.
        }
    }

    // Add the sort indicator to the active header.
    const activeHeader = headers[n];
    const activeSpan = activeHeader.querySelector(".sort") || document.createElement("span");
    activeSpan.classList.add("sort-symbol");
    if (!activeHeader.contains(activeSpan)) {
        activeHeader.appendChild(activeSpan);
    }

    // Perform sorting.
    while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];
            if (dir === "asc") {
                if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                    shouldSwitch = true;
                    break;
                }
            } else if (dir === "desc") {
                if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                    shouldSwitch = true;
                    break;
                }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount++;
        } else {
            if (switchcount === 0 && dir === "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }

    // Update the sort indicator based on the sorting direction.
    activeSpan.innerHTML = dir === "asc" ? " &#x25B4;" : " &#x25BE;";
}

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

// Add an event listener to the grade select element
// document.addEventListener("DOMContentLoaded", function() {
//     const gradeSelect = document.getElementById("grade");
//     const searchForm = document.getElementById("search-form");

//     if (gradeSelect && searchForm) {
//         gradeSelect.addEventListener("change", function() {
//             searchForm.submit();
//         });
//     }
// });

// Call the function immediately to set the time when the page loads
updateTime();

// Update the time every minute
setInterval(updateTime, 60000);