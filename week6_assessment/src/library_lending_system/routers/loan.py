from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from library_lending_system.database import get_db
from library_lending_system.models.book import Book
from library_lending_system.models.loan import Loan
from library_lending_system.models.member import Member
from library_lending_system.schemas.loan import LoanCreate, LoanResponse, LoanPage
import uuid

router = APIRouter(prefix="/loans", tags=["loans"])

MAX_DAYS_TO_LEND = 7


@router.post("", response_model=LoanResponse)
def create_loan(
    loan_data: LoanCreate,
    session: Session = Depends(get_db),
):
    # Check that member exists
    member = session.get(Member, loan_data.member_id)

    if member is None:
        raise HTTPException(
            status_code=404,
            detail="Member not found",
        )

    # Get book and lock the row until transaction finishes
    stmt = (
        select(Book)
        .where(Book.id == loan_data.book_id)
        .with_for_update()
    )

    book = session.scalar(stmt)

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    # Business rule
    if book.available_copies <= 0:
        raise HTTPException(
            status_code=409,
            detail="No copies available",
        )

    now = datetime.now()

    loan = Loan(
        member_id=loan_data.member_id,
        book_id=loan_data.book_id,
        borrowed_at=now,
        due_at=now + timedelta(days=MAX_DAYS_TO_LEND),
    )

    try:
        # Both changes belong to the same transaction
        book.available_copies -= 1
        session.add(loan)

        session.commit()

    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create loan",
        )

    session.refresh(loan)

    return loan

@router.patch("/{loan_id}/return", response_model=LoanResponse)
def return_book(
    loan_id: uuid.UUID,
    session: Session = Depends(get_db),
):
    loan = session.scalar(select(Loan).where(Loan.id == loan_id).with_for_update())

    if loan is None:
        raise HTTPException(
            status_code=404,
            detail="Loan not found",
        )

    if loan.returned_at is not None:
        raise HTTPException(
            status_code=409,
            detail="Loan has already been returned",
        )

    # Lock the book we're about to modify
    stmt = (
        select(Book)
        .where(Book.id == loan.book_id)
        .with_for_update()
    )

    book = session.scalar(stmt)

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    try:
        loan.returned_at = datetime.now()
        book.available_copies += 1

        session.commit()

    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to return book",
        )

    session.refresh(loan)

    return loan

@router.get("", response_model=LoanPage)
def get_loans(
    only_active: bool = Query(default=False),
    cursor: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db),
):
    stmt = select(Loan)

    if only_active:
        stmt = stmt.where(Loan.returned_at.is_(None))

    if cursor is not None:
        stmt = stmt.where(Loan.borrowed_at > cursor)

    stmt = stmt.order_by(Loan.borrowed_at).limit(limit)

    loans = session.scalars(stmt).all()

    return {
        "loans": loans,
        "cursor": loans[-1].borrowed_at if loans else None,
    }
