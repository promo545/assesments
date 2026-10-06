from collections.abc import Generator
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind = engine, autoflush= False, expire_on_commit= False)


def get_db() -> Generator[Session, None, None]:
    """
    Give one database session for one request
    """

    session = SessionLocal()
    try: yield session
    finally:
        session.close()


