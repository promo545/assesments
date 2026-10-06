import uuid

from fastapi import BackgroundTasks, Depends, HTTPException
from redis import Redis
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from bookmark_api.database import get_db
from bookmark_api.models import BookMark
from bookmark_api.redis_client import get_redis_client
from bookmark_api.schemas import BookMarkCreate, BookMarkUpdate
from bookmark_api.utils import logger, send_notification_to_user, write_audit_log

REDIS_SUMMARY_KEY_PREFIX = "bookmark:summary:"
SUMMARY_TTL_SECONDS = 60


def summary_key(user_id: uuid.UUID) -> str:
    """The one place that defines the per-user summary cache key."""
    return f"{REDIS_SUMMARY_KEY_PREFIX}{user_id}"


class BookmarkService:
    def __init__(self, session: Session, redis_client: Redis, background_task: BackgroundTasks):
        self.session = session
        self.redis_client = redis_client
        self.background_task = background_task

    def create(self, user_id: uuid.UUID, data: BookMarkCreate) -> BookMark:
        bookmark = BookMark(
            url=data.url,
            title=data.title,
            category=data.category,
            notes=data.notes,
            user_id=user_id,  # always from the authenticated user, never from the client
        )
        self.session.add(bookmark)
        self.session.commit()
        self.background_task.add_task(write_audit_log, "Bookmark created. sending notification to user...")
        self.background_task.add_task(send_notification_to_user)
        self.session.refresh(bookmark)
        self.redis_client.delete(summary_key(user_id))
        return bookmark

    def get_all_booksmarks(self, user_id: uuid.UUID, page: int, page_size: int, category: str | None = None):
        offset = (page - 1) * page_size
        stmt = select(BookMark).where(BookMark.user_id == user_id)
        if category:
            stmt = stmt.where(BookMark.category == category)
        stmt = stmt.order_by(BookMark.id).offset(offset).limit(page_size)
        return self.session.scalars(stmt).all()

    def get_bookmark_by_id(self, user_id: uuid.UUID, bookmark_id: int):
        stmt = select(BookMark).where(BookMark.user_id == user_id, BookMark.id == bookmark_id)

        try:
            bookmark = self.session.scalar(stmt)
        except SQLAlchemyError:
            raise HTTPException(status_code=503, detail="Something went wrong")

        if bookmark is None:
            raise HTTPException(status_code=404, detail=f"Bookmark with {bookmark_id} not found")
        return bookmark

    def update_bookmark(self, bookmark_id: int, data: BookMarkUpdate, user_id: uuid.UUID):
        stmt = select(BookMark).where(BookMark.user_id == user_id, BookMark.id == bookmark_id)
        existing_bookmark = self.session.scalar(stmt)
        if existing_bookmark is None:
            raise HTTPException(status_code=404, detail="Bookmark not found")

        for field, value in data.model_dump().items():
            setattr(existing_bookmark, field, value)

        self.session.commit()
        self.redis_client.delete(summary_key(user_id))
        self.session.refresh(existing_bookmark)
        return existing_bookmark

    def delete_bookmark(self, bookmark_id: int, user_id: uuid.UUID):
        stmt = select(BookMark).where(BookMark.user_id == user_id, BookMark.id == bookmark_id)
        existing_bookmark = self.session.scalar(stmt)

        if existing_bookmark is None:
            raise HTTPException(status_code=404, detail="Bookmark not found")

        try:
            self.session.delete(existing_bookmark)
            self.session.commit()
            self.redis_client.delete(summary_key(user_id))
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.info("Failed to delete bookmark %s: %s", bookmark_id, e)
            raise HTTPException(status_code=500, detail="Something went wrong")

        return {"message": "Deleted successfully"}

    def get_bookmark_summary(self, user_id: uuid.UUID):
        key = summary_key(user_id)

        # cache hit: no SQL is executed. Redis returns strings, so convert here.
        cached = self.redis_client.hgetall(key)
        if cached:
            return {
                "total_bookmarks": int(cached["total_bookmarks"]),
                "distinct_categories": int(cached["distinct_categories"]),
            }

        # cache miss: aggregate in SQL, then store with a TTL
        stmt = select(
            func.count(BookMark.id),
            func.count(func.distinct(BookMark.category)),
        ).where(BookMark.user_id == user_id)
        total_bookmarks, distinct_categories = self.session.execute(stmt).one()

        # one pipeline (MULTI/EXEC) so an entry can never exist without its TTL
        pipe = self.redis_client.pipeline()
        pipe.hset(
            key,
            mapping={
                "total_bookmarks": str(total_bookmarks),
                "distinct_categories": str(distinct_categories),
            },
        )
        pipe.expire(key, SUMMARY_TTL_SECONDS)
        pipe.execute()

        return {
            "total_bookmarks": total_bookmarks,
            "distinct_categories": distinct_categories,
        }


def get_bookmark_service(
    background_task: BackgroundTasks,
    session: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis_client),
) -> BookmarkService:
    return BookmarkService(session, redis_client, background_task)
