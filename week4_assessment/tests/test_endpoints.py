from support_api.exceptions import TicketNotFound
from support_api.models import TicketCreate, TicketPatch, TicketResponse, TicketUpdate


def test_get_existing_ticket_returns_200(api_client, mock_ticket_service, sample_ticket):
    mock_ticket_service.get_ticket.return_value = sample_ticket

    response = api_client.get("/tickets/1")

    assert response.status_code == 200
    assert response.json() == sample_ticket.model_dump()
    mock_ticket_service.get_ticket.assert_called_once_with(1)


def test_get_missing_ticket_uses_centralized_404_handler(
    api_client, mock_ticket_service
):
    mock_ticket_service.get_ticket.side_effect = TicketNotFound(
        "Ticket could not be found"
    )

    response = api_client.get("/tickets/99")

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket could not be found"}


def test_get_non_integer_ticket_id_does_not_call_service(
    api_client, mock_ticket_service
):
    response = api_client.get("/tickets/abc")

    assert response.status_code == 422
    mock_ticket_service.get_ticket.assert_not_called()


def test_get_all_tickets_uses_default_limit(api_client, mock_ticket_service):
    mock_ticket_service.get_tickets.return_value = []

    response = api_client.get("/tickets")

    assert response.status_code == 200
    assert response.json() == []
    mock_ticket_service.get_tickets.assert_called_once_with(10)


def test_get_all_tickets_passes_custom_limit(
    api_client, mock_ticket_service, sample_ticket
):
    mock_ticket_service.get_tickets.return_value = [sample_ticket]

    response = api_client.get("/tickets?limit=3")

    assert response.status_code == 200
    mock_ticket_service.get_tickets.assert_called_once_with(3)


def test_limit_zero_does_not_call_service(api_client, mock_ticket_service):
    response = api_client.get("/tickets?limit=0")

    assert response.status_code == 400
    assert response.json() == {"detail": "Limit must be within 1 and 100"}
    mock_ticket_service.get_tickets.assert_not_called()


def test_limit_above_one_hundred_does_not_call_service(
    api_client, mock_ticket_service
):
    response = api_client.get("/tickets?limit=101")

    assert response.status_code == 400
    mock_ticket_service.get_tickets.assert_not_called()


def test_non_integer_limit_does_not_call_service(api_client, mock_ticket_service):
    response = api_client.get("/tickets?limit=many")

    assert response.status_code == 422
    mock_ticket_service.get_tickets.assert_not_called()


def test_post_valid_body_returns_201_and_ticket_model(
    api_client, mock_ticket_service, sample_ticket
):
    mock_ticket_service.create_ticket.return_value = sample_ticket

    response = api_client.post(
        "/tickets",
        json={
            "subject": "Cannot sign in",
            "description": "The login form rejects my password",
            "severity": 3,
        },
    )

    assert response.status_code == 201
    assert response.json() == sample_ticket.model_dump()
    request = mock_ticket_service.create_ticket.call_args.args[0]
    assert isinstance(request, TicketCreate)
    assert request == TicketCreate(
        subject="Cannot sign in",
        description="The login form rejects my password",
        severity=3,
    )


def test_post_uses_description_and_severity_defaults(api_client, mock_ticket_service):
    def create_from_request(request):
        return TicketResponse(
            id=1,
            subject=request.subject,
            description=request.description,
            severity=request.severity,
            resolved=False,
        )

    mock_ticket_service.create_ticket.side_effect = create_from_request

    response = api_client.post("/tickets", json={"subject": "Printer issue"})

    assert response.status_code == 201
    assert response.json()["description"] is None
    assert response.json()["severity"] == 1
    assert response.json()["resolved"] is False


def test_post_does_not_pass_client_id_to_service(api_client, mock_ticket_service):
    mock_ticket_service.create_ticket.return_value = TicketResponse(
        id=1,
        subject="Printer issue",
        description=None,
        severity=1,
        resolved=False,
    )

    response = api_client.post(
        "/tickets", json={"id": 999, "subject": "Printer issue"}
    )

    request = mock_ticket_service.create_ticket.call_args.args[0]
    assert response.status_code == 201
    assert not hasattr(request, "id")
    assert response.json()["id"] == 1


