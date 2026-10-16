"""Database connection helpers."""

import os
from pathlib import Path

from dotenv import load_dotenv
from psycopg import connect

load_dotenv(Path(__file__).parent / ".env")


def get_connection():
    """Return a PostgreSQL connection using CONNECTION_STRING from .env."""
    connection_string = os.getenv("CONNECTION_STRING")
    if connection_string is None:
        raise RuntimeError("CONNECTION_STRING is not set")
    return connect(connection_string)
