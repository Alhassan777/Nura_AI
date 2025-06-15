"""
Database session management for Voice Service.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging

from .config import config

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    config.VOICE_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.

    This function creates and yields a database session,
    automatically handling cleanup and error recovery.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Database session context manager for manual usage.

    Use with: with get_db_context() as db:

    Ensures proper cleanup and error handling.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()
