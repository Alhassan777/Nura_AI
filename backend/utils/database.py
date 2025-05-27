"""
Database Utilities
Common database operations and connection management.
"""

import logging
from typing import Optional, Dict, Any, List, Union
from contextlib import asynccontextmanager
import asyncio
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


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
