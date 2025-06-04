"""
Database Utilities
Common database operations and connection management.
"""

import logging
import os
from typing import Optional, Dict, Any, List, Union, Generator
from contextlib import asynccontextmanager, contextmanager
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Centralized database configuration for all Nura services."""

    @staticmethod
    def get_database_url(service_name: Optional[str] = None) -> str:
        """
        Get database URL with smart fallback logic.

        Priority:
        1. Service-specific URL (e.g., VOICE_DATABASE_URL)
        2. SUPABASE_DATABASE_URL (production)
        3. DATABASE_URL (fallback)
        4. Localhost (development)

        Args:
            service_name: Optional service name for service-specific URL

        Returns:
            Database URL string
        """
        # Try service-specific URL first
        if service_name:
            service_url = os.getenv(f"{service_name.upper()}_DATABASE_URL")
            if service_url:
                return service_url

        # Try Supabase (production)
        supabase_url = os.getenv("SUPABASE_DATABASE_URL")
        if supabase_url:
            return supabase_url

        # Try generic DATABASE_URL
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url

        # Fallback to localhost for development
        return "postgresql://localhost:5432/nura_main"


class DatabaseManager:
    """Centralized database session manager for all services."""

    def __init__(
        self, service_name: Optional[str] = None, database_url: Optional[str] = None
    ):
        """
        Initialize database manager.

        Args:
            service_name: Service name for configuration
            database_url: Override database URL
        """
        self.service_name = service_name
        self.database_url = database_url or DatabaseConfig.get_database_url(
            service_name
        )

        # Create engine
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        logger.info(f"Database manager initialized for {service_name or 'default'}")

    @contextmanager
    def get_db(self) -> Generator[Session, None, None]:
        """
        Database session context manager.

        Works for both:
        1. FastAPI dependency injection: db: Session = Depends(get_db)
        2. Manual context manager: with get_db() as db:

        Ensures proper cleanup and error handling.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(
                f"Database session error in {self.service_name or 'default'}: {e}"
            )
            raise
        finally:
            session.close()


# Global database manager instances for common services
_managers = {}


def get_database_manager(service_name: Optional[str] = None) -> DatabaseManager:
    """
    Get or create a database manager for a service.

    Args:
        service_name: Service name (e.g., 'safety_network', 'voice', etc.)

    Returns:
        DatabaseManager instance
    """
    key = service_name or "default"

    if key not in _managers:
        _managers[key] = DatabaseManager(service_name)

    return _managers[key]


def get_db(service_name: Optional[str] = None) -> Generator[Session, None, None]:
    """
    Universal get_db function that all services can use.

    Args:
        service_name: Optional service name for service-specific configuration

    Yields:
        Database session

    Example:
        # In any service:
        from utils.database import get_db

        # Use default database
        with get_db() as db:
            ...

        # Use service-specific database
        with get_db('safety_network') as db:
            ...
    """
    manager = get_database_manager(service_name)
    with manager.get_db() as session:
        yield session


