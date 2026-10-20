import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from library_lending_system.models.base import Base

if TYPE_CHECKING:
    from library_lending_system.models.loan import Loan


class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(nullable=False)

    author: Mapped[str] = mapped_column(nullable=False, index=True)

    isbn: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
    )
    
    total_copies: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    available_copies: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    loans: Mapped[list["Loan"]] = relationship(
        back_populates="book"
    )

    __table_args__ = (
        CheckConstraint(
            "total_copies > 0",
            name="ck_total_copies_positive",
        ),
        CheckConstraint(
            "available_copies >= 0",
            name="ck_available_copies_non_negative",
        ),
        CheckConstraint(
            "available_copies <= total_copies",
            name="ck_available_copies_not_above_total",
        ),
    )
