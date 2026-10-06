import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, foreign, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key = True, default = uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), nullable= False)
    email: Mapped[str] = mapped_column(String(255), nullable= False, unique= True, index= True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable= False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default= datetime.utcnow, nullable= False)

class BookMark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(primary_key= True, nullable= False)
    url : Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default= datetime.utcnow, nullable= False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable= False)
    last_modified_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable= True)
