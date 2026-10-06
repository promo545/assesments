from fastapi import APIRouter, Depends, Query

from bookmark_api.auth import get_current_user
from bookmark_api.models import User
from bookmark_api.schemas import BookMarkCreate, BookMarkResponse, BookMarkUpdate
from bookmark_api.services import BookmarkService, get_bookmark_service

router = APIRouter(prefix="", tags=["bookmarks"])


@router.post("/bookmarks", response_model=BookMarkResponse, status_code=201)
def create_bookmark(
    data: BookMarkCreate,
    user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    return service.create(user.id, data)


@router.get("/bookmarks", response_model=list[BookMarkResponse])
def get_all_booksmarks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: str | None = Query(None),
    user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    return service.get_all_booksmarks(user.id, page, page_size, category)


# Must be declared BEFORE "/bookmarks/{bookmark_id}", otherwise FastAPI would try
# to parse the word "summary" as an integer bookmark id and return 422.
@router.get("/bookmarks/summary")
def get_bookmarks_summary(
    user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    return service.get_bookmark_summary(user.id)


@router.get("/bookmarks/{bookmark_id}", response_model=BookMarkResponse)
def get_bookmark(
    bookmark_id: int,
    user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    return service.get_bookmark_by_id(user.id, bookmark_id)


@router.put("/bookmarks/{bookmark_id}", response_model=BookMarkResponse)
def update_bookmark(
    data: BookMarkUpdate,
    bookmark_id: int,
    user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    return service.update_bookmark(bookmark_id, data, user.id)


@router.delete("/bookmarks/{bookmark_id}")
def delete_bookmark(
    bookmark_id: int,
    user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    return service.delete_bookmark(bookmark_id, user.id)
