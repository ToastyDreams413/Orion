from __future__ import annotations
import math
from ..models import EnvironmentState, EstimatedTrack, Zone

NO_FLY_ZONE = (140.0, -40.0, 80.0)
HAZARD_ZONE = (-180.0, 180.0, 110.0)


def _normalize(vx: float, vy: float) -> tuple[float, float]:
    mag = math.hypot(vx, vy) or 1.0
    return vx / mag, vy / mag


def enrich(track: EstimatedTrack, zone: Zone, env: EnvironmentState, tracks: list[EstimatedTrack]) -> None:
    dx, dy = zone.x - track.x, zone.y - track.y
    dist_center = math.hypot(dx, dy)
    dist_to_boundary = max(0.0, dist_center - zone.radius)
    ux, uy = _normalize(track.vx, track.vy)
    tx, ty = _normalize(dx, dy)
    directness = max(0.0, min(1.0, ux * tx + uy * ty))
    speed = math.hypot(track.vx, track.vy)
    closing = max(0.0, speed * directness)
    ttz = dist_to_boundary / closing if dist_to_boundary > 0.0 and closing > 0.1 else 0.0
    # closest approach of line P + v*t to the zone center, using only future time.
    v2 = max(1e-6, track.vx*track.vx + track.vy*track.vy)
    t_star = max(0.0, -((track.x-zone.x)*track.vx + (track.y-zone.y)*track.vy) / v2)
    closest_x = track.x + track.vx * t_star
    closest_y = track.y + track.vy * t_star
    cpa_center = math.hypot(closest_x - zone.x, closest_y - zone.y)
    cpa_boundary = max(0.0, cpa_center - zone.radius)
    no_fly = math.hypot(track.x - NO_FLY_ZONE[0], track.y - NO_FLY_ZONE[1]) < NO_FLY_ZONE[2]
    hazard = math.hypot(track.x - HAZARD_ZONE[0], track.y - HAZARD_ZONE[1]) < HAZARD_ZONE[2]

    cluster = 0
    heading = math.atan2(track.vy, track.vx)
    for other in tracks:
        if other.id == track.id:
            continue
        other_heading = math.atan2(other.vy, other.vx)
        angle_delta = abs((heading - other_heading + math.pi) % (2*math.pi) - math.pi)
        if math.hypot(track.x - other.x, track.y - other.y) < 170 and angle_delta < 0.45:
            cluster += 1
    swarm = min(1.0, cluster / 4.0)

    px, py = track.x, track.y
    pred = []
    enters_zone = False
    for _ in range(18):
        px += track.vx * 3.0
        py += track.vy * 3.0
        pred.append((px, py))
        if math.hypot(px - zone.x, py - zone.y) <= zone.radius:
            enters_zone = True
    kinetic_proxy = (track.sensor.get("size_est", 1.0) ** 0.55) * (math.hypot(track.vx, track.vy, track.vz) ** 2) / 100000.0
    impact_probability = 0.0
    if directness > 0.55:
        impact_probability += directness * 0.35
    if cpa_boundary < zone.radius * 0.35:
        impact_probability += 0.30
    if enters_zone or ttz < 180:
        impact_probability += 0.25
    if track.class_type in {"missile", "asteroid", "foreign_spaceship"}:
        impact_probability += 0.16
    impact_probability = max(0.0, min(1.0, impact_probability))

    track.predicted_path = pred
    track.directness = round(directness, 3)
    track.ttz = round(ttz, 1)
    track.cpa = round(cpa_boundary, 1)
    track.swarm_likelihood = round(swarm, 3)
    track.no_fly_intrusion = no_fly
    track.hazard_nearby = hazard
    track.sensor["distance_to_zone"] = round(dist_to_boundary, 1)
    track.sensor["closing_speed"] = round(closing, 2)
    track.sensor["impact_probability"] = round(impact_probability, 3)
    track.sensor["kinetic_energy_proxy"] = round(kinetic_proxy, 3)
    track.sensor["predicted_zone_intersection"] = enters_zone
