from fastapi.responses import JSONResponse

async def ticket_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )
