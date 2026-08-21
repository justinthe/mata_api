import os

import geoalchemy2  # noqa: F401 — registers geometry type handling with SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, create_engine, delete, insert, select
from sqlalchemy.engine import Engine

load_dotenv()

_engine: Engine | None = None


def get_connection() -> Engine:
    global _engine
    if _engine is not None:
        return _engine

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")
    # SQLAlchemy/psycopg2 reject the legacy "postgres://" scheme some hosts
    # (e.g. Render) still hand out.
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://"):]
    # Every prior call created a brand-new Engine (its own connection pool)
    # that was never disposed -- against a session-mode pooler with a fixed
    # client cap (e.g. Supabase's 15), that exhausted it within minutes.
    # Cache one Engine per process instead; keep the pool small since a
    # session-mode pooler holds each connection open for the session, not
    # just per-transaction.
    _engine = create_engine(database_url, pool_size=3, max_overflow=2)
    return _engine


def write_rows(table: str, rows: list[dict]) -> None:
    if not rows:
        return
    engine = get_connection()
    metadata = MetaData()
    tbl = Table(table, metadata, autoload_with=engine)
    with engine.begin() as conn:
        conn.execute(insert(tbl), rows)


def read_rows(table: str, filters: dict | None = None) -> list[dict]:
    engine = get_connection()
    metadata = MetaData()
    tbl = Table(table, metadata, autoload_with=engine)
    stmt = select(tbl)
    for column, value in (filters or {}).items():
        stmt = stmt.where(tbl.c[column].in_(value) if isinstance(value, list) else tbl.c[column] == value)
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(stmt)]


def delete_rows(table: str, filters: dict) -> int:
    engine = get_connection()
    metadata = MetaData()
    tbl = Table(table, metadata, autoload_with=engine)
    stmt = delete(tbl)
    for column, value in filters.items():
        stmt = stmt.where(tbl.c[column].in_(value) if isinstance(value, list) else tbl.c[column] == value)
    with engine.begin() as conn:
        return conn.execute(stmt).rowcount


def upsert_rows(table: str, rows: list[dict], conflict_columns: list[str]) -> None:
    """INSERT ... ON CONFLICT (conflict_columns) DO UPDATE. Only for tables
    with a real UNIQUE constraint on conflict_columns (e.g. raster_overlay) —
    every other table in this schema lacks one, use delete_rows + write_rows."""
    if not rows:
        return
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    engine = get_connection()
    metadata = MetaData()
    tbl = Table(table, metadata, autoload_with=engine)
    stmt = pg_insert(tbl).values(rows)
    update_cols = {k: stmt.excluded[k] for k in rows[0] if k not in conflict_columns}
    stmt = stmt.on_conflict_do_update(index_elements=conflict_columns, set_=update_cols)
    with engine.begin() as conn:
        conn.execute(stmt)
