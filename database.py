from fastapi import Depends
from typing import List
from datetime import datetime as dt, timezone
import pymongo

def convert_utc(utc_time):
    time = dt.fromisoformat(utc_time)
    return time.strftime("%d-%m-%Y %H:%M")

def qry(dbname, tourid, date, time, busid, mongodb):
    matching = mongodb[dbname].aggregate([
        { '$match': { 'date': date } },
        { '$unwind': '$slots'},  
        { '$match': { 'slots.slot': time } },
        { '$unwind': '$slots.tours'}, 
        { '$match': { 'slots.tours.id': tourid } },
        { '$unwind': '$slots.tours.buses'}, 
        { '$match': { 'slots.tours.buses.id': busid } }
    ])

    matching = list(matching)[0]
    return matching

def list_tours(mongodb):
    # find schedules gte today
    today = dt.today().strftime('%Y-%m-%d')
    schedules = mongodb["schedule"].find({"date": {"$gte": today}})

    on_going = []
    for schedule in schedules:
        slots = schedule.get('slots', [])

        for slot in slots:
            on_going.extend(tour['id'] for tour in slot.get('tours', []))

    on_going = list(set(on_going))

    tours = list(mongodb['tour'].find({ "id": {"$in": on_going} }))
    return tours

def find_tour(tourid, mongodb):
    tour = mongodb["tour"].find_one({"id": tourid})
    return tour

def find_schedules(tourid, mongodb):
    # https://stackoverflow.com/questions/8109122/how-to-sort-mongodb-with-pymongo
    # https://stackoverflow.com/questions/72316035/mongodb-how-to-filter-nested-array-of-objects
    # https://stackoverflow.com/questions/13449874/how-to-sort-array-inside-collection-record-in-mongodb
    schedules = mongodb['schedule'].aggregate([
        { '$unwind': '$slots'},       # flatten slots
        { '$unwind': '$slots.tours'}, # flatten slots.tours
        { '$match': { 'slots.tours.id': tourid } },
        { "$group": {                 # groupby date, slots/tours back to arr
            "_id": "$date",
            "slots": {
                "$push": {
                    "slot": "$slots.slot",
                    "tours": "$slots.tours"
            }}
        }},    
        { '$project': {               # rename groupby_id to date
            'date': '$_id',
            '_id': 0,
            'slots': 1
        }},
        { '$set': {                   # sort by slots.slot
            'slots': {
            '$sortArray': {
                'input': "$slots",
                'sortBy': { 'slot': pymongo.ASCENDING }
            }
            }
        }},                           # sort by date
        { '$sort': { 'date': pymongo.ASCENDING } }
    ])

    res = []
    for schedule in list(schedules):
        slots = schedule.get('slots', [])

        for slot in slots:
            buses = slot['tours'].get('buses', [])

            for bus in buses:
                _tour = {}
                _tour['date'] = schedule['date']
                _tour['slot'] = slot['slot']
                _tour['busid'] = bus['id']
                _tour['routes'] = bus['routes']
                _tour['status'] = find_status(tourid, _tour['date'], _tour['slot'], _tour['busid'], mongodb)

                res.append(_tour)

    return res

def find_single_schedule(tourid, datetime, busid, mongodb):
    date, time = datetime.split('T')
    tour = find_tour(tourid, mongodb)
    detail = qry('schedule', tourid, date, time, busid, mongodb)

    res = {}
    res['id'] = tourid
    res['name'] = tour['name']
    res['duration'] = tour['duration']
    res['date'] = date
    res['slot'] = time
    res['busid'] = busid
    res['routes'] = detail['slots']['tours']['buses']['routes']
    res['status'] = find_status(tourid, date, time, busid, mongodb)
    res['layout'] = set_occupied(tourid, date, time, busid, mongodb)

    return res
    
def find_layout_id(busid, mongodb):
    layout_id = mongodb["bus"].find_one({"id": busid})['layout_id']
    return layout_id 

def find_bus_layout(busid, mongodb):
    layout_id = find_layout_id(busid, mongodb)
    layout = mongodb["bus_layout"].find_one({"id": layout_id})['floors']
    return layout

