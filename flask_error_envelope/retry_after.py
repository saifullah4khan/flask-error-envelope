"""Derive a Retry-After value for 429 responses.

RFC 7231 says a 429 response SHOULD carry a Retry-After header so well-behaved
clients back off correctly. Flask-Limiter knows the limit window but does not
always emit the header, so we recover a value from the error object in three
tiers and fall back to a conservative default. Every step is defensive: a
malformed error object yields the fallback rather than a new exception.
"""

from __future__ import annotations

import re

# Matches the human-friendly limit strings flask-limiter emits, e.g.:
#   "5 per 1 minute"    -> n=5,  n2=1,    unit=minute -> 60s
#   "5/minute"          -> n=5,  n2=None, unit=minute -> 60s
#   "10 per 30 seconds" -> n=10, n2=30,   unit=second -> 30s
#   "200/hour"          -> n=200,n2=None, unit=hour   -> 3600s
_LIMIT_DESCRIPTION_RE = re.compile(
    r"(?P<n>\d+)\s*(?:per|/)\s*(?P<n2>\d+)?\s*(?P<unit>second|minute|hour|day)s?",
    re.IGNORECASE,
)

_UNIT_TO_SECONDS = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}

# Used when the window cannot be determined (a plain abort(429), or a
# flask-limiter version that does not expose the limit). One minute is long
# enough to avoid retry storms and short enough for a quick recovery.
FALLBACK_SECONDS = 60


def retry_after_seconds(error) -> int:
    """Best-effort Retry-After in seconds for a 429 *error*. Never raises."""
    # Tier 1: structured limit metadata (flask-limiter LimitItem.expiry).
    try:
        limit = getattr(error, "limit", None)
        if limit is not None:
            expiry = getattr(limit, "expiry", None)
            if isinstance(expiry, (int, float)) and expiry > 0:
                return max(1, int(expiry))
    except Exception:  # noqa: BLE001 - derivation must not raise
        pass

    # Tier 2: parse a human-readable limit description.
    try:
        description = getattr(error, "description", None) or ""
        match = _LIMIT_DESCRIPTION_RE.search(str(description))
        if match:
            n2 = int(match.group("n2") or "1")
            unit_seconds = _UNIT_TO_SECONDS.get(match.group("unit").lower(), 60)
            seconds = n2 * unit_seconds
            if seconds > 0:
                return seconds
    except Exception:  # noqa: BLE001 - derivation must not raise
        pass

    # Tier 3: conservative default.
    return FALLBACK_SECONDS
