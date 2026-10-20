import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from library_lending_system.database import DATABASE_URL, get_db
from library_lending_system.main import app
from library_lending_system.models.base import Base


@pytest.fixture(scope="session")
def test_engine():
    url = make_url(os.getenv("TEST_DATABASE_URL", DATABASE_URL))
    if url.get_backend_name() != "postgresql":
        pytest.fail("Tests require PostgreSQL")
    engine = create_engine(url.set(drivername="postgresql+psycopg"))
    # An isolated schema protects existing application tables and data.
    schema = "test_library_" + uuid.uuid4().hex
    with engine.begin() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    isolated = engine.execution_options(schema_translate_map={None: schema})
    Base.metadata.create_all(isolated)
    yield isolated
    with engine.begin() as connection:
        connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
    engine.dispose()


@pytest.fixture
def session(test_engine):
    with test_engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as session:
            yield session
        transaction.rollback()


@pytest.fixture
def client(session):
    def override():
        try:
            yield session
        except Exception:
            session.rollback()
            raise
    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
