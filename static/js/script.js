document.getElementById("bookButton").addEventListener("click", function(event) {
    // prevent default form submission behavior
    event.preventDefault();

    var telephone = document.querySelector("input[name='search']").value.trim();
    var email = document.querySelector("input[name='email']").value.trim();
    
    // booked unsuccessful: missing details
    if (telephone === "" || email === "") {
        alert("Please fill in both telephone and email.");
    } else {

        var bookedSeats = [];
        var seatsStatus = [];
        var seats = document.querySelectorAll(".seat input[type='checkbox']:checked");
        
        //booking unsuccessful: no seats checked
        if (seats.length === 0) {
            alert("You haven't selected any seat.");
        } else {
            // get all seats checked in bookedSeats
            // get all seats status (vip or not) in seatsStatus
            seats.forEach(function(seat) {
                bookedSeats.push(seat.id);

                if (seat.parentElement.classList.contains('yellow-seat')) {
                    seatsStatus.push(true);
                } else {
                    seatsStatus.push(false);
                }
                
            });

            // get list of all customers from all tours
            var customers = JSON.parse(document.getElementById("hiddenCustomers").value);

            var customerID = null;

            customers.forEach(customer => {
                // matching phone & email
                if (customer.tel === telephone && customer.email === email) {
                    customerID = customer.id;
                    // returning customer
                    alert("Booked seats: " + bookedSeats.join(", ") + ".\nYour Customer ID is " + customerID +".\nPlease go to Reservations to confirm your booking.");
                }
            });
            
            // set values of hidden fields
            document.getElementById("hiddenTelephone").value = telephone;
            document.getElementById("hiddenEmail").value = email;
            document.getElementById("hiddenSeats").value = bookedSeats.join(",");
            document.getElementById("hiddenSeatsStatus").value = seatsStatus.join(",");

            // submit form
            document.getElementById("bookingForm").submit();

            // new customers
            if (customerID === null) {
                // receive get_next_customer_id from database.py
                customerID = document.getElementById("hiddenCustomerId").value;
                alert("Booked seats: " + bookedSeats.join(", ") + ".\nYour Customer ID is " + customerID +".\nPlease go to Reservations to confirm your booking.");
            }
        }
    }
});