from fastapi import Depends, HTTPException

from support_api.repository import TicketRepository, get_repository
from support_api.services import TicketService


def get_limit(limit: int = 10) -> int:
    if limit < 1 or limit > 100:
        raise HTTPException(
                status_code= 400,
                detail= "Limit must be within 1 and 100")
    return limit


def get_ticket_service(repository: TicketRepository = Depends(get_repository)):
    return TicketService(repository)
