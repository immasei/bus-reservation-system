from flask import Blueprint, render_template, redirect, url_for, request
from datetime import datetime
import database

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return render_template('index.html')

@main.route("/tours")
def list_tours():
    tours = database.convert_utc()
    tours_status = database.get_tours_status(tours)

    return render_template('list_tours.html',
                           tours=tours, 
                           tours_status=tours_status)

@main.route("/tours/<tourid>")
def get_tour_detail(tourid):
    tours = database.convert_utc()

    tour = database.find_tour(tours, tourid)

    if tour is None:
        return redirect(url_for('main.list_tours'))

    tour_status = database.get_tour_status(tourid)
    floors_status = database.get_floors_status(tourid)
    employees = database.get_employees_detail(tour['employees_id'])
    schedules = database.get_tour_schedule(tourid)

    return render_template('tour_detail.html', 
                            tour=tour, 
                            floors_status=floors_status, 
                            tour_status=tour_status, 
                            employees=employees,
                            schedules=schedules)
        
@main.route("/tours/<tourid>/seats", methods=['POST', 'GET'])
def get_bus_layout(tourid):
    # UPDATE DB
    if request.method == 'POST':
        telephone = request.form.get('telephone')
        email = request.form.get('email')
        seats = request.form.get('seats').split(',')
        is_vip = request.form.get('status').split(',')

        database.create_tickets(tourid, telephone, email, seats, is_vip)

    tours = database.convert_utc()
    layout = database.get_bus_layout(tourid)
    tour = database.find_tour(tours, tourid)

    if tour is None:
        return redirect(url_for('main.list_tours'))

    return render_template('book_seats.html',
                            layout=layout,
                            tour=tour, 
                            customerid=f"C{database.get_next_customer_id()}")


@main.route("/tours/search", methods=['POST', 'GET'])
def search_tour_by_name():
    if(request.method == 'POST'):
        tours = database.search_tour_by_name(request.form['searchterm'])
        tours_status = database.get_tours_status(tours)
        return render_template('list_tours.html',
                                tours = tours, 
                                tours_status=tours_status)
    else:
        return redirect(url_for('main.list_tours'))

@main.route("/reservations")
def list_tickets():
    return render_template('list_tickets.html', 
                           tickets=[],
                           customerid='')

@main.route("/reservations/search", methods=['POST', 'GET'])
def search_tickets_by_customer_id():
    if(request.method == 'POST'):
        customerid = request.form['searchterm']
        tickets = database.search_tickets_by_customer_id(customerid)
    
        return render_template('list_tickets.html',
                                tickets=tickets,
                                customerid=customerid)
    else:
        return redirect(url_for('main.list_tickets'))

@main.route("/reservations/delete/<customerid>/<tourid>/<ticketid>")
def cancel_ticket(customerid, tourid, ticketid):
    tickets = database.cancel_ticket(customerid, tourid, ticketid)

    return render_template('list_tickets.html',
                                tickets=tickets,
                                customerid=customerid)

@main.route("/reservations/<customerid>/<tourid>/<ticketid>/update")
def confirm_ticket(customerid, tourid, ticketid):
    tickets = database.confirm_ticket(customerid, tourid, ticketid)

    print(tickets)

    return render_template('list_tickets.html',
                                tickets=tickets,
                                customerid=customerid)
