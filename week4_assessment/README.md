# Support Ticket API

A small FastAPI application for creating and managing customer support tickets. It
uses an in-memory repository so the project can focus on routing, validation,
dependency injection, application layering, exception handling, and testing.

## Project structure

```text
src/support_api/
├── main.py                 # FastAPI application setup
├── models.py               # Pydantic request and response models
├── repository.py           # In-memory ticket persistence
├── services.py             # Application behavior
├── dependencies.py         # FastAPI dependency providers
├── exceptions.py           # Domain exceptions
├── exception_handlers.py   # Domain-to-HTTP error translation
└── routers/
    └── ticket_endpoints.py # HTTP routes

tests/
├── conftest.py             # Shared fixtures and dependency overrides
├── test_services.py        # Service unit tests
├── test_endpoints.py       # Isolated HTTP endpoint tests
└── test_integration.py     # Real-layer workflows
```

The dependency flow is:

```text
HTTP route -> TicketService -> TicketRepository -> in-memory dictionary
```

Routes deal with HTTP input and output, the service coordinates application
behavior, and the repository owns storage. Routers never access the storage
dictionary directly.

## Setup

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest -q
```

Editable installation makes the `support_api` package importable while keeping it
connected to the files in `src`, so source changes are available without
reinstalling the project.

## API endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| `POST` | `/tickets` | Create a ticket and return `201` |
| `GET` | `/tickets?limit=10` | List tickets with a limit from 1 to 100 |
| `GET` | `/tickets/{ticket_id}` | Get one ticket |
| `PUT` | `/tickets/{ticket_id}` | Fully replace a ticket |
| `PATCH` | `/tickets/{ticket_id}` | Partially update supplied fields |
| `DELETE` | `/tickets/{ticket_id}` | Delete a ticket and return `204` |

Creation defaults `description` to `null`, `severity` to `1`, and `resolved` to
`false`. Severity must be between 1 and 5. A patch uses Pydantic's
`model_dump(exclude_unset=True)` so omitted fields remain unchanged while an
explicitly supplied `null` description is preserved.

## Exception boundaries

`TicketNotFound` is a domain exception rather than a FastAPI `HTTPException`.
Repository and service code should describe application failures without depending
on HTTP. The application-level exception handler translates `TicketNotFound` into
a `404` JSON response at the HTTP boundary. This separation keeps the lower layers
reusable and avoids repeated `try/except` blocks in every route.

## Test suite

The suite contains 37 focused tests:

- Service unit tests use `Mock(spec=TicketRepository)` and do not create an HTTP
  client.
- Endpoint tests use `TestClient` and override `get_ticket_service` with an isolated
  mock. They verify validation happens before service calls.
- Integration tests use the real router, service, repository, and in-memory state.
  A fixture clears storage and resets the ticket ID before and after each workflow.

The tests cover creation defaults, sequential IDs, repository delegation, list
limits, Pydantic model conversion, invalid bodies and path parameters, centralized
404 responses, PUT and PATCH models, explicitly supplied patch fields, empty
`204` responses, and persistent create/read/update/delete workflows.

## Imports and packaging

`sys.path` is Python's ordered list of locations searched when resolving imports.
In a src-layout project, the package lives below `src` instead of directly at the
repository root. Setting `PYTHONPATH=src` temporarily adds that directory to
`sys.path`, making `import support_api` possible.

Running `pip install -e .` installs the package in editable mode. Python then knows
where the source package is, but edits still happen in this repository rather than
in a copied package under `site-packages`.

An absolute import starts from the installed package name, for example:

```python
from support_api.models import TicketCreate
```

A relative import starts from the current package, for example:

```python
from .models import TicketCreate
```

This project consistently uses absolute `support_api` imports and does not mix them
with `src.support_api`, which could create duplicate module identities.

## Short explanation answers

### Why does `Depends(get_ticket_service)` receive a callable?

FastAPI needs the function itself so it can inspect its parameters and call it at
request time. Writing `Depends(get_ticket_service())` would call the function while
the route is being defined and pass its result instead.

### What is the lifecycle of a dependency that uses `yield`?

Code before `yield` performs setup. The yielded value is supplied to the route.
After the response finishes, FastAPI resumes the dependency and runs the cleanup
code after `yield`, including when request handling raises an exception.

### How do the three test levels differ?

A service unit test exercises `TicketService` with a mocked repository. An endpoint
test exercises FastAPI routing, validation, response handling, and dependency
injection with a mocked service. An integration test connects the real HTTP,
service, and repository layers and proves that state persists across requests.

### Why does `HTTPException` become an HTTP response in `TestClient`?

FastAPI catches `HTTPException` during request processing and its registered
handler converts the exception's status and detail into an HTTP response.
`TestClient` observes that response in the same way an external client would.

### Why must `dependency_overrides` use the exact dependency callable?

FastAPI stores overrides by callable identity. The dictionary key must therefore be
the same function object placed inside `Depends`; a similar function or the result
of calling it is a different key and will not replace the dependency.
