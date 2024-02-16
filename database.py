import json
from datetime import datetime, timezone

bus_file = 'jsondata/bus.json'
tour_file = 'jsondata/tour.json'
employee_file = 'jsondata/employee.json'

def read_json(file:str) -> dict:
    with open(file) as f:
        data = json.load(f)
        return data
    
def find_tour(tours, tourid):
    for tour in tours:
        if tour['id'] == tourid:
            return tour
        
def convert_utc():
    tours = read_json(tour_file).get('tours', [])

    # convert all utc time to DD-MM-YYY hh:mm format
    for tour in tours:
        routes = tour.get('routes', [])

        for stop in routes:
            departure_time = stop.get('departure_time', False)
            arrival_time = stop.get('arrival_time', False)

            if departure_time:
                time = datetime.fromisoformat(departure_time)
                stop['departure_time'] = time.strftime("%d-%m-%Y %H:%M")

            if arrival_time:
                time = datetime.fromisoformat(arrival_time)
                stop['arrival_time'] = time.strftime("%d-%m-%Y %H:%M")

        customers = tour.get('customers', [])
        for customer in customers:
            tickets = customer.get('tickets', [])

            for ticket in tickets:
                booking_date = ticket.get('booking_date', False)

                if booking_date:
                    time = datetime.fromisoformat(booking_date)
                    ticket['booking_date'] = time.strftime("%d-%m-%Y %H:%M")

    return tours

def get_tour_status(tour_id):
    floors_status = get_floors_status(tour_id)
    available_seats = 0
    total_seats = 0
    tour_status = {}

    for floor in floors_status:
        available_seats += floor['available']
        total_seats += floor['unavailable']+floor['available']

    tour_status['available_seats'] = available_seats
    tour_status['total_seats'] = total_seats

    return tour_status

def get_tours_status(tours):
    tours_status = {}

    for tour in tours:
        tours_status[tour['id']] = get_tour_status(tour['id'])

    return tours_status
                    
def set_occupied(tour_id):
    tours = read_json(tour_file).get('tours', [])
    buses = read_json(bus_file).get('buses', [])

    for tour in tours:
        if tour['id'] == tour_id:
            # for every tickets bought by customer from this tour, identify the seat id + bus id
            # then set seat as occupied in that bus
            # data remains in 'tickets', bus.json is just a blueprint for temporary use (ie verify all tickets of that trip using this bus)
            customers = tour.get('customers', [])
            bus_id = tour['bus_id']
            
            # get all tickets
            booked_seat_ids = []
            for customer in customers:
                tickets = customer.get('tickets', [])
                booked_seat_ids.extend([ticket['seat_id'] for ticket in tickets])

            # ticket contains seat_id -> seat occupied
            for bus in buses:
                if bus['id'] == bus_id:
                    floors = bus.get('floors', [])
                    for floor in floors:
                        seats = floor.get('seats', [])
                        for seat in seats:
                            if seat['id'] in booked_seat_ids:
                                seat['is_occupied'] = True
            break
    
    return buses
                    
def get_floors_status(tour_id):
    tours = read_json(tour_file).get('tours', [])
    buses = set_occupied(tour_id)
    floors_status = []

    for tour in tours:
        if tour['id'] == tour_id:
            bus_id = tour['bus_id']

            # get all seats that has been confirmed
            customers = tour.get('customers', [])
            confirmed_tickets = []
            for customer in customers:
                tickets = customer.get('tickets', [])
                confirmed_tickets.extend(ticket['seat_id'] for ticket in tickets if ticket['confirmed'])

            # stats
            for bus in buses:
                if bus['id'] == bus_id:
                    floors = bus.get('floors', [])
                    
                    for floor in floors:
                        seats = floor.get('seats', [])

                        unavailable = [seat['is_occupied'] for seat in seats].count(True)
                        confirmed = [seat['is_occupied'] for seat in seats if seat['id'] in confirmed_tickets].count(True)
                        processing = unavailable - confirmed

                        floor_status = {}
                        floor_status['id'] = floor['id']
                        floor_status['unavailable'] = unavailable   # ve da dat
                        floor_status['processing'] = processing     # ve dang cho xac nhan 
                        floor_status['confirmed'] = confirmed       # ve da xac nhan
                        floor_status['available'] = len(seats) - unavailable
                        floors_status.append(floor_status)

                    break
            break
                        
    return floors_status
            
