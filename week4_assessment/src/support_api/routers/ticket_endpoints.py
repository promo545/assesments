from fastapi import APIRouter, Depends, status

from support_api.dependencies import get_limit, get_ticket_service
from support_api.models import TicketCreate, TicketPatch, TicketResponse, TicketUpdate
from support_api.services import TicketService

router = APIRouter(prefix= "/tickets", tags= ["tickets"])


@router.post("", response_model= TicketResponse, status_code= status.HTTP_201_CREATED)
def create_ticket(ticket_request: TicketCreate, ticket_service: TicketService = Depends(get_ticket_service)) -> TicketResponse:
    ticket = ticket_service.create_ticket(ticket_request)
    return ticket


@router.get("", response_model= list[TicketResponse], status_code= status.HTTP_200_OK)
def get_tickets(limit: int = Depends(get_limit), ticket_service: TicketService = Depends(get_ticket_service))-> list[TicketResponse]:
    tickets = ticket_service.get_tickets(limit)
    return tickets
    
@router.get("/{ticket_id}", response_model= TicketResponse)
def get_ticket(ticket_id: int, ticket_service: TicketService = Depends(get_ticket_service)) -> TicketResponse:
    
    ticket = ticket_service.get_ticket(ticket_id)
    return ticket


@router.put("/{ticket_id}", response_model= TicketResponse)
def update_ticket(ticket_id: int, ticket_update_request: TicketUpdate, ticket_service: TicketService = Depends(get_ticket_service)):

    ticket =  ticket_service.update_ticket(ticket_id, ticket_update_request)
    return ticket

@router.delete("/{ticket_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, ticket_service: TicketService = Depends(get_ticket_service)):
    ticket_service.delete_ticket(ticket_id)

@router.patch("/{ticket_id}", response_model= TicketResponse, status_code= status.HTTP_200_OK)
def update_ticket_partially(ticket_id: int, ticket_patch: TicketPatch, ticket_service: TicketService = Depends(get_ticket_service)):
    return ticket_service.patch_ticket(ticket_id, ticket_patch)
