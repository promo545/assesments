# Week 6 — Library Lending System

A small FastAPI API using SQLAlchemy 2.x, Pydantic and external PostgreSQL (for example Neon). No authentication or audit tables.

## Run

Use Python 3.12+ and the existing `.venv`:

```bash
# Only if setting up a fresh checkout:
python -m venv .venv
.venv/bin/python -m pip install -e .
cp .env.example .env
# Edit .env and set DATABASE_URL to your external PostgreSQL URL.
.venv/bin/alembic upgrade head
.venv/bin/uvicorn library_lending_system.main:app --reload
```

Interactive API documentation: http://127.0.0.1:8000/docs. The application rejects missing configuration and non-PostgreSQL URLs. Credentials belong in `.env` or environment variables; `.env` is ignored by Git. Never commit a real connection URL. Neon URLs may include `sslmode=require`; both `postgresql://` and `postgresql+psycopg://` are supported.

## Endpoints

| Method | Route | Behavior |
| --- | --- | --- |
| POST | `/members` | Create member; unique email |
| POST | `/books` | Create book; unique ISBN; all copies initially available |
| GET | `/books/{id}` | Retrieve book |
| GET | `/books?author=...&only_available=true` | List or filter books; filters combine |
| PATCH | `/books/{id}` | Update title, author or ISBN |
| PUT | `/books/{id}/add-copies` | Increase total and available copies by positive `copies` |
| PUT | `/books/{id}/remove-copies` | Remove only available copies, keeping total positive |
| DELETE | `/books/{id}` | Delete only books with no borrowing history |
| POST | `/loans` | Borrow using `member_id` and `book_id`, for seven days |
| PATCH | `/loans/{id}/return` | Return an active loan |
| GET | `/members/{id}/loans` | Complete member borrowing history |
| GET | `/loans?only_active=true` | Active loans; omit flag to include returned loans |

The original `only_avaiable` spelling also remains supported. Loan listing retains the existing response `{loans, cursor}` and accepts `limit` (1–100) and a datetime `cursor`. Its timestamp cursor is a simple implementation: identical timestamps can cause rows to be skipped across pages. Book lists are unpaginated.

Missing resources return 404, conflicting operations return 409, and invalid request fields return 422. Empty metadata strings, explicit null metadata, and nonpositive copy changes are rejected. Total copies remain strictly positive, available copies stay nonnegative and never exceed total. Stock changes adjust both counts equally, preserving the number of outstanding loans. Historical loans prevent book deletion, including after return. Foreign keys provide an additional database safeguard.

## Transactions and concurrency

Borrow verifies the member, locks the book using `SELECT ... FOR UPDATE`, checks availability, inserts the loan and decreases stock in one commit. The row lock serializes simultaneous borrowers of the last copy. Return locks the loan before checking `returned_at`, then locks the book, updates both records and commits once. Locking the loan prevents concurrent double returns; locking the book prevents lost stock updates. Copy changes, metadata updates and deletion also lock the book. SQLAlchemy errors roll back, and the request dependency rolls back any propagated exception. Closing a session releases any remaining transaction. Repeated active loans by the same member are permitted if stock exists.

Dates use the existing PostgreSQL timestamp-without-time-zone schema and server-local Python timestamps; run the server in UTC for consistent deployment. No schema-breaking timezone conversion was introduced.

## Index choices

PostgreSQL automatically creates B-tree indexes for primary keys and unique constraints. No redundant email or ISBN index is needed.

| Index | Query improved and why | Write/storage tradeoff |
| --- | --- | --- |
| Primary keys on all three tables | Lookup by UUID and referenced-row checks avoid full scans | Each inserted row adds a unique index entry and consumes space |
| Unique `members.email` | Exact email lookup and duplicate detection use a B-tree search | Member inserts/email changes maintain the index; stores email keys |
| Unique `books.isbn` | Exact ISBN lookup and duplicate detection | Book inserts/ISBN changes maintain the index; stores ISBN keys |
| `ix_books_author` | Exact author filter locates matching rows without scanning every book | Inserts/author updates maintain another B-tree; duplicate author keys consume space |
| `ix_loans_member_id` | Member borrowing history and lazy `member.loans` lookup | Every loan insert maintains a UUID index entry |
| `ix_loans_book_id` | `book.loans` lookup and deletion-history checks | Every loan insert maintains a UUID index entry |
| Partial `ix_loans_active_borrowed_at` | Active-loan filter and ordering can scan only unreturned loans, ordered by borrowing time | Inserts add active entries; returns remove entries; smaller than indexing all historical loans |

