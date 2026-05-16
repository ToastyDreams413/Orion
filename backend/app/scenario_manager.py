from __future__ import annotations
import math
from .models import EnvironmentState, TruthObject, Zone
import random

SCENARIOS = {
    "mixed_airspace": "Balanced monitoring scene with real-world-style aircraft, a drone, and an unidentified track. Good for a simple first demo.",
    "storm_intrusion": "Severe weather and jamming degrade visibility and confidence while an unidentified aircraft-like track pushes toward restricted airspace.",
    "drone_swarm": "Coordinated small UAS tracks converge from multiple bearings, stressing group-behavior and swarm detection.",
    "ballistic_approach": "Long-range inbound ballistic and cruise-missile style tracks start far outside the defended region and approach at high speed.",
    "orbital_pass": "Catalog-style satellites and debris pass above the monitored area, emphasizing altitude and Earth-orbit classification.",
    "asteroid_pass": "Extraterrestrial-style objects approach from outside the local region with high altitude and non-terrestrial signatures.",
    "live_public_blend": "A mixed scene that blends simulated activity with public-source-informed aircraft, orbital, missile, and NEO signature profiles.",
    "layered_defense_drill": "A more realistic multi-domain drill: civil traffic, a suspicious drone, a cruise-missile-like low-altitude object, and a fighter patrol all compete for operator attention.",
    "false_alarm_filter": "A false-positive stress test where benign or explainable tracks look alarming until identity, trajectory, and signal confidence are considered together.",
}

AIRCRAFT_PROFILES = {
    "B737": dict(label="Boeing 737-style transport", country="civil/commercial", size=36, shape="twin-engine airliner", thermal=48, radiation=0.2, rcs=18, speed=145, alt=10500, transponder=True),
    "A320": dict(label="A320-style transport", country="civil/commercial", size=34, shape="twin-engine airliner", thermal=47, radiation=0.2, rcs=17, speed=143, alt=10400, transponder=True),
    "F16": dict(label="F-16-style fighter", country="United States / allied", size=15, shape="fighter", thermal=72, radiation=0.4, rcs=7, speed=230, alt=14500, transponder=False),
    "SU35": dict(label="Su-35-style fighter", country="Russia-style public profile", size=21, shape="fighter", thermal=79, radiation=0.5, rcs=9, speed=245, alt=14800, transponder=False),
    "RAFALE": dict(label="Rafale-style fighter", country="France-style public profile", size=15.3, shape="fighter", thermal=70, radiation=0.35, rcs=6.4, speed=225, alt=14200, transponder=False),
    "C130": dict(label="C-130-style transport", country="military transport", size=30, shape="four-engine transport", thermal=58, radiation=0.2, rcs=26, speed=130, alt=8000, transponder=True),
    "UAS": dict(label="Shahed-136-style one-way UAS", country="Iran-style public profile", size=3.5, shape="delta-wing small UAS", thermal=42, radiation=0.1, rcs=3.5, speed=58, alt=900, transponder=False),
}

MISSILE_PROFILES = {
    "SCUD": dict(label="Scud-style ballistic missile", country="legacy ballistic profile", size=11.0, shape="ballistic cone", thermal=125, radiation=18, rcs=8, speed=520, alt=90000, vz=-720, plume=0.98),
    "ISKANDER": dict(label="Iskander-style SRBM", country="Russia-style public profile", size=7.3, shape="maneuvering ballistic", thermal=138, radiation=20, rcs=7, speed=620, alt=76000, vz=-620, plume=0.99),
    "TOMAHAWK": dict(label="Tomahawk-style cruise missile", country="United States-style public profile", size=5.6, shape="low-observable cruise", thermal=92, radiation=6, rcs=4, speed=245, alt=2200, vz=-1, plume=0.72),
    "KALIBR": dict(label="Kalibr-style cruise missile", country="Russia-style public profile", size=6.2, shape="sea-launched cruise", thermal=95, radiation=6.5, rcs=4.5, speed=250, alt=2400, vz=-1, plume=0.74),
    "HYPER": dict(label="Hypersonic-glide style profile", country="generic public hypersonic profile", size=6.2, shape="glide body", thermal=160, radiation=26, rcs=6, speed=880, alt=62000, vz=-180, plume=0.86),
}

