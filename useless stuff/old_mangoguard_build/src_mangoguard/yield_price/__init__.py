"""Module 4 -- Yield + Mandi-price estimator.

XGBoost regressors over tabular features for:
* ``yield_kg_per_acre``  (Plan 5 Task 10)
* ``mandi_modal_price_inr_per_quintal`` at the harvest week (Plan 5 Task 11)

SHAP wrapper (Plan 5 Task 12) explains per-prediction contributions
plus global feature importance for the CREST report Section 8.

Spec section 4.5 O5 success criterion: both models must beat the
seasonal-mean baseline by >=15% MAE.
"""
