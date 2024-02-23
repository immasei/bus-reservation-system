from flask import Blueprint, render_template, redirect, url_for, request, flash
import database

main = Blueprint("main", __name__)
session = {}
session['isadmin'] = False

@main.route("/")
def index():
    if('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('main.login'))
    return render_template('welcome.html', session=session)

@main.route('/login', methods=['POST', 'GET'])
def login():
    if(request.method == 'POST'):

        if(request.form['username'] == "" or request.form['password'] == ""):
            flash('Please fill in all required fields.', "warning")
            return redirect(url_for('main.index'))
        
        user = database.check_login(request.form['username'], request.form['password'])
        if(user is None or len(user) < 1):
            flash('There was an error logging you in.', "danger")
            return redirect(url_for('main.index'))
        
        # successful login :)
        session['username'] = request.form['username']
        session['logged_in'] = True
        session['isadmin'] = user['is_admin']
        flash('Login Successful', "success")
        return redirect(url_for('main.index'))
    else:
        return render_template('index.html', session=session)

@main.route('/logout')
def logout():
    session['logged_in'] = False
    flash('You have been logged out.', "warning")
    return redirect(url_for('main.index'))

@main.route("/tours")
def list_tours():
    tours = database.list_tours()

    return render_template('list_tours.html', session=session,
                           tours=tours)

@main.route("/tours/<tourid>")
def list_single_tour(tourid):
    tour = database.find_tour(tourid)
    schedules = database.find_schedules(tourid)

    return render_template('list_single_tour.html', session=session,
                           tour=tour,
                           schedules=schedules)

@main.route("/tours/<tourid>/<datetime>/<busid>")
def list_single_schedule(tourid, datetime, busid):
    schedule = database.find_single_schedule(tourid, datetime, busid)

    return render_template('list_single_schedule.html', session=session,
                           schedule=schedule)

@main.route("/tours/<tourid>/<datetime>/<busid>/seats", methods=['POST', 'GET'])
def book_seats(tourid, datetime, busid):
    if request.method == 'POST':
        telephone = request.form.get('telephone')
        email = request.form.get('email')
        seats = request.form.get('seats').split(',')
        customer_id = database.create_tickets(tourid, datetime, busid, telephone, email, seats)

        message = f'Booked seats: {", ".join(seats)}.\n'
        message += f'Your Customer ID is {customer_id}.\n'
        message += "Please go to Reservations to confirm your booking."

        flash(message, "success")

    schedule = database.find_single_schedule(tourid, datetime, busid)

    return render_template('book_seats.html', session=session,
                           schedule=schedule)

@main.route("/reservations")
def list_tickets():
    flash('Use Customer ID to search for your reservations.', 'warning')
    return render_template('list_tickets.html', session=session,
                           tickets=[],
                           customerid='{}')

@main.route("/reservations/search", methods=['POST', 'GET'])
def search_tickets_by_customer_id():
    if(request.method == 'POST'):
        customerid = request.form['searchbooking']
        tickets = database.search_tickets_by_customer(customerid)

        return render_template('list_tickets.html', session=session,
                                tickets=tickets,
                                customerid=customerid)
    else:
        return redirect(url_for('main.list_tickets'))

@main.route("/reservations/delete/<customerid>/<ticketid>")
def cancel_ticket(customerid, ticketid):
    tickets = database.cancel_ticket(customerid, ticketid)

    flash(f'{ticketid} has been cancelled.', 'success')
    return render_template('list_tickets.html', session=session,
                                tickets=tickets,
                                customerid=customerid)

@main.route("/reservations/<customerid>/<ticketid>/update")
def confirm_ticket(customerid, ticketid):
    tickets = database.confirm_ticket(customerid, ticketid)
    
    flash(f'{ticketid} has been confirmed.', 'success')
    return render_template('list_tickets.html', session=session,
                                tickets=tickets,
                                customerid=customerid)

@main.route("/tours/search", methods=['POST', 'GET'])
def search_tour_by_name():
    if(request.method == 'POST'):
        tours = database.search_tour_by_name(request.form['searchtour'])

        return render_template('list_tours.html', session=session,
                                tours = tours)
    else:
        return redirect(url_for('main.list_tours'))