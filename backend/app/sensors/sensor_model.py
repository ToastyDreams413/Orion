from __future__ import annotations
import random
from ..models import EnvironmentState, SensorObservation, TruthObject

WEATHER_VIS = {"clear": 1.0, "rain": 0.82, "fog": 0.58, "storm": 0.48}


def observe(obj: TruthObject, env: EnvironmentState) -> SensorObservation:
    visibility = WEATHER_VIS.get(env.weather, 1.0) * env.visibility
    noise = (1.0 - visibility) * 24 + env.jamming * 46
    dropout = 1 if random.random() < env.jamming * 0.25 else 0
    x = obj.x + random.gauss(0, noise)
    y = obj.y + random.gauss(0, noise)
    z = max(0.0, obj.z + random.gauss(0, noise * 5))
    vx = obj.vx + random.gauss(0, noise * 0.2)
    vy = obj.vy + random.gauss(0, noise * 0.2)
    vz = obj.vz + random.gauss(0, noise * 0.15)
    radar_strength = max(0.05, min(1.0, (obj.rcs / 22.0) * visibility - env.jamming * 0.18 + random.gauss(0, 0.04)))
    thermal = max(0.0, obj.thermal + random.gauss(0, 5 + (1 - visibility) * 10))
    radiation = max(0.0, obj.radiation + random.gauss(0, 1.5 + env.jamming * 2))
    optical = max(0.02, min(1.0, visibility - env.jamming * 0.15 + random.gauss(0, 0.05)))
    signal = max(0.02, min(1.0, 1.0 - env.jamming * 0.55 - (1 - visibility) * 0.15 + random.gauss(0, 0.03)))
    acoustic_base = {"aircraft": 72, "drone": 48, "missile": 96, "satellite": 0, "debris": 0, "asteroid": 8, "foreign_spaceship": 28, "unknown": 35}.get(obj.class_type, 22)
    plume_base = obj.extra.get("plume", {"aircraft": 0.62, "drone": 0.25, "missile": 0.98, "satellite": 0.12, "debris": 0.0, "asteroid": 0.15, "foreign_spaceship": 0.62, "unknown": 0.55}.get(obj.class_type, 0.2))
    magnetic_base = {"satellite": 0.4, "debris": 0.15, "asteroid": 0.7, "missile": 0.55, "foreign_spaceship": 0.62}.get(obj.class_type, 0.25)
    spectral_class = {"aircraft": "hydrocarbon_exhaust", "drone": "electric_rotor", "missile": "rocket_or_turbofan_plume", "satellite": "solar_reflective", "debris": "cold_fragment", "asteroid": "rocky_metallic", "foreign_spaceship": "anomalous_composite", "unknown": "unresolved"}.get(obj.class_type, "unresolved")
    infrared_band = {"aircraft": "mid_ir_exhaust", "drone": "low_ir_electric", "missile": "hot_plume_ir", "satellite": "reflected_solar_ir", "debris": "cold_body", "asteroid": "thermal_rock", "foreign_spaceship": "broadband_anomaly", "unknown": "uncertain"}.get(obj.class_type, "uncertain")
    seeker_base = {"missile": 0.86, "foreign_spaceship": 0.34, "drone": 0.16, "aircraft": 0.08}.get(obj.class_type, 0.02)
    ionization_base = {"missile": 0.38, "asteroid": 0.42, "foreign_spaceship": 0.35, "satellite": 0.14, "debris": 0.10}.get(obj.class_type, 0.03)
    material_reflectivity = {"satellite": 0.78, "debris": 0.55, "aircraft": 0.42, "drone": 0.28, "missile": 0.33, "asteroid": 0.18, "foreign_spaceship": 0.66}.get(obj.class_type, 0.35)
    doppler_quality = max(0.05, min(1.0, radar_strength * signal - env.jamming*0.15 + random.gauss(0, 0.035)))
    return SensorObservation(
        id=obj.id, x=x, y=y, z=z, vx=vx, vy=vy, vz=vz,
        radar_strength=radar_strength, thermal=thermal, radiation=radiation,
        size_est=max(0.5, obj.size_m + random.gauss(0, max(0.4, obj.size_m * 0.07))),
        shape_est=obj.shape_class if optical > 0.55 else "uncertain",
        transponder=obj.transponder, optical_confidence=optical,
        signal_confidence=signal, dropout_count=dropout, jam_estimate=env.jamming,
        rcs_est=max(0.1, obj.rcs + random.gauss(0, max(0.3, obj.rcs * 0.08))),
        acoustic=max(0.0, acoustic_base + random.gauss(0, 8 + (1 - visibility) * 12)),
        plume_index=max(0.0, min(1.0, plume_base + random.gauss(0, 0.08 + env.jamming * 0.05))),
        magnetic=max(0.0, min(1.0, magnetic_base + random.gauss(0, 0.08))),
        spectral_class=spectral_class if optical > 0.45 else "uncertain",
        infrared_band=infrared_band,
        seeker_emissions=max(0.0, min(1.0, seeker_base + random.gauss(0, 0.06))),
        ionization=max(0.0, min(1.0, ionization_base + random.gauss(0, 0.06))),
        doppler_quality=round(doppler_quality, 3),
        material_reflectivity=max(0.0, min(1.0, material_reflectivity + random.gauss(0, 0.05))),
    )