async def execute_query(
    session: Session, query: str, params: Optional[Dict[str, Any]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Execute a raw SQL query safely.

    Args:
        session: Database session
        query: SQL query to execute
        params: Query parameters

    Returns:
        Query results as list of dictionaries, None if error
    """
    try:
        result = session.execute(text(query), params or {})

        # For SELECT queries, return results
        if query.strip().upper().startswith("SELECT"):
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]

        # For other queries, commit and return success indicator
        session.commit()
        return [{"affected_rows": result.rowcount}]

    except SQLAlchemyError as e:
        logger.error(f"Database query error: {str(e)}")
        session.rollback()
        return None
    except Exception as e:
        logger.error(f"Unexpected error executing query: {str(e)}")
        session.rollback()
        return None


def get_db_connection(database_url: str):
    """
    Get database connection (placeholder for connection factory).

    Args:
        database_url: Database connection URL

    Returns:
        Database connection object
    """
    # This would return an actual database connection
    # Implementation depends on the specific database adapter
    pass


async def create_tables_if_not_exist(session: Session, models: List[Any]) -> bool:
    """
    Create database tables if they don't exist.

    Args:
        session: Database session
        models: List of SQLAlchemy model classes

    Returns:
        True if successful, False otherwise
    """
    try:
        for model in models:
            # Check if table exists
            table_name = model.__tablename__
            exists_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = :table_name
                );
            """

            result = await execute_query(
                session, exists_query, {"table_name": table_name}
            )

            if result and not result[0].get("exists", False):
                # Table doesn't exist, create it
                model.metadata.create_all(bind=session.bind)
                logger.info(f"Created table: {table_name}")
            else:
                logger.debug(f"Table already exists: {table_name}")

        return True

    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        return False


async def check_database_health(session: Session) -> Dict[str, Any]:
    """
    Check database health and connectivity.

    Args:
        session: Database session

    Returns:
        Dictionary with health status
    """
    health_status = {
        "healthy": False,
        "connection": False,
        "query_test": False,
        "error": None,
    }

    try:
        # Test basic connection
        result = await execute_query(session, "SELECT 1 as test")

        if result and result[0].get("test") == 1:
            health_status["connection"] = True
            health_status["query_test"] = True
            health_status["healthy"] = True

    except Exception as e:
        health_status["error"] = str(e)
        logger.error(f"Database health check failed: {str(e)}")

    return health_status


async def get_table_info(session: Session, table_name: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a database table.

    Args:
        session: Database session
        table_name: Name of the table

    Returns:
        Dictionary with table information
    """
    try:
        # Get column information
        columns_query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position;
        """

        columns = await execute_query(
            session, columns_query, {"table_name": table_name}
        )

        # Get row count
        count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
        count_result = await execute_query(session, count_query)

        return {
            "table_name": table_name,
            "columns": columns or [],
            "row_count": count_result[0]["row_count"] if count_result else 0,
        }

    except Exception as e:
        logger.error(f"Error getting table info for {table_name}: {str(e)}")
        return None


async def backup_table(session: Session, table_name: str, backup_name: str) -> bool:
    """
    Create a backup of a table.

    Args:
        session: Database session
        table_name: Name of the table to backup
        backup_name: Name for the backup table

    Returns:
        True if successful, False otherwise
    """
    try:
        backup_query = f"""
            CREATE TABLE {backup_name} AS 
            SELECT * FROM {table_name}
        """

        result = await execute_query(session, backup_query)

        if result:
            logger.info(f"Created backup table {backup_name} from {table_name}")
            return True

        return False

    except Exception as e:
        logger.error(f"Error creating backup of {table_name}: {str(e)}")
        return False


async def cleanup_old_records(
    session: Session, table_name: str, date_column: str, days_old: int
) -> int:
    """
    Clean up old records from a table.

    Args:
        session: Database session
        table_name: Name of the table
        date_column: Name of the date column
        days_old: Number of days old to consider for cleanup

    Returns:
        Number of records deleted
    """
    try:
        cleanup_query = f"""
            DELETE FROM {table_name} 
            WHERE {date_column} < NOW() - INTERVAL '{days_old} days'
        """

        result = await execute_query(session, cleanup_query)

        if result:
            deleted_count = result[0].get("affected_rows", 0)
            logger.info(f"Cleaned up {deleted_count} old records from {table_name}")
            return deleted_count

        return 0

    except Exception as e:
        logger.error(f"Error cleaning up old records from {table_name}: {str(e)}")
        return 0


async def get_database_stats(session: Session) -> Dict[str, Any]:
    """
    Get database statistics.

    Args:
        session: Database session

    Returns:
        Dictionary with database statistics
    """
    stats = {"tables": {}, "total_size": "unknown", "connection_count": "unknown"}

    try:
        # Get table sizes
        size_query = """
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """

        table_sizes = await execute_query(session, size_query)

        if table_sizes:
            for table in table_sizes:
                stats["tables"][table["tablename"]] = {
                    "size": table["size"],
                    "size_bytes": table["size_bytes"],
                }

        # Get database size
        db_size_query = """
            SELECT pg_size_pretty(pg_database_size(current_database())) as database_size
        """

        db_size = await execute_query(session, db_size_query)
        if db_size:
            stats["total_size"] = db_size[0]["database_size"]

        # Get connection count
        conn_query = """
            SELECT count(*) as connection_count 
            FROM pg_stat_activity 
            WHERE state = 'active'
        """

        conn_count = await execute_query(session, conn_query)
        if conn_count:
            stats["connection_count"] = conn_count[0]["connection_count"]

    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")

    return stats


def format_sql_error(error: Exception) -> str:
    """
    Format SQL error for user-friendly display.

    Args:
        error: SQL exception

    Returns:
        Formatted error message
    """
    error_str = str(error)

    # Common error patterns and user-friendly messages
    error_mappings = {
        "duplicate key": "A record with this information already exists",
        "foreign key": "This operation would break data relationships",
        "not null": "Required field is missing",
        "check constraint": "Data validation failed",
        "connection": "Database connection error",
        "timeout": "Database operation timed out",
    }

    for pattern, message in error_mappings.items():
        if pattern in error_str.lower():
            return message

    # Return generic message for unknown errors
    return "A database error occurred"


async def migrate_data(
    session: Session, source_table: str, target_table: str, mapping: Dict[str, str]
) -> bool:
    """
    Migrate data between tables with column mapping.

    Args:
        session: Database session
        source_table: Source table name
        target_table: Target table name
        mapping: Dictionary mapping source columns to target columns

    Returns:
        True if successful, False otherwise
    """
    try:
        # Build column lists
        source_columns = ", ".join(mapping.keys())
        target_columns = ", ".join(mapping.values())

        migrate_query = f"""
            INSERT INTO {target_table} ({target_columns})
            SELECT {source_columns}
            FROM {source_table}
        """

        result = await execute_query(session, migrate_query)

        if result:
            migrated_count = result[0].get("affected_rows", 0)
            logger.info(
                f"Migrated {migrated_count} records from {source_table} to {target_table}"
            )
            return True

        return False

    except Exception as e:
        logger.error(
            f"Error migrating data from {source_table} to {target_table}: {str(e)}"
        )
        return False
