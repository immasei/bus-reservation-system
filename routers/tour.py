from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
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
        context={'schedule': schedule, 'message': {}}
    )

@router.post("/{tourid}/{datetime}/{busid}/booking", response_class=HTMLResponse)
async def book_seats(request: Request, tourid, datetime, busid, booking: Booking = Depends()):
    # print(booking.seats)
    customer_id = database.create_tickets(tourid, datetime, busid, booking, request.app.database)
    schedule = database.find_single_schedule(tourid, datetime, busid, request.app.database)

    text = f'Booked seats: {", ".join(booking.seats)}. '
    text += f'Your Customer ID is {customer_id}. '
    text += "Please go to Reservations to confirm your booking."

    message = {'category': 'success', 'text': text}
    
    return templates.TemplateResponse(
        request=request, 
        name='booking.html', 
        context={'schedule': schedule, 'message': message}
    )

