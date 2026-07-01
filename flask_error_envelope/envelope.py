"""The error envelope: one consistent JSON shape for every error response.

Every error the handlers produce looks like::

    {"error": {"status": 404, "message": "Not found."}}

with an optional machine-readable ``code`` and any ``extra`` fields you add.
Keeping a single predictable shape means clients can parse errors one way
instead of guessing per endpoint.
"""

from __future__ import annotations

from typing import Any, Optional

# Sensible default messages per status code. Used when a raised error does not
# carry its own description.
DEFAULT_MESSAGES = {
    400: "Bad request.",
    401: "Unauthorized.",
    403: "Forbidden.",
    404: "Not found.",
    405: "Method not allowed.",
    409: "Conflict.",
    422: "Unprocessable entity.",
    429: "Too many requests.",
    500: "An unexpected error occurred.",
}


def make_error(
    message: str,
    status: int,
    *,
    code: Optional[str] = None,
    extra: Optional[dict] = None,
) -> dict:
    """Build the error envelope dict.

    :param message: Human-readable description.
    :param status: HTTP status code, echoed inside the body so clients that
        only inspect the JSON still see it.
    :param code: Optional stable, machine-readable error code (for example
        ``"rate_limited"``) that clients can branch on without string-matching
        the message.
    :param extra: Optional additional fields merged into the ``error`` object.
    """
    error: dict[str, Any] = {"status": status, "message": message}
    if code:
        error["code"] = code
    if extra:
        error.update(extra)
    return {"error": error}


def default_message(status: int) -> str:
    """Return the default message for *status*, or a generic fallback."""
    return DEFAULT_MESSAGES.get(status, "Error.")
