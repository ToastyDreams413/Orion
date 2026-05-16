from __future__ import annotations
import time, requests
try:
    from sgp4.api import Satrec, jday
except Exception:
    Satrec = None
    jday = None

CACHE: dict[str, tuple[float, object]] = {}
TTL = 300

SOURCE_LINKS = {
    "opensky": "https://opensky-network.org/apidoc/rest.html",
    "celestrak": "https://celestrak.org/NORAD/elements/",
    "jpl_cad": "https://ssd-api.jpl.nasa.gov/doc/cad.html",
}


def _get(url: str):
    now = time.time()
    if url in CACHE and now - CACHE[url][0] < TTL:
        return CACHE[url][1]
    r = requests.get(url, timeout=1.8)
    r.raise_for_status()
    data = r.json()
    CACHE[url] = (now, data)
    return data


def fetch_opensky() -> list[dict]:
    data = _get("https://opensky-network.org/api/states/all")
    states = data.get("states") or []
    out = []
    for row in states[:15]:
        if len(row) < 9 or row[5] is None or row[6] is None:
            continue
        out.append({
            "icao24": row[0], "callsign": (row[1] or '').strip(), "origin_country": row[2],
            "lon": row[5], "lat": row[6], "velocity": row[9], "heading": row[10], "altitude": row[7],
        })
    return out


def fetch_celestrak_iss() -> dict:
    lines = requests.get("https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=TLE", timeout=1.8).text.strip().splitlines()
    if len(lines) < 3:
        raise ValueError("No ISS TLE returned")
    if Satrec is None or jday is None:
        return {"name": lines[0].strip(), "position_km": [], "velocity_km_s": [], "norad_id": "25544", "note": "sgp4 package unavailable; TLE fetched but not propagated"}
    sat = Satrec.twoline2rv(lines[1], lines[2])
    jd, fr = jday(*(time.gmtime()[:6]))
    e, r, v = sat.sgp4(jd, fr)
    if e != 0:
        raise ValueError(f"SGP4 error {e}")
    return {"name": lines[0].strip(), "position_km": r, "velocity_km_s": v, "norad_id": "25544"}


def fetch_neo() -> dict:
    data = _get("https://ssd-api.jpl.nasa.gov/cad.api?date-min=now&date-max=+7&dist-max=0.1")
    fields = data.get("fields", [])
    rows = data.get("data", [])
    if not rows:
        return {}
    first = dict(zip(fields, rows[0]))
    return first
