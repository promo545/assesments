import pytest

from support_api.exceptions import TicketNotFound
from support_api.models import TicketCreate, TicketPatch, TicketResponse, TicketUpdate


def return_saved_ticket(ticket):
    return ticket


def test_create_ticket_returns_correct_ticket(ticket_service, repository_mock):
    repository_mock.save_ticket.side_effect = return_saved_ticket
    request = TicketCreate(
        subject="Cannot sign in",
        description="The login form rejects my password",
        severity=3,
    )

    ticket = ticket_service.create_ticket(request)

    assert isinstance(ticket, TicketResponse)
    assert ticket.id == 1
    assert ticket.subject == "Cannot sign in"
    assert ticket.description == "The login form rejects my password"
    assert ticket.severity == 3
    assert ticket.resolved is False


def test_create_ticket_saves_created_ticket(ticket_service, repository_mock):
    repository_mock.save_ticket.side_effect = return_saved_ticket

    ticket = ticket_service.create_ticket(TicketCreate(subject="Printer issue"))

    repository_mock.save_ticket.assert_called_once_with(ticket)


def test_create_ticket_uses_creation_defaults(ticket_service, repository_mock):
    repository_mock.save_ticket.side_effect = return_saved_ticket

    ticket = ticket_service.create_ticket(TicketCreate(subject="Printer issue"))

    assert ticket.description is None
    assert ticket.severity == 1
    assert ticket.resolved is False


def test_create_ticket_assigns_sequential_ids(ticket_service, repository_mock):
    repository_mock.save_ticket.side_effect = return_saved_ticket

    first_ticket = ticket_service.create_ticket(TicketCreate(subject="First"))
    second_ticket = ticket_service.create_ticket(TicketCreate(subject="Second"))

    assert first_ticket.id == 1
    assert second_ticket.id == 2


def test_get_ticket_delegates_ticket_id(ticket_service, repository_mock, sample_ticket):
    repository_mock.get_ticket.return_value = sample_ticket

    ticket = ticket_service.get_ticket(1)

    assert ticket == sample_ticket
    repository_mock.get_ticket.assert_called_once_with(1)


def test_get_ticket_propagates_ticket_not_found(ticket_service, repository_mock):
    repository_mock.get_ticket.side_effect = TicketNotFound("Ticket could not be found")

    with pytest.raises(TicketNotFound):
        ticket_service.get_ticket(99)


def test_get_tickets_uses_default_limit(ticket_service, repository_mock):
    repository_mock.get_all_tickets.return_value = [
        TicketResponse(
            id=number,
            subject=f"Ticket {number}",
            description=None,
            severity=1,
            resolved=False,
        )
        for number in range(1, 13)
    ]

    tickets = ticket_service.get_tickets()

    assert len(tickets) == 10
    repository_mock.get_all_tickets.assert_called_once_with()


def test_get_tickets_uses_requested_limit(ticket_service, repository_mock):
    repository_mock.get_all_tickets.return_value = [
        TicketResponse(
            id=number,
            subject=f"Ticket {number}",
            description=None,
            severity=1,
            resolved=False,
        )
        for number in range(1, 6)
    ]

    tickets = ticket_service.get_tickets(limit=2)

    assert [ticket.id for ticket in tickets] == [1, 2]


def test_update_ticket_delegates_model(ticket_service, repository_mock, sample_ticket):
    request = TicketUpdate(
        subject="Updated subject",
        description="Updated description",
        severity=2,
        resolved=True,
    )
    repository_mock.update_ticket.return_value = sample_ticket

    result = ticket_service.update_ticket(1, request)

    assert result == sample_ticket
    repository_mock.update_ticket.assert_called_once_with(1, request)


def test_patch_ticket_delegates_model(ticket_service, repository_mock, sample_ticket):
    request = TicketPatch(resolved=True)
    repository_mock.patch_ticket.return_value = sample_ticket

    result = ticket_service.patch_ticket(1, request)

    assert result == sample_ticket
    repository_mock.patch_ticket.assert_called_once_with(1, request)


def test_delete_ticket_delegates_ticket_id(ticket_service, repository_mock, sample_ticket):
    repository_mock.delete_ticket.return_value = sample_ticket

    result = ticket_service.delete_ticket(1)

    assert result == sample_ticket
    repository_mock.delete_ticket.assert_called_once_with(1)
