"""Tests for the registered handlers via a small Flask app."""

from __future__ import annotations

import pytest
from flask import Flask, abort
from werkzeug.exceptions import TooManyRequests

from flask_error_envelope import register_error_handlers


@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    register_error_handlers(app)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/missing")
    def missing():
        abort(404)

    @app.get("/limited")
    def limited():
        raise TooManyRequests(description="5 per minute")

    @app.get("/boom")
    def boom():
        raise RuntimeError("secret internal detail")

    # Propagate real errors into our handler rather than the test-time reraise.
    app.config["PROPAGATE_EXCEPTIONS"] = False
    return app.test_client()


def test_successful_route_is_untouched(client):
    assert client.get("/ok").get_json() == {"ok": True}


def test_404_uses_the_envelope(client):
    resp = client.get("/missing")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"]["status"] == 404
    assert "message" in body["error"]


def test_405_uses_the_envelope(client):
    resp = client.post("/missing")  # route is GET-only
    assert resp.status_code == 405
    assert resp.get_json()["error"]["status"] == 405


def test_429_sets_retry_after(client):
    resp = client.get("/limited")
    assert resp.status_code == 429
    assert resp.headers["Retry-After"] == "60"
    assert resp.get_json()["error"]["status"] == 429


def test_unhandled_exception_becomes_clean_500(client):
    resp = client.get("/boom")
    assert resp.status_code == 500
    body = resp.get_json()
    assert body["error"]["status"] == 500
    # The internal message must not leak to the client.
    assert "secret internal detail" not in resp.get_data(as_text=True)


def test_retry_after_can_be_disabled():
    app = Flask(__name__)
    app.config["TESTING"] = True
    register_error_handlers(app, include_retry_after=False)

    @app.get("/limited")
    def limited():
        raise TooManyRequests(description="5 per minute")

    resp = app.test_client().get("/limited")
    assert resp.status_code == 429
    assert "Retry-After" not in resp.headers
