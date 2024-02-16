document.getElementById("bookButton").addEventListener("click", function(event) {
    // prevent the default form submission behavior
    event.preventDefault();

    var telephone = document.querySelector("input[name='search']").value.trim();
    var email = document.querySelector("input[name='email']").value.trim();
    
    if (telephone === "" || email === "") {
        alert("Please fill in both telephone and email.");
    } else {

        var bookedSeats = [];
        var seatsStatus = [];
        var seats = document.querySelectorAll(".seat input[type='checkbox']:checked");
        
        if (seats.length === 0) {
            alert("You haven't selected any seat.");
        } else {
            seats.forEach(function(seat) {
                bookedSeats.push(seat.id);

                if (seat.parentElement.classList.contains('yellow-seat')) {
                    seatsStatus.push(true);
                } else {
                    seatsStatus.push(false);
                }
                
            });
    
            alert("Booked seats: " + bookedSeats.join(", "));

            // set values of hidden fields
            document.getElementById("hiddenTelephone").value = telephone;
            document.getElementById("hiddenEmail").value = email;
            document.getElementById("hiddenSeats").value = bookedSeats.join(",");
            document.getElementById("hiddenSeatsStatus").value = seatsStatus.join(",");

            // submit form
            document.getElementById("bookingForm").submit();
        }
    }
});
