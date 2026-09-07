from support_api.exceptions import TicketNotFound
from support_api.models import TicketPatch, TicketResponse, TicketUpdate


class TicketRepository:

    def __init__(self):
        self._tickets = {}
    
    def get_all_tickets(self):
        return list(self._tickets.values())

    def save_ticket(self, ticket: TicketResponse):
        self._tickets[ticket.id] = ticket
        return ticket

    def get_ticket(self, ticket_id: int):

        ticket = self._tickets.get(ticket_id)
        if ticket is None:
            raise TicketNotFound("Ticket could not be found")
        return ticket
    
    def update_ticket(self, ticket_id : int, updated_ticket_request: TicketUpdate):
        existing_ticket = self.get_ticket(ticket_id)
        
        updated_ticket = TicketResponse(
                    id = ticket_id,
                    subject= updated_ticket_request.subject,
                    description= updated_ticket_request.description,
                    severity= updated_ticket_request.severity,
                    resolved= updated_ticket_request.resolved
                    )
        self.save_ticket(updated_ticket)
        return updated_ticket

    def delete_ticket(self, ticket_id : int):
        ticket_to_be_deleted = self.get_ticket(ticket_id)
        del self._tickets[ticket_id]
        return ticket_to_be_deleted

    def patch_ticket(self, ticket_id: int, patch_ticket_request: TicketPatch):
        exsisting_ticket = self.get_ticket(ticket_id)

        changes = patch_ticket_request.model_dump(exclude_unset=True)
        merged_data = {**exsisting_ticket.model_dump(), **changes}
        updated_ticket = TicketResponse(**merged_data)

        self.save_ticket(updated_ticket)
        return updated_ticket

repository = TicketRepository()

def get_repository():
    return repository

        
            

