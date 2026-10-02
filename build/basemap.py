"""Clip, simplify and round GeoJSON to a lon/lat box (base map and fault traces)."""
from paleo import simplify_line


def _inside(p, box):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


def clip_ring(ring, box):
    """Sutherland–Hodgman clip of a closed ring to the box; None if nothing is left."""
    if all(_inside(p, box) for p in ring):
        return ring
    x0, y0, x1, y1 = box
    edges = [(lambda p: p[0] >= x0, lambda a, b: _at_x(a, b, x0)),
             (lambda p: p[0] <= x1, lambda a, b: _at_x(a, b, x1)),
             (lambda p: p[1] >= y0, lambda a, b: _at_y(a, b, y0)),
             (lambda p: p[1] <= y1, lambda a, b: _at_y(a, b, y1))]
    pts = [list(p) for p in ring[:-1]] if ring[0] == ring[-1] else [list(p) for p in ring]
    for keep, cross in edges:
        out = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if keep(cur):
                if not keep(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif keep(prev):
                out.append(cross(prev, cur))
        pts = out
        if not pts:
            return None
    if len(pts) < 3:
        return None
    return pts + [list(pts[0])]


def _at_x(a, b, x):
    t = (x - a[0]) / (b[0] - a[0])
    return [x, a[1] + t * (b[1] - a[1])]


def _at_y(a, b, y):
    t = (y - a[1]) / (b[1] - a[1])
    return [a[0] + t * (b[0] - a[0]), y]


def _clip_segment(a, b, box):
    """Liang–Barsky: the part of segment a–b inside the box, or None."""
    x0, y0, x1, y1 = box
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0:
                return None
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return None
    start = a if t0 == 0 else [a[0] + t0 * dx, a[1] + t0 * dy]
    end = b if t1 == 1 else [a[0] + t1 * dx, a[1] + t1 * dy]
    return start, end


def clip_line(line, box):
    """Split a polyline into the runs that lie inside the box."""
    parts, cur = [], []
    for a, b in zip(line, line[1:]):
        seg = _clip_segment(a, b, box)
        if seg is None:
            if cur:
                parts.append(cur)
                cur = []
            continue
        start, end = seg
        if not cur:
            cur = [start]
        elif cur[-1] != start:
            parts.append(cur)
            cur = [start]
        cur.append(end)
        if end is not b:
            parts.append(cur)
            cur = []
    if cur:
        parts.append(cur)
    return [p for p in parts if len(p) >= 2]


def _tidy(points, tol, ndigits):
    pts = simplify_line([(p[0], p[1]) for p in points], tol) if tol else [(p[0], p[1]) for p in points]
    out = []
    for x, y in pts:
        q = [round(x, ndigits), round(y, ndigits)]
        if not out or out[-1] != q:
            out.append(q)
    return out


def clip_features(fc, box, tol=0.02, ndigits=3, keep=()):
    features = []
    for f in fc.get("features", []):
        g = f.get("geometry") or {}
        props = {k: f.get("properties", {}).get(k) for k in keep}
        if g.get("type") in ("LineString", "MultiLineString"):
            lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
            parts = [_tidy(p, tol, ndigits) for line in lines for p in clip_line(line, box)]
            parts = [p for p in parts if len(p) >= 2]
            if parts:
                features.append({"type": "Feature", "properties": props,
                                 "geometry": {"type": "MultiLineString", "coordinates": parts}})
        elif g.get("type") in ("Polygon", "MultiPolygon"):
            polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            out = []
            for poly in polys:
                outer = clip_ring(poly[0], box)
                if outer is None:
                    continue
                outer = _tidy(outer, tol, ndigits)
                if len(outer) < 4:
                    continue
                holes = [_tidy(h, tol, ndigits) for h in (clip_ring(r, box) for r in poly[1:]) if h]
                out.append([outer] + [h for h in holes if len(h) >= 4])
            if out:
                geom = {"type": "Polygon", "coordinates": out[0]} if len(out) == 1 else {"type": "MultiPolygon", "coordinates": out}
                features.append({"type": "Feature", "properties": props, "geometry": geom})
    return {"type": "FeatureCollection", "features": features}
