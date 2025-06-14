#!/usr/bin/env python3

from utils.database import get_db
from sqlalchemy import text


def check_constraints():
    db = next(get_db())

    # Check indexes on safety_network_requests table
    result = db.execute(
        text(
            """
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'safety_network_requests'
    """
        )
    ).fetchall()

    print("Current indexes on safety_network_requests:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")

    # Check constraints
    constraints = db.execute(
        text(
            """
        SELECT conname, contype, pg_get_constraintdef(oid) as definition
        FROM pg_constraint 
        WHERE conrelid = 'safety_network_requests'::regclass
    """
        )
    ).fetchall()

    print("\nCurrent constraints:")
    for row in constraints:
        print(f"  {row[0]} ({row[1]}): {row[2]}")


if __name__ == "__main__":
    check_constraints()
