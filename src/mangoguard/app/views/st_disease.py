"""Disease Detector page (Plan 6 Task 3) -- upload a leaf photo, get class + Grad-CAM."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st


def render(state: dict[str, Any]) -> None:
    st.title("📷 Disease Detector")
    st.write(
        "Upload a mango leaf or fruit photo to identify the most-likely disease. "
        "The model is MobileNetV3-Small fine-tuned on MangoLeafBD + Alphonso "
        "Visit-1 photos. The heatmap shows what the model looked at."
    )

    uploaded = st.file_uploader(
        "Choose an image", type=["jpg", "jpeg", "png"], accept_multiple_files=False
    )
    if uploaded is None:
        st.info("Upload a leaf / fruit photo to start.")
        return

    tmp_path = Path("artifacts") / "uploaded.jpg"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_path, "wb") as f:
        f.write(uploaded.read())

    from mangoguard.disease_detector.infer import predict_image  # noqa: PLC0415

    try:
        prediction = predict_image(tmp_path)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Inference failed: {exc}")
        return

    cols = st.columns(2)
    with cols[0]:
        st.image(str(tmp_path), caption="Uploaded photo", use_container_width=True)
    with cols[1]:
        st.image(
            prediction.heatmap_overlay,
            caption="Grad-CAM heatmap (red = model looked here)",
            use_container_width=True,
        )

    if prediction.low_confidence:
        st.warning(
            f"Low confidence ({prediction.confidence:.0%}) -- consult an "
            "extension officer or take another photo with better lighting."
        )
    else:
        st.success(
            f"Predicted: **{prediction.class_name}** " f"({prediction.confidence:.0%} confidence)"
        )
    st.subheader("All class probabilities")
    st.dataframe(
        [
            {"class": k, "probability": round(v, 4)}
            for k, v in sorted(prediction.class_probabilities.items(), key=lambda kv: -kv[1])
        ],
        hide_index=True,
    )
