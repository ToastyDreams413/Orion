from __future__ import annotations
from pathlib import Path
import subprocess
from ..models import EstimatedTrack
ROOT = Path(__file__).resolve().parents[3]


def _clamp(x: float, a: float, b: float) -> float:
    return max(a, min(b, x))

def _score_track_python(t: EstimatedTrack) -> dict:
    speed = (t.vx**2 + t.vy**2) ** 0.5
    ttz = t.ttz if t.ttz is not None else 999.0
    intent = 0.0
    if ttz >= 0 and ttz < 360:
        intent += _clamp((360.0 - ttz) / 360.0, 0.0, 1.0) * 0.42
    intent += _clamp(t.directness, 0.0, 1.0) * 0.32
    intent += 0.18 if t.no_fly_intrusion else 0.0
    intent += 0.07 if t.hazard_nearby else 0.0
    if not t.sensor.get('transponder'):
        intent += 0.10
    if t.class_type in {"missile", "asteroid", "foreign_spaceship"} and t.directness > 0.45:
        intent += 0.16
    intent = _clamp(intent, 0.0, 1.0)

    capability = 0.0
    capability += _clamp(speed / 700.0, 0.0, 1.0) * 0.27
    capability += _clamp(float(t.sensor.get('size_est', 0) or 0) / 40.0, 0.0, 1.0) * 0.14
    capability += _clamp(float(t.sensor.get('thermal', 0) or 0) / 140.0, 0.0, 1.0) * 0.16
    capability += _clamp(float(t.sensor.get('radiation', 0) or 0) / 35.0, 0.0, 1.0) * 0.16
    capability += _clamp(t.swarm_likelihood, 0.0, 1.0) * 0.08
    if t.class_type == "missile": capability += 0.34
    if t.class_type == "asteroid": capability += 0.32
    if t.class_type == "foreign_spaceship": capability += 0.24
    if t.class_type in {"satellite", "debris"}: capability += 0.10
    capability = _clamp(capability, 0.0, 1.0)

    confidence = 1.0
    confidence -= _clamp(t.uncertainty / 210.0, 0.0, 1.0) * 0.30
    confidence -= _clamp(float(t.sensor.get('jam_estimate', 0) or 0), 0.0, 1.0) * 0.20
    if t.source_type in {"fused", "celestrak", "nasa_jpl"}: confidence += 0.06
    confidence = _clamp(confidence, 0.10, 1.0)

    env = 0.0
    env += 0.28 if t.hazard_nearby else 0.0
    env += _clamp(float(t.sensor.get('jam_estimate', 0) or 0), 0.0, 1.0) * 0.24
    env += _clamp(t.uncertainty / 240.0, 0.0, 1.0) * 0.16
    if t.origin_type == "extraterrestrial": env += 0.12
    env = _clamp(env, 0.0, 1.0)

    anomaly = _clamp((t.anomaly_score + 1.0) / 2.0, 0.0, 1.0)
    final_score = _clamp((intent * 0.42 + capability * 0.32 + env * 0.10 + anomaly * 0.16) * (0.72 + 0.28 * confidence), 0.0, 1.0)
    if t.class_type in {"missile", "asteroid", "foreign_spaceship"} and t.directness > 0.42:
        final_score = max(final_score, _clamp(0.48 + capability * 0.28 + intent * 0.22, 0.0, 1.0))
    if t.class_type == "missile" and ttz >= 0 and ttz < 480 and t.directness > 0.45:
        final_score = max(final_score, 0.86)
    if t.class_type == "asteroid" and t.directness > 0.45 and (float(t.sensor.get('radiation', 0) or 0) > 10 or speed > 90):
        final_score = max(final_score, 0.82)
    if t.class_type == "foreign_spaceship" and t.directness > 0.50:
        final_score = max(final_score, 0.74)
    level = "benign"
    if final_score >= 0.72: level = "critical"
    elif final_score >= 0.42: level = "suspicious"
    elif final_score >= 0.20: level = "unknown"
    return {"intent": intent, "capability": capability, "confidence": confidence, "environment": env, "anomaly": anomaly, "threat_score": final_score, "threat_level": level}

def _run_engine_python(tracks: list[EstimatedTrack]) -> dict[str, dict]:
    return {t.id: _score_track_python(t) for t in tracks}


def engine_path() -> Path:
    candidates = [
        ROOT / "engine" / "build" / "threat_engine.exe",
        ROOT / "engine" / "build" / "Release" / "threat_engine.exe",
        ROOT / "engine" / "build" / "threat_engine",
        ROOT / "engine" / "build" / "Release" / "threat_engine",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("Build engine first. Could not find threat_engine executable.")


def run_engine(tracks: list[EstimatedTrack]) -> dict[str, dict]:
    lines = []
    for t in tracks:
        speed = (t.vx**2 + t.vy**2) ** 0.5
        fields = [
            t.id,
            t.class_type,
            f"{((t.x**2+t.y**2)**0.5):.3f}",
            f"{(t.ttz or 999.0):.3f}",
            f"{t.directness:.3f}",
            f"{speed:.3f}",
            f"{t.uncertainty:.3f}",
            f"{t.sensor.get('jam_estimate', 0):.3f}",
            f"{t.sensor.get('thermal', 0):.3f}",
            f"{t.sensor.get('radiation', 0):.3f}",
            f"{t.sensor.get('size_est', 0):.3f}",
            f"{t.anomaly_score:.3f}",
            f"{t.swarm_likelihood:.3f}",
            "1" if t.sensor.get('transponder') else "0",
            "1" if t.no_fly_intrusion else "0",
            "1" if t.hazard_nearby else "0",
            t.source_type,
            t.origin_type,
        ]
        lines.append(" ".join(fields))
    try:
        exe = engine_path()
        out = subprocess.run([str(exe)], input="\n".join(lines) + "\n", text=True, capture_output=True, check=True)
    except Exception:
        return _run_engine_python(tracks)
    results = {}
    for line in out.stdout.strip().splitlines():
        tid, intent, capability, confidence, env, anomaly, final_score, level = line.split()
        results[tid] = {
            "intent": float(intent),
            "capability": float(capability),
            "confidence": float(confidence),
            "environment": float(env),
            "anomaly": float(anomaly),
            "threat_score": float(final_score),
            "threat_level": level,
        }
    return results
