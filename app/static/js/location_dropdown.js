document.addEventListener("DOMContentLoaded", () => {
    const buildingSelect = document.getElementById("building");
    const floorSelect = document.getElementById("floor");
    const roomSelect = document.getElementById("room");

    if (!buildingSelect || !floorSelect || !roomSelect) return;

    buildingSelect.addEventListener("change", async () => {
        const buildingId = buildingSelect.value;

        floorSelect.innerHTML =
            '<option value="">Choose Floor</option>';
        roomSelect.innerHTML =
            '<option value="">Choose Floor First</option>';

        if (!buildingId) return;

        floorSelect.innerHTML =
            '<option value="">Loading...</option>';

        try {
            const response = await fetch(`/issues/floors/${buildingId}`);
            if (!response.ok) throw new Error("Failed to load floors");

            const floors = await response.json();

            floorSelect.innerHTML =
                '<option value="">Select Floor</option>';

            floors.forEach(floor => {
                const option = document.createElement("option");
                option.value = floor.id;
                option.textContent = floor.number;
                floorSelect.appendChild(option);
            });
        } catch (error) {
            console.error(error);
            floorSelect.innerHTML =
                '<option value="">Could not load floors</option>';
        }
    });

    floorSelect.addEventListener("change", async () => {
        const floorId = floorSelect.value;

        roomSelect.innerHTML =
            '<option value="">Choose Room</option>';

        if (!floorId) return;

        roomSelect.innerHTML =
            '<option value="">Loading...</option>';

        try {
            const response = await fetch(`/issues/rooms/${floorId}`);
            if (!response.ok) throw new Error("Failed to load rooms");

            const rooms = await response.json();

            roomSelect.innerHTML =
                '<option value="">Select Room</option>';

            rooms.forEach(room => {
                const option = document.createElement("option");
                option.value = room.id;
                option.textContent = room.name;
                roomSelect.appendChild(option);
            });
        } catch (error) {
            console.error(error);
            roomSelect.innerHTML =
                '<option value="">Could not load rooms</option>';
        }
    });
});
