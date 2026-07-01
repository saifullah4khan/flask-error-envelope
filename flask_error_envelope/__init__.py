"""flask-error-envelope: consistent, typed JSON error responses for Flask APIs.

Call :func:`register_error_handlers(app)` once and every error, from a 404 to
an unhandled exception, comes back in the same envelope shape with the right
status code (and a Retry-After header on 429s).
"""

from __future__ import annotations

from .envelope import DEFAULT_MESSAGES, default_message, make_error
from .handlers import register_error_handlers
from .retry_after import retry_after_seconds

__all__ = [
    "register_error_handlers",
    "make_error",
    "default_message",
    "DEFAULT_MESSAGES",
    "retry_after_seconds",
]
