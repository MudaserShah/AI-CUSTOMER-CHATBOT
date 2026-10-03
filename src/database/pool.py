"""
Shared PostgreSQL connection pool.

Before this, every repository method opened a brand-new TCP connection
to Postgres (psycopg.connect(...)) and tore it down when the `with`
block exited. Under real traffic that's a new connection + handshake
per query — slow, and it can exhaust Postgres's max_connections.

get_pool() returns one process-wide psycopg_pool.ConnectionPool,
created lazily on first use and reused by every repository. init_pool()
/ close_pool() are called explicitly from the FastAPI lifespan in
main.py so the pool opens at startup (failing fast if the DB is
unreachable, same philosophy as the config fail-fast in Phase 0) and
closes cleanly at shutdown, instead of relying on import-time side
effects (the same anti-pattern flagged for the LangGraph checkpointer
— see src/agent/agent.py).
"""
import threading

from psycopg_pool import ConnectionPool

from src.rag.config import settings

_pool: ConnectionPool | None = None
_lock = threading.Lock()


def init_pool(min_size: int = 1, max_size: int = 10) -> ConnectionPool:
    """Create and open the pool. Safe to call more than once — a second
    call is a no-op if the pool already exists. Called from the FastAPI
    lifespan at startup."""
    global _pool
    with _lock:
        if _pool is None:
            _pool = ConnectionPool(
                conninfo=settings.postgres_uri,
                min_size=min_size,
                max_size=max_size,
                open=True,
            )
    return _pool


def get_pool() -> ConnectionPool:
    """Return the shared pool, creating it on first use if the FastAPI
    lifespan hasn't already (e.g. when a repository is used directly
    in a script or test, outside the running API)."""
    if _pool is None:
        return init_pool()
    return _pool


def close_pool() -> None:
    global _pool
    with _lock:
        if _pool is not None:
            _pool.close()
            _pool = None
