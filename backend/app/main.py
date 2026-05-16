from __future__ import annotations
import math
import os
import json
from pathlib import Path
from typing import Any
import re
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .models import EnvironmentState, EstimatedTrack
from .scenario_manager import SCENARIOS, default_zone, make_truth, spawn_custom_object
from .physics.dynamics import step_truth
from .sensors.sensor_model import observe
from .tracking.kalman_tracker import TrackManager
from .features.feature_extractor import enrich, HAZARD_ZONE, NO_FLY_ZONE
from .scoring.anomaly_model import AnomalyModel
from .scoring.fusion import run_engine
from .scoring.signature_matcher import score_track_against_profiles
from .scoring.ml_models import MLStack
from .scoring.advisor_model import predict_advisor_action
from .catalog.public_sources import fetch_opensky, fetch_celestrak_iss, fetch_neo, SOURCE_LINKS
from .qa_engine import OrionQA

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = ROOT.parent
load_dotenv(ROOT / ".env", override=False)
load_dotenv(PROJECT_ROOT / ".env", override=False)
STATIC = ROOT / "backend" / "app" / "static"

class SettingsModel(BaseModel):
    scenario: str = "mixed_airspace"
    weather: str = "clear"
    wind: float = 0.2
    visibility: float = 0.9
    jamming: float = 0.1
    hazard_intensity: float = 0.2
    live_data: bool = True
    guided_mode: bool = True
    three_d: bool = False

class StepRequest(BaseModel):
    dt: float = 1.0

class AddObjectRequest(BaseModel):
    kind: str = "drone"

class RemoveObjectRequest(BaseModel):
    track_id: str

class RenameObjectRequest(BaseModel):
    track_id: str
    label: str

class ResponseRequest(BaseModel):
    track_id: str
    action: str

class AskRequest(BaseModel):
    question: str

class AdvisorRequest(BaseModel):
    question: str = ""
    track_id: str | None = None


QA = OrionQA()


GLOBAL_AIRCRAFT = [
    {"id":"GL-101", "label":"Pacific commercial corridor", "lat":35.7, "lon":-140.2, "altitude_ft":36000, "heading":82, "category":"civil transport"},
    {"id":"GL-118", "label":"North Atlantic transport", "lat":51.6, "lon":-32.4, "altitude_ft":38000, "heading":101, "category":"civil transport"},
    {"id":"GL-207", "label":"European air picture", "lat":48.8, "lon":2.3, "altitude_ft":31000, "heading":72, "category":"regional aircraft"},
    {"id":"GL-244", "label":"Middle East patrol track", "lat":25.2, "lon":55.3, "altitude_ft":29000, "heading":315, "category":"military aircraft"},
    {"id":"GL-319", "label":"Indo-Pacific air corridor", "lat":1.3, "lon":103.9, "altitude_ft":35000, "heading":42, "category":"civil transport"},
    {"id":"GL-402", "label":"East Asia surveillance contact", "lat":35.6, "lon":139.7, "altitude_ft":33000, "heading":270, "category":"unknown aircraft"},
    {"id":"GL-515", "label":"South Atlantic transit", "lat":-23.4, "lon":-43.2, "altitude_ft":34000, "heading":18, "category":"civil transport"},
    {"id":"GL-618", "label":"Southern Ocean sparse contact", "lat":-33.9, "lon":151.2, "altitude_ft":37000, "heading":248, "category":"civil transport"},
]