The planner may choose a sequential scan for small tables or broad filters. There are no indexes on every column: stock and timestamp changes should avoid unnecessary maintenance. Apply the second Alembic migration to add these indexes to existing databases.

## Database and ORM explanations

1. **ACID:** Atomicity makes all transaction changes succeed or fail together. Consistency preserves declared constraints and application invariants. Isolation controls how concurrent transactions observe one another. Durability means acknowledged commits survive failure according to the database's persistence guarantees.
2. **Transaction:** A unit of database work whose changes form one logical operation, such as creating a loan and decrementing stock.
3. **Commit versus rollback:** Commit makes the transaction's changes durable. Rollback discards its uncommitted changes and releases transaction locks.
4. **Dirty read:** Reading changes another transaction has not committed. PostgreSQL does not allow dirty reads, even when READ UNCOMMITTED is requested.
5. **Non-repeatable read:** Reading the same row twice and seeing different values because another transaction committed an update between reads.
6. **Phantom read:** Repeating a query and seeing a changed set of matching rows after another transaction inserts, deletes or updates rows.
7. **Index:** A lookup structure that reduces the rows a query must inspect. It costs storage and makes relevant writes more expensive to maintain.
8. **Session:** Tracks ORM objects, their identities and pending changes, and coordinates flushing and database transactions. Queries can begin a transaction automatically.
9. **Session versus connection:** A Session is an ORM unit of work. A connection is a communication channel to PostgreSQL. A Session borrows connections as needed and can span multiple sequential transactions.
10. **`scalar()` versus `scalars()`:** `session.scalar(select(Book)...)` returns the first scalar result (here a Book) or None. `session.scalars(select(Book))` returns a scalar result stream; `.all()` materializes all returned Book objects instead of row wrappers.
11. **`relationship()`:** Provides Python object navigation such as `member.loans`, `loan.member`, `book.loans` and `loan.book`, with ORM loading and synchronization behavior.
12. **Relationship versus foreign key:** A ForeignKey enforces references in PostgreSQL. A relationship configures Python navigation; it does not replace referential integrity.
13. **Pooling:** Reuses established connections, avoiding repeated TCP/TLS/authentication overhead and bounding connection usage.
14. **`from_attributes=True`:** Lets Pydantic read ORM attributes directly and serialize them through declared response schemas without manually building dictionaries.

PostgreSQL's default READ COMMITTED isolation permits non-repeatable and phantom reads. Explicit row locks protect the read-check-write stock operations here. Relationships load lazily by default; bulk traversal can cause N+1 queries. For bulk history views, `selectinload(Member.loans).selectinload(Loan.book)` can fetch related objects in batches.

## Connection/session lifecycle

`request → Session → pooled DB connection → PostgreSQL → connection returned to pool`

Each request gets its own Session from `get_db`. The first database operation checks out a connection and starts a transaction. Commit or rollback ends the transaction and normally returns the connection; a later refresh/query can check out another connection. The dependency closes the Session after response handling, releasing remaining resources and rolling back uncommitted work.

The engine uses a pool of five connections, up to ten overflow connections, a 30-second checkout timeout, pre-ping to detect stale connections, and 1,800-second recycling. These limits apply per process; multiple workers multiply them. The pool stores database connections, not Sessions: a Session contains request-specific ORM identities, pending changes and transaction state, so sharing it between requests would mix unrelated work. Alembic uses its own short-lived, unpooled migration connections.

## Tests

```bash
.venv/bin/python -m pytest -q
```

Tests use actual PostgreSQL via `TEST_DATABASE_URL`, falling back to `DATABASE_URL`. They create a random isolated schema, create ORM tables there, run each test inside an outer transaction with savepoints, and drop only that generated schema afterward. The database role needs schema-creation permission. Existing application tables are untouched. No SQLite or in-memory database is used. Test setup checks ORM metadata; Alembic migrations are verified separately with `alembic upgrade head`.

Coverage includes create/retrieve, duplicate ISBN, author and availability filters, borrowing and relationships, exhausted-stock rollback, returns and double returns, member history, active loans, metadata and copy validation, deletion rules and missing-member behavior.
