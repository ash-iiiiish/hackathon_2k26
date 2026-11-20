"""Thin Postgres helpers on top of a psycopg2 connection pool."""
from contextlib import contextmanager
from pathlib import Path

import psycopg2
import psycopg2.extras
import psycopg2.pool

from backend.config import DATABASE_URL

psycopg2.extras.register_default_jsonb(loads=__import__("json").loads)

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def init_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(1, 10, DATABASE_URL)
    schema = (Path(__file__).parent / "schema.sql").read_text()
    with cursor() as cur:
        cur.execute(schema)


@contextmanager
def cursor():
    """Yield a dict cursor inside a transaction; commit on success, roll back on error."""
    conn = _pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def rows(sql, params=None):
    with cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def row(sql, params=None):
    with cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def run(sql, params=None):
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


def Json(value):
    return psycopg2.extras.Json(value)
