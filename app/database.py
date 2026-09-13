"""Database session and engine configuration.

This module sets up the SQLite engine, session factory, and a FastAPI
dependency `get_db` that provides database sessions with automated cleanup.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = "sqlite:///./sales_mis.db"

# SQLite requires check_same_thread=False for multi-threaded FastAPI requests
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session per request.

    Yields:
        Session: Active SQLAlchemy session.

    Ensures the session is cleanly closed after request execution,
    rolling back any uncommitted changes if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
