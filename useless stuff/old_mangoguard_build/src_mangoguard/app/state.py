"""Shared session-state helper for the Streamlit app.

The default block selection, market segment, and feed-store path are
tracked here so all pages stay synchronized. We keep this in a pure
dict (wrapped over ``st.session_state``) so unit tests can call
``get_session_state()`` without importing streamlit.
"""

from __future__ import annotations

from typing import Any

_DEFAULT_BLOCK_ID = "ratnagiri_block_A"
_DEFAULT_FEED_PATH = "feeds.db"
_DEFAULT_DAYS_UNTIL_HARVEST = 45


def _default_state() -> dict[str, Any]:
    return {
        "page": "home",
        "block_id": _DEFAULT_BLOCK_ID,
        "feed_store_path": _DEFAULT_FEED_PATH,
        "days_until_harvest": _DEFAULT_DAYS_UNTIL_HARVEST,
        "target_market": "DOMESTIC_MANDI",
    }


def get_session_state() -> dict[str, Any]:
    """Return a mutable dict-like object stored in ``st.session_state``.

    Falls back to a plain dict when streamlit isn't running (tests).
    """
    try:
        import streamlit as st  # noqa: PLC0415

        # Probe whether we're actually inside a Streamlit ScriptRunContext.
        # Accessing st.session_state outside one is allowed but the proxy
        # doesn't pass isinstance(dict). We treat that as "no streamlit
        # session" and return a plain dict.
        try:
            _ = st.session_state.get("__probe", None)
        except Exception:  # noqa: BLE001
            return _default_state()
        if not isinstance(st.session_state, dict):
            # Outside a real script run -- fall back to plain dict.
            return _default_state()
        for key, default in _default_state().items():
            if key not in st.session_state:
                st.session_state[key] = default
        return st.session_state
    except ImportError:
        return _default_state()
    except Exception:  # noqa: BLE001 -- st.session_state can't be accessed outside a Streamlit script
        return _default_state()
