from fastapi import APIRouter, Body, Request, Form, Response, HTTPException, status, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.encoders import jsonable_encoder
from typing import List
from datetime import datetime
import sys

sys.path.insert(0, '../')
import database
from models import Booking

router = APIRouter()
# https://fastapi.tiangolo.com/tutorial/bigger-applications/
templates = Jinja2Templates(directory="templates")

@router.get("/", response_description="List all ongoing tours", response_class=HTMLResponse)
async def list_tours(request: Request):
    tours = database.list_tours(request.app.database)
    # from pprint import pprint
    # pprint(database.find_single_schedule('T1', '2024-12-25T9:00', 'B3', request.app.database))
    # pprint(database.find_tickets('T1', '2024-12-25', '9:00', 'B3', request.app.database))
    # pprint(database.find_single_schedule('T1', '2024-12-25', '9:00', 'B3', request.app.database))
    # pprint(database.find_all_customers(request.app.database))
    return templates.TemplateResponse(
        request=request, name='tours.html', context={'tours': tours}
    )

@router.get("/{tourid}", response_description="Get a tour by id", response_class=HTMLResponse)
async def list_tour_schedules(request: Request, tourid):
    tour = database.find_tour(tourid, request.app.database)
    schedules = database.find_schedules(tourid, request.app.database)
    
    return templates.TemplateResponse(
        request=request, 
        name='tour_schedules.html', 
        context={'tour': tour, 'schedules': schedules}
    )

# <td><button><a href="{{ url_for('main.book_seats', tourid=schedule.id,  datetime=schedule.date ~ 'T' ~ schedule.slot, busid=schedule.bus_id) }}">Book now</a></button></td>

@router.get("/{tourid}/{datetime}/{busid}", response_description="Get a schedule by id", response_class=HTMLResponse)
async def get_schedule_detail(request: Request, tourid, datetime, busid):
    schedule = database.find_single_schedule(tourid, datetime, busid, request.app.database)
    
    return templates.TemplateResponse(
        request=request, 
        name='schedule_detail.html', 
        context={'schedule': schedule}
    )

@router.get("/{tourid}/{datetime}/{busid}/booking", response_class=HTMLResponse)
async def get_seats_layout(request: Request, tourid, datetime, busid):
    schedule = database.find_single_schedule(tourid, datetime, busid, request.app.database)
    
    return templates.TemplateResponse(
        request=request, 
        name='booking.html', 
        context={'schedule': schedule, 'message': ''}
    )

@router.post("/{tourid}/{datetime}/{busid}/booking", response_class=HTMLResponse)
async def book_seats(request: Request, tourid, datetime, busid, booking: Booking = Depends()):
    # print(booking.seats)
    customer_id = database.create_tickets(tourid, datetime, busid, booking, request.app.database)
    schedule = database.find_single_schedule(tourid, datetime, busid, request.app.database)

    message = f'Booked seats: {", ".join(booking.seats)}. '
    message += f'Your Customer ID is {customer_id}. '
    message += "Please go to Reservations to confirm your booking."
    
    return templates.TemplateResponse(
        request=request, 
        name='booking.html', 
        context={'schedule': schedule, 'message': message}
    )

