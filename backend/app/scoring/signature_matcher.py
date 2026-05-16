from __future__ import annotations
import math
from ..models import EstimatedTrack


def _safe_float(v, default):
    try:
        return float(v)
    except Exception:
        return default


def build_profiles(live_cache: dict) -> dict:
    opensky = live_cache.get("opensky") or []
    if opensky:
        avg_vel = sum(_safe_float(r.get("velocity"), 220) or 220 for r in opensky[:8]) / max(1, len(opensky[:8]))
        avg_alt = sum(_safe_float(r.get("altitude"), 10000) or 10000 for r in opensky[:8]) / max(1, len(opensky[:8]))
    else:
        avg_vel, avg_alt = 220.0, 10000.0
    iss = live_cache.get("iss") or {}
    iss_alt = 408000.0
    if iss.get("position_km"):
        x,y,z = iss["position_km"]
        iss_alt = max(380000.0, (x*x+y*y+z*z) ** 0.5 * 1000 - 6371000)
    neo = live_cache.get("neo") or {}
    neo_vel = _safe_float(neo.get("v_rel"), 26000.0)
    return {
        "Boeing 737-style transport": {"family":"aircraft", "country":"civil/commercial", "speed":145, "alt":10500, "thermal":48, "radiation":0.2, "rcs":18, "plume":0.62, "acoustic":72, "size":36, "transponder":1.0, "evidence":"OpenSky aircraft state-vector regime + transport-aircraft priors", "url":"https://openskynetwork.github.io/opensky-api/rest.html"},
        "F-16-style fighter": {"family":"aircraft", "country":"United States / allied", "speed":230, "alt":14500, "thermal":72, "radiation":0.4, "rcs":7, "plume":0.75, "acoustic":88, "size":15, "transponder":0.0, "evidence":"public fighter-aircraft performance/signature prior", "url":"https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104505/f-16-fighting-falcon/"},
        "C-130-style transport": {"family":"aircraft", "country":"military transport", "speed":130, "alt":8000, "thermal":58, "radiation":0.2, "rcs":26, "plume":0.72, "acoustic":83, "size":30, "transponder":1.0, "evidence":"public transport-aircraft prior", "url":"https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104517/c-130-hercules/"},
        "Su-35-style fighter": {"family":"aircraft", "country":"Russia-style public profile", "speed":245, "alt":14800, "thermal":79, "radiation":0.5, "rcs":9, "plume":0.78, "acoustic":90, "size":21, "transponder":0.0, "evidence":"public fighter-aircraft performance/signature prior", "url":"https://en.wikipedia.org/wiki/Sukhoi_Su-35"},
        "Rafale-style fighter": {"family":"aircraft", "country":"France-style public profile", "speed":225, "alt":14200, "thermal":70, "radiation":0.35, "rcs":6.4, "plume":0.74, "acoustic":86, "size":15.3, "transponder":0.0, "evidence":"public fighter-aircraft performance/signature prior", "url":"https://en.wikipedia.org/wiki/Dassault_Rafale"},
        "OpenSky live-aircraft average": {"family":"aircraft", "country":"public live ADS-B sample", "speed":avg_vel, "alt":avg_alt, "thermal":48, "radiation":0.2, "rcs":18, "plume":0.62, "acoustic":72, "size":32, "transponder":1.0, "evidence":"OpenSky live state vectors" if opensky else "fallback OpenSky-style prior", "url":"https://openskynetwork.github.io/opensky-api/rest.html"},
        "small quadrotor UAS": {"family":"drone", "country":"generic small UAS", "speed":70, "alt":600, "thermal":28, "radiation":0.1, "rcs":4.5, "plume":0.25, "acoustic":48, "size":3.5, "transponder":0.0, "evidence":"small-UAS proxy priors", "url":"https://www.faa.gov/uas"},
        "Shahed-136-style one-way UAS": {"family":"drone", "country":"Iran-style public profile", "speed":58, "alt":900, "thermal":42, "radiation":0.1, "rcs":3.5, "plume":0.35, "acoustic":62, "size":3.5, "transponder":0.0, "evidence":"public one-way UAS signature prior", "url":"https://missilethreat.csis.org/"},
        "Scud-style ballistic missile": {"family":"missile", "country":"legacy ballistic profile", "speed":520, "alt":90000, "thermal":125, "radiation":18, "rcs":8, "plume":0.98, "acoustic":96, "size":11, "transponder":0.0, "evidence":"CSIS Missile Threat ballistic-missile profile family", "url":"https://missilethreat.csis.org/missile/"},
        "Iskander-style SRBM": {"family":"missile", "country":"Russia-style public profile", "speed":620, "alt":76000, "thermal":138, "radiation":20, "rcs":7, "plume":0.99, "acoustic":98, "size":7.3, "transponder":0.0, "evidence":"CSIS Missile Threat country/profile family", "url":"https://missilethreat.csis.org/country/russia/"},
        "Tomahawk-style cruise missile": {"family":"missile", "country":"United States-style public profile", "speed":245, "alt":2200, "thermal":92, "radiation":6, "rcs":4, "plume":0.72, "acoustic":86, "size":5.6, "transponder":0.0, "evidence":"CSIS Missile Threat cruise-missile family", "url":"https://missilethreat.csis.org/missile/"},
        "Kalibr-style cruise missile": {"family":"missile", "country":"Russia-style public profile", "speed":250, "alt":2400, "thermal":95, "radiation":6.5, "rcs":4.5, "plume":0.74, "acoustic":87, "size":6.2, "transponder":0.0, "evidence":"CSIS Missile Threat cruise-missile family", "url":"https://missilethreat.csis.org/country/russia/"},
        "hypersonic-glide style profile": {"family":"missile", "country":"generic public hypersonic profile", "speed":880, "alt":62000, "thermal":160, "radiation":26, "rcs":6, "plume":0.86, "acoustic":92, "size":6.2, "transponder":0.0, "evidence":"public hypersonic/glide-vehicle proxy prior", "url":"https://missilethreat.csis.org/"},
        "ISS-like orbital object": {"family":"satellite", "country":"international/orbital", "speed":260, "alt":iss_alt, "thermal":10, "radiation":0.0, "rcs":34, "plume":0.1, "acoustic":0, "size":110, "transponder":0.0, "evidence":"CelesTrak GP/TLE orbital reference" if iss else "fallback orbital prior", "url":"https://celestrak.org/NORAD/elements/"},
        "small satellite bus": {"family":"satellite", "country":"orbital", "speed":250, "alt":420000, "thermal":10, "radiation":0.0, "rcs":6, "plume":0.1, "acoustic":0, "size":12, "transponder":0.0, "evidence":"CelesTrak satellite-bus prior", "url":"https://celestrak.org/NORAD/elements/"},
        "orbital debris fragment": {"family":"debris", "country":"orbital", "speed":185, "alt":max(iss_alt,650000), "thermal":3, "radiation":0.0, "rcs":2, "plume":0.0, "acoustic":0, "size":4, "transponder":0.0, "evidence":"CelesTrak debris/orbital-object prior", "url":"https://celestrak.org/NORAD/elements/"},
        "near-Earth object profile": {"family":"asteroid", "country":"extraterrestrial", "speed":max(120, neo_vel/220.0), "alt":850000, "thermal":52, "radiation":28, "rcs":16, "plume":0.15, "acoustic":6, "size":70, "transponder":0.0, "evidence":"NASA/JPL SBDB close-approach prior" if neo else "fallback NEO prior", "url":"https://ssd-api.jpl.nasa.gov/doc/cad.html"},
        "anomalous craft prior": {"family":"foreign_spaceship", "country":"unknown/non-terrestrial prototype", "speed":170, "alt":26000, "thermal":96, "radiation":16, "rcs":15, "plume":0.62, "acoustic":28, "size":18, "transponder":0.0, "evidence":"prototype anomalous-craft prior", "url":"https://ssd-api.jpl.nasa.gov/doc/cad.html"},
    }


