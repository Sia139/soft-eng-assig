$(document).ready(function () {
    function setupSearch(inputSelector, resultsSelector, apiUrl, formatResult, onSelect) {
        $(inputSelector).on("input", function () {
            var query = $(this).val();
            if (query.length >= 1) {
                $.get(apiUrl, { query: query }, function (data) {
                    $(resultsSelector).empty().show();
                    if (data.length === 0) {
                        $(resultsSelector).append("<li>No results found</li>");
                    } else {
                        data.forEach(function (item) {
                            $(resultsSelector).append(formatResult(item));
                        });
                    }
                }).fail(function () {
                    $(resultsSelector).hide();
                    console.error("Error fetching data from", apiUrl);
                });
            } else {
                $(resultsSelector).hide();
            }
        });

        $(document).on("click", `${resultsSelector} a`, function (event) {
            event.preventDefault();
            onSelect($(this));
            $(resultsSelector).hide();
        });
    }

    setupSearch(
        "#guardian_search",
        "#guardian_results",
        "/teacher/searchParents",
        function (parent) {
            return `<li><a href="#" data-id="${parent.id}" data-username="${parent.username}">ID: ${parent.id}, Username: ${parent.username}</a></li>`;
        },
        function ($selected) {
            var parentId = $selected.data("id");
            var parentUsername = $selected.data("username");
            $("#guardian_search").val(`ID: ${parentId}, Username: ${parentUsername}`);
            $("#guardian_id").val(parentId);
        }
    );

    setupSearch(
        "#student_search",
        "#student_results",
        "/accountant/search-students",
        function (student) {
            return `<li><a href="#" data-id="${student.id}" data-studentname="${student.name}" data-grade="${student.grade}">ID: ${student.id}, Student name: ${student.name}, Grade: ${student.grade}</a></li>`;
        },
        function ($selected) {
            var studentId = $selected.data("id");
            var studentName = $selected.data("studentname");
            var studentGrade = $selected.data("grade");
            $("#student_search").val(`ID: ${studentId}, Student name: ${studentName}, Grade: ${studentGrade}`);
            $("#student_id").val(studentId);
        }
    );
});