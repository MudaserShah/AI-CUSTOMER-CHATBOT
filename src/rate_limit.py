"""
Shared slowapi Limiter instance.

Defined in its own module (rather than inside main.py) so route files
can import and apply @limiter.limit(...) without a circular import on
main.py.

Keyed by remote IP for now. Once every route requires auth (see
src/auth/dependencies.py), this should be switched to key by the
authenticated customer_id instead, so one customer can't exhaust
another customer's quota from a shared IP (e.g. behind one NAT/proxy).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
