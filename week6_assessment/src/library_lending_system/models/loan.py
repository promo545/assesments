import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Uuid, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from library_lending_system.models.base import Base

if TYPE_CHECKING:
    from library_lending_system.models.book import Book
    from library_lending_system.models.member import Member


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("members.id"),
        nullable=False,
    )

    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("books.id"),
        nullable=False,
    )

    borrowed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    due_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    member: Mapped["Member"] = relationship(
        back_populates="loans"
    )

    book: Mapped["Book"] = relationship(
        back_populates="loans"
    )

    __table_args__ = (
        Index("ix_loans_member_id", "member_id"),
        Index("ix_loans_book_id", "book_id"),
        Index("ix_loans_active_borrowed_at", "borrowed_at", postgresql_where=text("returned_at IS NULL")),
        CheckConstraint(
            "returned_at IS NULL OR returned_at >= borrowed_at",
            name="ck_return_date_is_not_before_borrow",
        ),
        CheckConstraint(
            "due_at >= borrowed_at",
            name="ck_due_is_not_before_borrow",
        ),
    )
