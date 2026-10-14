document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("issueChart");

    if (canvas) {
        new Chart(canvas.getContext("2d"), {
            type: "pie",
            data: {
                labels: [
                    "Submitted",
                    "In Progress",
                    "On Hold",
                    "Resolved",
                    "Closed",
                    "Rejected"
                ],
                datasets: [{
                    label: "Issues by Status",
                    data: [
                        window.submittedCount,
                        window.inProgressCount,
                        window.onHoldCount,
                        window.resolvedCount,
                        window.closedCount,
                        window.rejectedCount
                    ]
                }]
            }
        });
    }
});

const categoryCtx = document
    .getElementById("categoryChart")
    .getContext("2d");

new Chart(categoryCtx, {

    type: "bar",

    data: {

        labels: window.categoryLabels,

        datasets: [{

            label: "Issues per Category",

            data: window.categoryCounts

        }]

    }

});