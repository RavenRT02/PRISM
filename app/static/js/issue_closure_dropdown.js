function toggleClosureForm() {
    const form = document.getElementById('closureForm');
    const button = document.getElementById('initiateClosureBtn');

    if (form.style.display === 'none') {
        form.style.display = 'block';
        button.textContent = 'Cancel Issue Closure';
    } else {
        form.style.display = 'none';
        button.textContent = 'Initiate Issue Closure';
    }
}