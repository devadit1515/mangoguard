"""Module 1 -- disease detector (MobileNetV3-Small + Grad-CAM).

Supporting CREST module. The focal research module is the
market-conditioned recommender (``recommend.recommend``); this exists
to satisfy spec O1 (per-leaf disease classification) and to feed the
Streamlit dashboard's "upload a photo" experience.

Stages:
1. ``data`` -- MangoLeafBD + Alphonso Visit-1 dataset loaders.
2. ``model`` -- MobileNetV3-Small architecture with custom 256-unit head.
3. ``train`` -- two-phase fine-tuning (frozen backbone -> full unfreeze).
4. ``gradcam`` -- Grad-CAM++ explanation heatmap.
5. ``infer`` -- single-image inference for the Streamlit app.
"""
