class DatabaseError(Exception):
    """Raised when a database operation fails.

    Wraps the original psycopg error so callers (services/routes) can
    catch one clean exception type instead of needing to know about
    psycopg internals, and so the real error gets logged server-side
    while the API returns a generic message to the client.
    """
