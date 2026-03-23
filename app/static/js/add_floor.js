const buildingSelect = document.querySelector("select[name='building_id']");
const floorList = document.querySelectorAll(".floor-list li");
const floorTitle = document.getElementById("floorListTitle");


// Hide floors initially

floorList.forEach(item => {
    item.style.display = "none";
});


buildingSelect.addEventListener("change", function () {

    const buildingId = this.value;

    floorList.forEach(item => {

        if (item.dataset.building === buildingId)
            item.style.display = "list-item";
        else
            item.style.display = "none";

    });

    const buildingName =
        this.options[this.selectedIndex].text;

    floorTitle.textContent =
        buildingId
        ? `Existing floors in ${buildingName}`
        : "Existing Floors";

});