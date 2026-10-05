"""
Shared base class for repositories.

Before this, CustomerRepository, OrderRepository, and RefundRepository
each had their own identical copy of __init__ and _get_connection
(connect_uri override + pool fallback). Three copies of the same logic
means a future fix (e.g. adding connection timeout handling) has to be
remembered and applied three times — this is the F9 DRY fix from the
production-readiness report.

Every repository should inherit from this and call super().__init__()
if it overrides __init__.
"""
from typing import Optional

import psycopg

from src.database.pool import get_pool


class BaseRepository:

    def __init__(self, connection_uri: Optional[str] = None):
        # connection_uri lets tests/scripts point at a different database
        # by opening a direct connection instead of the shared pool.
        # Normal app usage leaves this unset and uses the pool.
        self._override_uri = connection_uri

    def _get_connection(self):
        if self._override_uri:
            return psycopg.connect(self._override_uri)
        return get_pool().connection()
