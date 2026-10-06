"""
API tests that run the REAL BookmarkService.

Only infrastructure is replaced:
  DB    -> in-memory SQLite
  Redis -> fakeredis

Install: pip install pytest httpx fakeredis
"""
import os

# bookmark_api.auth / bookmark_api.database read env vars at import time,
# so these must be set BEFORE importing the app.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import fakeredis
import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from bookmark_api.main import app
from bookmark_api.models import Base, User, BookMark
from bookmark_api.database import get_db
from bookmark_api.redis_client import get_redis_client
from bookmark_api.auth import JWT_SECRET, password_hasher, create_access_token

PASSWORD = "S3cret-pass!"
SUMMARY_KEY_PREFIX = "bookmark:summary:"


# ------------------------------------------------------------------ fixtures
@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db(session_factory):
    s = session_factory()
    yield s
    s.close()


@pytest.fixture
def fake_redis():
    r = fakeredis.FakeRedis(decode_responses=True)  # matches your real client
    yield r
    r.flushall()


@pytest.fixture(autouse=True)
def silence_background_tasks(monkeypatch):
    """Don't run real audit logging / notifications during tests."""
    monkeypatch.setattr("bookmark_api.services.write_audit_log", lambda *a, **k: None)
    monkeypatch.setattr("bookmark_api.services.send_notification_to_user", lambda *a, **k: None)
    monkeypatch.setattr("bookmark_api.routers.auth.write_audit_log", lambda *a, **k: None)


@pytest.fixture
def client(session_factory, fake_redis):
    def override_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis_client] = lambda: fake_redis
    # get_bookmark_service is NOT overridden: the real service is built
    # from the fake DB + fake Redis above.
    yield TestClient(app)  # no `with`: skips lifespan/startup hooks
    app.dependency_overrides.clear()


# ------------------------------------------------------------------- helpers
@dataclass
class Account:
    email: str
    headers: dict