def get_employees_detail(employee_ids):
    employees = read_json(employee_file).get('employees', [])
    in_charge = []

    for employee in employees:
        if employee['id'] in employee_ids:
            in_charge.append(employee)
    
    return in_charge

def get_tour_schedule(tour_id):
    tours = convert_utc()
    schedule = []

    for tour in tours:
        if tour['id'] == tour_id:
            routes = tour.get('routes', [])
            for stop in routes:
                
                data = {}
                data['id'] = stop['stop_id']
                data['name'] = stop['name']

                arrival = stop.get('arrival_time', False)
                departure = stop.get('departure_time', False)

                if arrival:
                    arrival = arrival.split()[1]
                if departure:
                    departure = departure.split()[1]

                if arrival and departure:
                    data['time'] = f'{arrival} - {departure}'
                elif arrival:
                    data['time'] = arrival
                elif departure:
                    data['time'] = departure
                else:
                    data['time'] = ''
                schedule.append(data)

            break

    return schedule

def fill_missing_seats(seats):
    full_seats = []

    for row in range(1, max(seat['row'] for seat in seats) + 1):
        # seats of current row
        row_seats = [seat for seat in seats if seat['row'] == row]
        # max column number
        max_column = max(seat['column'] for seat in row_seats)

        # fill in seats by mising column
        for column in range(1, max_column + 1):
            # seat of current column exists
            if not any(seat['column'] == column for seat in row_seats):
                # seat is missing
                full_seats.append({
                    "id": "",
                    "column": column,
                    "row": row,
                    "is_vip": False,
                    "is_occupied": False
                })

    # mising seats + original seats
    full_seats.extend(seats)
    # sort seats based on row & column
    full_seats.sort(key=lambda x: (x['row'], x['column']))

    return full_seats

def get_bus_layout(tour_id):
    tours = read_json(tour_file).get('tours', [])
    buses = set_occupied(tour_id)

    floors_layout = []

    for tour in tours:
        if tour['id'] == tour_id:
            bus_id = tour['bus_id']

            for bus in buses:
                if bus['id'] == bus_id:
                    floors = bus.get('floors', [])

                    for floor in floors:
                        # sorted then merge
                        seats = fill_missing_seats(floor.get('seats', []))
                        seats_by_row = {}

                        for seat in seats:
                            if seat['row'] not in seats_by_row:
                                seats_by_row[seat['row']] = [seat]
                            else:
                                seats_by_row[seat['row']].append(seat)

                        seats = []
                        for row in seats_by_row:
                            seats.append(seats_by_row[row])

                        floors_layout.append(seats)

                    break
            break
    
    return floors_layout

def get_new_ticket_id(tour_id):
    """
        ticket id is unique per tour_id (aka bus_id) only
    """
    tours = read_json(tour_file).get('tours', [])
    tickets = 0

    for tour in tours:
        if tour['id'] == tour_id:
            customers = tour.get('customers', [])
            for customer in customers:
                tickets += len(customer.get('tickets', []))
            break
   
    return tickets + 1

def get_new_customer_id():
    """
        customer id is unique across all tours
    """
    tours = read_json(tour_file).get('tours', [])
    customers_id = []

    for tour in tours:
        customers = tour.get('customers', [])
        customers_id.extend(customer['id'] for customer in customers)
   
    return len(set(customers_id)) + 1

