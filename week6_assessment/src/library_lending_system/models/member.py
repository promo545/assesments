import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from library_lending_system.models.base import Base

if TYPE_CHECKING:
    from library_lending_system.models.loan import Loan


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    loans: Mapped[list["Loan"]] = relationship(
        back_populates="member"
    )
