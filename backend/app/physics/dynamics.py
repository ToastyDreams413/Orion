from __future__ import annotations
import math
from ..models import EnvironmentState, TruthObject

WEATHER_FACTORS = {
    "clear": (0.0, 1.0),
    "rain": (0.1, 0.85),
    "fog": (0.05, 0.65),
    "storm": (0.22, 0.55),
}


def step_truth(obj: TruthObject, dt: float, env: EnvironmentState) -> None:
    wind_bias = env.wind * 18.0
    wx = wind_bias
    wy = wind_bias * 0.35
    if obj.class_type in {"aircraft", "drone", "unknown"}:
        drag = 0.996 if obj.class_type == "aircraft" else 0.992
        turn = 0.0
        if obj.id.startswith("D") or obj.id.startswith("SW"):
            turn = 0.05 if obj.y > 0 else -0.05
        cos_t, sin_t = math.cos(turn), math.sin(turn)
        vx, vy = obj.vx * cos_t - obj.vy * sin_t, obj.vx * sin_t + obj.vy * cos_t
        obj.vx = vx * drag + wx * 0.02
        obj.vy = vy * drag + wy * 0.02
        obj.vz = max(min(obj.vz, 25), -25)
    elif obj.class_type == "missile":
        obj.vz -= 9.8 * dt * 4.0
        obj.vx *= 0.999
        obj.vy *= 0.999
    elif obj.class_type in {"satellite", "debris"}:
        r = math.hypot(obj.x, obj.y) + 1e-6
        tangential_boost = 0.0005 * dt
        obj.vx += -obj.y / r * tangential_boost
        obj.vy += obj.x / r * tangential_boost
    elif obj.class_type == "asteroid":
        r = math.hypot(obj.x, obj.y) + 1e-6
        grav = -0.12 * dt
        obj.vx += grav * obj.x / r
        obj.vy += grav * obj.y / r
        obj.vz += grav * 0.2

    obj.x += (obj.vx + wx * 0.2) * dt
    obj.y += (obj.vy + wy * 0.2) * dt
    obj.z = max(0.0, obj.z + obj.vz * dt)
