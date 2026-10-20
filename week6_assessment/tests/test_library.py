from sqlalchemy import func, select

from library_lending_system.models import Book, Loan, Member


def book(client, copies=2, isbn="978-test", author="Ursula Le Guin"):
    response = client.post("/books", json={"title": "A Wizard of Earthsea", "author": author, "isbn": isbn, "total_copies": copies})
    assert response.status_code == 200
    return response.json()


def member(client):
    response = client.post("/members", json={"name": "Reader", "email": "reader@example.com"})
    assert response.status_code == 200
    return response.json()


def borrow(client, member_data, book_data):
    return client.post("/loans", json={"member_id": member_data["id"], "book_id": book_data["id"]})


def test_create_and_retrieve_book(client):
    created = book(client)
    assert client.get(f'/books/{created["id"]}').json() == created


def test_duplicate_isbn(client, session):
    book(client)
    response = client.post("/books", json={"title": "Duplicate", "author": "Other", "isbn": "978-test", "total_copies": 1})
    assert response.status_code == 409
    assert session.scalar(select(func.count()).select_from(Book)) == 1


def test_author_and_availability_filters(client):
    created = book(client)
    book(client, isbn="other", author="Another author")
    assert client.get("/books", params={"author": created["author"]}).json() == [created]
    assert len(client.get("/books", params={"only_available": True}).json()) == 2


def test_borrow_and_navigation(client, session):
    created, reader = book(client), member(client)
    response = borrow(client, reader, created)
    assert response.status_code == 200
    loan = session.scalar(select(Loan))
    assert loan.book.available_copies == 1
    assert loan.member.loans == [loan]
    assert loan.book.loans == [loan]
    assert loan.due_at > loan.borrowed_at
    assert client.get(f'/members/{reader["id"]}/loans').json()[0]["id"] == response.json()["id"]
    assert len(client.get("/loans", params={"only_active": True}).json()["loans"]) == 1


def test_unavailable_borrow_has_no_partial_changes(client, session):
    created, reader = book(client, copies=1), member(client)
    assert borrow(client, reader, created).status_code == 200
    assert borrow(client, reader, created).status_code == 409
    assert session.scalar(select(func.count()).select_from(Loan)) == 1
    assert session.scalar(select(Book.available_copies)) == 0


def test_return_and_double_return(client, session):
    created, reader = book(client, copies=1), member(client)
    loan = borrow(client, reader, created).json()
    path = f'/loans/{loan["id"]}/return'
    response = client.patch(path)
    assert response.status_code == 200
    assert response.json()["returned_at"] is not None
    assert session.scalar(select(Book.available_copies)) == 1
    assert client.patch(path).status_code == 409
    assert session.scalar(select(Book.available_copies)) == 1
    assert client.get("/loans", params={"only_active": True}).json()["loans"] == []


def test_copy_validation_metadata_and_delete(client):
    created = book(client)
    path = f'/books/{created["id"]}'
    assert client.put(path + "/add-copies", json={"copies": -1}).status_code == 422
    assert client.put(path + "/remove-copies", json={"copies": 2}).status_code == 409
    assert client.put(path + "/add-copies", json={"copies": 1}).json()["total_copies"] == 3
    assert client.put(path + "/remove-copies", json={"copies": 1}).json()["available_copies"] == 2
    assert client.patch(path, json={"title": "Updated"}).json()["title"] == "Updated"
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404


def test_preserve_borrowing_history(client):
    created, reader = book(client), member(client)
    borrow(client, reader, created)
    assert client.delete(f'/books/{created["id"]}').status_code == 409
    assert client.put(f'/books/{created["id"]}/remove-copies', json={"copies": 2}).status_code == 409


def test_missing_member_does_not_change_stock(client, session):
    import uuid
    created = book(client)
    assert borrow(client, {"id": str(uuid.uuid4())}, created).status_code == 404
    assert session.scalar(select(func.count()).select_from(Loan)) == 0
    assert session.scalar(select(Book.available_copies)) == 2


def test_failed_loan_insert_rolls_back_stock(client, session):
    from sqlalchemy import event
    from sqlalchemy.exc import SQLAlchemyError
    created, reader = book(client), member(client)

    def fail_insert(mapper, connection, target):
        raise SQLAlchemyError("Simulated loan insert failure")

    event.listen(Loan, "before_insert", fail_insert)
    try:
        assert borrow(client, reader, created).status_code == 500
    finally:
        event.remove(Loan, "before_insert", fail_insert)
    assert session.scalar(select(Book.available_copies)) == 2
    assert session.scalar(select(func.count()).select_from(Loan)) == 0


def test_failed_return_rolls_back_both_changes(client, session):
    from sqlalchemy import event
    from sqlalchemy.exc import SQLAlchemyError
    created, reader = book(client), member(client)
    loan = borrow(client, reader, created).json()

    def fail_update(mapper, connection, target):
        raise SQLAlchemyError("Simulated loan update failure")

    event.listen(Loan, "before_update", fail_update)
    try:
        assert client.patch(f'/loans/{loan["id"]}/return').status_code == 500
    finally:
        event.remove(Loan, "before_update", fail_update)
    assert session.scalar(select(Book.available_copies)) == 1
    assert session.scalar(select(Loan)).returned_at is None
