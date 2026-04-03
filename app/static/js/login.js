function copyEmailToHidden(targetId) {

    const emailField =
        document.querySelector("input[name='email']");

    if (!emailField.value) {

        alert("Please enter your email first.");

        return false;
    }

    document
        .getElementById(targetId)
        .value = emailField.value;
}

function togglePasswords(...fieldIds) {

    fieldIds.forEach(function(id) {

        const field = document.getElementById(id);

        if (!field) return;

        field.type = field.type === "password" ? "text" : "password";

    });

}