SPACE_PROFILES = {
    "ISS": dict(label="ISS-like orbital object", size=110, shape="large station", thermal=10, radiation=0, rcs=34, speed=260, alt=410000),
    "DEBRIS": dict(label="catalog debris fragment", size=3.5, shape="fragment", thermal=2, radiation=0, rcs=2, speed=190, alt=720000),
    "NEO": dict(label="near-Earth object profile", size=70, shape="irregular rocky body", thermal=55, radiation=34, rcs=17, speed=120, alt=850000),
}


def default_zone() -> Zone:
    return Zone(x=0.0, y=0.0, radius=120.0, name="Protected Asset")


def _toward(x: float, y: float, speed: float, jitter: float = 0.0) -> tuple[float, float]:
    dx, dy = -x, -y
    mag = math.hypot(dx, dy) or 1.0
    ux, uy = dx / mag, dy / mag
    if jitter:
        ux += random.uniform(-jitter, jitter)
        uy += random.uniform(-jitter, jitter)
        mag = math.hypot(ux, uy) or 1.0
        ux, uy = ux / mag, uy / mag
    return ux * speed, uy * speed


def _air(id: str, profile: str, x: float, y: float, vx: float | None = None, vy: float | None = None) -> TruthObject:
    p = AIRCRAFT_PROFILES[profile]
    if vx is None or vy is None:
        vx, vy = _toward(x, y, p["speed"], 0.08)
    return TruthObject(id, "aircraft", "simulated", "terrestrial", x, y, p["alt"], vx, vy, 0,
                       p["size"], p["shape"], p["thermal"], p["radiation"], p["rcs"], p["transponder"], p["label"],
                       {"profile_key": profile, "country": p["country"], "profile_label": p["label"]})


def _missile(id: str, profile: str, x: float, y: float) -> TruthObject:
    p = MISSILE_PROFILES[profile]
    vx, vy = _toward(x, y, p["speed"], 0.02)
    return TruthObject(id, "missile", "simulated", "terrestrial", x, y, p["alt"], vx, vy, p["vz"],
                       p["size"], p["shape"], p["thermal"], p["radiation"], p["rcs"], False, p["label"],
                       {"profile_key": profile, "country": p["country"], "profile_label": p["label"], "plume": p["plume"]})