GLOBAL_TRACK_GEO = {
    "mixed_airspace": {"A1": (34.3, -130.0, "Pacific approach corridor"), "F2": (32.8, -117.6, "US coastal patrol"), "D7": (33.95, -118.28, "Los Angeles basin"), "U3": (55.7, -161.0, "Alaska approach")},
    "storm_intrusion": {"WX1": (45.7, -126.8, "Pacific Northwest offshore"), "JAM1": (47.4, -122.4, "Puget Sound electronic interference"), "UNK2": (48.9, -124.9, "Northwest coastal track"), "CM1": (41.2, -146.0, "North Pacific low-altitude approach")},
    "drone_swarm": {"AUX1": (37.0, -122.9, "Bay Area support track"), **{f"SW{i}": (37.6 + (i%5)*0.09, -122.6 + (i//5)*0.20, "Bay Area swarm") for i in range(1,11)}},
    "ballistic_approach": {"BM1": (58.5, -164.5, "Alaska / Arctic approach"), "BM2": (31.0, -151.0, "Pacific ballistic track"), "CR1": (35.4, -124.7, "California coastal cruise track"), "CIV1": (36.7, -119.8, "Central California civil corridor")},
    "orbital_pass": {"SAT1": (39.0, -104.5, "orbital pass ground track"), "SAT2": (28.5, -80.6, "orbital pass ground track"), "DEB1": (43.0, -90.0, "orbital debris ground track")},
    "asteroid_pass": {"NEO1": (34.8, -111.7, "Southwest projected corridor"), "X1": (40.1, -103.7, "Central US anomalous contact")},
    "layered_defense_drill": {"CIV1": (40.0, -74.5, "Northeast civil corridor"), "PAT1": (38.9, -77.0, "National Capital Region patrol"), "LOW1": (36.2, -75.6, "Atlantic low-altitude approach"), "UAS1": (38.3, -76.9, "Chesapeake restricted airspace"), "UNK1": (42.4, -71.1, "New England uncorrelated radar")},
    "false_alarm_filter": {"MED1": (38.7, -121.5, "Northern California support flight"), "CIV2": (33.9, -118.4, "Los Angeles civil corridor"), "BAL1": (39.7, -104.9, "Denver balloon-like reflector"), "DR1": (32.9, -117.1, "San Diego survey drone")},
    "live_public_blend": {"A1": (34.1, -135.0, "Pacific civil corridor"), "F2": (32.6, -117.2, "San Diego coastal patrol"), "MS1": (47.6, -152.0, "North Pacific high-speed contact"), "SAT2": (31.0, -95.0, "orbital pass ground track"), "NEO1": (39.3, -112.0, "western US projected corridor"), "D7": (34.0, -118.2, "Los Angeles unknown UAS")},
}

def _global_track_location(t, settings=None):
    scenario = getattr(settings, "scenario", "mixed_airspace") if settings else "mixed_airspace"
    row = GLOBAL_TRACK_GEO.get(scenario, {}).get(t.id)
    if row:
        return {"lat": row[0], "lon": row[1], "area": row[2]}
    # deterministic fallback for injected objects
    h = 0
    for ch in str(t.id or "X"):
        h = ((h * 31) + ord(ch)) & 0xFFFFFFFF
    risk = t.class_type in {"missile", "asteroid", "foreign_spaceship", "unknown"}
    anchors = [(51, -168), (24, -151), (38, -52), (56, -96)] if risk else [(34, -118), (38, -122), (40, -74), (47, -122), (32, -97)]
    a = anchors[h % len(anchors)]
    return {"lat": round(a[0] + (((h >> 8) % 90) - 45) / 30, 3), "lon": round(a[1] + (((h >> 16) % 120) - 60) / 20, 3), "area": "outer US approach sector" if risk else "US airspace sector"}

def _fmt_seconds(v):
    if v is None: return "unknown"
    try:
        v = float(v)
    except Exception:
        return "unknown"
    if v < 60: return f"{int(v)}s"
    return f"{int(v//60)}m {int(v%60)}s"

def _track_display(t) -> str:
    return f"{t.id}" + (f" ({t.label})" if getattr(t, "label", "") else "")


def _find_track_from_question(tracks, question: str):
    q = (question or "").lower()
    for t in tracks:
        names = [t.id.lower(), str(getattr(t, "label", "") or "").lower()]
        for name in names:
            if not name:
                continue
            # Track IDs should match as standalone tokens, while user-facing labels
            # may be partial phrases. This avoids accidental single-letter matches.
            if name == t.id.lower():
                if re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", q):
                    return t
            elif name in q:
                return t
    return None


def _find_tracks_from_question(tracks, question: str) -> list:
    q = (question or "").lower()
    hits = []
    seen = set()
    for t in tracks:
        candidates = [str(t.id or "").lower(), str(getattr(t, "label", "") or "").lower()]
        best_pos = None
        for name in candidates:
            if not name:
                continue
            pos = None
            if name == str(t.id or "").lower():
                m = re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", q)
                if m:
                    pos = m.start()
            else:
                idx = q.find(name)
                if idx >= 0:
                    pos = idx
            if pos is not None:
                best_pos = pos if best_pos is None else min(best_pos, pos)
        if best_pos is not None and t.id not in seen:
            hits.append((best_pos, t))
            seen.add(t.id)
    return [t for _, t in sorted(hits, key=lambda x: x[0])]


def _metric_name_from_question(ql: str) -> str:
    if "capability" in ql:
        return "capability"
    if "intent" in ql:
        return "intent"
    if "confidence" in ql and "advisor" not in ql:
        return "confidence"
    if "environment" in ql or "jamming" in ql or "weather" in ql:
        return "environment"
    if "impact" in ql or "probability" in ql:
        return "impact"
    if "time" in ql or "ttz" in ql or "soon" in ql:
        return "ttz"
    if "threat" in ql or "risk" in ql or "score" in ql:
        return "threat"
    return "threat"


def _metric_value(t, metric: str) -> float | None:
    m = _track_metrics(t)
    if metric == "capability":
        return m["capability"]
    if metric == "intent":
        return m["intent"]
    if metric == "confidence":
        return m["confidence_component"]
    if metric == "environment":
        return m["environment"]
    if metric == "impact":
        return m["impact"]
    if metric == "ttz":
        return None if m["ttz"] is None else float(m["ttz"])
    return m["score"]


def _status_reasons(t) -> list[str]:
    m = _track_metrics(t)
    reasons: list[str] = []
    if t.threat_level in {"critical", "suspicious"}:
        if m["intent"] >= 0.65 or m["directness"] >= 0.75:
            reasons.append(f"it is moving on a direct or nearly direct approach vector (intent {m['intent']:.2f}, directness {m['directness']:.2f})")
        if m["impact"] >= 0.55:
            reasons.append(f"its projected path has high exposure to a protected zone (impact probability {m['impact']:.0%})")
        if m["ttz"] is not None and m["ttz"] < 120:
            reasons.append(f"the time window is short (TTZ {_fmt_seconds(m['ttz'])})")
        if t.class_type in {"missile", "asteroid", "foreign_spaceship"}:
            reasons.append(f"its class is high-consequence in the simulation ({t.class_type})")
        if t.class_type == "unknown":
            reasons.append("its identity is unresolved, so the system cannot treat it like routine civil traffic")
        if t.class_type == "drone" and not t.sensor.get("transponder", False):
            reasons.append("it is a low-altitude or small unmanned contact without a normal transponder profile")
        if t.no_fly_intrusion:
            reasons.append("it intersects or pressures a protected/restricted airspace")
        if m["signal_confidence"] < 0.55:
            reasons.append(f"sensor confidence is weak ({m['signal_confidence']:.2f}), which increases uncertainty")
    elif t.threat_level == "unknown":
        reasons.append("the evidence is incomplete or mixed, so Orion keeps it in a watch state instead of calling it benign")
        if m["signal_confidence"] < 0.60:
            reasons.append(f"sensor confidence is only {m['signal_confidence']:.2f}")
        if m["signature_confidence"] < 0.55 and not t.sensor.get("transponder", False):
            reasons.append("there is no strong public/signature match to explain the track")
    else:
        reasons.append("its current fused score is low and the path does not show urgent protected-zone pressure")
        if t.sensor.get("transponder", False):
            reasons.append("it has a transponder/civil-style identity signal")
        if m["signature"]:
            reasons.append(f"signature matching supports a benign profile: {m['signature']} ({m['signature_confidence']:.0%})")
    if not reasons and getattr(t, "explanation", None):
        reasons.extend([str(x) for x in t.explanation[:3]])
    return reasons[:6]


def _status_explanation(t) -> str:
    m = _track_metrics(t)
    reasons = _status_reasons(t)
    return (
        f"{_track_display(t)} is labeled {t.threat_level} because " + "; ".join(reasons) + ". "
        f"Key numbers: threat {m['score']:.2f}, intent {m['intent']:.2f}, capability {m['capability']:.2f}, "
        f"signal confidence {m['signal_confidence']:.2f}, impact probability {m['impact']:.0%}, TTZ {_fmt_seconds(m['ttz'])}."
    )


def _classification_explanation(t) -> str:
    m = _track_metrics(t)
    sensor = t.sensor or {}
    sig = (t.catalog or {}).get("signature_match", {})
    ml = (t.catalog or {}).get("ml_assessment", {})
    pieces = [
        f"Orion currently classifies {_track_display(t)} as {t.class_type}.",
        f"Assessment confidence is mixed from several signals: simulation confidence {float(getattr(t, 'confidence', 0.0) or 0.0):.2f}, signal confidence {m['signal_confidence']:.2f}, ML top confidence {m['ml_confidence']:.0%}, signature confidence {m['signature_confidence']:.0%}.",
    ]
    evidence = []
    if sig.get("label"):
        evidence.append(f"signature/catalog match: {sig.get('label')} at {float(sig.get('confidence',0) or 0):.0%}")
    if ml.get("predicted_label"):
        evidence.append(f"ML class prediction: {ml.get('predicted_label')} at {m['ml_confidence']:.0%}")
    if float(sensor.get("plume_index", 0) or 0) > 0.35:
        evidence.append(f"plume index {float(sensor.get('plume_index',0) or 0):.2f}")
    if float(sensor.get("speed", sensor.get("horizontal_speed", 0)) or 0) > 0:
        evidence.append(f"speed proxy {float(sensor.get('speed', sensor.get('horizontal_speed',0)) or 0):.1f}")
    if sensor.get("transponder") is not None:
        evidence.append(f"transponder={sensor.get('transponder')}")
    if getattr(t, "explanation", None):
        evidence.extend([str(x) for x in t.explanation[:2]])
    pieces.append("Evidence used: " + ("; ".join(evidence[:6]) if evidence else "no strong class-specific evidence is available in the current packet" ) + ".")
    pieces.append("In a real system, this would need independent sensor confirmation; in Orion it is a simulated classification, not a verified real-world identification.")
    return " ".join(pieces)


def _hypothetical_missile_answer(tracks, settings=None) -> str:
    missile_tracks = [t for t in tracks if getattr(t, "class_type", "") == "missile"]
    if missile_tracks:
        ranked_m = _ranked_tracks(missile_tracks)
        ms = ranked_m[0]
        rec, label, reasons = _advisor_playbook(ms)
        return (
            f"There is currently a missile-class simulated track: {_track_display(ms)}. {_status_explanation(ms)} "
            f"Recommended simulated response: {label}. Sequence: confirm the track with priority sensors, project the path and TTZ, alert affected airspace/civil channels if exposure is plausible, and exercise the simulated defensive/intercept workflow only as a controlled scenario branch. Reason: {'; '.join(reasons)}."
        )
    return (
        "If a missile-class track appeared in Orion, I would not treat it like a routine aircraft. The simulated playbook is: "
        "1) immediately raise sensor priority and verify the class with radar/thermal/plume/signature evidence, "
        "2) estimate trajectory, time-to-zone, and affected protected regions, "
        "3) issue airspace/civil protection advisories if exposure is plausible, "
        "4) activate the simulated defensive/intercept workflow only inside the demo, and "
        "5) keep the event log updated with the recommendation, evidence, and human decision. "
        "That is simulation-only decision support, not real-world operational guidance."
    )


def _highest_priority_track(tracks):
    return sorted(tracks, key=lambda t: (t.threat_score, -float(t.ttz or 999999), t.directness), reverse=True)[0]


def _score_explanation(name: str, value: float | None = None) -> str:
    ranges = {
        "capability": "Capability estimates consequence potential if the object became hostile or hazardous. Low values usually mean limited speed, size, signature, or consequence; high values mean the object could cause more damage or is in a more dangerous class such as missile, asteroid, or unusual high-energy contact.",
        "intent": "Intent estimates whether behavior looks directed at the protected zone, using directness, closing speed, projected path, zone intrusion, and time-to-zone.",
        "confidence": "Confidence estimates how trustworthy Orion thinks the assessment is, based on sensor quality, dropout count, jamming, optical confidence, and model agreement.",
        "environment": "Environmental risk estimates how much weather, hazards, visibility, and jamming are degrading the situation or making the track harder to interpret.",
        "threat": "Threat score is the fused summary score combining intent, capability, confidence, environment, anomaly/model evidence, and signature matching. It drives benign/unknown/suspicious/critical labels."
    }
    base = ranges.get(name, "This score is one normalized component in Orion's simulated decision-support model.")
    if value is None:
        return base
    band = "low" if value < 0.33 else "moderate" if value < 0.66 else "high"
    return f"{base} A value of {value:.2f} is {band} on Orion's 0–1 scale."


def _track_metrics(t) -> dict[str, Any]:
    sig = t.catalog.get("signature_match", {}) if t.catalog else {}
    ml = t.catalog.get("ml_assessment", {}) if t.catalog else {}
    return {
        "id": t.id,
        "name": _track_display(t),
        "class": t.class_type,
        "level": t.threat_level,
        "score": float(t.threat_score or 0.0),
        "intent": float(t.sub_scores.get("intent", 0.0)),
        "capability": float(t.sub_scores.get("capability", 0.0)),
        "confidence_component": float(t.sub_scores.get("confidence", 0.0)),
        "environment": float(t.sub_scores.get("environment", 0.0)),
        "impact": float(t.sensor.get("impact_probability", 0) or 0),
        "ttz": t.ttz,
        "cpa": t.cpa,
        "directness": t.directness,
        "signal_confidence": float(t.sensor.get("signal_confidence", t.confidence) or 0.0),
        "signature": sig.get("label", ""),
        "signature_confidence": float(sig.get("confidence", 0) or 0),
        "ml_label": ml.get("predicted_label", ""),
        "ml_confidence": max((ml.get("probabilities") or {}).values() or [0.0]),
    }


def _priority_score(t) -> float:
    m = _track_metrics(t)
    time_pressure = 0.0 if m["ttz"] is None else max(0.0, min(1.0, (600.0 - float(m["ttz"])) / 600.0))
    class_pressure = 0.18 if t.class_type in {"missile", "asteroid", "foreign_spaceship"} else 0.07 if t.class_type in {"unknown", "drone"} else 0.0
    return (
        m["score"] * 0.46
        + m["impact"] * 0.18
        + m["directness"] * 0.14
        + time_pressure * 0.12
        + m["capability"] * 0.08
        + class_pressure
    )


def _ranked_tracks(tracks):
    return sorted(tracks, key=_priority_score, reverse=True)


def _advisor_playbook(t) -> tuple[str, str, list[str]]:
    m = _track_metrics(t)
    urgent = (m["ttz"] is not None and m["ttz"] < 300) or m["impact"] > 0.45 or t.threat_level == "critical"
    uncertain = m["signal_confidence"] < 0.55 or t.class_type == "unknown"
    if t.class_type == "aircraft" and t.sensor.get("transponder", False) and t.threat_level in {"benign", "unknown", "suspicious"}:
        return "contact_aircraft", "attempt communications / identity verification", ["standard escalation for transponder-positive aircraft", "keeps response reversible while evidence is collected"]
    if t.class_type in {"missile", "asteroid", "foreign_spaceship"} and urgent:
        return "simulate_intercept", "activate simulated intercept / mitigation workflow", ["high consequence class", "projected path or time pressure justifies exercising the defensive branch", "still presented as a simulation-only workflow"]
    if t.class_type in {"drone", "unknown"} and (t.no_fly_intrusion or m["directness"] > 0.48):
        return "scramble_patrol", "dispatch patrol/inspection assets and raise sensor priority", ["unresolved identity near protected airspace", "patrol improves identification without immediately assuming hostile intent"]
    if urgent:
        return "airspace_advisory", "issue local airspace/civil protection advisory and increase tracking", ["time pressure is elevated", "public-safety branch is more appropriate than kinetic assumptions"]
    if uncertain or t.threat_level in {"suspicious", "unknown"}:
        return "increase_tracking", "raise sensor priority and collect one more observation window", ["evidence is not strong enough for a harder escalation", "better tracks improve confidence and reduce false positives"]
    return "monitor", "continue routine monitoring", ["low current score", "no urgent protected-zone crossing signal"]


def _option_matrix(target) -> list[tuple[str, str, float, str]]:
    m = _track_metrics(target)
    base = float(target.threat_score or 0.0)
    urgent = 0.0 if m["ttz"] is None else max(0.0, min(1.0, (420.0 - float(m["ttz"])) / 420.0))
    uncertainty = max(0.0, 1.0 - m["signal_confidence"])
    impact = m["impact"]
    rows = [
        ("monitor", "Routine monitoring", max(0.05, 1.0 - base - urgent * .2), "best only when score and approach pressure are low"),
        ("increase_tracking", "Raise sensor priority", min(0.95, .42 + uncertainty*.32 + base*.22), "improves confidence before committing to a harder branch"),
        ("identity_check", "Identity / transponder check", min(0.90, .35 + (.25 if target.class_type == "aircraft" else .05) + uncertainty*.25), "useful for aircraft-like or ambiguous tracks"),
        ("scramble_patrol", "Dispatch patrol / inspection", min(0.92, .20 + base*.45 + uncertainty*.18 + (0.15 if target.no_fly_intrusion else 0)), "reversible escalation for drone/unknown/aircraft ambiguity"),
        ("airspace_advisory", "Airspace or civil advisory", min(0.90, .18 + impact*.38 + urgent*.25 + base*.20), "reduces exposure when projected path pressure is growing"),
        ("simulate_intercept", "Simulated intercept workflow", min(0.94, .08 + impact*.44 + urgent*.30 + (.18 if target.class_type in {"missile", "asteroid", "foreign_spaceship"} else 0)), "reserved for high-consequence classes or strong zone-intersection evidence"),
    ]
    return sorted(rows, key=lambda r: r[2], reverse=True)


def _scenario_summary(tracks) -> dict[str, Any]:
    ranked = _ranked_tracks(tracks)
    counts = {"critical":0, "suspicious":0, "unknown":0, "benign":0}
    for t in tracks:
        counts[t.threat_level] = counts.get(t.threat_level, 0) + 1
    pressure = sum(_priority_score(t) for t in ranked[:3]) / max(1, min(3, len(ranked)))
    posture = "routine monitoring"
    if counts.get("critical", 0):
        posture = "active response coordination"
    elif counts.get("suspicious", 0) >= 2:
        posture = "heightened watch"
    elif counts.get("suspicious", 0) or counts.get("unknown", 0):
        posture = "focused monitoring"
    return {"ranked": ranked, "counts": counts, "pressure": pressure, "posture": posture}



def _heading_cardinal(vx: float, vy: float) -> str:
    if abs(vx) + abs(vy) < 1e-6:
        return "holding position"
    angle = (math.degrees(math.atan2(vy, vx)) + 360) % 360
    names = ["east", "northeast", "north", "northwest", "west", "southwest", "south", "southeast"]
    return names[int((angle + 22.5) // 45) % 8]


def _track_brief(t) -> str:
    m = _track_metrics(t)
    alt = f"{int(t.z)} altitude-units"
    motion = _heading_cardinal(t.vx, t.vy)
    ttz = _fmt_seconds(m["ttz"])
    area = t.sensor.get("global_area", "global sector") if getattr(t, "sensor", None) else "global sector"
    lat = t.sensor.get("global_lat", None) if getattr(t, "sensor", None) else None
    lon = t.sensor.get("global_lon", None) if getattr(t, "sensor", None) else None
    place = f"{area} ({lat:.1f}, {lon:.1f})" if isinstance(lat, (int, float)) and isinstance(lon, (int, float)) else area
    return (
        f"{_track_display(t)}: {t.class_type}, {t.threat_level}, threat {m['score']:.2f}, "
        f"intent {m['intent']:.2f}, capability {m['capability']:.2f}, "
        f"area {place}, {alt}, moving {motion}, TTZ {ttz}"
    )


def _extract_score_value(question: str) -> float | None:
    nums = re.findall(r"(?<![A-Za-z])-?\d+(?:\.\d+)?", question or "")
    for n in nums:
        try:
            v = float(n)
        except Exception:
            continue
        if 0 <= v <= 1:
            return v
    return None


def _question_intents(ql: str) -> set[str]:
    intents: set[str] = set()
    if any(x in ql for x in ["where", "location", "located", "position", "coordinates", "map", "area", "region"]):
        intents.add("location")
    if any(x in ql for x in ["biggest threat", "biggest threats", "highest risk", "most dangerous", "most important", "highest priority", "focus", "priority", "rank", "ranking", "which object", "which track"]):
        intents.add("priority")
    if any(x in ql for x in ["list", "all objects", "all tracks", "summary", "status", "overview", "situation", "sitrep"]):
        intents.add("overview")
    if any(x in ql for x in ["why", "reason", "rationale", "evidence", "explain", "concern", "worried"]):
        intents.add("explain")
    if any(x in ql for x in ["sensor", "radar", "optical", "thermal", "signature", "catalog", "model", "ml", "anomaly", "confidence"]):
        intents.add("sensors")
    if any(x in ql for x in ["time", "timeline", "soon", "wait", "minutes", "seconds", "ttz", "closest", "approach", "how long", "reach", "arrive", "zone"]):
        intents.add("timeline")
    if any(x in ql for x in ["option", "compare", "choice", "should", "recommend", "response", "action", "next", "what do", "what should", "what would", "recommend"]):
        intents.add("options")
    if any(x in ql for x in ["environment", "weather", "jamming", "visibility", "wind", "hazard"]):
        intents.add("environment")
    return intents


def _format_top_tracks(ranked, n=3) -> str:
    return " ".join(f"{i+1}) {_track_brief(t)}." for i, t in enumerate(ranked[:n]))


def _settings_summary(settings) -> str:
    if not settings:
        return "Environment details are available in the simulation settings panel; the current advisor still factors environment score per track."
    return (
        f"Current environment: weather={settings.weather}, visibility={settings.visibility:.2f}, "
        f"jamming={settings.jamming:.2f}, wind={settings.wind:.2f}, hazard intensity={settings.hazard_intensity:.2f}. "
        "High jamming or low visibility should push the response toward more sensing and verification before harder simulated actions."
    )


def _fallback_advisor_assessment(tracks, question: str = "", track_id: str | None = None, settings=None) -> dict[str, Any]:
    """Local advisor used both as a fallback and as the grounding layer for the LLM.

    It intentionally covers many commander-style question shapes so the advisor
    remains useful even without an API key: status explanations, score lookup,
    comparisons, classification confidence, locations, timelines, response
    options, hypothetical missile questions, and broad situation reports.
    """
    if not tracks:
        return {"answer":"No tracks are currently available. The simulated advisor recommends routine monitoring until sensors report objects.", "confidence":0.35, "recommendation":"monitor", "track_id":None, "evidence":[], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    q = (question or "").strip()
    ql = q.lower()
    intents = _question_intents(ql)
    by_id = {t.id: t for t in tracks}
    mentioned = _find_tracks_from_question(tracks, q)
    target = (mentioned[0] if mentioned else None) or (by_id.get(track_id) if track_id else None)
    summary = _scenario_summary(tracks)
    ranked = summary["ranked"]
    top = ranked[0]

    asks_capability = "capability" in ql
    asks_intent = "intent" in ql
    asks_confidence_score = "confidence" in ql and "advisor" not in ql
    asks_environment = "environment" in ql
    asks_threat_score = "threat score" in ql or "risk score" in ql or ("threat" in ql and "score" in ql)
    asks_value = any(x in ql for x in ["what is", "what's", "show", "value", "score", "mean", "means", "explain", "how much"])
    asks_compare = any(x in ql for x in ["compare", "versus", " vs ", "difference", "higher", "lower", "more", "less"])
    asks_status_reason = any(x in ql for x in ["why is", "why was", "why did", "why does", "why", "suspicious", "critical", "benign", "unknown", "flagged"])
    asks_classification = any(x in ql for x in ["how do we know", "how do you know", "classified", "classification", "is it a", "is a missile", "why is it a", "what makes"])
    hypothetical_missile = ("missile" in ql and any(x in ql for x in ["if", "what should", "what would", "suppose", "hypothetical", "appeared", "shows up", "there was", "there is"]))

    # Hypothetical or general missile response should not fall back to whatever
    # current aircraft happens to be the top track.
    if hypothetical_missile and not target:
        return {"answer": _hypothetical_missile_answer(tracks, settings), "confidence": 0.86, "recommendation":"missile_playbook", "track_id": None, "evidence": [], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    # Multi-track comparisons, e.g. "how does capability of MS1 compare to A1?"
    if asks_compare and len(mentioned) >= 2:
        metric = _metric_name_from_question(ql)
        rows = []
        for t in mentioned[:4]:
            val = _metric_value(t, metric)
            if metric == "ttz":
                val_text = _fmt_seconds(val)
            else:
                val_text = "n/a" if val is None else f"{val:.2f}"
            rows.append((t, val, val_text))
        if metric == "ttz":
            best = min([r for r in rows if r[1] is not None], key=lambda r: r[1], default=None)
            relation = f"Shortest time pressure: {_track_display(best[0])}." if best else "TTZ is unavailable for the compared tracks."
        else:
            ordered = sorted([r for r in rows if r[1] is not None], key=lambda r: r[1], reverse=True)
            relation = f"Highest {metric}: {_track_display(ordered[0][0])}." if ordered else f"{metric} values are unavailable."
            if len(ordered) >= 2:
                relation += f" Gap: {abs(float(ordered[0][1]) - float(ordered[1][1])):.2f}."
        details = "; ".join(f"{_track_display(t)} {metric}={val_text} ({t.threat_level}, threat {float(t.threat_score or 0):.2f})" for t, val, val_text in rows)
        answer = f"Comparison: {details}. {relation} {_score_explanation(metric if metric != 'ttz' else 'threat') if metric != 'ttz' else 'Lower TTZ means less time before the projected protected-zone interaction.'}"
        return {"answer": answer, "confidence": 0.90, "recommendation":"compare_tracks", "track_id": mentioned[0].id, "evidence": [], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    # Explain abstract scores, including "what does capability 0.22 mean?"
    if target is None and asks_value and (asks_capability or asks_intent or asks_confidence_score or asks_environment or asks_threat_score):
        key = "capability" if asks_capability else "intent" if asks_intent else "confidence" if asks_confidence_score else "environment" if asks_environment else "threat"
        val = _extract_score_value(q)
        return {"answer": _score_explanation(key, val), "confidence": 0.88, "recommendation":"explain_score", "track_id":None, "evidence":[], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    if target is None:
        target = top

    rec, label, playbook_reasons = _advisor_playbook(target)
    model_hint = predict_advisor_action(target)
    matrix = _option_matrix(target)
    m = _track_metrics(target)

    if model_hint and model_hint.get("action"):
        playbook_reasons.append(f"optional trained advisor model suggests {model_hint['action']} at {float(model_hint.get('confidence', 0.0)):.0%}")
        if float(model_hint.get("confidence", 0.0)) > 0.72 and model_hint.get("action") != rec:
            playbook_reasons.append("model/playbook disagreement flagged for operator review")

    confidence = 0.46 + min(0.24, m["score"] * 0.20) + min(0.14, m["signal_confidence"] * 0.14) + min(0.10, matrix[0][2] * 0.10)
    if model_hint:
        confidence += min(0.06, float(model_hint.get("confidence", 0.0)) * 0.06)
    if m["signature_confidence"] > 0.55:
        confidence += 0.05
    if summary["counts"].get("critical", 0) > 1:
        confidence -= 0.04
    confidence = max(0.34, min(0.94, confidence))

    evidence = [
        f"Scenario posture: {summary['posture']} ({summary['counts'].get('critical',0)} critical, {summary['counts'].get('suspicious',0)} suspicious, {summary['counts'].get('unknown',0)} unknown).",
        f"Track: {_track_display(target)} has threat {m['score']:.2f}, intent {m['intent']:.2f}, capability {m['capability']:.2f}, impact probability {m['impact']:.0%}.",
        f"Time pressure: TTZ {_fmt_seconds(m['ttz'])}, closest approach {int(m['cpa'] or 0)} units, directness {m['directness']:.2f}.",
    ]
    if target.explanation:
        evidence.append("Main explanation: " + target.explanation[0] + ".")
    if m["ml_label"]:
        evidence.append(f"ML support layer predicts {m['ml_label']} behavior with {m['ml_confidence']:.0%} top confidence.")
    if m["signature"]:
        evidence.append(f"Signature matching suggests {m['signature']} at {m['signature_confidence']:.0%} confidence.")

    # Object classification confidence: "how do we know MS1 is a missile?"
    if target and asks_classification:
        return {"answer": _classification_explanation(target), "confidence": round(confidence, 2), "recommendation":"classification_explanation", "track_id":target.id, "evidence":evidence[:6], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    # Status/risk explanation: "why is U3 suspicious?", "why did A1 become benign/unknown?"
    if target and asks_status_reason and "options" not in intents:
        change_note = ""
        if any(x in ql for x in ["go from", "changed", "become", "became", "turn", "went from", "unknown to", "suspicious to"]):
            change_note = " Orion does not currently store a full per-track status history in this local demo, so I can explain the current label and the likely reason for the change, but not prove the exact earlier transition unless it appears in the event log."
        answer = _status_explanation(target) + change_note + f" Current playbook: {label}, because {'; '.join(playbook_reasons)}."
        return {"answer": answer, "confidence": round(confidence, 2), "recommendation":"status_explanation", "track_id":target.id, "evidence":evidence[:6], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    # Direct score/value questions for a named object.
    if asks_value and (asks_capability or asks_intent or asks_confidence_score or asks_environment or asks_threat_score):
        if asks_capability:
            key, val = "capability", float(target.sub_scores.get("capability", 0.0))
        elif asks_intent:
            key, val = "intent", float(target.sub_scores.get("intent", 0.0))
        elif asks_confidence_score:
            key, val = "confidence", float(target.sub_scores.get("confidence", 0.0))
        elif asks_environment:
            key, val = "environment", float(target.sub_scores.get("environment", 0.0))
        else:
            key, val = "threat", float(target.threat_score or 0.0)
        visible = "; ".join((target.explanation or ["no major abnormal behavior detected"])[:3])
        answer = f"For {_track_display(target)}, {key} is {val:.2f}. {_score_explanation(key, val)} Supporting evidence: {visible}."
        return {"answer": answer, "confidence":0.89, "recommendation":"explain_score", "track_id":target.id, "evidence":target.explanation[:5], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    option_text = "; ".join(f"{name} {score:.0%} because {why}" for _, name, score, why in matrix[:3])
    top_line = ", ".join(f"{t.id}:{t.threat_level}/{t.threat_score:.2f}" for t in ranked[:5])

    if "location" in intents and "priority" in intents:
        answer = (
            f"The biggest simulated threats by location are: {_format_top_tracks(ranked, 4)} "
            f"First map focus: {_track_display(top)}, because it has the strongest combined threat, approach, consequence, and time-pressure score. "
            "Coordinates are simulated global latitude/longitude values used for the demo, not live operational geolocation."
        )
        return {"answer": answer, "confidence": round(confidence, 2), "recommendation":"rank_locations", "track_id":top.id, "evidence":evidence[:6], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    if "overview" in intents and "options" not in intents and "explain" not in intents:
        answer = (
            f"Current sitrep: {summary['posture']}. Tracks: {len(tracks)} total; "
            f"{summary['counts'].get('critical',0)} critical, {summary['counts'].get('suspicious',0)} suspicious, {summary['counts'].get('unknown',0)} unknown, {summary['counts'].get('benign',0)} benign. "
            f"Top ranked objects: {_format_top_tracks(ranked, 4)} "
            f"Recommended next step: {label} for {_track_display(target)} with advisor confidence {confidence:.0%}."
        )
        return {"answer": answer, "confidence": round(confidence, 2), "recommendation": rec, "track_id": target.id, "evidence": evidence[:6], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    if "location" in intents:
        answer = (
            f"{_track_display(target)} is in {target.sensor.get('global_area', 'a global sector')} near {target.sensor.get('global_lat', 'n/a')}, {target.sensor.get('global_lon', 'n/a')}, with altitude {target.z:.0f}, moving {_heading_cardinal(target.vx, target.vy)}. "
            f"Closest approach is about {int(m['cpa'] or 0)} units and time-to-zone is {_fmt_seconds(m['ttz'])}."
        )
        return {"answer": answer, "confidence": round(confidence, 2), "recommendation":"locate_track", "track_id":target.id, "evidence":evidence[:6], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    if "sensors" in intents and "options" not in intents:
        sensor = target.sensor or {}
        catalog = target.catalog or {}
        sig = catalog.get("signature_match", {})
        ml = catalog.get("ml_assessment", {})
        answer = (
            f"Sensor/model readout for {_track_display(target)}: signal confidence {m['signal_confidence']:.2f}, "
            f"radar strength {float(sensor.get('radar_strength', 0) or 0):.2f}, optical confidence {float(sensor.get('optical_confidence', 0) or 0):.2f}, "
            f"thermal {float(sensor.get('thermal', 0) or 0):.2f}, plume index {float(sensor.get('plume_index', 0) or 0):.2f}, jamming estimate {float(sensor.get('jam_estimate', 0) or 0):.2f}. "
            f"Catalog/signature layer: {sig.get('label', 'no strong match')} at {float(sig.get('confidence', 0) or 0):.0%}. "
            f"ML layer: {ml.get('predicted_label', 'no class output')} with top confidence {m['ml_confidence']:.0%}. "
            f"Operationally, this means {'collect another observation window before escalating' if m['signal_confidence'] < .55 else 'the current assessment is usable for simulated planning, while still checking for false positives'}."
        )
        return {"answer": answer, "confidence": round(confidence, 2), "recommendation":"inspect_sensors", "track_id":target.id, "evidence":evidence[:6], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    if "timeline" in intents and "options" not in intents:
        answer = (
            f"Timeline estimate for {_track_display(target)}: TTZ {_fmt_seconds(m['ttz'])}, closest approach {int(m['cpa'] or 0)} units, directness {m['directness']:.2f}, impact probability {m['impact']:.0%}. "
            f"If leadership waits, the cost is reduced verification time. Near-term sequence: raise sensor priority, verify identity/signature, issue advisory or dispatch patrol if the path remains concerning, and reserve simulated intercept/mitigation workflow for high-consequence tracks with strong path evidence."
        )
        return {"answer": answer, "confidence": round(confidence, 2), "recommendation":"timeline", "track_id":target.id, "evidence":evidence[:6], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    if "environment" in intents and "options" not in intents:
        answer = (
            f"{_settings_summary(settings)} For {_track_display(target)}, the per-track environment component is {m['environment']:.2f}. "
            f"Degraded sensing can make a benign object look suspicious or hide a real approach, so under degraded conditions the safer simulated sequence is sensor priority, identity check, communication, patrol inspection, then advisory if exposure grows."
        )
        return {"answer": answer, "confidence": round(confidence, 2), "recommendation":"environment_assessment", "track_id":target.id, "evidence":evidence[:6], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    if "priority" in intents and "options" not in intents:
        answer = (
            f"Focus first on {_track_display(top)}. Ranking logic: fused threat, approach geometry, capability, impact probability, and TTZ. "
            f"Current ranking: {_format_top_tracks(ranked, 5)} "
            f"Immediate recommendation: {label} for {_track_display(target)}."
        )
        return {"answer": answer, "confidence": round(confidence, 2), "recommendation":"prioritize", "track_id":top.id, "evidence":evidence[:6], "mode":"scenario-advisor", "used_model":"Orion playbook + rule/ML fusion"}

    # Default, but still conversational and state-grounded.
    if target is not top and target is not None:
        opening = f"For {_track_display(target)}, I would {label}."
    elif "options" in intents:
        opening = f"My recommendation is to {label} for {_track_display(target)}."
    else:
        opening = f"Based on the current simulation, the main issue is {_track_display(target)}, and I would {label}."

    answer = (
        f"{opening} Advisor confidence: {confidence:.0%}. "
        f"Why: {' '.join(evidence[:5])} "
        f"Response comparison: {option_text}. "
        f"Current ranked tracks: {top_line}. "
        f"Suggested command sequence: keep actions reversible first, improve identification, warn affected airspace/civil channels if exposure grows, and reserve simulated intercept/mitigation workflow for high-consequence tracks with strong path evidence. "
        "This is simulation-only decision support for the Orion demo, not an operational instruction."
    )
    model_name = "Orion playbook + rule/ML fusion"
    if model_hint:
        model_name += " + optional trained advisor RF"
    return {"answer": answer, "confidence": round(confidence, 2), "recommendation": rec, "track_id": target.id, "evidence": evidence[:6], "mode":"scenario-advisor", "used_model": model_name}





# ---------------------------
# Hybrid LLM Scenario Advisor
# ---------------------------
# The deterministic advisor above remains the source-of-truth fallback.  The
# production-style advisor below gives the LLM a compact, structured snapshot of
# the active simulation, plus the transparent playbook recommendation, then asks
# it to synthesize a commander-facing answer.  This keeps the strongest UX part
# of the project conversational without letting the model invent track data.

def _advisor_llm_client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return None
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    return OpenAI(api_key=api_key, base_url=base_url)


def _safe_round(value, digits=3):
    try:
        if value is None:
            return None
        return round(float(value), digits)
    except Exception:
        return value


def _advisor_track_packet(t) -> dict[str, Any]:
    m = _track_metrics(t)
    sig = t.catalog.get("signature_match", {}) if getattr(t, "catalog", None) else {}
    ml = t.catalog.get("ml_assessment", {}) if getattr(t, "catalog", None) else {}
    sensor = t.sensor or {}
    rec, label, reasons = _advisor_playbook(t)
    options = [
        {"action": code, "label": name, "fit": _safe_round(score, 3), "why": why}
        for code, name, score, why in _option_matrix(t)[:5]
    ]
    return {
        "id": t.id,
        "display_name": _track_display(t),
        "label": getattr(t, "label", ""),
        "class_type": t.class_type,
        "threat_level": t.threat_level,
        "priority_score": _safe_round(_priority_score(t), 3),
        "threat_score": _safe_round(t.threat_score, 3),
        "sub_scores": {
            "intent": _safe_round(m["intent"], 3),
            "capability": _safe_round(m["capability"], 3),
            "confidence": _safe_round(m["confidence_component"], 3),
            "environment": _safe_round(m["environment"], 3),
        },
        "impact_probability": _safe_round(m["impact"], 3),
        "time_to_zone_seconds": _safe_round(m["ttz"], 1),
        "closest_approach_units": _safe_round(m["cpa"], 1),
        "directness": _safe_round(m["directness"], 3),
        "signal_confidence": _safe_round(m["signal_confidence"], 3),
        "area": sensor.get("global_area", "global sector"),
        "lat": _safe_round(sensor.get("global_lat"), 3),
        "lon": _safe_round(sensor.get("global_lon"), 3),
        "altitude": _safe_round(sensor.get("altitude", getattr(t, "z", None)), 1),
        "motion": _heading_cardinal(getattr(t, "vx", 0.0), getattr(t, "vy", 0.0)),
        "transponder": sensor.get("transponder", None),
        "sensor_readings": {
            "radar_strength": _safe_round(sensor.get("radar_strength"), 3),
            "optical_confidence": _safe_round(sensor.get("optical_confidence"), 3),
            "thermal": _safe_round(sensor.get("thermal"), 3),
            "plume_index": _safe_round(sensor.get("plume_index"), 3),
            "jamming_estimate": _safe_round(sensor.get("jam_estimate"), 3),
            "dropout_count": sensor.get("dropout_count", None),
        },
        "signature_match": {
            "label": sig.get("label", ""),
            "confidence": _safe_round(sig.get("confidence", 0.0), 3),
            "source_evidence": sig.get("source_evidence", ""),
        },
        "ml_assessment": {
            "predicted_label": ml.get("predicted_label", ""),
            "top_confidence": _safe_round(max((ml.get("probabilities") or {}).values() or [0.0]), 3),
            "cluster_id": ml.get("cluster_id", None),
        },
        "playbook_recommendation": {"action": rec, "label": label, "reasons": reasons},
        "response_option_matrix": options,
        "explanations": list(getattr(t, "explanation", []) or [])[:5],
    }


def _advisor_context_packet(tracks, question: str, track_id: str | None, settings, fallback: dict[str, Any]) -> dict[str, Any]:
    summary = _scenario_summary(tracks) if tracks else {"ranked": [], "counts": {}, "posture": "no tracks"}
    ranked = summary.get("ranked", [])
    target = None
    if tracks:
        by_id = {t.id: t for t in tracks}
        target = _find_track_from_question(tracks, question) or (by_id.get(track_id) if track_id else None) or ranked[0]
    model_hint = predict_advisor_action(target) if target else None
    packet = {
        "advisor_role": "Orion Scenario Advisor for a fictional defense simulation. Human decision support only; no real-world targeting or autonomous action.",
        "user_question": question or "What should I focus on right now?",
        "scenario": getattr(settings, "scenario", "unknown") if settings else "unknown",
        "environment": {
            "weather": getattr(settings, "weather", None),
            "visibility": _safe_round(getattr(settings, "visibility", None), 3),
            "jamming": _safe_round(getattr(settings, "jamming", None), 3),
            "wind": _safe_round(getattr(settings, "wind", None), 3),
            "hazard_intensity": _safe_round(getattr(settings, "hazard_intensity", None), 3),
        },
        "summary": {
            "posture": summary.get("posture"),
            "counts": summary.get("counts"),
            "pressure": _safe_round(summary.get("pressure"), 3),
            "total_tracks": len(tracks or []),
        },
        "selected_or_inferred_focus_track": target.id if target else None,
        "ranked_tracks_top": [_advisor_track_packet(t) for t in ranked[:8]],
        "deterministic_fallback_answer": fallback.get("answer", ""),
        "deterministic_recommendation": {
            "action": fallback.get("recommendation"),
            "confidence": fallback.get("confidence"),
            "track_id": fallback.get("track_id"),
            "evidence": fallback.get("evidence", []),
        },
        "optional_trained_policy_model": model_hint or {"available": False},
        "allowed_simulated_response_categories": [
            "monitor",
            "increase_tracking",
            "identity_check",
            "contact_aircraft",
            "scramble_patrol",
            "airspace_advisory",
            "evacuation_advisory",
            "simulate_intercept",
            "stand_down",
        ],
        "answering_rules": [
            "Use only the provided simulation state and say when information is unavailable.",
            "Be conversational and useful for a leader/operator, but keep it simulation-only.",
            "For serious threats, recommend verification and graduated response categories, not real-world weapon instructions.",
            "When possible, mention track IDs, areas, scores, uncertainty, and why the recommendation follows from the evidence.",
            "If the user asks a broad question, rank the situation; if they name a track, answer about that track.",
        ],
    }
    return packet


def _llm_scenario_answer(question: str, packet: dict[str, Any]) -> dict[str, Any] | None:
    client = _advisor_llm_client()
    if client is None:
        return None
    model = os.getenv("OPENAI_ADVISOR_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini")).strip() or "gpt-4o-mini"
    system_prompt = (
        "You are Orion's LLM Scenario Advisor for a fictional defense simulation. "
        "Your job is to help a human leader understand the CURRENT SIMULATION STATE. "
        "You are a decision-support assistant, not a weapons controller. You must not provide real-world targeting, strike planning, evasion, or operational weapon instructions. "
        "Use only the JSON packet supplied by the backend. Do not invent tracks, scores, locations, sensor readings, model outputs, or events. "
        "Blend three layers: (1) the ranked simulation state, (2) the transparent deterministic playbook, and (3) the optional trained policy model when present. "
        "Answer the user's exact question, not just the default recommendation. "
        "For broad questions, give a prioritized situation assessment. For track-specific questions, focus on that track. "
        "For comparison questions, compare the named tracks directly. For 'why suspicious' questions, state the specific suspicious signals. "
        "Always preserve uncertainty and recommend reversible verification steps when the evidence is ambiguous. "
        "Keep the answer concise but substantive, usually 2-5 short paragraphs or bullets. "
        "End with a clear simulated next step when the question asks what to do."
    )
    user_prompt = (
        f"User question: {question or 'What should I focus on right now?'}\n\n"
        "Backend-provided simulation/advisor packet:\n"
        f"{json.dumps(packet, indent=2, sort_keys=True)}\n\n"
        "Return the best grounded advisor answer. Do not return JSON."
    )
    errors: list[str] = []

    # Prefer the modern Responses API when available. Some existing virtualenvs
    # have older OpenAI SDKs installed, so fall back to Chat Completions instead
    # of silently dropping to the local advisor.
    try:
        if hasattr(client, "responses"):
            response = client.responses.create(
                model=model,
                temperature=0.25,
                max_output_tokens=650,
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                    {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
                ],
            )
            text = getattr(response, "output_text", None)
            if not text:
                text_parts: list[str] = []
                for item in getattr(response, "output", []) or []:
                    for part in getattr(item, "content", []) or []:
                        if getattr(part, "type", "") in {"output_text", "text"}:
                            text_parts.append(getattr(part, "text", ""))
                text = "".join(text_parts)
            text = (text or "").strip()
            if text:
                return {"answer": text, "used_model": model, "llm_ok": True, "api": "responses"}
            errors.append("Responses API returned an empty answer.")
        else:
            errors.append("Installed OpenAI SDK has no client.responses API.")
    except Exception as e:
        errors.append(f"Responses API failed: {type(e).__name__}: {e}")

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.25,
            max_tokens=650,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        if text:
            return {"answer": text, "used_model": model, "llm_ok": True, "api": "chat.completions"}
        errors.append("Chat Completions returned an empty answer.")
    except Exception as e:
        errors.append(f"Chat Completions failed: {type(e).__name__}: {e}")

    return {"answer": "", "used_model": model, "llm_ok": False, "error": " | ".join(errors)}


def advisor_assessment(tracks, question: str = "", track_id: str | None = None, settings=None) -> dict[str, Any]:
    """Hybrid advisor: deterministic/ML analysis first, LLM synthesis second.

    The deterministic answer is still computed first so the project remains reliable
    without an API key.  When an OpenAI key is configured, an LLM receives a compact
    simulation packet and turns that grounded analysis into a much stronger, more
    flexible command-style response.
    """
    fallback = _fallback_advisor_assessment(tracks, question, track_id, settings)
    if not tracks:
        return fallback
    packet = _advisor_context_packet(tracks, question, track_id, settings, fallback)
    llm = _llm_scenario_answer(question, packet)
    if llm and llm.get("llm_ok") and llm.get("answer"):
        return {
            **fallback,
            "answer": llm["answer"],
            "mode": "hybrid-llm-scenario-advisor",
            "used_model": f"{llm['used_model']} + Orion playbook/ML fusion",
            "grounding": {
                "focus_track": packet.get("selected_or_inferred_focus_track"),
                "top_tracks": [t["id"] for t in packet.get("ranked_tracks_top", [])[:5]],
                "source": "live simulation state + deterministic playbook + optional trained policy model",
            },
        }
    if llm and llm.get("error"):
        fallback["llm_error"] = llm["error"]
        fallback["answer"] = (
            "LLM advisor was requested because OPENAI_API_KEY is set, but the OpenAI call failed. "
            "I am showing the local advisor answer below so the simulation still runs.\n\n"
            f"LLM error: {llm['error']}\n\n"
            f"Local fallback answer: {fallback.get('answer', '')}"
        )
        fallback["used_model"] = f"LLM failed ({llm.get('used_model', 'configured model')}); local Orion playbook/ML fallback used"
        fallback["mode"] = "hybrid-fallback-llm-error"
    else:
        fallback["used_model"] = "Orion playbook/ML fusion fallback; set OPENAI_API_KEY for LLM advisor"
        fallback["mode"] = "hybrid-fallback-local"
    return fallback


class World:
    def __init__(self):
        self.zone = default_zone()
        self.settings = EnvironmentState()
        self.truth = make_truth(self.settings)
        self.tracker = TrackManager()
        self.anomaly = AnomalyModel()
        self.ml = MLStack()
        self.time_s = 0.0
        self.selected = None
        self.events: list[dict[str, Any]] = []
        self.live_cache: dict[str, Any] = {}
        self._last_live_fetch: float = -9999.0
        self.spawn_counter: int = 1
        self._last_levels: dict[str, str] = {}
        self._last_intrusions: set[str] = set()
        self._last_anomaly: set[str] = set()
        self._last_signature: set[str] = set()
        self._step(0.1)

    def reset(self, scenario: str | None = None):
        if scenario:
            self.settings.scenario = scenario
        self.truth = make_truth(self.settings)
        self.tracker = TrackManager()
        self.time_s = 0.0
        self.events = []
        self.spawn_counter = 1
        self._last_levels = {}
        self._last_intrusions = set()
        self._last_anomaly = set()
        self._last_signature = set()
        self.events.insert(0, {"time": round(self.time_s,1), "kind": "unknown", "message": f"Scenario loaded: {self.settings.scenario.replace('_', ' ' )}."})
        self._step(0.1)

    def _make_explanation(self, t: EstimatedTrack):
        reasons = []
        if t.directness > 0.75: reasons.append("moving directly toward the protected zone")
        if (t.ttz or 999) < 240: reasons.append(f"projected to approach within {int(t.ttz or 0)} seconds")
        if t.sensor.get("impact_probability", 0) > 0.55: reasons.append("short-horizon prediction intersects or closely approaches the protected area")
        if not t.sensor.get("transponder", True): reasons.append("identification is disabled or missing")
        if t.no_fly_intrusion: reasons.append("inside a restricted no-fly area")
        if t.swarm_likelihood > 0.4: reasons.append("shows coordinated group behavior")
        if t.origin_type == "extraterrestrial": reasons.append("classified as non-terrestrial or extraterrestrial-style")
        if t.sensor.get("radiation", 0) > 10: reasons.append("radiation signature is above normal background")
        if t.sensor.get("plume_index", 0) > 0.7: reasons.append("plume or propulsion signature is elevated")
        sig = t.catalog.get("signature_match", {}) if t.catalog else {}
        if sig.get("confidence", 0) > 0.58:
            reasons.append(f"public signature match suggests {sig.get('label')}")
        if t.class_type in {"missile", "asteroid", "foreign_spaceship"} and not any("high capability" in r for r in reasons):
            reasons.append("object family has high consequence potential in this scenario")
        if not reasons: reasons = ["currently behaving within expected bounds"]
        t.explanation = reasons[:5]
        plain = f"{t.id} is {t.threat_level}. "
        if t.threat_level in {"suspicious", "critical"}:
            plain += "Flagged because it is " + ", ".join(reasons[:3]) + "."
        else:
            plain += "It looks stable because it is " + ", ".join(reasons[:2]) + "."
        t.summary = plain

    def _blend_live_data(self):
        if self.live_cache and (self.time_s - self._last_live_fetch) < 300:
            return
        live = {"opensky": [], "iss": {}, "neo": {}, "links": SOURCE_LINKS}
        try:
            live["opensky"] = fetch_opensky()[:8]
        except Exception:
            live["opensky"] = []
        try:
            live["iss"] = fetch_celestrak_iss()
        except Exception:
            live["iss"] = {}
        try:
            live["neo"] = fetch_neo()
        except Exception:
            live["neo"] = {}
        self.live_cache = live
        self._last_live_fetch = self.time_s

    def _step(self, dt: float):
        self.time_s += dt
        for obj in self.truth:
            step_truth(obj, dt, self.settings)
        obs = [observe(obj, self.settings) for obj in self.truth]
        tracks = self.tracker.update(self.truth, obs, dt)
        for t in tracks:
            enrich(t, self.zone, self.settings, tracks)
            t.anomaly_score = self.anomaly.score(t)
        scores = run_engine(tracks)
        self._blend_live_data()
        for t in tracks:
            s = scores[t.id]
            t.sub_scores = {k: round(v, 3) for k, v in s.items() if k in {"intent", "capability", "confidence", "environment"}}
            t.threat_score = round(s["threat_score"], 3)
            t.threat_level = s["threat_level"]
            t.catalog["signature_match"] = score_track_against_profiles(t, self.live_cache)
            t.catalog["ml_assessment"] = self.ml.assess(t)
            # Post-fusion escalation: combine C++ score with signature, impact probability, and ML label.
            sig = t.catalog.get("signature_match", {})
            ml = t.catalog.get("ml_assessment", {})
            impact = float(t.sensor.get("impact_probability", 0) or 0)
            if t.class_type in {"missile", "asteroid", "foreign_spaceship"}:
                if impact > 0.45 or t.directness > 0.55 or (t.ttz or 999) < 420:
                    t.threat_score = max(t.threat_score, 0.82 if t.class_type != "foreign_spaceship" else 0.72)
                if t.sensor.get("predicted_zone_intersection") or (t.cpa is not None and t.cpa < self.zone.radius * 0.35):
                    t.threat_score = max(t.threat_score, 0.88 if t.class_type != "foreign_spaceship" else 0.76)
            if sig.get("family") in {"missile", "asteroid", "foreign_spaceship"} and sig.get("confidence", 0) > 0.55:
                t.threat_score = max(t.threat_score, 0.76)
            if ml.get("predicted_label") in {"critical", "missile", "asteroid", "foreign_spaceship"} and max((ml.get("probabilities") or {}).values() or [0]) > 0.42:
                t.threat_score = max(t.threat_score, 0.68)
            unresolved = (t.class_type == "unknown" or float(sig.get("confidence", 0) or 0) < 0.32) and not t.sensor.get("transponder", False)
            if unresolved and t.age_s > 8 and (t.no_fly_intrusion or t.directness > 0.44 or (t.cpa is not None and t.cpa < self.zone.radius * 0.95)):
                t.threat_score = max(t.threat_score, 0.56)
                t.catalog.setdefault("risk_tags", []).append("unresolved unknown")
            if unresolved and t.age_s > 16 and (t.no_fly_intrusion or t.directness > 0.58 or (t.cpa is not None and t.cpa < self.zone.radius * 0.6) or impact > 0.18):
                t.threat_score = max(t.threat_score, 0.81)
                t.catalog.setdefault("risk_tags", []).append("unknown dangerous")
            if t.threat_score >= 0.76:
                t.threat_level = "critical"
            elif t.threat_score >= 0.46:
                t.threat_level = "suspicious"
            elif t.threat_score >= 0.22:
                t.threat_level = "unknown"
            else:
                t.threat_level = "benign"
            loc = _global_track_location(t, self.settings)
            t.sensor["global_lat"] = loc["lat"]
            t.sensor["global_lon"] = loc["lon"]
            t.sensor["global_area"] = loc["area"]
            t.catalog["us_perspective"] = {
                "protected_reference": "United States protected airspace network",
                "priority_logic": "Objects are prioritized by consequence class, approach geometry, transponder/identity, sensor confidence, and whether the path could affect US airspace.",
            }
            self._make_explanation(t)
        self.tracks = tracks
        current_intrusions: set[str] = set()
        current_anomaly: set[str] = set()
        current_signature: set[str] = set()
        for t in tracks:
            prev_level = self._last_levels.get(t.id)
            if prev_level != t.threat_level:
                if t.threat_level == "critical":
                    self.events.insert(0, {"time": round(self.time_s,1), "kind": "critical", "message": f"{t.id} escalated to critical: {t.explanation[0]}"})
                elif t.threat_level == "suspicious" and prev_level not in {"suspicious", "critical"}:
                    self.events.insert(0, {"time": round(self.time_s,1), "kind": "suspicious", "message": f"{t.id} became suspicious: {t.explanation[0]}"})
            self._last_levels[t.id] = t.threat_level

            if t.no_fly_intrusion:
                current_intrusions.add(t.id)
                if t.id not in self._last_intrusions:
                    self.events.insert(0, {"time": round(self.time_s,1), "kind": "suspicious", "message": f"{t.id} entered the restricted zone."})

            if t.anomaly_score > 0.62:
                current_anomaly.add(t.id)
                if t.id not in self._last_anomaly:
                    self.events.insert(0, {"time": round(self.time_s,1), "kind": "unknown", "message": f"{t.id} triggered a behavior anomaly spike ({t.anomaly_score:.2f})."})

            sig = t.catalog.get("signature_match", {}) if t.catalog else {}
            if sig.get("confidence", 0) > 0.72 and sig.get("label"):
                current_signature.add(t.id)
                if t.id not in self._last_signature:
                    self.events.insert(0, {"time": round(self.time_s,1), "kind": "unknown", "message": f"{t.id} matched public signature profile {sig.get('label')}."})

        self._last_intrusions = current_intrusions
        self._last_anomaly = current_anomaly
        self._last_signature = current_signature
        self.events = self.events[:40]


    def add_object(self, kind: str):
        obj = spawn_custom_object(kind, self.spawn_counter)
        self.spawn_counter += 1
        self.truth.append(obj)
        self.events.insert(0, {"time": round(self.time_s,1), "kind": "unknown", "message": f"Operator injected {obj.label.lower()} ({obj.id}) for testing."})
        self.events = self.events[:25]
        self._step(0.1)

    def remove_object(self, track_id: str):
        before = len(self.truth)
        self.truth = [obj for obj in self.truth if obj.id != track_id]
        if len(self.truth) != before:
            self.events.insert(0, {"time": round(self.time_s,1), "kind": "unknown", "message": f"Operator removed {track_id} from the scenario."})
            self.events = self.events[:25]
            self._step(0.1)

    def rename_object(self, track_id: str, label: str):
        clean = " ".join((label or "").strip().split())[:64]
        if not clean:
            return
        changed = False
        for obj in self.truth:
            if obj.id == track_id:
                obj.label = clean
                obj.extra["profile_label"] = clean
                changed = True
        for tr in getattr(self, "tracks", []):
            if tr.id == track_id:
                tr.label = clean
                tr.sensor["profile_label"] = clean
        if changed:
            self.events.insert(0, {"time": round(self.time_s,1), "kind": "unknown", "message": f"Renamed {track_id} to {clean}."})
            self.events = self.events[:40]

    def respond(self, track_id: str, action: str):
        labels = {
            "monitor": "Continued routine monitoring",
            "increase_tracking": "Raised sensor priority",
            "identity_check": "Requested identity / transponder verification",
            "contact_aircraft": "Attempted aircraft communications",
            "scramble_patrol": "Dispatched patrol / inspection aircraft",
            "airspace_advisory": "Issued airspace advisory",
            "evacuation_advisory": "Issued civil protection advisory",
            "simulate_intercept": "Simulated defensive intercept workflow",
            "stand_down": "Marked response as stand down",
        }
        label = labels.get(action, action.replace("_", " ").title())
        self.events.insert(0, {"time": round(self.time_s,1), "kind": "unknown", "message": f"Response selected for {track_id}: {label}."})
        self.events = self.events[:40]

    def state(self):
        weather_penalty = {"clear":0.0,"rain":0.1,"fog":0.2,"storm":0.28}.get(self.settings.weather,0.0)
        summary = {
            "total": len(self.tracks),
            "benign": sum(1 for t in self.tracks if t.threat_level == "benign"),
            "unknown": sum(1 for t in self.tracks if t.threat_level == "unknown"),
            "suspicious": sum(1 for t in self.tracks if t.threat_level == "suspicious"),
            "critical": sum(1 for t in self.tracks if t.threat_level == "critical"),
            "message": f"{len(self.tracks)} objects tracked. {sum(1 for t in self.tracks if t.threat_level in {'suspicious','critical'})} need attention.",
            "sensor_penalty": round(weather_penalty + self.settings.jamming*0.4 + (1-self.settings.visibility)*0.25, 3)
        }
        return {
            "time_s": round(self.time_s, 1),
            "settings": self.settings.__dict__,
            "summary": summary,
            "zone": self.zone.__dict__,
            "tracks": [t.to_dict() for t in self.tracks],
            "events": self.events,
            "scenarios": SCENARIOS,
            "hazard_zone": {"x": HAZARD_ZONE[0], "y": HAZARD_ZONE[1], "radius": HAZARD_ZONE[2]},
            "no_fly_zone": {"x": NO_FLY_ZONE[0], "y": NO_FLY_ZONE[1], "radius": NO_FLY_ZONE[2]},
            "live_catalog": self.live_cache,
            "global_aircraft": GLOBAL_AIRCRAFT,
            "supported_object_kinds": ["aircraft", "drone", "missile", "satellite", "debris", "asteroid", "foreign_spaceship"],
            "response_options": ["monitor", "increase_tracking", "identity_check", "contact_aircraft", "scramble_patrol", "airspace_advisory", "evacuation_advisory", "simulate_intercept"],
            "supported_regions": ["Southern California", "Bay Area", "Nevada Test Range", "Pacific Northwest", "East Coast"],
        }

WORLD = World()
app = FastAPI(title="Orion")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

@app.get("/")
def root():
    return FileResponse(STATIC / "index.html")

@app.get("/api/state")
def api_state():
    return WORLD.state()

@app.post("/api/step")
def api_step(req: StepRequest):
    WORLD._step(req.dt)
    return WORLD.state()

@app.post("/api/reset")
def api_reset(settings: SettingsModel):
    WORLD.settings = EnvironmentState(**settings.model_dump())
    WORLD.reset(settings.scenario)
    return WORLD.state()

@app.post("/api/settings")
def api_settings(settings: SettingsModel):
    old_scenario = WORLD.settings.scenario
    WORLD.settings = EnvironmentState(**settings.model_dump())
    if settings.scenario != old_scenario:
        WORLD.reset(settings.scenario)
    else:
        WORLD._step(0.1)
    return WORLD.state()


@app.post("/api/add_object")
def api_add_object(req: AddObjectRequest):
    WORLD.add_object(req.kind)
    return WORLD.state()


@app.post("/api/remove_object")
def api_remove_object(req: RemoveObjectRequest):
    WORLD.remove_object(req.track_id)
    return WORLD.state()


@app.post("/api/rename_object")
def api_rename_object(req: RenameObjectRequest):
    WORLD.rename_object(req.track_id, req.label)
    return WORLD.state()


@app.post("/api/respond")
def api_respond(req: ResponseRequest):
    WORLD.respond(req.track_id, req.action)
    return WORLD.state()

@app.post("/api/ask")
def api_ask(req: AskRequest):
    return QA.answer(req.question)


@app.get("/api/ask_status")
def api_ask_status():
    return QA.status()

@app.get("/api/advisor_status")
def api_advisor_status():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_ADVISOR_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini")).strip() or "gpt-4o-mini"
    return {
        "llm_enabled": bool(key and OpenAI is not None),
        "model": model,
        "openai_sdk_imported": OpenAI is not None,
        "key_detected": bool(key),
        "key_preview": (key[:7] + "..." + key[-4:]) if key else "",
        "supports_responses_api": bool(OpenAI is not None and hasattr(OpenAI(api_key=key or "dummy"), "responses")),
        "fallback": "local playbook + optional ML policy",
    }

@app.post("/api/advisor")
def api_advisor(req: AdvisorRequest):
    return advisor_assessment(WORLD.tracks, req.question, req.track_id, WORLD.settings)
