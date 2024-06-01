# Bus Reservation System (n-level bus)

### Library Installation

```
  pip install flask
```

```
  pip install flask_socketio
```

### Run program

```
  python3 run.py
```

### ERROR 404: Access to 127.0.0.1 was denied

* Follow this link:
  
  * Press `Flush socket pools`

```
  chrome://net-internals/#sockets
```

### Functionalities

* `Homepage`:
  
  * Root `/`
  * Connect to `[Tours]` or `[Reservations]`  
 
 <p align='center'>
  <img align='center' src='readme-resources/homepage.png' width='750'/>
</p>

<br>
 
* `Tours`:
  * List all tours
  * Can connect to:
 
    * `[More]`: detailed information about a tour
      * Includes:
        
        * Employees
        * Tickets Avalablity
          
          * `sold` 
          * `processing` 
          * `available`
          
    * `[Book now]` to book tickets
    
  * Search bar
 
<p align='center'>
  <img align='center' src='readme-resources/all_tours.gif' width='750'/>
</p>

<br>

* `Bookings`
  
  * Required for success booking:
    
    * Fill in email + tel (no verification here)
    * Pick at least 1 seat
      
  * After success booking:
    
    * User is provided a customerID
    * customerID is per (email, tel)
    * Ticket is `Processing`: booked and wait for confirmations
    * Booked tickets are listed in `[Reservations]`, search by customerID
   
 
```
GUI - Booking
```  
<p align='center'>
  <img align='center' src='readme-resources/bus_layout.gif' width='750'/>
</p>

```
GUI - Picking seats
```
<p align='center'>
  <img align='center' src='readme-resources/pick_seats.gif' width='750'/>
</p>

```
GUI - Tickets bbooked
```
<p align='center'>
  <img align='center' src='readme-resources/get_customer_id.png' width='750'/>
</p>

<br>

* `Reservations`:
  * List all booked tickets of user using customerID
  * `Cancel` ticket or `Confirm` ticket.

  * If `Confirm`:
    * Tickets/ Seats is `Sold`
    * Confirmed tickets can't be `Cancel`led
      
  * If `Cancel`:
    * Ticket is deleted, seats become `Available`

 <p align='center'>
  <img align='center' src='readme-resources/find_reservations.png' width='750'/>
</p>
 
  
