from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Literal

OriginType = Literal["terrestrial", "orbital_earth_origin", "extraterrestrial", "unknown"]
SourceType = Literal["simulated", "opensky", "celestrak", "nasa_jpl", "fused"]
ClassType = Literal["aircraft", "drone", "missile", "satellite", "debris", "asteroid", "foreign_spaceship", "unknown"]
ThreatLevel = Literal["benign", "unknown", "suspicious", "critical"]

@dataclass
class EnvironmentState:
    scenario: str = "mixed_airspace"
    weather: str = "clear"
    wind: float = 0.2
    visibility: float = 0.9
    jamming: float = 0.1
    hazard_intensity: float = 0.2
    live_data: bool = True
    guided_mode: bool = True
    three_d: bool = False

@dataclass
class Zone:
    x: float
    y: float
    radius: float
    name: str

@dataclass
class TruthObject:
    id: str
    class_type: ClassType
    source_type: SourceType
    origin_type: OriginType
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    size_m: float
    shape_class: str
    thermal: float
    radiation: float
    rcs: float
    transponder: bool
    label: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

@dataclass
class SensorObservation:
    id: str
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    radar_strength: float
    thermal: float
    radiation: float
    size_est: float
    shape_est: str
    transponder: bool
    optical_confidence: float
    signal_confidence: float
    dropout_count: int
    jam_estimate: float
    rcs_est: float
    acoustic: float
    plume_index: float
    magnetic: float
    spectral_class: str
    infrared_band: str
    seeker_emissions: float
    ionization: float
    doppler_quality: float
    material_reflectivity: float

@dataclass
class EstimatedTrack:
    id: str
    class_type: ClassType
    source_type: SourceType
    origin_type: OriginType
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    uncertainty: float
    confidence: float
    history: list[tuple[float, float]] = field(default_factory=list)
    predicted_path: list[tuple[float, float]] = field(default_factory=list)
    sensor: dict[str, Any] = field(default_factory=dict)
    catalog: dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    explanation: list[str] = field(default_factory=list)
    sub_scores: dict[str, float] = field(default_factory=dict)
    anomaly_score: float = 0.0
    threat_score: float = 0.0
    threat_level: ThreatLevel = "unknown"
    swarm_likelihood: float = 0.0
    cpa: float = 0.0
    ttz: float | None = None
    directness: float = 0.0
    no_fly_intrusion: bool = False
    hazard_nearby: bool = False
    physics_model: str = ""
    tracking_model: str = "Kalman-lite"
    prediction_model: str = "Constant velocity"
    ai_model: str = "IsolationForest"
    label: str = ""
    age_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["history"] = [list(p) for p in self.history]
        d["predicted_path"] = [list(p) for p in self.predicted_path]
        return d
