"""Fetch and simplify paleogeographic slices from the GPlates Web Service."""
import json
import math
import os
import sys
from pathlib import Path

GWS_URL = "https://gws.gplates.org"
MODEL = "TorsvikCocks2017"
KANCHANABURI = (99.53, 14.02)
SLICE_AGES = [470, 430, 400, 360, 320, 290, 270, 250, 230, 200, 150, 100, 66, 40, 20, 5, 0]
MAX_SLICE_BYTES = 100_000
# GPlates returns HTTP 500 for TorsvikCocks2017 coastlines at 0 Ma; present-day coastlines are
# observed geography, so any model gives the same shapes there.
PRESENT_COAST_MODEL = "MULLER2022"


class SliceTooLargeError(Exception):
    pass


class UnplacedPointError(Exception):
    """GPlates returns 999.99 when the model has no plate for the point at that age."""


def _seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def simplify_line(points, tol):
    """Douglas–Peucker in lon/lat degrees. Endpoints are always kept."""
    points = list(points)
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        dmax, idx = 0.0, None
        for i in range(start + 1, end):
            d = _seg_dist(points[i], points[start], points[end])
            if d > dmax:
                dmax, idx = d, i
        if idx is not None and dmax > tol:
            keep[idx] = True
            stack.extend([(start, idx), (idx, end)])
    return [p for p, k in zip(points, keep) if k]


def _clean_ring(ring, tol, ndigits):
    pts = simplify_line([(p[0], p[1]) for p in ring], tol)
    out = []
    for x, y in pts:
        q = [round(x, ndigits), round(y, ndigits)]
        if not out or out[-1] != q:
            out.append(q)
    if out and out[0] != out[-1]:
        out.append(list(out[0]))
    return out if len(out) >= 4 else None


def simplify_geojson(fc, tol=0.5, ndigits=1):
    features = []
    for f in fc.get("features", []):
        g = f.get("geometry") or {}
        if g.get("type") == "Polygon":
            polys = [g["coordinates"]]
        elif g.get("type") == "MultiPolygon":
            polys = g["coordinates"]
        else:
            continue
        out_polys = []
        for poly in polys:
            if not poly:
                continue
            outer = _clean_ring(poly[0], tol, ndigits)
            if outer is None:
                continue
            holes = [r for r in (_clean_ring(h, tol, ndigits) for h in poly[1:]) if r]
            out_polys.append([outer] + holes)
        if not out_polys:
            continue
        geom = ({"type": "Polygon", "coordinates": out_polys[0]} if len(out_polys) == 1
                else {"type": "MultiPolygon", "coordinates": out_polys})
        features.append({"type": "Feature", "properties": {}, "geometry": geom})
    return {"type": "FeatureCollection", "features": features}


def fetch_slice(age, session, base_url=GWS_URL, model=MODEL, timeout=90, coast_model=None):
    lon, lat = KANCHANABURI
    r = session.get(f"{base_url}/reconstruct/reconstruct_points/",
                    params={"points": f"{lon},{lat}", "time": age, "model": model}, timeout=timeout)
    r.raise_for_status()
    px, py = r.json()["coordinates"][0]
    if abs(px) > 360 or abs(py) > 90:
        raise UnplacedPointError(f"model {model} cannot place Kanchanaburi at {age} Ma (got {px}, {py})")
    r = session.get(f"{base_url}/reconstruct/coastlines/",
                    params={"time": age, "model": coast_model or model}, timeout=timeout)
    r.raise_for_status()
    raw = r.json()
    tol = 0.3
    for _ in range(8):
        sl = {"age": age, "model": model, "kanchanaburi": [round(px, 2), round(py, 2)],
              "coast_model": coast_model or model, "coastlines": simplify_geojson(raw, tol=tol, ndigits=1)}
        if len(json.dumps(sl, separators=(",", ":")).encode("utf-8")) <= MAX_SLICE_BYTES:
            return sl
        tol *= 1.5
    raise SliceTooLargeError(f"slice {age} Ma is still over {MAX_SLICE_BYTES} bytes after simplification")


def write_slice_atomic(path, sl):
    path = Path(path)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(sl, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


def fetch_all(out_dir, session, ages):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for age in ages:
        path = out_dir / f"{age}.json"
        if path.exists():
            print(f"skip {age} Ma (exists)")
            continue
        try:
            sl = fetch_slice(age, session, coast_model=PRESENT_COAST_MODEL if age == 0 else None)
        except Exception as exc:  # noqa: BLE001 — report any failure with its age
            print(f"ERROR: slice {age} Ma failed: {exc}", file=sys.stderr)
            return 1
        write_slice_atomic(path, sl)
        print(f"wrote {age} Ma ({path.stat().st_size // 1024} KB), Kanchanaburi at {sl['kanchanaburi']}")
    return 0


def load_slices(paleo_dir):
    slices = {}
    for p in sorted(Path(paleo_dir).glob("*.json")):
        sl = json.loads(p.read_text(encoding="utf-8"))
        slices[str(sl["age"])] = sl
    return slices


def check_present(slices):
    present = slices.get("0")
    if present is None:
        return "0 Ma slice is missing"
    lon, lat = present["kanchanaburi"]
    if abs(lon - KANCHANABURI[0]) > 0.05 or abs(lat - KANCHANABURI[1]) > 0.05:
        return f"0 Ma Kanchanaburi position {present['kanchanaburi']} != {list(KANCHANABURI)}"
    return None
