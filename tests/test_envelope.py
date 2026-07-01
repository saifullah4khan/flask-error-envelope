"""Tests for the envelope builder and the Retry-After derivation."""

from __future__ import annotations

from flask_error_envelope import make_error
from flask_error_envelope.retry_after import FALLBACK_SECONDS, retry_after_seconds


def test_basic_envelope_shape():
    assert make_error("Not found.", 404) == {
        "error": {"status": 404, "message": "Not found."}
    }


def test_envelope_with_code_and_extra():
    body = make_error("Too many requests.", 429, code="rate_limited", extra={"limit": "5/min"})
    assert body["error"]["code"] == "rate_limited"
    assert body["error"]["limit"] == "5/min"
    assert body["error"]["status"] == 429


class FakeLimit:
    def __init__(self, expiry):
        self.expiry = expiry


class FakeError:
    def __init__(self, limit=None, description=None):
        if limit is not None:
            self.limit = limit
        if description is not None:
            self.description = description


def test_retry_after_from_limit_expiry():
    assert retry_after_seconds(FakeError(limit=FakeLimit(30))) == 30


def test_retry_after_from_description():
    assert retry_after_seconds(FakeError(description="10 per 30 seconds")) == 30
    assert retry_after_seconds(FakeError(description="200/hour")) == 3600
    assert retry_after_seconds(FakeError(description="5 per minute")) == 60


def test_retry_after_falls_back():
    assert retry_after_seconds(FakeError()) == FALLBACK_SECONDS
    assert retry_after_seconds(object()) == FALLBACK_SECONDS


def test_retry_after_ignores_bogus_expiry():
    # A non-positive or non-numeric expiry should not be used.
    assert retry_after_seconds(FakeError(limit=FakeLimit(0))) == FALLBACK_SECONDS
    assert retry_after_seconds(FakeError(limit=FakeLimit("soon"))) == FALLBACK_SECONDS
