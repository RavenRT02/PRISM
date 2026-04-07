document.addEventListener("DOMContentLoaded", function () {

    const ctx = document
        .getElementById("issueChart")
        .getContext("2d");

    new Chart(ctx, {

        type: "pie",

        data: {

            labels: [
                "Issues",
                "Prioritized",
                "On Hold",
                "Resolved",
                "Closed"
            ],

            datasets: [{

                label: "Issue Distribution",

                data: [
                    window.issuesCount,
                    window.prioritizedCount,
                    window.onHoldCount,
                    window.resolvedCount,
                    window.closedCount
                ]

            }]

        }

    });

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