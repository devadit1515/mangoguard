"""Tests for the shared HTTP-with-retry helper."""

from __future__ import annotations

import pytest
import requests
import responses

from mangoguard.connectors._http import get_with_retry


@responses.activate
def test_success_on_first_try():
    responses.add(responses.GET, "https://example.com/x", json={"ok": True}, status=200)
    sleeps: list[float] = []

    r = get_with_retry("https://example.com/x", sleep=sleeps.append)

    assert r.status_code == 200
    assert r.json() == {"ok": True}
    assert sleeps == []  # no retries -> no sleeps


@responses.activate
def test_retries_on_503_then_succeeds():
    responses.add(responses.GET, "https://example.com/x", status=503)
    responses.add(responses.GET, "https://example.com/x", status=503)
    responses.add(responses.GET, "https://example.com/x", json={"ok": True}, status=200)
    sleeps: list[float] = []

    r = get_with_retry("https://example.com/x", sleep=sleeps.append)

    assert r.status_code == 200
    assert sleeps == [1.0, 1.5]  # backoff_base^0, backoff_base^1


@responses.activate
def test_retries_on_429_then_succeeds():
    responses.add(responses.GET, "https://example.com/x", status=429)
    responses.add(responses.GET, "https://example.com/x", json={}, status=200)
    sleeps: list[float] = []

    r = get_with_retry("https://example.com/x", sleep=sleeps.append)

    assert r.status_code == 200
    assert sleeps == [1.0]


@responses.activate
def test_gives_up_after_max_retries_on_5xx():
    for _ in range(4):  # 1 + 3 retries
        responses.add(responses.GET, "https://example.com/x", status=503)
    sleeps: list[float] = []

    r = get_with_retry("https://example.com/x", sleep=sleeps.append)

    # After exhausting retries, the final 503 response is returned to caller
    assert r.status_code == 503
    assert sleeps == [1.0, 1.5, 1.5**2]


@responses.activate
def test_passes_through_404_without_retry():
    responses.add(responses.GET, "https://example.com/x", status=404)
    sleeps: list[float] = []

    r = get_with_retry("https://example.com/x", sleep=sleeps.append)

    assert r.status_code == 404
    assert sleeps == []  # 404 is not retryable


@responses.activate
def test_retries_on_connection_error_then_succeeds():
    responses.add(
        responses.GET,
        "https://example.com/x",
        body=requests.ConnectionError("net down"),
    )
    responses.add(responses.GET, "https://example.com/x", json={"ok": True}, status=200)
    sleeps: list[float] = []

    r = get_with_retry("https://example.com/x", sleep=sleeps.append)

    assert r.status_code == 200
    assert sleeps == [1.0]


@responses.activate
def test_raises_on_persistent_connection_error():
    for _ in range(4):
        responses.add(
            responses.GET,
            "https://example.com/x",
            body=requests.ConnectionError("net down"),
        )
    sleeps: list[float] = []

    with pytest.raises(requests.ConnectionError):
        get_with_retry("https://example.com/x", sleep=sleeps.append)

    assert sleeps == [1.0, 1.5, 1.5**2]


def test_passes_params_and_headers_to_requests_get(monkeypatch):
    captured: dict = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        captured["headers"] = headers
        captured["timeout"] = timeout

        class _R:
            status_code = 200

        return _R()

    monkeypatch.setattr("mangoguard.connectors._http.requests.get", fake_get)

    get_with_retry(
        "https://example.com/x",
        params={"key": "abc", "limit": 10},
        headers={"X-Auth": "tok"},
        timeout=5.0,
    )

    assert captured["params"] == {"key": "abc", "limit": 10}
    assert captured["headers"] == {"X-Auth": "tok"}
    assert captured["timeout"] == 5.0
