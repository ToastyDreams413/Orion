from __future__ import annotations
import random
import numpy as np
from sklearn.ensemble import IsolationForest
from ..models import EstimatedTrack

class AnomalyModel:
    def __init__(self):
        rng = np.random.default_rng(42)
        X = []
        for _ in range(800):
            speed = abs(rng.normal(120, 45))
            directness = float(np.clip(rng.normal(0.35, 0.2), 0, 1))
            ttz = abs(rng.normal(220, 80))
            uncertainty = abs(rng.normal(35, 15))
            radiation = abs(rng.normal(0.8, 0.5))
            thermal = abs(rng.normal(28, 10))
            swarm = float(np.clip(rng.normal(0.1, 0.08), 0, 1))
            transponder = float(rng.choice([0, 1], p=[0.1, 0.9]))
            X.append([speed, directness, ttz, uncertainty, radiation, thermal, swarm, transponder])
        self.model = IsolationForest(n_estimators=120, contamination=0.08, random_state=42)
        self.model.fit(np.array(X))

    def score(self, track: EstimatedTrack) -> float:
        speed = (track.vx ** 2 + track.vy ** 2) ** 0.5
        x = np.array([[speed, track.directness, track.ttz or 999.0, track.uncertainty, track.sensor.get("radiation", 0.0), track.sensor.get("thermal", 0.0), track.swarm_likelihood, 1.0 if track.sensor.get("transponder") else 0.0]])
        return float(-self.model.score_samples(x)[0])
