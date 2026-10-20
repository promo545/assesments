import uuid

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from library_lending_system.database import get_db
from library_lending_system.models.book import Book
from library_lending_system.schemas.book import BookCreate, BookResponse, BookUpdate, BookMetadataUpdate

router = APIRouter(prefix= "/books", tags=["books"])

@router.post("", response_model= BookResponse)
def create_book(book_data: BookCreate, session: Session = Depends(get_db)):
    book = Book(
           title = book_data.title,
           author = book_data.author,
           isbn = book_data.isbn,
           total_copies = book_data.total_copies,
           available_copies = book_data.total_copies,
            )

    try:
        session.add(book)
        session.commit()
        session.refresh(book)

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code = 409,
            detail= "isbn is duplicate",
                )
    return book

@router.get("/{book_id}", response_model= BookResponse)
def get_book_by_id(book_id: uuid.UUID, session: Session = Depends(get_db)):

    book = session.scalar(select(Book).where(Book.id == book_id))

    if book is None:
        raise HTTPException(
            status_code= 404,
            detail= "Book not found",
                )
    return book
@router.get("", response_model= list[BookResponse])
def get_books(author: str | None = Query(default= None), only_avaiable: bool = Query(default= False), only_available: bool = Query(default=False), session :Session = Depends(get_db)):
    
    stmt = select(Book)

    if author is not None:
        stmt = stmt.where(Book.author == author)
    if only_avaiable or only_available:
        stmt = stmt.where(Book.available_copies > 0)
    books = session.scalars(stmt).all()
    return books
@router.put("/{book_id}/add-copies", response_model= BookResponse)
def add_book_copies(book_id: uuid.UUID, update: BookUpdate, session: Session = Depends(get_db)):

    book = session.scalar(select(Book).where(Book.id == book_id).with_for_update())

    if book is None:
        raise HTTPException(status_code = 404, detail = "Book not found")

    book.total_copies += update.copies
    book.available_copies += update.copies
    
    session.commit()
    session.refresh(book)

    return book

@router.put("/{book_id}/remove-copies", response_model= BookResponse)
def remove_book_copies(book_id: uuid.UUID, update: BookUpdate, session: Session = Depends(get_db)):

    book = session.scalar(select(Book).where(Book.id == book_id).with_for_update())

    if book is None:
        raise HTTPException(status_code = 404, detail = "Book not found")

    if update.copies > book.available_copies or update.copies >= book.total_copies:
        raise HTTPException(status_code=409, detail="Cannot remove borrowed copies or the last total copy")

    book.total_copies -= update.copies
    book.available_copies -= update.copies
    
    session.commit()
    session.refresh(book)

    return book

@router.delete("/{book_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_book(book_id: uuid.UUID, session: Session = Depends(get_db)):
    
    book = session.scalar(select(Book).where(Book.id == book_id).with_for_update())

    if book is None:
        raise HTTPException(status_code = 404, detail = "Book not found")

    if book.loans:
        raise HTTPException(status_code=409, detail="Books with borrowing history cannot be deleted")

    session.delete(book)
    session.commit()



@router.patch("/{book_id}", response_model=BookResponse)
def update_book_metadata(book_id: uuid.UUID, update: BookMetadataUpdate, session: Session = Depends(get_db)):
    book = session.scalar(select(Book).where(Book.id == book_id).with_for_update())
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="ISBN already exists")
    return book
