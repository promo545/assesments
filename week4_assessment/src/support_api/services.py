from support_api.models import TicketCreate, TicketPatch, TicketResponse, TicketUpdate
from support_api.repository import TicketRepository


class TicketService:
    current_id = 0

    def __init__(self, repository: TicketRepository):
        self.repository = repository

    def create_ticket(self, create_ticket_request : TicketCreate):
        TicketService.current_id += 1

        ticket_id = TicketService.current_id
        ticket = TicketResponse(
                    id= ticket_id, 
                    subject=create_ticket_request.subject, 
                    description=create_ticket_request.description, 
                    severity=create_ticket_request.severity, 
                    resolved=False)

        return self.repository.save_ticket(ticket)

    def delete_ticket(self, ticket_id: int):
        return self.repository.delete_ticket(ticket_id)

    def update_ticket(self, ticket_id: int, update_ticket_request: TicketUpdate):
        return self.repository.update_ticket(ticket_id, update_ticket_request)

    def patch_ticket(self, ticket_id : int, patch_ticket_request : TicketPatch):
        return self.repository.patch_ticket(ticket_id, patch_ticket_request)
    
    def get_ticket(self, ticket_id : int):
        return self.repository.get_ticket(ticket_id)

    def get_tickets(self, limit: int = 10):
        return self.repository.get_all_tickets()[:limit]

