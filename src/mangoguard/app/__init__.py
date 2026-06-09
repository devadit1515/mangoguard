"""Streamlit dashboard for MangoGuard (Plan 6).

The user-facing 5-page application:
1. Home / Connector status (st_home.py)
2. Disease Detector (st_disease.py)
3. Orchard Health (st_orchard.py)
4. Spray Recommender (st_recommender.py)  -- FOCAL module
5. Yield + Mandi Price (st_yield_price.py)
6. AskHapus chatbot (st_chatbot.py)

Run via ``streamlit run src/mangoguard/app/main.py`` after activating
the env with the ``ml`` + ``dashboard`` + ``geo`` extras installed.
"""