def find_price_layout(tourid, date, time, busid, mongodb):
    price = qry('price', tourid, date, time, busid, mongodb)
    return price['slots']['tours']['buses']['floors']

def set_vip(tourid, date, time, busid, mongodb):
    bus_layout = find_bus_layout(busid, mongodb)
    price_layout = find_price_layout(tourid, date, time, busid, mongodb)

    floor_layout = {floor['id']: floor['seats'] for floor in bus_layout}
    
    for floor in price_layout:
        pseats = floor.get('seats', [])

        for pseat in pseats:
            bseats = floor_layout.get(floor['id'], [])

            for bseat in bseats:
                if pseat['id'] == bseat['id']:
                    pseat['is_vip'] = bseat['is_vip']
                    pseat['row'] = bseat['row']
                    pseat['column'] = bseat['column']

    return price_layout

def find_all_tickets(mongodb):
    tickets_db = mongodb['ticket'].aggregate([
         { '$set': {                   
            'slots': {
            '$sortArray': {
                'input': "$slots",
                'sortBy': { 'slot': pymongo.ASCENDING }
            }
            }
        }},           
        { '$sort': { 'date': pymongo.ASCENDING } }
    ])

    res = []

    for schedule in list(tickets_db):
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
                            ticket['tourid'] = tour['id']
                            ticket['tour_name'] = find_tour(tour['id'], mongodb)['name']
                            ticket['busid'] = bus['id']
                            ticket['customer_id'] = customer['id']
                            ticket['booking_date'] = convert_utc(ticket['booking_date'])

                            bus_layout = set_vip(ticket['tourid'], ticket['date'], ticket['slot'], ticket['busid'], mongodb)
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

                            res.append(ticket)
                
    return res

def find_tickets(tourid, date, time, busid, mongodb):
    # find tickets for a particular tour
    tickets = find_all_tickets(mongodb)
    res = []

    for ticket in tickets:
        if ticket['tourid'] == tourid and ticket['date'] == date \
            and ticket['slot'] == time and ticket['busid'] == busid:
            res.append(ticket)

    return res

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

def set_occupied(tourid, date, time, busid, mongodb):
    tickets = find_tickets(tourid, date, time, busid, mongodb)
    bus_layout = set_vip(tourid, date, time, busid, mongodb)

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

def find_status(tourid, date, time, busid, mongodb):
    tour_status = {}
    layout = set_occupied(tourid, date, time, busid, mongodb)
    tour_status['total_seats'] = 0
    tour_status['total_available_seats'] = 0

    for floor in layout:
        tour_status['total_available_seats'] += floor['available_seats']
        tour_status['total_seats'] += floor['available_seats']
        tour_status['total_seats'] += floor['processing_seats']
        tour_status['total_seats'] += floor['confirmed_seats']

    return tour_status

def create_space_for_ticket(tourid, date, time, busid, mongodb):
    mongodb['ticket'].update_one(
        { 'date': date },
        { '$setOnInsert': { 'date': date, 'slots': [] } },
        upsert=True
    )

    mongodb['ticket'].update_one(
        { 'date': date, 
          'slots.slot': { '$ne': time } },
        { '$push': { 'slots': { 'slot': time, 'tours': [] } }}
    )

    mongodb['ticket'].update_one(
        { 'date': date, 
          'slots.slot': time, 
          'slots.tours.id': {'$ne': tourid} },
        { '$push': { 'slots.$[slotElem].tours': { 'id': tourid, 'buses': [] } } },
        array_filters=[ { 'slotElem.slot': time} ]
    )

    mongodb['ticket'].update_one(
        { 'date': date, 
          'slots.slot': time, 
          'slots.tours.id': tourid, 
          'slots.tours.buses.id': { '$ne': busid } },
        { '$push': {
                'slots.$[slotElem].tours.$[tourElem].buses': { 'id': busid, 'customers': [] }
            }
        },
        array_filters=[ {'slotElem.slot': time}, {'tourElem.id': tourid} ]
    )

