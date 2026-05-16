from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import joblib
except Exception:  # pragma: no cover
    joblib = None

ACTIONS = [
    "monitor",
    "increase_tracking",
    "identity_check",
    "contact_aircraft",
    "scramble_patrol",
    "airspace_advisory",
    "evacuation_advisory",
    "simulate_intercept",
]


def advisor_feature_vector(track: Any) -> list[float]:
    sensor = getattr(track, "sensor", {}) or {}
    sub = getattr(track, "sub_scores", {}) or {}
    catalog = getattr(track, "catalog", {}) or {}
    sig = catalog.get("signature_match", {}) or {}
    ml = catalog.get("ml_assessment", {}) or {}
    probs = ml.get("probabilities", {}) or {}
    ttz = getattr(track, "ttz", None)
    return [
        float(getattr(track, "threat_score", 0.0) or 0.0),
        float(sub.get("intent", 0.0) or 0.0),
        float(sub.get("capability", 0.0) or 0.0),
        float(sub.get("confidence", 0.0) or 0.0),
        float(sub.get("environment", 0.0) or 0.0),
        float(sensor.get("impact_probability", 0.0) or 0.0),
        9999.0 if ttz is None else float(ttz),
        float(getattr(track, "cpa", 9999.0) or 9999.0),
        float(getattr(track, "directness", 0.0) or 0.0),
        float(sensor.get("signal_confidence", getattr(track, "confidence", 0.0)) or 0.0),
        float(sig.get("confidence", 0.0) or 0.0),
        max([float(v) for v in probs.values()] or [0.0]),
        1.0 if getattr(track, "class_type", "") == "missile" else 0.0,
        1.0 if getattr(track, "class_type", "") == "aircraft" else 0.0,
        1.0 if getattr(track, "class_type", "") == "drone" else 0.0,
        1.0 if getattr(track, "class_type", "") == "unknown" else 0.0,
        1.0 if getattr(track, "class_type", "") in {"asteroid", "foreign_spaceship"} else 0.0,
        1.0 if bool(sensor.get("transponder", False)) else 0.0,
        1.0 if bool(getattr(track, "no_fly_intrusion", False)) else 0.0,
    ]


def _model_path() -> Path:
    raw = os.environ.get("ORION_ADVISOR_MODEL")
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent / "advisor_policy_model.joblib"


def predict_advisor_action(track: Any) -> dict[str, Any] | None:
    """Return optional trained advisor model output.

    The project works without this file. If the user runs train_advisor_model.py,
    this function becomes a learned second opinion for the advisor playbook.
    """
    if joblib is None:
        return None
    path = _model_path()
    if not path.exists():
        return None
    try:
        model = joblib.load(path)
        x = [advisor_feature_vector(track)]
        label = str(model.predict(x)[0])
        confidence = 0.0
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(x)[0]
            confidence = float(max(proba))
        return {"action": label, "confidence": confidence, "model_path": str(path)}
    except Exception:
        return None
