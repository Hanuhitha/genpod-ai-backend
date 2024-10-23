"""
This module manages the persistence of data for a single agent using a 
SQLite database.
"""
import os

db_dir = os.path.join(os.getcwd(), "output", "databases")


def get_client_local_db_file_path() -> str:
    """Returns the path to the SQLite database file."""

    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    return os.path.join(db_dir, "genpod.db")


def get_client_local_asyncdb_file_path() -> str:
    """Returns the path to the SQLite database file."""

    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    return os.path.join(db_dir, "genpod_async.db")
