# Secure Bookmark Manager API

A production-style FastAPI service where each user registers, logs in, and manages **only their own** bookmarks.

**Stack:** FastAPI · Pydantic · SQLAlchemy 2.0 · PostgreSQL · Alembic · Redis · JWT (python-jose) · pwdlib · pytest

## Project structure

```
week5_assessment/
├── src/bookmark_api/
│   ├── main.py            # app, router registration, timing middleware
│   ├── database.py        # engine, SessionLocal, get_db dependency
│   ├── models.py          # User, BookMark (SQLAlchemy 2.0 Mapped[...])
│   ├── schemas.py         # Pydantic request/response models
│   ├── auth.py            # password hasher, JWT creation, get_current_user
│   ├── redis_client.py    # Redis client + get_redis_client dependency
│   ├── services.py        # BookmarkService (queries + caching) + get_bookmark_service
│   ├── utils.py           # logger, background-task functions
│   └── routers/
│       ├── auth.py        # POST /users, POST /login
│       └── bookmarks.py   # bookmark CRUD + summary
├── alembic/               # migrations
├── tests/
├── alembic.ini
├── pyproject.toml
└── README.md
```

**Why I added `services.py`:** route handlers stay thin (parse input, call the service, return the result), while the SQL queries and the cache logic live in one `BookmarkService` class. The service gets its session, Redis client and background-task object through dependency injection, so it can be tested with a real SQLite session and fakeredis, or with mocks for failure cases.

## Setup

```bash
git clone <repo-url> && cd week5_assessment
python -m venv .venv && source .venv/bin/activate
pip install -e .
pip install pytest pytest-cov httpx fakeredis      # test tooling

or 

uv sync
```

Create a `.env` file (never commit it). The variables the app reads:

```
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/bookmarks
JWT_SECRET=<long random string>
REDIS_URL=<redis host>          # used as the host name
REDIS_PORT=6379
REDIS_USER=<redis username>
REDIS_PASSWORD=<redis password>
```

Apply the migrations and start the server:

```bash
alembic upgrade head
uvicorn bookmark_api.main:app --reload
```

Interactive docs are at `http://127.0.0.1:8000/docs`.

Run the tests with a coverage report:

