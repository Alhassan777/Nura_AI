"""
Database configuration for Chat Service.
Handles Supabase PostgreSQL connection and session management.
"""

import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator

from .config import ChatConfig

logger = logging.getLogger(__name__)

# Get database URL from chat config
database_url = ChatConfig.get_database_url()

# Create engine with connection pooling
engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger.info("Chat database configuration initialized")


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Database session context manager.

    Works for both:
    1. FastAPI dependency injection: db: Session = Depends(get_db)
    2. Manual context manager: with get_db_context() as db:

    Ensures proper cleanup and error handling.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()


def get_session_sync() -> Session:
    """Get a synchronous database session (manual cleanup required)."""
    return SessionLocal()
