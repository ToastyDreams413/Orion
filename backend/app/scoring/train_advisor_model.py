"""Train an optional synthetic advisor policy model for Orion.

Run from the project root:
    python -m backend.app.scoring.train_advisor_model

This creates backend/app/scoring/advisor_policy_model.joblib. The live app does not
require it, but when present the AI Advisor will include it as a learned second
opinion alongside the rule/ML fusion playbook.
"""
from __future__ import annotations

from pathlib import Path
import random
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

ACTIONS = [
    "monitor", "increase_tracking", "identity_check", "contact_aircraft",
    "scramble_patrol", "airspace_advisory", "evacuation_advisory", "simulate_intercept"
]


def label_policy(row):
    threat, intent, cap, conf, env, impact, ttz, cpa, direct, sigconf, mlconf, is_missile, is_air, is_drone, is_unknown, is_space, transponder, intrusion = row
    urgent = ttz < 300 or impact > 0.45 or threat > 0.76
    uncertain = conf < 0.45 or is_unknown > 0.5
    if is_air and transponder and threat < 0.65:
        return "contact_aircraft" if intent > 0.35 or intrusion else "identity_check"
    if (is_missile or is_space) and urgent:
        return "simulate_intercept"
    if intrusion and (is_drone or is_unknown or threat > 0.55):
        return "scramble_patrol"
    if urgent or impact > 0.30:
        return "airspace_advisory"
    if uncertain or threat > 0.35:
        return "increase_tracking"
    return "monitor"


def make_row():
    threat = random.random()
    intent = random.random()
    cap = random.random()
    conf = random.random()
    env = random.random()
    impact = min(1.0, max(0.0, random.gauss(threat * intent, 0.18)))
    ttz = random.uniform(30, 1800)
    cpa = random.uniform(0, 2200)
    direct = random.random()
    sigconf = random.random()
    mlconf = random.random()
    cls = random.choice(["missile", "aircraft", "drone", "unknown", "space", "benign"])
    is_missile = cls == "missile"
    is_air = cls == "aircraft"
    is_drone = cls == "drone"
    is_unknown = cls == "unknown"
    is_space = cls == "space"
    transponder = is_air and random.random() > 0.25
    intrusion = random.random() < (0.15 + threat * 0.45)
    return [threat, intent, cap, conf, env, impact, ttz, cpa, direct, sigconf, mlconf, float(is_missile), float(is_air), float(is_drone), float(is_unknown), float(is_space), float(transponder), float(intrusion)]


def main():
    random.seed(7)
    X = [make_row() for _ in range(25000)]
    y = [label_policy(row) for row in X]
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=7, stratify=y)
    model = RandomForestClassifier(n_estimators=160, max_depth=12, min_samples_leaf=3, class_weight="balanced", random_state=7, n_jobs=-1)
    model.fit(x_train, y_train)
    print(classification_report(y_test, model.predict(x_test)))
    out = Path(__file__).resolve().parent / "advisor_policy_model.joblib"
    joblib.dump(model, out)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