def find_all_customers(mongodb):
    tickets = mongodb['ticket'].aggregate([
         { '$set': {                   
            'slots': {
            '$sortArray': {
                'input': "$slots",
                'sortBy': { 'slot': pymongo.ASCENDING }
            }
            }
        }},           
        { '$sort': { 'date': pymongo.ASCENDING } },
        { '$unwind': '$slots' },
        { '$unwind': '$slots.tours' },
        { '$unwind': '$slots.tours.buses' },
        { '$unwind': '$slots.tours.buses.customers' },
        { '$group': {
            '_id': None,
            'customers': { '$push': '$slots.tours.buses.customers' }
        }},
        { '$project': {
            '_id': 0,
            'customers': 1
        }}
    ])
    return list(tickets)[0]['customers']

def find_customer_id(Booking, mongodb):
    customers = find_all_customers(mongodb)
    
    for customer in customers:
        if customer['telephone'] == Booking.telephone \
            and customer['email'] == Booking.email:
            return customer['id']
    
    customers_id = [int(customer['id'].lstrip('C')) for customer in customers]
    
    if not customers_id:
        return 'C1'

    return f'C{max(customers_id)+1}'

def find_ticket_id(mongodb):
    tickets = find_all_tickets(mongodb)
    tickets_id = [int(ticket['id'].lstrip('TK')) for ticket in tickets]

    if not tickets_id:
        return 1

    return max(tickets_id)

def create_tickets(tourid, datetime, busid, Booking, mongodb):
    date, time = datetime.split('T')
    customer_id = find_customer_id(Booking, mongodb)
    ticket_id = find_ticket_id(mongodb)
    create_space_for_ticket(tourid, date, time, busid, mongodb)

    tickets = []
    for seatid in Booking.seats:
        ticket = {
            "id": f'TK{ticket_id}',
            "booking_date": dt.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "seat_id": seatid,
            "confirmed": False
        }
        ticket_id += 1
        tickets.append(ticket)

    customer = { 'id': customer_id,
                 'telephone': Booking.telephone,
                 'email': Booking.email,
                 'tickets': [] }

    mongodb['ticket'].update_one(
        { 'date': date, 
          'slots.slot': time, 
          'slots.tours.id': tourid, 
          'slots.tours.buses.id': busid, 
          'slots.tours.buses.customers.id': { '$ne': customer_id } },
        { '$push': {
                'slots.$[slotElem].tours.$[tourElem].buses.$[busElem].customers': customer
        }},
        array_filters=[{'slotElem.slot': time}, {'tourElem.id': tourid}, {'busElem.id': busid}]
    )

    mongodb['ticket'].update_one(
        { 'date': date, 
          'slots.slot': time, 
          'slots.tours.id': tourid, 
          'slots.tours.buses.id': busid, 
          'slots.tours.buses.customers.id': customer_id },
        { '$push': {
                "slots.$[slotElem].tours.$[tourElem].buses.$[busElem].customers.$[custElem].tickets": 
                { '$each': tickets }
        }},
        array_filters=[{'slotElem.slot': time}, {'tourElem.id': tourid}, {'busElem.id': busid}, {'custElem.id': customer_id}]
    )

    return customer_id

def search_tickets_by_customer(customer_id, mongodb):
    tickets = find_all_tickets(mongodb)
    res = [ticket for ticket in tickets if ticket['customer_id'] == customer_id.upper()]

    return res

def confirm_ticket(customer_id, ticket_id, mongodb):
    mongodb['ticket'].update_one(
        { 'slots.tours.buses.customers': {
            '$elemMatch': { 'id': customer_id, 'tickets.id': ticket_id }
        }},
        { '$set': {
            'slots.$[].tours.$[].buses.$[].customers.$[customer].tickets.$[ticket].confirmed': True
        }},
        array_filters=[ { 'customer.id': customer_id }, { 'ticket.id': ticket_id } ]
    )

    tickets = search_tickets_by_customer(customer_id, mongodb)
    return tickets

def cancel_ticket(customer_id, ticket_id, mongodb):
    mongodb['ticket'].update_one(
        { 'slots.tours.buses.customers.id': customer_id },
        { '$pull': {
            'slots.$[].tours.$[].buses.$[].customers.$[customer].tickets': { 'id': ticket_id }
        }},
        array_filters=[ { 'customer.id': customer_id } ]
    )

    tickets = search_tickets_by_customer(customer_id, mongodb)
    return tickets