document.addEventListener("DOMContentLoaded", () => {

    const buildingSelect = document.getElementById("building");
    const floorSelect = document.getElementById("floor");
    const roomSelect = document.getElementById("room");


    buildingSelect.addEventListener("change", async () => {

        const buildingId = buildingSelect.value;

        floorSelect.innerHTML = "<option>Loading...</option>";
        roomSelect.innerHTML = "<option>Select floor first</option>";

        if (!buildingId) return;

        const response = await fetch(`/issues/floors/${buildingId}`);
        const floors = await response.json();

        floorSelect.innerHTML = "<option>Select Floor</option>";

        floors.forEach(floor => {

            const option = document.createElement("option");

            option.value = floor.id;
            option.textContent = floor.number;

            floorSelect.appendChild(option);

        });

    });


    floorSelect.addEventListener("change", async () => {

        const floorId = floorSelect.value;

        roomSelect.innerHTML = "<option>Loading...</option>";

        if (!floorId) return;

        const response = await fetch(`/issues/rooms/${floorId}`);
        const rooms = await response.json();

        roomSelect.innerHTML = "<option>Select Room</option>";

        rooms.forEach(room => {

            const option = document.createElement("option");

            option.value = room.id;
            option.textContent = room.name;

            roomSelect.appendChild(option);

        });

    });

});