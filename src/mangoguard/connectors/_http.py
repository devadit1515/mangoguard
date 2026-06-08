"""Shared HTTP helper with retry + exponential backoff for every connector.

Used by AGMARKNET, IMD (API path), DBSKKV, CROPSAP. Sentinel-2 talks to GEE
via the earthengine-api SDK, not raw HTTP, so it does not use this helper.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

import requests

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def get_with_retry(
    url: str,
    *,
    params: dict[str, str | int] | None = None,
    headers: dict[str, str] | None = None,
    max_retries: int = 3,
    backoff_base: float = 1.5,
    timeout: float = 30.0,
    sleep: Callable[[float], None] | None = None,  # injectable for tests
) -> requests.Response:
    """GET ``url`` with exponential-backoff retry on transient failures.

    Retries on ``requests.ConnectionError``, ``requests.Timeout``, and HTTP
    status codes in ``{429, 500, 502, 503, 504}``. All other responses
    (including 4xx other than 429) are returned to the caller unchanged.

    Sleep duration between attempts is ``backoff_base ** attempt`` seconds.
    With defaults this yields 1.0s, 1.5s, 2.25s before the 4th and final
    attempt -- bounded total wait of ~4.75s in the worst-retry case.
    """
    sleep_fn = sleep if sleep is not None else time.sleep
    last_exc: Exception | None = None
    response: requests.Response | None = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
        except (requests.ConnectionError, requests.Timeout) as e:
            last_exc = e
            if attempt >= max_retries:
                raise
            wait = backoff_base**attempt
            logger.warning(
                "GET %s failed with %s on attempt %d/%d; sleeping %.2fs",
                url,
                type(e).__name__,
                attempt + 1,
                max_retries + 1,
                wait,
            )
            sleep_fn(wait)
            continue

        if response.status_code in _RETRYABLE_STATUS and attempt < max_retries:
            wait = backoff_base**attempt
            logger.warning(
                "GET %s returned %d on attempt %d/%d; sleeping %.2fs",
                url,
                response.status_code,
                attempt + 1,
                max_retries + 1,
                wait,
            )
            sleep_fn(wait)
            continue

        return response

    # Unreachable in practice -- loop either returns or raises above.
    if last_exc is not None:
        raise last_exc
    assert response is not None
    return response
