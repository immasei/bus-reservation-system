import json
from datetime import datetime, timezone

dir = 'jsondata/'
user_db = dir + 'user.json'
schedule_db = dir + 'schedule.json'
tour_db = dir + 'tour.json'
pricing_db = dir + 'pricing.json'
ticket_db = dir + 'ticket.json'
bus_db = dir + 'bus.json'
default_bus_db = dir + 'default_bus.json'

# pricing (xac dinh price + slot + date + tour + bus) + schedule (xac dinh slot + date + tour + bus) + default_price (xac dinh is_vip + row + col) lien ket voi nhau
# + ticket 

def read(file:str) -> dict:
    with open(file) as f:
        data = json.load(f)
        return data

def sort(schedules):
    def get_slot_datetime(schedule_slot):
        slot_time = datetime.strptime(schedule_slot["slot"], "%H:%M")
        return slot_time

    sorted_schedules = sorted(schedules, key=lambda x: x["date"])
    for schedule in sorted_schedules:
        schedule["slots"] = sorted(schedule["slots"], key=get_slot_datetime)

    return sorted_schedules

def check_login(username, password):
    '''
    Check Login given a username and password
    '''
    users = read(user_db).get('users', [])

    for user in users:
        if user['username'] == username and user['password'] == password:
            return user
    
def list_tours():
    '''
    tour.json in schedule.json 
    '''
    schedules = sort(read(schedule_db).get('schedules', []))
    tours = read(tour_db).get('tours', [])

    on_going = []
    for schedule in schedules:
        slots = schedule.get('slots', [])

        for slot in slots:
            on_going.extend(tour['id'] for tour in slot.get('tours', []))

    for tour in tours:
        if tour['id'] not in on_going:
            tours.remove(tour)
    
    return tours

def find_tour(tour_id):
    '''
    tour.json smr
    '''
    tours = read(tour_db).get('tours', [])
    tour_info = {}

    for tour in tours:
        if tour['id'] == tour_id:
            tour_info['id'] = tour_id
            tour_info['name'] = tour['name']
            tour_info['duration'] = tour['duration']
            tour_info['routes'] = tour['routes']
    
    return tour_info

def find_schedules(tour_id):
    '''
    schedule.json
    '''
    tour_summary = find_tour(tour_id)
    schedules = sort(read(schedule_db).get('schedules', []))
    tour_schedules = []

    for schedule in schedules:
        slots = schedule.get('slots', [])

        for slot in slots:
            tours = slot.get('tours', [])

            for tour in tours:
                if tour['id'] == tour_id:
                    buses = tour.get('buses', [])

                    for bus in buses:

                        tour_info = {}
                        tour_info['id'] = tour_id
                        tour_info['name'] = tour_summary['name']
                        tour_info['duration'] = tour_summary['duration']
                        tour_info['date'] = schedule['date']
                        tour_info['slot'] = slot['slot']
                        tour_info['bus_id'] = bus['id']
                        tour_info['routes'] = bus['routes']
                        tour_info['status'] = find_status(tour_id, tour_info['date'], tour_info['slot'], bus['id'])
                        tour_info['layout'] = set_occupied(tour_id, tour_info['date'], tour_info['slot'], bus['id'])

                        tour_schedules.append(tour_info)

    return tour_schedules

def find_single_schedule(tour_id, date_time, bus_id):
    date = date_time.split('T')[0]
    time = date_time.split('T')[1] 

    schedules = find_schedules(tour_id)
    tour_schedule = {}

    for schedule in schedules:
        if schedule['date'] == date and schedule['slot'] == time and schedule['bus_id'] == bus_id:
            tour_schedule = schedule

    return tour_schedule

def find_status(tour_id, date, time, bus_id):
    tour_status = {}
    layout = set_occupied(tour_id, date, time, bus_id)
    tour_status['total_seats'] = 0
    tour_status['total_available_seats'] = 0

    for floor in layout:
        tour_status['total_available_seats'] += floor['available_seats']
        tour_status['total_seats'] += floor['available_seats']
        tour_status['total_seats'] += floor['processing_seats']
        tour_status['total_seats'] += floor['confirmed_seats']

    return tour_status

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
                    "is_available": False,
                    "is_vip": False
                })

    # mising seats + original seats
    full_seats.extend(seats)
    # sort seats based on row & column
    full_seats.sort(key=lambda x: (x['row'], x['column']))

    return full_seats

