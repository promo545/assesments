import time

from fastapi import FastAPI, Request

from bookmark_api.routers.auth import router as auth_router
from bookmark_api.routers.bookmarks import router as bookmark_router
from bookmark_api.utils import logger

app = FastAPI()
app.include_router(bookmark_router)
app.include_router(auth_router)


@app.middleware("http")
async def request_timer(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    end = time.perf_counter()

    elapsed = end - start
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"
    logger.info(
        "%s %s -> %s in %.6fs",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response