def make_account(client, name) -> Account:
    email = f"{name}@example.com"
    r = client.post("/users", json={"username": name, "email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    r = client.post("/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return Account(email, {"Authorization": f"Bearer {r.json()['access_token']}"})


def user_id_of(db, email):
    return db.scalars(select(User).where(User.email == email)).one().id


def add_bookmark(client, acct, url="https://example.com", title="Example", category="dev", notes="n"):
    r = client.post(
        "/bookmarks",
        json={"url": url, "title": title, "category": category, "notes": notes},
        headers=acct.headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def seed_three(client, acct):
    """2 x dev, 1 x news -> total 3, distinct categories 2."""
    return [
        add_bookmark(client, acct, url="https://a.com", category="dev"),
        add_bookmark(client, acct, url="https://b.com", category="dev"),
        add_bookmark(client, acct, url="https://c.com", category="news"),
    ]


@pytest.fixture
def alice(client):
    return make_account(client, "alice")


@pytest.fixture
def bob(client):
    return make_account(client, "bob")


# ---------------------------------------------------------------------- auth
def test_password_is_hashed_not_plaintext(client, db):
    make_account(client, "alice")

    user = db.scalars(select(User).where(User.email == "alice@example.com")).one()

    assert user.password_hash != PASSWORD
    assert PASSWORD not in user.password_hash
    assert password_hasher.verify(PASSWORD, user.password_hash)


def test_valid_login_returns_bearer_token(client):
    client.post("/users", json={"username": "alice", "email": "alice@example.com", "password": PASSWORD})

    r = client.post("/login", json={"email": "alice@example.com", "password": PASSWORD})

    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_invalid_login_returns_401(client):
    client.post("/users", json={"username": "alice", "email": "alice@example.com", "password": PASSWORD})

    wrong_pw = client.post("/login", json={"email": "alice@example.com", "password": "nope"})
    unknown = client.post("/login", json={"email": "ghost@example.com", "password": PASSWORD})

    assert wrong_pw.status_code == 401
    assert unknown.status_code == 401


def test_protected_endpoint_without_token_is_rejected(client):
    assert client.get("/bookmarks").status_code == 401
    assert client.get("/bookmarks/summary").status_code == 401


def test_invalid_jwt_is_rejected(client, alice, db):
    uid = str(user_id_of(db, alice.email))
    forged = jwt.encode({"sub": uid}, "wrong-secret", algorithm="HS256")

    garbage = client.get("/bookmarks", headers={"Authorization": "Bearer not.a.jwt"})
    wrong_signature = client.get("/bookmarks", headers={"Authorization": f"Bearer {forged}"})

    assert garbage.status_code == 401
    assert wrong_signature.status_code == 401


def test_valid_jwt_for_deleted_user_is_rejected(client):
    import uuid
    token = create_access_token(uuid.uuid4())  # correctly signed, but no such user

    r = client.get("/bookmarks", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 401


# ----------------------------------------------------------------- ownership
def test_user_cannot_access_another_users_bookmark(client, alice, bob):
    created = add_bookmark(client, alice)
    url = f"/bookmarks/{created['id']}"
    update_body = {"url": "https://x.com", "title": "hacked", "category": "dev", "notes": "n"}

    assert client.get(url, headers=bob.headers).status_code == 404
    assert client.put(url, json=update_body, headers=bob.headers).status_code == 404
    assert client.delete(url, headers=bob.headers).status_code == 404

    assert client.get("/bookmarks", headers=bob.headers).json() == []
    assert client.get(url, headers=alice.headers).status_code == 200  # untouched


def test_create_bookmark_is_associated_with_authenticated_user(client, db, alice, bob):
    created = add_bookmark(client, alice)

    row = db.scalars(select(BookMark).where(BookMark.id == created["id"])).one()

    assert row.user_id == user_id_of(db, alice.email)
    assert row.user_id != user_id_of(db, bob.email)


# ------------------------------------------------------- pagination / filter
def test_pagination(client, alice):
    for i in range(5):
        add_bookmark(client, alice, url=f"https://e.com/{i}", title=f"t{i}")

    def page(n):
        r = client.get("/bookmarks", params={"page": n, "page_size": 2}, headers=alice.headers)
        assert r.status_code == 200
        return r.json()

    p1, p2, p3 = page(1), page(2), page(3)

    assert (len(p1), len(p2), len(p3)) == (2, 2, 1)
    assert len({b["id"] for b in p1 + p2 + p3}) == 5  # no overlap, nothing missing


def test_category_filtering(client, alice):
    seed_three(client, alice)

    r = client.get("/bookmarks", params={"category": "dev"}, headers=alice.headers)

    assert r.status_code == 200
    assert len(r.json()) == 2
    assert all(b["category"] == "dev" for b in r.json())


def test_category_filter_does_not_leak_other_users_bookmarks(client, alice, bob):
    add_bookmark(client, alice, url="https://a.com", category="dev")
    add_bookmark(client, bob, url="https://b.com", category="dev")

    r = client.get("/bookmarks", params={"category": "dev"}, headers=alice.headers)

    assert [b["url"] for b in r.json()] == ["https://a.com"]


def test_category_filter_with_unknown_category_returns_empty_list(client, alice):
    seed_three(client, alice)

    r = client.get("/bookmarks", params={"category": "nope"}, headers=alice.headers)

    assert r.status_code == 200
    assert r.json() == []


def test_category_filter_works_with_pagination(client, alice):
    for i in range(3):
        add_bookmark(client, alice, url=f"https://dev{i}.com", category="dev")
    add_bookmark(client, alice, url="https://news.com", category="news")

    params = {"category": "dev", "page_size": 2}
    page1 = client.get("/bookmarks", params={**params, "page": 1}, headers=alice.headers).json()
    page2 = client.get("/bookmarks", params={**params, "page": 2}, headers=alice.headers).json()

    assert (len(page1), len(page2)) == (2, 1)
    assert all(b["category"] == "dev" for b in page1 + page2)


# ------------------------------------------------------------------- summary
def test_summary_returns_correct_aggregates(client, alice):
    seed_three(client, alice)

    r = client.get("/bookmarks/summary", headers=alice.headers)

    assert r.status_code == 200
    assert r.json() == {"total_bookmarks": 3, "distinct_categories": 2}  # spelling matches your code


def test_first_summary_is_cache_miss_and_populates_redis(client, db, fake_redis, alice):
    seed_three(client, alice)
    key = f"{SUMMARY_KEY_PREFIX}{user_id_of(db, alice.email)}"
    fake_redis.flushall()
    assert not fake_redis.exists(key)

    client.get("/bookmarks/summary", headers=alice.headers)

    assert fake_redis.exists(key)
    assert fake_redis.hgetall(key) == {"total_bookmarks": "3", "distinct_categories": "2"}
    assert 0 < fake_redis.ttl(key) <= 60


def test_second_summary_is_served_from_cache(client, db, alice):
    seed_three(client, alice)
    first = client.get("/bookmarks/summary", headers=alice.headers).json()

    # Change the DB behind the service's back. If the next response is still
    # the old numbers, it can only have come from Redis.
    db.add(BookMark(url="https://sneaky.com", title="s", category="other",
                    notes="n", user_id=user_id_of(db, alice.email)))
    db.commit()

    second = client.get("/bookmarks/summary", headers=alice.headers).json()

    assert second == first == {"total_bookmarks": 3, "distinct_categories": 2}


@pytest.mark.parametrize(
    "operation, expected",
    [
        ("create", {"total_bookmarks": 4, "distinct_categories": 3}),
        ("update", {"total_bookmarks": 3, "distinct_categories": 3}),
        ("delete", {"total_bookmarks": 2, "distinct_categories": 2}),
    ],
)
def test_mutations_invalidate_summary_cache(client, db, fake_redis, alice, operation, expected):
    created = seed_three(client, alice)
    key = f"{SUMMARY_KEY_PREFIX}{user_id_of(db, alice.email)}"
    client.get("/bookmarks/summary", headers=alice.headers)  # warm the cache
    assert fake_redis.exists(key)

    assert created[0]["category"] == "dev"       # the expected numbers below depend on this
    first_id = created[0]["id"]

    if operation == "create":
        add_bookmark(client, alice, url="https://d.com", category="misc")
    elif operation == "update":
        r = client.put(
            f"/bookmarks/{first_id}",
            json={"url": "https://a.com", "title": "Example", "category": "misc", "notes": "n"},
            headers=alice.headers,
        )
        assert r.status_code == 200, r.text
    else:
        assert client.delete(f"/bookmarks/{first_id}", headers=alice.headers).status_code == 200

    assert not fake_redis.exists(key), "cache key should be deleted after a write"
    assert client.get("/bookmarks/summary", headers=alice.headers).json() == expected


# ---------------------------------------------------------------- middleware
def test_middleware_adds_process_time_header(client):
    r = client.get("/bookmarks")  # even a 401 passes through the middleware

    assert "x-process-time" in r.headers
    assert float(r.headers["x-process-time"]) >= 0


# ---------------------------------------------------------------- validation
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": "t", "category": "dev", "notes": "n"},                                  # no url
        {"url": "https://a.com", "category": "dev", "notes": "n"},                        # no title
        {"url": "https://a.com", "title": "t", "notes": "n"},                             # no category
        {"url": ["not", "a", "string"], "title": "t", "category": "dev", "notes": "n"},   # wrong type
    ],
)
def test_invalid_bookmark_payload_returns_422(client, alice, payload):
    assert client.post("/bookmarks", json=payload, headers=alice.headers).status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"username": "a", "email": "a@b.com"},                                  # no password
        {"email": "a@b.com", "password": PASSWORD},                             # no username
        {"username": "a", "email": "not-an-email", "password": PASSWORD},       # bad email
    ],
)
def test_invalid_user_payload_returns_422(client, payload):
    assert client.post("/users", json=payload).status_code == 422


def test_login_with_malformed_email_returns_422(client):
    r = client.post("/login", json={"email": "not-an-email", "password": PASSWORD})
    assert r.status_code == 422


@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 0}, {"page_size": 101}])
def test_invalid_pagination_params_return_422(client, alice, params):
    assert client.get("/bookmarks", params=params, headers=alice.headers).status_code == 422


# --------------------------------------------------- spec alignment additions
def test_duplicate_email_returns_409(client):
    body = {"username": "a", "email": "a@example.com", "password": PASSWORD}

    assert client.post("/users", json=body).status_code == 200
    assert client.post("/users", json=body).status_code == 409


def test_expired_jwt_is_rejected(client, alice, db):
    uid = str(user_id_of(db, alice.email))
    expired = jwt.encode(
        {"sub": uid, "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        JWT_SECRET,
        algorithm="HS256",
    )

    r = client.get("/bookmarks", headers={"Authorization": f"Bearer {expired}"})

    assert r.status_code == 401


def test_middleware_logs_method_path_status_and_time(client, caplog):
    with caplog.at_level(logging.INFO):
        client.get("/bookmarks")

    text = " ".join(r.getMessage() for r in caplog.records)
    assert "GET" in text and "/bookmarks" in text and "401" in text
