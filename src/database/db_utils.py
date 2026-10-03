"""
Shared decorator for repository methods.

Every repository method talks to Postgres via psycopg. Without this,
a connection failure or query error inside any method becomes an
unhandled exception that bubbles all the way up to FastAPI as a raw
500 with a stack trace. This decorator catches psycopg errors at the
one place they can actually occur (the DB call), logs the real error
with the method name for debugging, and re-raises a clean
DatabaseError that the route layer knows how to turn into a proper
API response (see src/routes/chat_routes.py, refund_routes.py).

This is a stopgap over duplicating try/except in every method body.
The real fix for the duplication itself (F9 — every repository
method repeats connect/cursor/execute boilerplate) is a shared base
repository, planned for Phase 3.
"""
import functools
import logging

import psycopg

from src.database.errors import DatabaseError

logger = logging.getLogger(__name__)


def handle_db_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except psycopg.Error as exc:
            logger.exception("Database error in %s", func.__qualname__)
            raise DatabaseError(
                f"Database operation failed in {func.__qualname__}"
            ) from exc
    return wrapper
