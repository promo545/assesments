from fastapi import FastAPI
from library_lending_system.routers.member import router as member_router
from library_lending_system.routers.book import router as book_router

import library_lending_system.models
app = FastAPI()

app.include_router(member_router)
app.include_router(book_router)

from library_lending_system.routers.loan import router as loan_router

app.include_router(loan_router)
