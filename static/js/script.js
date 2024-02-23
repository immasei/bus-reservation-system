function addFlashMessage(category, message) {
    var flashMessagesContainer = document.getElementById('flash-messages');
    var existingFlashMessage = flashMessagesContainer.querySelector('.alert');

    if (existingFlashMessage) {
        // If a flash message already exists, replace its content with the new one
        existingFlashMessage.innerHTML = `
            <strong>${message}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        existingFlashMessage.classList.remove('alert-warning', 'alert-danger'); // Remove previous classes
        existingFlashMessage.classList.add('alert-' + category); // Add new class
    } else {
        // If no flash message exists, add a new one
        var div = document.createElement('div');
        div.classList.add('alert', 'alert-' + category, 'alert-dismissible', 'fade', 'show');
        div.setAttribute('role', 'alert');
        div.innerHTML = `
            <strong>${message}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        flashMessagesContainer.appendChild(div);
    }
}

document.getElementById("bookButton").addEventListener("click", function(event) {
    // prevent default form submission behavior
    event.preventDefault();

    var telephone = document.querySelector("input[name='search']").value.trim();
    var email = document.querySelector("input[name='email']").value.trim();
    
    // booked unsuccessful: missing details
    if (telephone === "" || email === "") {
        addFlashMessage('warning', "Please fill in both telephone and email.");
    } else {
        var bookedSeats = [];
        var seatsStatus = [];
        var seats = document.querySelectorAll(".seat input[type='checkbox']:checked");
        
        //booking unsuccessful: no seats checked
        if (seats.length === 0) {
            addFlashMessage('danger', "You haven't selected any seat.");
        } else {
            // get all seats checked in bookedSeats
            seats.forEach(function(seat) {
                bookedSeats.push(seat.id);

                // get all seats status (vip or not) in seatsStatus
                // if (seat.parentElement.classList.contains('yellow-seat')) {
                //     seatsStatus.push(true);
                // } else {
                //     seatsStatus.push(false);
                // }
                
            });

            // get list of all customers from all tours
            // var customers = JSON.parse(document.getElementById("hiddenCustomers").value);

            // var customerID = null;

            // customers.forEach(customer => {
            //     // matching phone & email
            //     if (customer.tel === telephone && customer.email === email) {
            //         customerID = customer.id;
            //         // returning customer
            //         alert("Booked seats: " + bookedSeats.join(", ") + ".\nYour Customer ID is " + customerID +".\nPlease go to Reservations to confirm your booking.");
            //     }
            // });
            
            // set values of hidden fields
            document.getElementById("hiddenTelephone").value = telephone;
            document.getElementById("hiddenEmail").value = email;
            document.getElementById("hiddenSeats").value = bookedSeats.join(",");
            // document.getElementById("hiddenSeatsStatus").value = seatsStatus.join(",");

            // submit form
            document.getElementById("bookingForm").submit();

            // new customers
            // if (customerID === null) {
            //     // receive get_next_customer_id from database.py
            //     customerID = document.getElementById("hiddenCustomerId").value;
            //     alert("Booked seats: " + bookedSeats.join(", ") + ".\nYour Customer ID is " + customerID +".\nPlease go to Reservations to confirm your booking.");
            // }
        }
    }
});