"""Database connections (PostgreSQL + pgvector).

Opening a connection to a cloud database is slow (TLS handshake, auth — several seconds
from India to a US server). So the API keeps a small POOL of open connections and lends
one out per request, instead of opening a new one every time.
"""
import atexit
from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from core import config


def _configure(conn: psycopg.Connection) -> None:
    register_vector(conn)  # lets us send/receive vector columns


def connect() -> psycopg.Connection:
    """A fresh, standalone connection — for scripts (db/load.py) that run once.

        with connect() as conn:
            conn.execute("SELECT 1")
    """
    conn = psycopg.connect(config.database_url(), row_factory=dict_row)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    _configure(conn)
    return conn


@lru_cache  # one pool for the whole process
def pool() -> ConnectionPool:
    new_pool = ConnectionPool(
        config.database_url(),
        min_size=1,
        max_size=5,
        kwargs={"row_factory": dict_row},
        configure=_configure,
        check=ConnectionPool.check_connection,  # replace connections the server closed while idle
        open=True,
    )
    atexit.register(new_pool.close)  # close connections cleanly when the program exits
    return new_pool


@contextmanager
def pooled() -> Iterator[psycopg.Connection]:
    """Borrow a connection from the pool — for the API.

        with pooled() as conn:
            conn.execute("SELECT 1")
    """
    with pool().connection() as conn:
        yield conn
