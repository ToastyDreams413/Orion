from __future__ import annotations
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from ..models import EstimatedTrack

class MLStack:
    def __init__(self):
        rng = np.random.default_rng(7)
        X=[]; y=[]
        # benign aircraft-ish
        for _ in range(500):
            speed=abs(rng.normal(135,35)); accel=abs(rng.normal(4,2)); direct=float(np.clip(rng.normal(0.28,0.15),0,1)); ttz=abs(rng.normal(280,120)); rad=abs(rng.normal(0.5,0.4)); therm=abs(rng.normal(34,9)); plume=float(np.clip(rng.normal(0.42,0.15),0,1)); swarm=float(np.clip(rng.normal(0.08,0.07),0,1)); trans=1.0 if rng.random()<0.85 else 0.0; uncert=abs(rng.normal(24,12));
            X.append([speed,accel,direct,ttz,rad,therm,plume,swarm,trans,uncert]); y.append('benign')
        # suspicious/drone/unknown
        for _ in range(320):
            speed=abs(rng.normal(95,45)); accel=abs(rng.normal(10,5)); direct=float(np.clip(rng.normal(0.62,0.18),0,1)); ttz=abs(rng.normal(150,70)); rad=abs(rng.normal(2.2,1.7)); therm=abs(rng.normal(48,16)); plume=float(np.clip(rng.normal(0.55,0.18),0,1)); swarm=float(np.clip(rng.normal(0.35,0.2),0,1)); trans=1.0 if rng.random()<0.25 else 0.0; uncert=abs(rng.normal(42,18));
            X.append([speed,accel,direct,ttz,rad,therm,plume,swarm,trans,uncert]); y.append('suspicious')
        # critical/missile/asteroid-like
        for _ in range(220):
            speed=abs(rng.normal(260,85)); accel=abs(rng.normal(18,8)); direct=float(np.clip(rng.normal(0.84,0.12),0,1)); ttz=abs(rng.normal(75,35)); rad=abs(rng.normal(12,7)); therm=abs(rng.normal(95,25)); plume=float(np.clip(rng.normal(0.82,0.14),0,1)); swarm=float(np.clip(rng.normal(0.12,0.1),0,1)); trans=1.0 if rng.random()<0.05 else 0.0; uncert=abs(rng.normal(54,20));
            X.append([speed,accel,direct,ttz,rad,therm,plume,swarm,trans,uncert]); y.append('critical')
        X=np.asarray(X)
        self.classifier = RandomForestClassifier(n_estimators=160, max_depth=8, random_state=7)
        self.classifier.fit(X, y)
        self.clusterer = KMeans(n_clusters=4, random_state=7, n_init=10)
        self.clusterer.fit(X[:, :6])

    def assess(self, track: EstimatedTrack) -> dict:
        speed = track.sensor.get('speed', (track.vx**2 + track.vy**2) ** 0.5)
        accel = track.sensor.get('acceleration', 0.0)
        direct = track.directness
        ttz = track.ttz or 999.0
        rad = track.sensor.get('radiation', 0.0)
        therm = track.sensor.get('thermal', 0.0)
        plume = track.sensor.get('plume_index', 0.0)
        swarm = track.swarm_likelihood
        trans = 1.0 if track.sensor.get('transponder') else 0.0
        uncert = track.uncertainty
        x = np.array([[speed, accel, direct, ttz, rad, therm, plume, swarm, trans, uncert]])
        probs = self.classifier.predict_proba(x)[0]
        labels = list(self.classifier.classes_)
        top_idx = int(np.argmax(probs))
        cluster = int(self.clusterer.predict(x[:, :6])[0])
        importance = {name: float(val) for name, val in zip(['speed','acceleration','directness','time_to_zone','radiation','thermal','plume_index','swarm_likelihood','transponder','uncertainty'], self.classifier.feature_importances_)}
        top_features = sorted(importance.items(), key=lambda kv: kv[1], reverse=True)[:4]
        return {
            'predicted_label': labels[top_idx],
            'probabilities': {lab: round(float(prob), 3) for lab, prob in zip(labels, probs)},
            'cluster_id': cluster,
            'top_features': top_features,
            'models': ['IsolationForest','RandomForest','KMeans']
        }
