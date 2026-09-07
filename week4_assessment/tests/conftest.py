from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from support_api.dependencies import get_ticket_service
from support_api.main import app
from support_api.models import TicketResponse
from support_api.repository import TicketRepository, repository
from support_api.services import TicketService


@pytest.fixture
def repository_mock():
    return Mock(spec=TicketRepository)


@pytest.fixture
def ticket_service(repository_mock):
    TicketService.current_id = 0
    service = TicketService(repository_mock)

    yield service

    TicketService.current_id = 0


@pytest.fixture
def sample_ticket():
    return TicketResponse(
        id=1,
        subject="Cannot sign in",
        description="The login form rejects my password",
        severity=3,
        resolved=False,
    )


@pytest.fixture
def mock_ticket_service():
    return Mock(spec=TicketService)


@pytest.fixture
def api_client(mock_ticket_service):
    def override_ticket_service():
        return mock_ticket_service

    app.dependency_overrides[get_ticket_service] = override_ticket_service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def real_client():
    app.dependency_overrides.clear()
    repository._tickets.clear()
    TicketService.current_id = 0

    with TestClient(app) as client:
        yield client

    repository._tickets.clear()
    TicketService.current_id = 0
    app.dependency_overrides.clear()