def make_truth(env: EnvironmentState) -> list[TruthObject]:
    s = env.scenario
    if s == "mixed_airspace":
        return [
            _air("A1", "B737", -760, -360, 138, 26),
            _air("F2", "F16", 740, 360, -190, -52),
            TruthObject("D7", "drone", "simulated", "terrestrial", 470, -380, 650, -52, 48, 0, 3.2, "quad rotor", 28, 0.1, 4, False, "Small UAS", {"profile_label": "small quadrotor"}),
            TruthObject("U3", "unknown", "simulated", "unknown", -380, 620, 2800, 62, -112, -3, 7, "unresolved", 40, 2.4, 10, False, "Unidentified track", {"profile_label": "unresolved aerial"}),
        ]
    if s == "storm_intrusion":
        return [
            _air("WX1", "C130", -980, -520, 128, 70),
            TruthObject("JAM1", "drone", "simulated", "terrestrial", 690, 280, 420, -82, -45, 0, 3.0, "quad rotor", 38, 0.1, 5, False, "Jamming drone", {"profile_label": "electronic support drone"}),
            TruthObject("UNK2", "unknown", "simulated", "unknown", -720, 760, 2100, 88, -150, -6, 9, "uncertain", 48, 5.5, 12, False, "Low-confidence intruder", {"profile_label": "storm-obscured intruder"}),
            _missile("CM1", "TOMAHAWK", -2600, 900),
        ]
    if s == "drone_swarm":
        base = []
        for i in range(10):
            ang = math.radians(36 * i)
            x, y = 760*math.cos(ang), 760*math.sin(ang)
            vx, vy = _toward(x, y, 72, 0.015)
            base.append(TruthObject(f"SW{i+1}", "drone", "simulated", "terrestrial", x, y, 240 + 25*(i%3), vx, vy, 0, 2.7, "quad rotor", 26, 0.1, 3, False, "Swarm drone", {"profile_label": "coordinated quadrotor"}))
        base.append(_air("AUX1", "C130", -1080, 610, 120, -45))
        return base
    if s == "ballistic_approach":
        return [
            _missile("BM1", "SCUD", -3600, 1250),
            _missile("BM2", "ISKANDER", 3300, -980),
            _missile("CR1", "TOMAHAWK", -2800, -680),
            _air("CIV1", "B737", 1100, 760, -105, -70),
        ]
    if s == "orbital_pass":
        p = SPACE_PROFILES["ISS"]
        q = SPACE_PROFILES["DEBRIS"]
        return [
            TruthObject("SAT1", "satellite", "celestrak", "orbital_earth_origin", -1300, -720, p["alt"], 270, 160, 0, p["size"], p["shape"], p["thermal"], p["radiation"], p["rcs"], False, "ISS-like orbital object", {"norad_id": "25544", "profile_key": "ISS", "profile_label": p["label"]}),
            TruthObject("SAT2", "satellite", "celestrak", "orbital_earth_origin", -900, -420, 420000, 250, 150, 0, 13, "satellite bus", 10, 0.0, 6, False, "Small satellite", {"profile_label": "small satellite bus"}),
            TruthObject("DEB1", "debris", "celestrak", "orbital_earth_origin", 1040, 620, q["alt"], -220, -150, 0, q["size"], q["shape"], q["thermal"], q["radiation"], q["rcs"], False, "Orbital debris", {"profile_key": "DEBRIS", "profile_label": q["label"]}),
        ]
    if s == "asteroid_pass":
        p = SPACE_PROFILES["NEO"]
        vx, vy = _toward(-3400, -2600, 125, 0.01)
        return [
            TruthObject("NEO1", "asteroid", "nasa_jpl", "extraterrestrial", -3400, -2600, p["alt"], vx, vy, -65, p["size"], p["shape"], p["thermal"], p["radiation"], p["rcs"], False, "Near-Earth object", {"profile_key": "NEO", "profile_label": p["label"]}),
            TruthObject("X1", "foreign_spaceship", "simulated", "extraterrestrial", -1900, 1380, 26000, 146, -105, -8, 18, "lenticular craft", 96, 16, 15, False, "Foreign craft", {"profile_label": "anomalous craft prior"}),
        ]
    if s == "layered_defense_drill":
        return [
            _air("CIV1", "A320", -980, -260, 145, 18),
            _air("PAT1", "F16", 860, 520, -220, -76),
            _missile("LOW1", "KALIBR", -3100, 420),
            TruthObject("UAS1", "drone", "simulated", "terrestrial", 680, -520, 520, -68, 52, 0, 3.4, "fixed-wing UAS", 36, 0.1, 4.2, False, "Unidentified low UAS", {"profile_label": "low-altitude UAS"}),
            TruthObject("UNK1", "unknown", "simulated", "unknown", -480, 760, 1800, 54, -98, -2, 6.5, "uncertain", 44, 1.2, 9, False, "Uncorrelated radar contact", {"profile_label": "unresolved radar contact"}),
        ]
    if s == "false_alarm_filter":
        return [
            _air("MED1", "C130", -720, 300, 112, -20),
            _air("CIV2", "B737", 980, -320, -132, 38),
            TruthObject("BAL1", "unknown", "simulated", "terrestrial", 520, 640, 4200, -46, -72, -1, 12, "weather balloon-like", 18, 0.0, 2.6, False, "Weather balloon lookalike", {"profile_label": "balloon-like reflector"}),
            TruthObject("DR1", "drone", "simulated", "terrestrial", -460, -720, 310, 38, 61, 0, 2.8, "quad rotor", 25, 0.1, 3.2, False, "Survey drone", {"profile_label": "survey drone"}),
        ]
    if s == "live_public_blend":
        return [
            _air("A1", "B737", -760, -180, 126, 30),
            _air("F2", "F16", 1120, 520, -220, -90),
            _missile("MS1", "HYPER", -3200, 1500),
            TruthObject("SAT2", "satellite", "celestrak", "orbital_earth_origin", 1050, -180, 405000, -220, 120, 0, 11, "satellite bus", 8, 0.0, 6, False, "Overhead satellite", {"profile_label": "CelesTrak-style satellite"}),
            TruthObject("NEO1", "asteroid", "nasa_jpl", "extraterrestrial", -2900, -2300, 820000, 72, 82, -60, 62, "irregular rocky body", 50, 34, 18, False, "Near-Earth object", {"profile_key": "NEO", "profile_label": "NASA/JPL NEO-style object"}),
            TruthObject("D7", "drone", "simulated", "terrestrial", 520, -420, 450, -58, 50, 0, 3.2, "quad rotor", 26, 0.1, 4, False, "Unknown drone", {"profile_label": "small UAS"}),
        ]
    return []


