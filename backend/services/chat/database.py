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

from .models import Base
from .config import ChatConfig

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration and connection management."""

    def __init__(self):
        # Get database URL from chat config
        self.database_url = ChatConfig.get_database_url()

        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        logger.info("Chat database configuration initialized")

    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create database tables: {str(e)}")
            raise

    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("⚠️ Database tables dropped")
        except Exception as e:
            logger.error(f"❌ Failed to drop database tables: {str(e)}")
            raise

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()

    def get_session_sync(self) -> Session:
        """Get a synchronous database session (manual cleanup required)."""
        return self.SessionLocal()


# Global database instance
db_config = DatabaseConfig()


# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    with db_config.get_session() as session:
        yield session


# Convenience functions
def create_tables():
    """Create all database tables."""
    db_config.create_tables()


def drop_tables():
    """Drop all database tables."""
    db_config.drop_tables()


# Context manager for manual session management
@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    with db_config.get_session() as session:
        yield session
