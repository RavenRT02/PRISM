const buildingSelect = document.getElementById("buildingSelect");
const floorSelect = document.getElementById("floorSelect");

const floorOptions = floorSelect.querySelectorAll("option");

const roomItems = document.querySelectorAll(".room-list li");
const roomTitle = document.getElementById("roomListTitle");


// Hide floors initially

floorOptions.forEach(option => {

    if (option.value !== "")
        option.style.display = "none";

});


// Hide rooms initially

roomItems.forEach(room => {
    room.style.display = "none";
});


// Building selection logic

buildingSelect.addEventListener("change", function () {

    const buildingId = this.value;

    floorSelect.value = "";

    floorOptions.forEach(option => {

        if (option.value === "")
            return;

        if (option.dataset.building === buildingId)
            option.style.display = "block";
        else
            option.style.display = "none";

    });

    // Hide rooms when building changes

    roomItems.forEach(room => {
        room.style.display = "none";
    });

    roomTitle.textContent = "Existing Rooms";

});


// Floor selection logic

floorSelect.addEventListener("change", function () {

    const floorId = this.value;
    const buildingName =
        buildingSelect.options[buildingSelect.selectedIndex].text;

    const floorName =
        this.options[this.selectedIndex].text;

    roomItems.forEach(room => {

        if (room.dataset.floor === floorId)
            room.style.display = "list-item";
        else
            room.style.display = "none";

    });

    if (floorId)
        roomTitle.textContent =
            `Existing rooms in ${buildingName}, ${floorName}`;
    else
        roomTitle.textContent = "Existing Rooms";

});