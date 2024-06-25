from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Annotated
import sys

sys.path.insert(0, '../')
import database

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def get_reservations(request: Request):
    return templates.TemplateResponse(
        request=request, name='reservation.html',
        context={'tickets': [], 'customerid': '', 'message': {}}
    )

@router.post("/", response_class=HTMLResponse)
async def list_reservations(request: Request, customerid: Annotated[str, Form()]):
    tickets = database.search_tickets_by_customer(customerid, request.app.database)
    message = {'category': 'secondary', 'text': f'List all reservations for {customerid}.'}

    return templates.TemplateResponse(
        request=request, name='reservation.html',
        context={'tickets': tickets, 'customerid': customerid, 'message': message}
    )

@router.get("/{customerid}/{ticketid}/cancel", response_class=HTMLResponse)
def cancel_ticket(request: Request, customerid, ticketid):
    tickets = database.cancel_ticket(customerid, ticketid, request.app.database)
    message = {'category': 'success', 'text': f'{ticketid} has been cancelled.'}

    return templates.TemplateResponse(
        request=request, name='reservation.html',
        context={'tickets': tickets, 'customerid': customerid, 'message': message}
    )

@router.get("/{customerid}/{ticketid}/confirm", response_class=HTMLResponse)
def confirm_ticket(request: Request, customerid, ticketid):
    tickets = database.confirm_ticket(customerid, ticketid, request.app.database)
    message = {'category': 'success', 'text': f'{ticketid} has been confirmed.'}

    return templates.TemplateResponse(
        request=request, name='reservation.html',
        context={'tickets': tickets, 'customerid': customerid, 'message': message}
    )