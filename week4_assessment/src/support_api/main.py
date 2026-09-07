from fastapi import FastAPI
from support_api.services import TicketService
from support_api.exception_handlers import ticket_not_found_handler
from support_api.routers.ticket_endpoints import router as ticket_router
from support_api.exceptions import TicketNotFound

app = FastAPI()

app.include_router(ticket_router)
app.add_exception_handler(
    TicketNotFound,
    ticket_not_found_handler,
)
