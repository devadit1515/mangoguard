"""MangoGuard Streamlit entry-point (Plan 6 Task 1).

Run via::

    streamlit run src/mangoguard/app/main.py

The sidebar offers six pages; each page is a thin Streamlit view over
the underlying mangoguard.* modules. The app target audience is the
cooperating Konkan Alphonso farmer (smartphone-first) + the FPO field
officer (laptop-first).
"""

from __future__ import annotations

import streamlit as st

from mangoguard.app.state import get_session_state

PAGES = {
    "🏠 Home": "home",
    "📷 Disease Detector": "disease",
    "🌳 Orchard Health": "orchard",
    "💊 Spray Recommender": "recommender",
    "💰 Yield + Mandi Price": "yield_price",
    "💬 AskHapus": "chatbot",
}


def main() -> None:
    st.set_page_config(
        page_title="MangoGuard",
        page_icon="🥭",
        layout="wide",
    )
    state = get_session_state()
    st.sidebar.title("🥭 MangoGuard")
    st.sidebar.caption("Mid-sized Konkan Alphonso orchard manager -- v1.0.0-rc1")
    choice = st.sidebar.radio("Navigate", list(PAGES.keys()))
    target = PAGES[choice]
    state["page"] = target

    if target == "home":
        from mangoguard.app.views import st_home  # noqa: PLC0415

        st_home.render(state)
    elif target == "disease":
        from mangoguard.app.views import st_disease  # noqa: PLC0415

        st_disease.render(state)
    elif target == "orchard":
        from mangoguard.app.views import st_orchard  # noqa: PLC0415

        st_orchard.render(state)
    elif target == "recommender":
        from mangoguard.app.views import st_recommender  # noqa: PLC0415

        st_recommender.render(state)
    elif target == "yield_price":
        from mangoguard.app.views import st_yield_price  # noqa: PLC0415

        st_yield_price.render(state)
    elif target == "chatbot":
        from mangoguard.app.views import st_chatbot  # noqa: PLC0415

        st_chatbot.render(state)


if __name__ == "__main__":  # pragma: no cover -- streamlit entrypoint
    main()
