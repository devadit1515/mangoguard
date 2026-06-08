"""HMAC request-signing helpers for vendor connectors.

Currently used by Pessl iMETOS / FieldClimate (the only Plan 3 vendor that
exposes a documented public REST API with HMAC auth). Documented at
``https://api.fieldclimate.com/v2/docs/`` -- signed string format is
``{HTTP_METHOD}{URL_PATH}{RFC1123_DATE}{PUBLIC_KEY}``, signature is
``hmac_sha256(private_key, signed_string).hexdigest()``.

Pessl returns 401 for off-by-one signed-string assembly, so this helper is
deliberately a thin wrapper that tests can pin exactly.
"""

from __future__ import annotations

import hmac
from datetime import datetime, timezone
from email.utils import format_datetime
from hashlib import sha256


def sign_pessl_request(
    method: str,
    path: str,
    public_key: str,
    private_key: str,
    *,
    now: datetime | None = None,
) -> dict[str, str]:
    """Build the 3 required headers for a Pessl FieldClimate v2 request.

    Returns ``{"Accept", "Authorization", "Date"}`` ready to drop into a
    ``requests.get(url, headers=...)`` call.

    Parameters
    ----------
    method
        Uppercased HTTP verb. ``"GET"``, ``"POST"``, etc.
    path
        URL path WITHOUT scheme/host. Must start with ``/``. Example:
        ``"/user/stations"``.
    public_key, private_key
        HMAC credentials issued at ``ng.fieldclimate.com -> User ->
        API services``.
    now
        Override the RFC 1123 ``Date`` header for deterministic tests.
        Defaults to current UTC time.
    """
    if not method or not method.isupper():
        msg = f"method must be uppercase HTTP verb, got {method!r}"
        raise ValueError(msg)
    if not path.startswith("/"):
        msg = f"path must start with '/', got {path!r}"
        raise ValueError(msg)

    when = now if now is not None else datetime.now(timezone.utc)
    date_header = format_datetime(when, usegmt=True)
    signed_string = f"{method}{path}{date_header}{public_key}"
    signature = hmac.new(
        private_key.encode("utf-8"),
        signed_string.encode("utf-8"),
        sha256,
    ).hexdigest()

    return {
        "Accept": "application/json",
        "Authorization": f"hmac {public_key}:{signature}",
        "Date": date_header,
    }
