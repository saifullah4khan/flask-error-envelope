# flask-error-envelope

Consistent, typed JSON error responses for Flask APIs, from one call.

## The problem

In a Flask API that grows organically, errors come out in whatever shape each
route happened to use. A 404 from the router is HTML, a validation error is one
JSON shape, a hand-written 403 is another, and an unhandled exception leaks a
stack trace with a 500. Clients then have to special-case every one of those,
and the stack trace is a small security problem on top.

This library registers a couple of error handlers so every error, whether it
is a routing 404, an `abort(403)`, a rate-limit 429, or an uncaught exception,
comes back in the same envelope with the correct status code.

## Quickstart

```bash
pip install flask-error-envelope
```

```python
from flask import Flask
from flask_error_envelope import register_error_handlers

app = Flask(__name__)
register_error_handlers(app)
```

Now every error looks like this:

```json
{"error": {"status": 404, "message": "Not found."}}
```

You can build the same envelope yourself for handled errors:

```python
from flask import request
from flask_error_envelope import make_error

@app.post("/widgets")
def create_widget():
    if not request.is_json:
        return make_error("JSON body required.", 400, code="not_json"), 400
    ...
```

## Design decisions

**Two handlers cover everything.** One handler catches every werkzeug
`HTTPException`, which is what Flask raises for 404, 405, and friends and what
`abort(code)` produces, so all of them render through the same envelope with
their real status code. A second catch-all handles any other exception. There
is no per-status boilerplate to keep in sync.

**Unhandled exceptions never leak.** The catch-all logs the real exception
server-side (so you keep the stack trace where it belongs) and returns a
generic 500 envelope. The client sees "An unexpected error occurred." and
never the internal message.

**429 responses carry a Retry-After header.** RFC 7231 says a rate-limited
response should tell the client when to try again. The value is derived in
tiers: a structured limit expiry if present (as Flask-Limiter provides), then a
parse of the human-readable limit string, then a conservative 60-second
fallback. The derivation is fully defensive, so a malformed error object yields
the fallback rather than turning a 429 into a 500.

**Typed codes are supported but optional.** The envelope always has `status`
and `message`; you can add a stable `code` (like `"rate_limited"`) so clients
branch on a constant instead of string-matching the message, plus any `extra`
fields you need.

**No framework lock-in beyond Flask.** There is no dependency on a particular
rate limiter or extension. If Flask-Limiter is present the Retry-After value is
more precise; if it is not, everything still works.

## API

| Function | Purpose |
| --- | --- |
| `register_error_handlers(app, *, include_retry_after=True, logger_=None)` | Attach the handlers to a Flask app. |
| `make_error(message, status, *, code=None, extra=None)` | Build the envelope dict for a handled error. |
| `retry_after_seconds(error)` | Derive a Retry-After value from a 429 error object. |

## Testing

```bash
pip install -e ".[dev]"
pytest
```

The suite covers the envelope shape, all three Retry-After tiers (including
bogus input), and the handlers end to end on a real Flask app: a 404, a 405, a
429 with its header, and an unhandled exception that must not leak its message.

## License

MIT. See [LICENSE](LICENSE).
