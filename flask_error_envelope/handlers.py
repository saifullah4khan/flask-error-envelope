"""Register error handlers that render the JSON envelope on any Flask app.

Two handlers do the work: one for every ``HTTPException`` (404, 405, 429, and
the rest) and one catch-all for uncaught exceptions, which becomes a clean 500
instead of leaking a stack trace to the client.
"""

from __future__ import annotations

import logging
from typing import Optional

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .envelope import default_message, make_error
from .retry_after import retry_after_seconds

logger = logging.getLogger(__name__)


def register_error_handlers(
    app: Flask,
    *,
    include_retry_after: bool = True,
    logger_: Optional[logging.Logger] = None,
) -> None:
    """Attach envelope-producing error handlers to *app*.

    :param app: The Flask application (or blueprint-carrying app).
    :param include_retry_after: When True, 429 responses get a Retry-After
        header derived from the error.
    :param logger_: Logger for the 500 handler; defaults to this module's.
    """
    log = logger_ or logger

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        status = error.code or 500
        # werkzeug fills in a helpful description; fall back to our defaults.
        message = error.description or default_message(status)
        response = jsonify(make_error(message, status))
        response.status_code = status
        if status == 429 and include_retry_after:
            response.headers["Retry-After"] = str(retry_after_seconds(error))
        return response

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception):
        # HTTPExceptions are handled above; Flask routes them there by class,
        # so anything reaching here is a genuine unhandled error.
        log.exception("Unhandled exception: %s", error)
        # Never leak the internal message or stack to the client.
        return jsonify(make_error(default_message(500), 500)), 500