def set_vip(tour_id, date, time, bus_id):
    # right join default bus (in default_bus) + bus layout (in pricing)
    default_bus = find_default_bus_layout(bus_id)
    current_bus = find_bus_layout(tour_id, date, time, bus_id)
    default_layout = {floor['id']: floor['seats'] for floor in default_bus}
    
    for floor in current_bus:
        seats = floor.get('seats', [])

        for seat in seats:
            default_seats = default_layout.get(floor['id'], [])

            for default_seat in default_seats:
                if seat['id'] == default_seat['id']:
                    seat['is_vip'] = default_seat['is_vip']
                    seat['row'] = default_seat['row']
                    seat['column'] = default_seat['column']

    return current_bus

def set_occupied(tour_id, date, time, bus_id):
    # join tickets (in ticket) + bus layout (from set_vip)
    tickets = find_tickets(tour_id, date, time, bus_id)
    bus_layout = set_vip(tour_id, date, time, bus_id)

    occupied_seats = {ticket['seat_id']: (ticket['customer_id'], ticket['confirmed']) for ticket in tickets}

    for floor in bus_layout:
        seats = floor.get('seats', [])
        floor['available_seats'] = len(seats)
        floor['processing_seats'] = 0
        floor['confirmed_seats'] = 0

        for seat in seats:
            seat['confirmed'] = False
            if seat['id'] in occupied_seats:
                seat['is_available'] = False
                seat['customer_id'] = occupied_seats[seat['id']][0]
                seat['confirmed'] = occupied_seats[seat['id']][1]

            if not seat['is_available']:
                floor['available_seats'] -= 1
                
                if seat['confirmed']:
                    floor['confirmed_seats'] += 1
                else:
                    floor['processing_seats'] += 1

    for floor in bus_layout:
        seats = fill_missing_seats(floor.get('seats', []))
        floor.pop('seats', None)
        
        seats_by_row = {}

        for seat in seats:
            if seat['row'] not in seats_by_row:
                seats_by_row[seat['row']] = [seat]
            else:
                seats_by_row[seat['row']].append(seat)

        seats = []
        for row in seats_by_row:
            seats.append(seats_by_row[row])

        floor['rows'] = seats

    return bus_layout   

def find_tickets(tour_id, date, time, bus_id):
    # ticket.json, find tickets for a particular tour
    tickets = find_all_tickets()
    tour_tickets = []

    for ticket in tickets:
        if ticket['tour_id'] == tour_id and ticket['date'] == date and ticket['slot'] == time and ticket['bus_id'] == bus_id:
            tour_tickets.append(ticket)

    return tour_tickets

def find_bus_layout(tour_id, date, time, bus_id):
    # pricing.json, find layout (floors and seats)
    prices = sort(read(pricing_db).get('prices', []))
    bus_layout = []

    for schedule in prices:
        if schedule['date'] == date:
            slots = schedule.get('slots', [])

            for slot in slots:
                if slot['slot'] == time:
                    tours = slot.get('tours', [])

                    for tour in tours:
                        if tour['id'] == tour_id:
                            buses = tour.get('buses', [])

                            for bus in buses:
                                if bus['id'] == bus_id:
                                    bus_layout = bus['floors']
                                    break # found bus
                            break # found tour
                    break # found slot
            break # found date

    return bus_layout

def find_default_bus_layout(bus_id):
    # default_bus.json, find layout (floors and seats)
    layouts = read(default_bus_db).get('bus_layouts', [])
    layout_id = find_layout_id(bus_id)
    default_bus = []

    for layout in layouts:
        if layout['id'] == layout_id:
            default_bus = layout.get('floors', [])
            break # found layout

    return default_bus
            
def find_layout_id(bus_id):
    # bus.json, find layout_id
    layout_id = None
    buses = read(bus_db).get('buses', [])

    for bus in buses:
        if bus['id'] == bus_id:
            layout_id = bus['layout_id']
            break # found bus
    
    return layout_id
    
