"""Database connection helper (PostgreSQL + pgvector)."""
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from core import config


def connect() -> psycopg.Connection:
    """Open a connection. Rows come back as dicts, and vector columns work.

    Use it with `with`, which commits on success and rolls back on error:
        with connect() as conn:
            conn.execute("SELECT 1")
    """
    conn = psycopg.connect(config.database_url(), row_factory=dict_row)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn
