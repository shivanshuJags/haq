"""Database connections (PostgreSQL + pgvector).

The API only reads the database ONCE, at startup (core/catalog.py loads every scheme and its
embedding into memory). Requests never wait on the database — which matters because a free Neon
database sleeps when idle and can take 5–30s to wake up and connect from far away.
"""
import time

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from core import config

CONNECT_TIMEOUT = 30  # seconds per attempt — a sleeping Neon database can be slow to wake
ATTEMPTS = 4


def connect() -> psycopg.Connection:
    """Open a connection, retrying a few times. Rows come back as dicts, and vector columns work.

        with connect() as conn:
            conn.execute("SELECT 1")
    """
    last_error: Exception | None = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            conn = psycopg.connect(config.database_url(), row_factory=dict_row, connect_timeout=CONNECT_TIMEOUT)
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            register_vector(conn)
            return conn
        except psycopg.OperationalError as error:
            last_error = error
            print(f"Database connection attempt {attempt}/{ATTEMPTS} failed: {error}", flush=True)
            time.sleep(2 * attempt)
    raise RuntimeError(f"Could not connect to the database after {ATTEMPTS} attempts") from last_error