def create_tickets(tour_id, customer_tel, customer_email, booked_seats, is_vip):
    tours = read_json(tour_file).get('tours', [])

    for tour in tours:
        if tour['id'] == tour_id:
            customers = tour.get('customers', [])
            
            price = tour.get('price', {})
            vip_price = price.get('vip', 0)
            no_vip_price = price.get('no-vip', 0)

            # create tickets for booked seats
            new_tickets = []
            current_id = get_new_ticket_id(tour_id)
            for seat in booked_seats:
                new_ticket = {
                    "id": f'TK{current_id}',
                    "booking_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
                    "seat_id": seat, 
                    "confirmed": False
                }
                current_id += 1

                # get ticket price
                new_ticket['price'] = no_vip_price
                if is_vip[booked_seats.index(seat)] == 'true':                
                    new_ticket['price'] = vip_price
                new_tickets.append(new_ticket)

            # returning customer
            found = False
            for customer in customers:
                if customer['tel'] == customer_tel and customer['email'] == customer_email:
                    customer.get('tickets', []).extend(new_tickets)
                    found = True
                break
                
            # new customer
            if not found:
                new_customer = {
                    "id": f'C{get_new_customer_id()}',
                    "tel": customer_tel,
                    "email": customer_email,
                    "tickets": new_tickets
                }
                tour.get('customers', []).append(new_customer)

    tour_data = {"tours": tours}

    with open(tour_file, 'w') as f:
        json.dump(tour_data, f, indent=4) 
    
    return tours

def search_tour_by_name(name):
    tours = read_json(tour_file).get('tours', [])
    matchings = []
    print(name.lower())

    for tour in tours:
        print(tour['name'].lower())
        if name.lower() in tour['name'].lower():
            matchings.append(tour)

    return matchings

def search_tickets_by_customer_id(customer_id):
    tours = convert_utc()
    reservations = []

    for tour in tours:
        routes = tour.get('routes', [])
        customers = tour.get('customers', [])
        price = tour.get('price', [])

        for customer in customers:
            if customer['id'] == customer_id:
                tickets = customer.get('tickets', [])
                for ticket in tickets:

                    reservation = {
                        "id": ticket['id'],
                        "tour": tour['name'],
                        "tourid": tour['id'],
                        "bus": tour["bus_id"],
                        "seat": ticket['seat_id'],
                        "departure": routes[0]['departure_time'],
                        "booking_date": ticket['booking_date'],
                        "price": ticket['price'],
                        "confirmed": ticket['confirmed']
                    } 

                    for type in price:
                        if ticket['price'] == price[type]:
                            reservation['type'] = type

                    reservations.append(reservation)
                break

    return reservations

def cancel_ticket(customer_id, tour_id, ticket_id):
    tours = read_json(tour_file).get('tours', [])

    for tour in tours:
        if tour['id'] == tour_id:
            customers = tour.get('customers', [])

            for customer in customers:
                if customer['id'] == customer_id:
                    tickets = customer.get('tickets', [])

                    for ticket in tickets:
                        if ticket['id'] == ticket_id:
                            customer['tickets'].remove(ticket)

                    # if len(tickets) == 0:
                    #     tour['customers'].remove(customer)
    
    tour_data = {"tours": tours}

    with open(tour_file, 'w') as f:
        json.dump(tour_data, f, indent=4) 

    remaining_tickets = search_tickets_by_customer_id(customer_id)

    return remaining_tickets

def confirm_ticket(customer_id, tour_id, ticket_id):
    tours = read_json(tour_file).get('tours', [])

    for tour in tours:
        if tour['id'] == tour_id:
            customers = tour.get('customers', [])

            for customer in customers:
                if customer['id'] == customer_id:
                    tickets = customer.get('tickets', [])

                    for ticket in tickets:
                        print(ticket['id'])
                        if ticket['id'] == ticket_id:
                            ticket['confirmed'] = True
    
    tour_data = {"tours": tours}

    with open(tour_file, 'w') as f:
        json.dump(tour_data, f, indent=4) 

    updated_tickets = search_tickets_by_customer_id(customer_id)

    return updated_tickets