def spawn_custom_object(kind: str, idx: int) -> TruthObject:
    far = kind in {"missile", "asteroid", "satellite", "debris", "foreign_spaceship"}
    radius = random.uniform(2200, 3600) if far else random.uniform(780, 1200)
    ang = random.uniform(0, 2*math.pi)
    x, y = radius * math.cos(ang), radius * math.sin(ang)

    if kind == "missile":
        obj = _missile(f"MS{idx}", random.choice(list(MISSILE_PROFILES)), x, y)
        obj.label = f"User {obj.label}"
        return obj
    if kind == "aircraft":
        obj = _air(f"AC{idx}", random.choice(list(AIRCRAFT_PROFILES)), x, y)
        obj.label = f"User {obj.label}"
        return obj

    speed_by = {"drone": 72, "satellite": 245, "debris": 185, "asteroid": 120, "foreign_spaceship": 175}
    vx, vy = _toward(x, y, speed_by.get(kind, 70), 0.025)
    configs = {
        "drone": dict(prefix="DR", class_type="drone", source_type="simulated", origin_type="terrestrial", z=600, vz=0, size_m=3.5, shape_class="quad rotor", thermal=30, radiation=0.1, rcs=4, transponder=False, label="User drone", extra={"profile_label":"small UAS"}),
        "satellite": dict(prefix="SAT", class_type="satellite", source_type="celestrak", origin_type="orbital_earth_origin", z=410000, vz=0, size_m=12, shape_class="satellite bus", thermal=10, radiation=0.0, rcs=6, transponder=False, label="User satellite", extra={"profile_label":"small satellite bus"}),
        "debris": dict(prefix="DEB", class_type="debris", source_type="celestrak", origin_type="orbital_earth_origin", z=780000, vz=0, size_m=5.2, shape_class="fragment", thermal=4, radiation=0.0, rcs=2, transponder=False, label="User debris", extra={"profile_label":"debris fragment"}),
        "asteroid": dict(prefix="NEO", class_type="asteroid", source_type="nasa_jpl", origin_type="extraterrestrial", z=850000, vz=-55, size_m=58, shape_class="irregular rocky body", thermal=52, radiation=34, rcs=16, transponder=False, label="User asteroid", extra={"profile_key":"NEO", "profile_label":"near-Earth object profile"}),
        "foreign_spaceship": dict(prefix="X", class_type="foreign_spaceship", source_type="simulated", origin_type="extraterrestrial", z=26000, vz=-8, size_m=18, shape_class="lenticular craft", thermal=96, radiation=16, rcs=15, transponder=False, label="Foreign spaceship", extra={"profile_label":"anomalous craft prior"}),
    }
    cfg = configs.get(kind, configs["drone"])
    return TruthObject(f"{cfg['prefix']}{idx}", cfg["class_type"], cfg["source_type"], cfg["origin_type"], x, y, cfg["z"], vx, vy, cfg["vz"], cfg["size_m"], cfg["shape_class"], cfg["thermal"], cfg["radiation"], cfg["rcs"], cfg["transponder"], cfg["label"], cfg["extra"])
