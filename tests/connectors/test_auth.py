"""Tests for HMAC request-signing helpers."""

from __future__ import annotations

import hmac
from datetime import datetime, timezone
from hashlib import sha256

import pytest

from mangoguard.connectors._auth import sign_pessl_request

# Synthetic fake credentials -- never used against the real Pessl API.
_FAKE_PUBLIC = "abc123pubkey"
_FAKE_PRIVATE = "secret-private-key-for-testing"
_FIXED_TS = datetime(2025, 7, 12, 10, 30, 0, tzinfo=timezone.utc)


def test_sign_pessl_request_returns_three_required_headers():
    headers = sign_pessl_request(
        "GET", "/user/stations", _FAKE_PUBLIC, _FAKE_PRIVATE, now=_FIXED_TS
    )
    assert set(headers.keys()) == {"Accept", "Authorization", "Date"}
    assert headers["Accept"] == "application/json"


def test_authorization_uses_hmac_scheme_and_public_key():
    headers = sign_pessl_request(
        "GET", "/user/stations", _FAKE_PUBLIC, _FAKE_PRIVATE, now=_FIXED_TS
    )
    auth = headers["Authorization"]
    assert auth.startswith(f"hmac {_FAKE_PUBLIC}:")
    sig = auth.split(":", 1)[1]
    # 64 hex chars for sha256 hexdigest
    assert len(sig) == 64
    assert all(c in "0123456789abcdef" for c in sig)


def test_date_header_is_rfc1123_gmt():
    headers = sign_pessl_request(
        "GET", "/user/stations", _FAKE_PUBLIC, _FAKE_PRIVATE, now=_FIXED_TS
    )
    # 2025-07-12 10:30:00 UTC is a Saturday
    assert headers["Date"] == "Sat, 12 Jul 2025 10:30:00 GMT"


def test_signature_matches_documented_pessl_formula():
    """Independently recompute the signature using the documented formula."""
    method = "GET"
    path = "/data/00000000/raw/from/2025-07-01/to/2025-07-08"
    date_header = "Sat, 12 Jul 2025 10:30:00 GMT"
    signed_string = f"{method}{path}{date_header}{_FAKE_PUBLIC}"
    expected_sig = hmac.new(
        _FAKE_PRIVATE.encode("utf-8"),
        signed_string.encode("utf-8"),
        sha256,
    ).hexdigest()

    headers = sign_pessl_request(method, path, _FAKE_PUBLIC, _FAKE_PRIVATE, now=_FIXED_TS)
    actual_sig = headers["Authorization"].split(":", 1)[1]
    assert actual_sig == expected_sig


def test_different_methods_produce_different_signatures():
    g = sign_pessl_request("GET", "/x", _FAKE_PUBLIC, _FAKE_PRIVATE, now=_FIXED_TS)
    p = sign_pessl_request("POST", "/x", _FAKE_PUBLIC, _FAKE_PRIVATE, now=_FIXED_TS)
    assert g["Authorization"] != p["Authorization"]


def test_different_paths_produce_different_signatures():
    a = sign_pessl_request("GET", "/a", _FAKE_PUBLIC, _FAKE_PRIVATE, now=_FIXED_TS)
    b = sign_pessl_request("GET", "/b", _FAKE_PUBLIC, _FAKE_PRIVATE, now=_FIXED_TS)
    assert a["Authorization"] != b["Authorization"]


def test_lowercase_method_rejected():
    with pytest.raises(ValueError, match="uppercase"):
        sign_pessl_request("get", "/x", _FAKE_PUBLIC, _FAKE_PRIVATE, now=_FIXED_TS)


def test_path_must_start_with_slash():
    with pytest.raises(ValueError, match="must start with"):
        sign_pessl_request("GET", "user/stations", _FAKE_PUBLIC, _FAKE_PRIVATE, now=_FIXED_TS)


def test_now_defaults_to_current_time_when_not_provided():
    """Two consecutive calls without `now=` produce valid RFC1123 GMT Date headers."""
    a = sign_pessl_request("GET", "/x", _FAKE_PUBLIC, _FAKE_PRIVATE)
    b = sign_pessl_request("GET", "/x", _FAKE_PUBLIC, _FAKE_PRIVATE)
    assert a["Date"].endswith(" GMT")
    assert b["Date"].endswith(" GMT")
