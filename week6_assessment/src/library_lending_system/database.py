import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL to an external PostgreSQL connection URL")
url = make_url(DATABASE_URL)
if url.get_backend_name() != "postgresql":
    raise RuntimeError("DATABASE_URL must use PostgreSQL")
url = url.set(drivername="postgresql+psycopg")
engine = create_engine(
    url, pool_size=5, max_overflow=10, pool_timeout=30,
    pool_recycle=1800, pool_pre_ping=True,
)
LocalSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    with LocalSession() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
