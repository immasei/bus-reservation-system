function flash(category, message) {
    // https://www.w3schools.com/bootstrap/bootstrap_alerts.asp
    // https://stackoverflow.com/questions/17650776/add-remove-html-inside-div-using-javascript
    var flash = document.getElementById('flash');
    $('#flash').empty();
    flash.innerHTML = '<div class="alert alert-' + category +  ' alert-dismissible">' +
                        '<strong>' + message + '</strong>' +
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>';
}