def find_all_tickets():
    tickets_db = sort(read(ticket_db).get('tickets', []))
    all_tickets = []

    for schedule in tickets_db:
        slots = schedule.get('slots', [])

        for slot in slots:
            tours = slot.get('tours', [])

            for tour in tours:
                buses = tour.get('buses', [])

                for bus in buses:
                    customers = bus.get('customers', [])

                    for customer in customers:
                        tickets = customer.get('tickets', [])

                        for ticket in tickets:
                            ticket['date'] = schedule['date'] 
                            ticket['slot'] = slot['slot'] 
                            ticket['tour_id'] = tour['id']
                            ticket['tour_name'] = find_tour(tour['id'])['name']
                            ticket['bus_id'] = bus['id']
                            ticket['customer_id'] = customer['id']
                            ticket['booking_date'] = convert_utc(ticket['booking_date'])

                            bus_layout = set_vip(ticket['tour_id'], ticket['date'], ticket['slot'], ticket['bus_id'])
                            for floor in bus_layout:
                                seats = floor.get('seats', [])
                                
                                for seat in seats:
                                    if seat['id'] == ticket['seat_id']:
                                        ticket['price'] = seat['price']
                                        ticket['discount'] = seat['discount']

                                        ticket['type'] = 'no-vip'
                                        if seat['is_vip']:
                                            ticket['type'] = 'vip'
                                        break # found seat

                            all_tickets.append(ticket)
                
    return all_tickets

def find_all_customers():
    tickets = sort(read(ticket_db).get('tickets', []))
    all_customers = []

    for schedule in tickets:
        slots = schedule.get('slots', [])

        for slot in slots:
            tours = slot.get('tours', [])

            for tour in tours:
                buses = tour.get('buses', [])

                for bus in buses:
                    all_customers.extend(bus.get('customers', []))
    
    return all_customers

def find_ticket_id():
    tickets = find_all_tickets()
    tickets_id = [int(list(ticket['id'])[-1]) for ticket in tickets]

    if not tickets_id:
        return 1

    return max(tickets_id)+1

def find_customer_id(telephone, email):
    customers = find_all_customers()
    
    for customer in customers:
        if customer['telephone'] == telephone and customer['email'] == email:
            return customer['id']
    
    customers_id = [int(list(customer['id'])[-1]) for customer in customers]
    
    if not customers_id:
        return "C1"

    return f'C{max(customers_id)+1}'

def update_by_schedule(tour_id, date, time, bus_id):
    tickets = sort(read(ticket_db).get('tickets', []))

    found_date = [schedule for schedule in tickets if schedule['date'] == date]
    if not found_date:
        new_date = {
            "date": date,
            "slots": []
        }
        tickets.append(new_date)

    for schedule in tickets:
        if schedule['date'] == date:
            found_slot = [slot for slot in schedule.get('slots', []) if slot['slot'] == time]

            if not found_slot:
                new_slot = {
                    "slot": time,
                    "tours": []
                }

                schedule.get('slots', []).append(new_slot)
            break # found date

    for schedule in tickets:
        if schedule['date'] == date:
            slots = schedule.get('slots', [])

            for slot in slots:
                if slot['slot'] == time:
                    found_tour = [tour for tour in slot.get('tours', []) if tour['id'] == tour_id]

                    if not found_tour:
                        new_tour = {
                            "id": tour_id,
                            "buses": []
                        }
                        slot.get('tours', []).append(new_tour)
                    break # found slot
            break # found date

    for schedule in tickets:
        if schedule['date'] == date:
            slots = schedule.get('slots', [])

            for slot in slots:
                if slot['slot'] == time:
                    tours = slot.get('tours', [])

                    for tour in tours:
                        if tour['id'] == tour_id:
                            found_bus = [bus for bus in tour.get('buses', []) if bus['id'] == bus_id]

                            if not found_bus:
                                new_bus = {
                                    "id": bus_id,
                                    "customers": []
                                }
                                tour.get('buses', []).append(new_bus)
                            break # found tour
                    break # found slot
            break # found date

    return tickets