```bash
pytest -s tests/
pytest --cov=bookmark_api --cov-report=term-missing tests/
```
reult : -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
===================================== tests coverage =====================================
____________________ coverage: platform linux, python 3.14.3-final-0 _____________________

Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/bookmark_api/__init__.py                0      0   100%
src/bookmark_api/auth.py                   38      1    97%   48
src/bookmark_api/database.py               13      3    77%   20-23
src/bookmark_api/main.py                   17      0   100%
src/bookmark_api/models.py                 23      0   100%
src/bookmark_api/redis_client.py           11      1    91%   22
src/bookmark_api/routers/__init__.py        0      0   100%
src/bookmark_api/routers/auth.py           27      0   100%
src/bookmark_api/routers/bookmarks.py      24      0   100%
src/bookmark_api/schemas.py                11      0   100%
src/bookmark_api/services.py               84      6    93%   59-60, 91-94
src/bookmark_api/utils.py                   7      2    71%   6, 9
---------------------------------------------------------------------
TOTAL                                     255     13    95%
============================ 36 passed, 73 warnings in 6.60s =============================
## API

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/users` | no | Register (password hashed, never returned) |
| POST | `/login` | no | Email + password → `{"access_token", "token_type": "bearer"}` |
| POST | `/bookmarks` | yes | Create a bookmark owned by the authenticated user |
| GET | `/bookmarks?page=&page_size=&category=` | yes | Paginated, ordered by id, optional category filter |
| GET | `/bookmarks/{id}` | yes | One of the caller's bookmarks |
| PUT | `/bookmarks/{id}` | yes | Replace a bookmark |
| DELETE | `/bookmarks/{id}` | yes | Delete a bookmark |
| GET | `/bookmarks/summary` | yes | `{"total_bookmarks", "distinct_categories"}` (cached) |

Design decisions:

- `/bookmarks/summary` is declared **before** `/bookmarks/{bookmark_id}` in the router. Otherwise FastAPI would try to parse the word "summary" as an integer id and return 422.
- `user_id` is **never** accepted from the client. It comes from the token via `get_current_user`.
- Another user's bookmark returns **404**, not 403, so its existence is not revealed.
- Unknown email and wrong password both return the same `401 Invalid credentials`, which avoids user enumeration.
- Passwords are hashed with pwdlib's recommended settings (Argon2). Tokens are HS256 with a 30-minute expiry.

## Database models & Alembic

The project uses SQLAlchemy 2.0 ORM models for `User` and `BookMark`.

### User model

`User` contains:

- `id`: UUID primary key
- `username`: string
- `email`: unique and indexed string
- `password_hash`: hashed password
- `created_at`: datetime

### BookMark model

`BookMark` contains:

- `id`: integer primary key
- `url`: string
- `title`: string
- `category`: string
- `notes`: optional string
- `created_at`: datetime
- `user_id`: UUID foreign key referencing `users.id`
- `last_modified_at`: optional datetime

A bookmark always belongs to one user through `user_id`.

The `user_id` is not accepted from the client when creating a bookmark. It is derived from the authenticated user.

### Migration history

The initial migration is:

`1186b62f930b_initial_tables.py`

It creates the `users` and `bookmarks` tables, adds the unique email index, and creates the foreign key from `bookmarks.user_id` to `users.id`.

The next revision is:

`8e704f4fc56b_default_for_last_modified_at.py`

This revision was generated after modifying the model, but Alembic produced an empty migration. The generated `upgrade()` and `downgrade()` functions contain only `pass`.

I kept and inspected this migration because it demonstrates an important point: `alembic revision --autogenerate` does not guarantee that Alembic will detect the schema change I intended.

The next revision is:

`b40c16f579ba_default_for_last_modified_at.py`

This migration changes `bookmarks.last_modified_at` from `nullable=False` to `nullable=True`.

Its downgrade reverses that change and makes the column non-nullable again.

### `alembic revision --autogenerate` vs `alembic upgrade head`

`alembic revision --autogenerate -m "message"` compares the SQLAlchemy model metadata with the current database schema and creates a new migration script inside `alembic/versions/`.

It does not modify the database.

The generated migration must be inspected before applying it because Alembic may:

- generate an empty migration
- miss some changes
- interpret a change differently from what was intended
- require manual edits

`alembic upgrade head` executes all unapplied migrations in revision order until the database reaches the latest migration.

The workflow used in this project is:

1. Modify the SQLAlchemy model.
2. Run `alembic revision --autogenerate -m "description"`.
3. Inspect the generated `upgrade()` and `downgrade()` functions.
4. Adjust the migration manually if necessary.
5. Run `alembic upgrade head`.
6. Verify the resulting database schema.

The migration chain for this project is:

`1186b62f930b`
→ `8e704f4fc56b`
→ `b40c16f579ba`

## Authentication (README questions, Part 2)

**1. What does `OAuth2PasswordBearer` do?**
It is a FastAPI dependency that reads the `Authorization: Bearer <token>` header and hands the raw token string to the endpoint dependency (`get_current_user`). If the header is missing or is not a Bearer header, it responds with 401. It also registers the security scheme in the OpenAPI docs.

**2. What does it NOT do?**
It does not decode the token, check the signature or expiry, look up the user, or issue tokens. It is also not a full OAuth flow (no authorization server, consent screens, scopes or third-party login). All verification happens in `get_current_user`.

**3. What does `jwt.decode()` return?**
The token's payload as a Python `dict` (the claims, e.g. `{"sub": "<uuid string>", "exp": ...}`), after verifying the signature and the `exp` claim. If the token is invalid or expired it raises `JWTError` (or a subclass). Note `sub` is a string, so it is converted back with `uuid.UUID(...)`.

**4. Why is a JWT payload encoded but not secret?**
The header and payload are only base64url-encoded, so anyone holding the token can decode and read them. The signature proves the token was not modified and was issued by someone who knows the secret, but it does not hide the contents. So no passwords or other secrets belong in the payload.

**5. Why should password verification still happen even if login tokens are cached somewhere?**
A cached token only proves that someone logged in earlier. Returning it without checking the password would let anyone who knows an email address obtain a valid token. The password check is what proves the caller holds the credentials *now*, and it also respects password changes.

## SQLAlchemy queries (README questions, Part 3)

**1. `session.scalar(stmt)` vs `session.scalars(stmt)` vs `session.execute(stmt)`**

- `session.execute(stmt)` returns a `Result` of `Row` tuples, even for a single entity (`(BookMark,)`). It is the right choice for multi-column queries, such as the summary: `session.execute(stmt).one()` gives `(total, distinct)`.
- `session.scalars(stmt)` returns a `ScalarResult` containing just the first column of each row, which for `select(BookMark)` means the ORM objects themselves. Follow it with `.all()`, `.first()` or `.one()`.
- `session.scalar(stmt)` returns the first column of the first row, or `None` if there is no row. It is a shortcut for one object (e.g. looking up a user by id).

**2. What does `.all()` do after `session.scalars()`?**
It consumes the result and returns a list of all the objects, so every matching row is loaded into memory. That is why the list endpoint pairs it with `limit()`.

**3. Why do multiple conditions in `where(...)` behave like AND?**
`where(a, b)` is shorthand for `where(a).where(b)` and for `and_(a, b)`, and SQLAlchemy joins them with `AND`. `get_bookmark_by_id` relies on this: `where(BookMark.user_id == user_id, BookMark.id == bookmark_id)` matches only when the bookmark exists **and** belongs to the caller. OR needs `or_(...)`.

**4. WHERE vs HAVING**
`WHERE` filters individual rows **before** grouping and aggregation. `HAVING` filters **groups after** aggregation and can use aggregate functions, e.g. `group_by(category).having(func.count() > 1)`. The summary query uses `WHERE user_id = ...` only, because it aggregates over one user's rows without grouping.

**5. Why can `session.refresh(obj)` change the attributes of an existing ORM object?**
`refresh` re-reads the row from the database and overwrites the attributes on the same Python object. It picks up values the database produced or changed after the object was created: the generated `id`, server defaults, and `last_modified_at` (set by `func.now()` / `onupdate`). The session is created with `expire_on_commit=False`, so objects are not reloaded automatically after `commit()`, which is why `create` and `update_bookmark` call `refresh` explicitly.

## Redis cache (README questions, Part 4)

`GET /bookmarks/summary` is cached per user as a Redis **hash** under `bookmark:summary:<user_id>` with a **60 second TTL**. On a hit, the SQL aggregate is not executed. On a miss, the service runs the aggregate query (`count(id)` and `count(distinct category)`), stores the hash, sets the TTL, and returns the result. Create, update and delete each delete the caller's key after committing. The key format lives in one helper (`summary_key`) so it cannot drift between methods, and `hset` + `expire` are sent in a single Redis pipeline so an entry can never be stored without its TTL.

**1. Cache hit and cache miss**
A hit means the requested data is found in the cache, so the database query is skipped. A miss means it is not there (never cached, expired, or invalidated), so the data is computed from PostgreSQL, stored, and returned.

**2. Why must the user id be part of the cache key?**
Without it all users would share one entry, and one user would be served another user's totals. That would be both wrong and a data leak.

**3. What is cache invalidation?**
Removing or updating cached data when the underlying data changes, so the cache does not serve stale values. Here, writing a bookmark deletes that user's summary key, and the next read rebuilds it.

**4. Why is TTL alone not always enough for correctness?**
A TTL only limits how long stale data can survive. A user who adds a bookmark would still see the old count until the TTL ran out. Explicit invalidation keeps reads correct immediately, and the TTL acts as a safety net if an invalidation is ever missed.

**5. Where should conversion back to int/Decimal happen?**
At the boundary where data is read out of Redis, which here is `get_bookmark_summary`, immediately after `hgetall` (`int(...)`). With `decode_responses=True` Redis returns strings, so the cache layer converts them before anything else sees the values. Money-like values should use `Decimal(str_value)`, never `float`.

## Middleware, logging & background tasks (README questions, Part 5)

The `request_timer` middleware records `time.perf_counter()`, awaits `call_next(request)`, computes `end - start`, adds the `X-Process-Time` response header, and logs the method, path, status code and elapsed time with the standard `logging` module (no `print`).

Background tasks: `write_audit_log` is scheduled after a user is registered, and `write_audit_log` plus `send_notification_to_user` after a bookmark is created.

**1. What does `call_next(request)` represent?**
The rest of the application: the next middleware, then routing, dependencies and the endpoint. It returns the `Response`. Code before it runs on the way in, code after it runs on the way out.

**2. What happens if `call_next(request)` never completes?**
The middleware awaits forever. The client's request hangs until a timeout, the connection stays tied up, and the code after `call_next` (timing header, log line) never runs. Timeouts around slow calls and server-level timeouts are the mitigation.

**3. Why is `time.perf_counter()` preferred over wall-clock time?**
It is a monotonic, high-resolution clock meant for measuring intervals. Wall-clock time can jump (NTP sync, daylight saving, manual changes), which could produce a negative or wrong duration.

**4. Why can't the endpoint use the return value of a background task?**
Background tasks run **after** the response has been built and sent. By the time they execute, the endpoint has already returned and its result is already on the way to the client. Starlette discards a task's return value, so the response can't depend on it. Anything the response needs must be computed before returning.

## Tests

`tests/test_project.py` runs the real routes, auth dependency and `BookmarkService` against an **in-memory SQLite database** and **fakeredis**. Only infrastructure is replaced, via `app.dependency_overrides` for `get_db` and `get_redis_client`, and the background-task functions are patched to no-ops. Nothing in the application's own logic is mocked, so the tests can catch real bugs in ownership checks, SQL and cache handling.

They cover: password hashing, valid and invalid login, missing, invalid and expired JWTs, duplicate registration (409), cross-user access (404), user association on create, pagination, category filtering, summary aggregates, cache miss then hit (the hit is proven by changing the database behind the cache and getting the old value), invalidation on create/update/delete, the `X-Process-Time` header and the request log line, and 422 validation errors.

## Design walk-through (Part 7)

**1. Trace of a protected request** (`GET /bookmarks` with `Authorization: Bearer <jwt>`)

1. The client sends the request with the Bearer token.
2. `request_timer` middleware starts `perf_counter()` and awaits `call_next(request)`.
3. FastAPI routes to the endpoint and resolves its dependencies.
4. `OAuth2PasswordBearer` extracts the token from the header (401 if missing).
5. `get_current_user` decodes and verifies the JWT (signature and `exp`), converts `sub` to a `UUID`, and queries the user using the session from `get_db`. Any failure, or an unknown user, is a 401.
6. `get_bookmark_service` builds `BookmarkService` with the same request-scoped session (FastAPI reuses the `get_db` result within one request), the Redis client and the background-task object.
7. Query parameters are validated (`page >= 1`, `1 <= page_size <= 100`), then the endpoint calls the service, which runs `select(BookMark).where(user_id == ...)...`.
8. The returned ORM objects are converted to `list[BookMarkResponse]` and serialized to JSON.
9. Back in the middleware: elapsed = `end - start`, the `X-Process-Time` header is added, and the method, path, status and time are logged.
10. `get_db`'s `finally` closes the session when the request finishes, and any background tasks run after the response is sent.

**2. `model_config = {"from_attributes": True}`**
By default a Pydantic model is built from a dict (or another model). A SQLAlchemy object is neither, so validation would fail. With `from_attributes=True`, Pydantic reads each field with attribute access (`obj.id`, `obj.url`, ...), so a `BookMarkResponse` can be built from a `BookMark` ORM instance with matching attribute names. Attributes not declared on the schema (such as `user_id`) are ignored, which also makes the response model a filter that keeps unwanted fields from leaking. FastAPI validates return values for `response_model` with attribute reading enabled, which is why `UserResponse` works for the ORM `User` even without the config. The setting is needed when you call `BookMarkResponse.model_validate(orm_obj)` yourself.

**3. Why `os.getenv()` is typed `str | None`**
If the variable is not set, `os.getenv` returns `None` (or the default you pass), so its declared return type is `str | None`. `int(os.getenv("PORT"))` could therefore be `int(None)`, which raises `TypeError` at runtime, and type checkers warn about it. The fixes are to pass a string default (`int(os.getenv("PORT", "8000"))`, which narrows the type to `str`), to use `os.environ["PORT"]` so a missing value fails immediately with `KeyError`, or to check for `None` explicitly. Required secrets such as `JWT_SECRET` use `os.environ[...]` so the app fails fast at startup.

