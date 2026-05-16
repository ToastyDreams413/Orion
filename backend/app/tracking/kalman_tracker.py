from __future__ import annotations
from collections import defaultdict
from ..models import EstimatedTrack, SensorObservation, TruthObject

class TrackManager:
    def __init__(self):
        self.tracks: dict[str, EstimatedTrack] = {}

    def update(self, truths: list[TruthObject], observations: list[SensorObservation], dt: float) -> list[EstimatedTrack]:
        truth_by_id = {t.id: t for t in truths}
        for obs in observations:
            truth = truth_by_id[obs.id]
            prev = self.tracks.get(obs.id)
            alpha = 0.65 if prev else 1.0
            x = obs.x if prev is None else alpha * obs.x + (1-alpha) * (prev.x + prev.vx * dt)
            y = obs.y if prev is None else alpha * obs.y + (1-alpha) * (prev.y + prev.vy * dt)
            z = obs.z if prev is None else alpha * obs.z + (1-alpha) * max(0, prev.z + prev.vz * dt)
            vx = obs.vx if prev is None else alpha * obs.vx + (1-alpha) * prev.vx
            vy = obs.vy if prev is None else alpha * obs.vy + (1-alpha) * prev.vy
            vz = obs.vz if prev is None else alpha * obs.vz + (1-alpha) * prev.vz
            uncertainty = max(8.0, (1 - obs.signal_confidence + obs.jam_estimate) * 120 + obs.dropout_count * 20)
            conf = max(0.05, min(1.0, (obs.radar_strength * 0.45 + obs.optical_confidence * 0.25 + obs.signal_confidence * 0.30) - obs.dropout_count * 0.08))
            history = prev.history[-25:] if prev else []
            history = history + [(x, y)]
            speed = (vx * vx + vy * vy + vz * vz) ** 0.5
            horiz_speed = (vx * vx + vy * vy) ** 0.5
            accel = 0.0 if prev is None or dt <= 0 else (((vx - prev.vx) ** 2 + (vy - prev.vy) ** 2 + (vz - prev.vz) ** 2) ** 0.5) / dt
            heading_deg = (__import__('math').degrees(__import__('math').atan2(vy, vx)) + 360.0) % 360.0
            self.tracks[obs.id] = EstimatedTrack(
                id=obs.id,
                class_type=truth.class_type,
                source_type=truth.source_type,
                origin_type=truth.origin_type,
                x=x, y=y, z=z, vx=vx, vy=vy, vz=vz,
                uncertainty=uncertainty, confidence=conf, history=history,
                sensor={
                    "radar_strength": round(obs.radar_strength, 3),
                    "speed": round(speed, 2),
                    "horizontal_speed": round(horiz_speed, 2),
                    "velocity_vector": [round(vx,2), round(vy,2), round(vz,2)],
                    "acceleration": round(accel, 2),
                    "heading_deg": round(heading_deg, 1),
                    "climb_rate": round(vz, 2),
                    "altitude": round(z, 1),
                    "thermal": round(obs.thermal, 2),
                    "radiation": round(obs.radiation, 2),
                    "size_est": round(obs.size_est, 2),
                    "shape_est": obs.shape_est,
                    "optical_confidence": round(obs.optical_confidence, 3),
                    "signal_confidence": round(obs.signal_confidence, 3),
                    "dropout_count": obs.dropout_count,
                    "jam_estimate": round(obs.jam_estimate, 3),
                    "rcs_est": round(obs.rcs_est, 2),
                    "acoustic": round(obs.acoustic, 2),
                    "plume_index": round(obs.plume_index, 3),
                    "magnetic": round(obs.magnetic, 3),
                    "spectral_class": obs.spectral_class,
                    "transponder": obs.transponder,
                    "infrared_band": obs.infrared_band,
                    "seeker_emissions": round(obs.seeker_emissions, 3),
                    "ionization": round(obs.ionization, 3),
                    "doppler_quality": round(obs.doppler_quality, 3),
                    "material_reflectivity": round(obs.material_reflectivity, 3),
                    "profile_label": truth.extra.get("profile_label", truth.label),
                    "country_or_family": truth.extra.get("country", "n/a"),
                },
                label=truth.label,
                age_s=(getattr(prev, "age_s", 0.0) + dt) if prev else dt,
                physics_model={
                    "aircraft": "Bounded turn + drag + wind drift",
                    "drone": "Agile airframe + wind drift",
                    "missile": "Simplified ballistic descent",
                    "satellite": "Catalog orbit pass",
                    "debris": "Catalog orbit pass",
                    "asteroid": "Close-approach approximation",
                    "foreign_spaceship": "Anomalous non-terrestrial motion prior",
                    "unknown": "Generic aerial object",
                }.get(truth.class_type, "Generic"),
            )
        return list(self.tracks.values())
