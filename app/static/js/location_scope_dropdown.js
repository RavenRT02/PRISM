
document.addEventListener("DOMContentLoaded", () => {
    const scopeSelect = document.getElementById("location_scope");
    const buildingSelect = document.getElementById("building");
    const floorSelect = document.getElementById("floor");
    const roomSelect = document.getElementById("room");

    const floorField = document.getElementById("floorField");
    const roomField = document.getElementById("roomField");

    const imageUpload = document.getElementById("imageUpload");
    const fileNameDisplay = document.getElementById("fileNameDisplay");

    // Stop if this script is loaded on a page
    // that does not contain the issue form.
    if (
        !scopeSelect ||
        !buildingSelect ||
        !floorSelect ||
        !roomSelect ||
        !floorField ||
        !roomField
    ) {
        return;
    }

    function updateLocationFields() {
        const scope = scopeSelect.value;

        // Reset ALL location selections whenever scope changes
        buildingSelect.value = "";
        floorSelect.innerHTML =
            '<option value="">Choose Building First</option>';
        roomSelect.innerHTML =
            '<option value="">Choose Floor First</option>';

        // Building is always required
        buildingSelect.required = true;

        const showFloor = scope !== "BUILDING";
        const showRoom = scope === "ROOM";

        floorField.classList.toggle("d-none", !showFloor);
        roomField.classList.toggle("d-none", !showRoom);

        floorSelect.required = showFloor;
        roomSelect.required = showRoom;

        // Update placeholder text based on the selected scope
        if (!showFloor) {
            floorSelect.innerHTML =
                '<option value="">Not required for building-wide issues</option>';
        }

        if (!showRoom) {
            roomSelect.innerHTML =
                '<option value="">Not required for this scope</option>';
        }
    }

    scopeSelect.addEventListener("change", updateLocationFields);

    // Set the correct field visibility when the page first loads
    updateLocationFields();

    // Display selected image filename.
    if (imageUpload && fileNameDisplay) {
        imageUpload.addEventListener("change", function () {
            if (this.files && this.files.length > 0) {
                fileNameDisplay.textContent =
                    "Selected: " + this.files[0].name;
                fileNameDisplay.classList.remove("d-none");
            } else {
                fileNameDisplay.classList.add("d-none");
            }
        });
    }
});
