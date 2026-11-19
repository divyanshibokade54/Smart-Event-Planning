"""Safely reset the local database after explicit confirmation."""

import sys

from database.connection import Base, engine
from database import models  # noqa: F401 - imports all models before table creation
from database.init_db import initialize_database


def reset_database(*, confirmed: bool, seed: bool = False) -> None:
    """Drop and recreate all tables only when the caller confirms explicitly."""
    if not confirmed:
        raise ValueError("Database reset was not confirmed.")

    Base.metadata.drop_all(bind=engine)
    initialize_database()

    if seed:
        from database.seed_data import seed as seed_database

        seed_database()


def main() -> None:
    """Ask for confirmation before destroying the current database schema."""
    answer = input(
        "This will DELETE all database tables and data. "
        "Type RESET to continue: "
    ).strip()
    if answer != "RESET":
        print("Reset cancelled. No database changes were made.")
        return

    reset_database(confirmed=True, seed="--seed" in sys.argv)
    print("Database reset completed successfully.")


if __name__ == "__main__":
    main()