def create_tickets(tour_id, date_time, bus_id, telephone, email, seats):
    # ticket.json
    date = date_time.split('T')[0]
    time = date_time.split('T')[1] 
    tickets = update_by_schedule(tour_id, date, time, bus_id)
    customer_id = find_customer_id(telephone, email)
    
    new_tickets = []
    ticket_id = find_ticket_id()
    for seat_id in seats:
        new_ticket = {
            "id": f'TK{ticket_id}',
            "booking_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "seat_id": seat_id,
            "confirmed": False
        }
        new_tickets.append(new_ticket)
        ticket_id += 1

    for schedule in tickets:
        if schedule['date'] == date:
            slots = schedule.get('slots', [])

            for slot in slots:
                if slot['slot'] == time:
                    tours = slot.get('tours', [])

                    for tour in tours:
                        if tour['id'] == tour_id:
                            buses = tour.get('buses', [])

                            for bus in buses:
                                if bus['id'] == bus_id:
                                    customers = bus.get('customers', [])

                                    found_customer = False
                                    for customer in customers:
                                        # returning customer
                                        if customer['id'] == customer_id:
                                            customer.get('tickets', []).extend(new_tickets)
                                            found_customer = True
                                            break # found customer

                                    # new customer
                                    if not found_customer:
                                        new_customer = {
                                                "id": customer_id,
                                                "telephone": telephone,
                                                "email": email,
                                                "tickets": new_tickets
                                            }
                                
                                        bus.get('customers', []).append(new_customer)
                                    break # found bus
                            break # found tour
                    break # found slot     
            break # found date

    tickets_data = {"tickets": sort(tickets)}

    with open(ticket_db, 'w') as f:
        json.dump(tickets_data, f, indent=4)

    return customer_id

def search_tickets_by_customer(customer_id):
    # ticket.json, find tickets for a particular customer
    tickets = find_all_tickets()
    tour_tickets = [ticket for ticket in tickets if ticket['customer_id'] == customer_id.upper()]

    return tour_tickets

def convert_utc(utc_time):
    time = datetime.fromisoformat(utc_time)
    return time.strftime("%d-%m-%Y %H:%M")

def confirm_ticket(customer_id, ticket_id):
    tickets_db = sort(read(ticket_db).get('tickets', []))

    for schedule in tickets_db:
        slots = schedule.get('slots', [])

        for slot in slots:
            tours = slot.get('tours', [])

            for tour in tours:
                buses = tour.get('buses', [])

                for bus in buses:
                    customers = bus.get('customers', [])

                    for customer in customers:
                        if customer['id'] == customer_id:
                            tickets = customer.get('tickets', [])

                            for ticket in tickets:
                                if ticket['id'] == ticket_id:
                                    ticket['confirmed'] = True
                                    break # found ticket
                            break # found customer

    tickets_data = {"tickets": sort(tickets_db)}

    with open(ticket_db, 'w') as f:
        json.dump(tickets_data, f, indent=4)

    updated_tickets = search_tickets_by_customer(customer_id)

    return updated_tickets

def cancel_ticket(customer_id, ticket_id):
    tickets_db = sort(read(ticket_db).get('tickets', []))

    for schedule in tickets_db:
        slots = schedule.get('slots', [])

        for slot in slots:
            tours = slot.get('tours', [])

            for tour in tours:
                buses = tour.get('buses', [])

                for bus in buses:
                    customers = bus.get('customers', [])

                    for customer in customers:
                        if customer['id'] == customer_id:
                            tickets = customer.get('tickets', [])

                            for ticket in tickets:
                                if ticket['id'] == ticket_id:
                                    customer['tickets'].remove(ticket)
                                    break # found ticket

                            # if len(tickets) == 0:
                            #     tour['customers'].remove(customer)
                                
                            break # found customer

    tickets_data = {"tickets": sort(tickets_db)}

    with open(ticket_db, 'w') as f:
        json.dump(tickets_data, f, indent=4)

    updated_tickets = search_tickets_by_customer(customer_id)

    return updated_tickets

def search_tour_by_name(name):
    tours = list_tours()
    matchings = []

    for tour in tours:
        if name.lower() in tour['name'].lower():
            matchings.append(tour)

    return matchings      