def score_track_against_profiles(track: EstimatedTrack, live_cache: dict) -> dict:
    profiles = build_profiles(live_cache)
    speed = math.hypot(track.vx, track.vy)
    obs = {
        "speed": speed,
        "alt": track.z,
        "thermal": track.sensor.get("thermal", 0),
        "radiation": track.sensor.get("radiation", 0),
        "rcs": track.sensor.get("rcs_est", track.sensor.get("radar_strength", 0) * 20),
        "plume": track.sensor.get("plume_index", 0),
        "acoustic": track.sensor.get("acoustic", 0),
        "size": track.sensor.get("size_est", 0),
        "transponder": 1.0 if track.sensor.get("transponder") else 0.0,
    }
    scored=[]
    for label, prof in profiles.items():
        terms = [
            ("speed", abs(obs["speed"] - prof["speed"]) / max(55.0, prof["speed"] * 0.50)),
            ("altitude", abs(obs["alt"] - prof["alt"]) / max(3500.0, prof["alt"] * 0.42)),
            ("thermal", abs(obs["thermal"] - prof["thermal"]) / max(10.0, prof["thermal"] * 0.45 + 8)),
            ("radiation", abs(obs["radiation"] - prof["radiation"]) / max(2.5, prof["radiation"] * 0.45 + 2)),
            ("rcs", abs(obs["rcs"] - prof["rcs"]) / max(2.0, prof["rcs"] * 0.42 + 1.2)),
            ("plume", abs(obs["plume"] - prof["plume"]) / 0.26),
            ("acoustic", abs(obs["acoustic"] - prof["acoustic"]) / max(12.0, prof["acoustic"] * 0.44 + 10)),
            ("size", abs(obs["size"] - prof["size"]) / max(2.0, prof["size"] * 0.50 + 1.5)),
            ("transponder", abs(obs["transponder"] - prof["transponder"]) / 0.7),
        ]
        # Class-family prior nudges, not hard truth.
        family = prof.get("family")
        family_penalty = 0.0 if family == track.class_type else 0.75 if track.class_type in {"missile", "asteroid", "satellite", "debris", "foreign_spaceship"} else 0.25
        dist = sum(v for _, v in terms) + family_penalty
        confidence = max(0.0, min(0.99, 1.0 - dist / 9.5))
        detail = []
        for name, term in terms:
            key = "alt" if name == "altitude" else name
            detail.append({"name": name, "observed": round(obs[key],3) if isinstance(obs[key],(int,float)) else obs[key], "profile": round(prof[key],3) if isinstance(prof[key],(int,float)) else prof[key], "match": round(max(0.0, 1.0 - min(1.0, term)), 3)})
        scored.append((confidence, label, prof["evidence"], prof.get("url"), detail, family, prof.get("country", "n/a")))
    scored.sort(reverse=True)
    top = scored[0]
    return {
        "label": top[1],
        "family": top[5],
        "country_or_family": top[6],
        "confidence": round(top[0], 3),
        "source_evidence": top[2],
        "source_url": top[3],
        "feature_alignment": top[4],
        "candidates": [{"label": label, "family": family, "country_or_family": country, "confidence": round(conf, 3), "evidence": evidence, "url": url} for conf, label, evidence, url, _detail, family, country in scored[:4]],
    }
