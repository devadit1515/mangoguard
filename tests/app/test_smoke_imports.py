"""Smoke tests -- every Streamlit view module imports cleanly.

Streamlit views can't be unit-tested for behavior without a running
streamlit context, but we can at least catch import-time errors
(missing module, syntax errors, broken upstream imports). This file
imports each page once.
"""

from __future__ import annotations


def test_app_main_imports():
    from mangoguard.app import main  # noqa: F401,PLC0415


def test_state_module_imports_and_returns_dict():
    from mangoguard.app.state import get_session_state  # noqa: PLC0415

    state = get_session_state()
    assert isinstance(state, dict)
    assert "block_id" in state
    assert "feed_store_path" in state


def test_st_home_imports():
    from mangoguard.app.views import st_home  # noqa: F401,PLC0415


def test_st_disease_imports():
    from mangoguard.app.views import st_disease  # noqa: F401,PLC0415


def test_st_orchard_imports():
    from mangoguard.app.views import st_orchard  # noqa: F401,PLC0415


def test_st_recommender_imports():
    from mangoguard.app.views import st_recommender  # noqa: F401,PLC0415


def test_st_yield_price_imports():
    from mangoguard.app.views import st_yield_price  # noqa: F401,PLC0415


def test_st_chatbot_imports():
    from mangoguard.app.views import st_chatbot  # noqa: F401,PLC0415


def test_views_have_render_function():
    """Every page module must expose a render(state) callable."""
    from mangoguard.app.views import (  # noqa: PLC0415
        st_chatbot,
        st_disease,
        st_home,
        st_orchard,
        st_recommender,
        st_yield_price,
    )

    for module in (
        st_home,
        st_disease,
        st_orchard,
        st_recommender,
        st_yield_price,
        st_chatbot,
    ):
        assert hasattr(module, "render"), f"{module.__name__} missing render()"
        assert callable(module.render)