def test_post_severity_below_range_does_not_call_service(
    api_client, mock_ticket_service
):
    response = api_client.post(
        "/tickets", json={"subject": "Invalid", "severity": 0}
    )

    assert response.status_code == 422
    mock_ticket_service.create_ticket.assert_not_called()


def test_post_severity_above_range_does_not_call_service(
    api_client, mock_ticket_service
):
    response = api_client.post(
        "/tickets", json={"subject": "Invalid", "severity": 6}
    )

    assert response.status_code == 422
    mock_ticket_service.create_ticket.assert_not_called()


def test_post_missing_subject_does_not_call_service(api_client, mock_ticket_service):
    response = api_client.post("/tickets", json={"severity": 3})

    assert response.status_code == 422
    mock_ticket_service.create_ticket.assert_not_called()


def test_put_passes_ticket_update_model(api_client, mock_ticket_service):
    mock_ticket_service.update_ticket.return_value = TicketResponse(
        id=5,
        subject="Replacement",
        description=None,
        severity=4,
        resolved=True,
    )

    response = api_client.put(
        "/tickets/5",
        json={
            "subject": "Replacement",
            "description": None,
            "severity": 4,
            "resolved": True,
        },
    )

    assert response.status_code == 200
    mock_ticket_service.update_ticket.assert_called_once_with(
        5,
        TicketUpdate(
            subject="Replacement",
            description=None,
            severity=4,
            resolved=True,
        ),
    )


def test_put_missing_required_field_does_not_call_service(
    api_client, mock_ticket_service
):
    response = api_client.put(
        "/tickets/5",
        json={"subject": "Replacement", "severity": 4},
    )

    assert response.status_code == 422
    mock_ticket_service.update_ticket.assert_not_called()


def test_put_invalid_severity_does_not_call_service(api_client, mock_ticket_service):
    response = api_client.put(
        "/tickets/5",
        json={"subject": "Replacement", "severity": 9, "resolved": False},
    )

    assert response.status_code == 422
    mock_ticket_service.update_ticket.assert_not_called()


def test_patch_passes_ticket_patch_model(api_client, mock_ticket_service):
    mock_ticket_service.patch_ticket.return_value = TicketResponse(
        id=2,
        subject="Existing subject",
        description="Existing description",
        severity=2,
        resolved=True,
    )

    response = api_client.patch("/tickets/2", json={"resolved": True})

    assert response.status_code == 200
    mock_ticket_service.patch_ticket.assert_called_once_with(
        2, TicketPatch(resolved=True)
    )


def test_patch_preserves_explicitly_supplied_null(api_client, mock_ticket_service):
    mock_ticket_service.patch_ticket.return_value = TicketResponse(
        id=2,
        subject="Existing subject",
        description=None,
        severity=2,
        resolved=False,
    )

    response = api_client.patch("/tickets/2", json={"description": None})

    request = mock_ticket_service.patch_ticket.call_args.args[1]
    assert response.status_code == 200
    assert request.model_fields_set == {"description"}
    assert request.model_dump(exclude_unset=True) == {"description": None}


def test_empty_patch_has_no_explicit_fields(api_client, mock_ticket_service, sample_ticket):
    mock_ticket_service.patch_ticket.return_value = sample_ticket

    response = api_client.patch("/tickets/1", json={})

    request = mock_ticket_service.patch_ticket.call_args.args[1]
    assert response.status_code == 200
    assert request.model_fields_set == set()


def test_patch_invalid_severity_does_not_call_service(
    api_client, mock_ticket_service
):
    response = api_client.patch("/tickets/1", json={"severity": 10})

    assert response.status_code == 422
    mock_ticket_service.patch_ticket.assert_not_called()


def test_delete_returns_204_without_body(api_client, mock_ticket_service):
    mock_ticket_service.delete_ticket.return_value = None

    response = api_client.delete("/tickets/3")

    assert response.status_code == 204
    assert response.content == b""
    mock_ticket_service.delete_ticket.assert_called_once_with(3)
