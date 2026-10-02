"""Geomagnetic polarity segments for the timeline strip: GTS2020 chrons back to C33r, then
superchrons, with 'mixed' filling intervals of frequent or poorly known reversals."""
import json
from pathlib import Path

POLARITIES = ("normal", "reversed", "mixed")
MIXED_NAME = "Frequent reversals / poorly known"

# Older than the GTS2020 C-sequence table. top_ma None = continues from the youngest older boundary.
SUPERCHRONS = [
    {"top_ma": None, "base_ma": 121.4, "polarity": "normal", "name": "Cretaceous Normal Superchron (C34n)",
     "source": "gts2020", "approx": False},
    {"top_ma": 265.0, "base_ma": 318.0, "polarity": "reversed", "name": "Kiaman Reverse Superchron",
     "source": "kiaman", "approx": False},
    {"top_ma": 462.0, "base_ma": 482.0, "polarity": "reversed", "name": "Moyero Reverse Superchron",
     "source": "moyero", "approx": True},
]

SOURCES = {
    "gts2020": {"text": "Ogg 2020, Geomagnetic Polarity Time Scale, Geologic Time Scale 2020 ch. 5 (chron table via PmagPy, Tauxe et al. 2016)",
                "url": "https://doi.org/10.1016/B978-0-12-824360-2.00005-X"},
    "kiaman": {"text": "Opdyke et al. 2000, Base of the Kiaman (318 Ma), GSA Bulletin 112:1315; Isozaki 2009, Illawarra Reversal (~265 Ma), Gondwana Research 15:421",
               "url": "https://doi.org/10.1130/0016-7606(2000)112<1315:BOTKID>2.0.CO;2"},
    "moyero": {"text": "Pavlov & Gallet 2005, A third superchron during the Early Paleozoic, Episodes 28:78–84 (~20 Myr, Lower–Middle Ordovician; boundaries approximate)",
               "url": "https://doi.org/10.18814/epiiugs/2005/v28i2/001"},
}


def build_segments(ts, labels, superchrons, oldest_ma):
    """ts: chron boundaries from 0 Ma (GTS2020 C-sequence); polarity alternates from normal at 0.
    labels: [name, start_ma] pairs; each segment takes the latest label starting at or before it."""
    segs = []
    for i, (top, base) in enumerate(zip(ts, ts[1:])):
        name = [n for n, start in labels if start <= top + 1e-9][-1]
        segs.append({"top_ma": top, "base_ma": base, "polarity": "normal" if i % 2 == 0 else "reversed",
                     "name": name, "source": "gts2020", "approx": False})
    cursor = ts[-1]
    for sc in superchrons:
        top = cursor if sc["top_ma"] is None else sc["top_ma"]
        if top > cursor:
            segs.append({"top_ma": cursor, "base_ma": top, "polarity": "mixed", "name": MIXED_NAME,
                         "source": None, "approx": False})
        segs.append({**sc, "top_ma": top})
        cursor = sc["base_ma"]
    if cursor < oldest_ma:
        segs.append({"top_ma": cursor, "base_ma": oldest_ma, "polarity": "mixed", "name": MIXED_NAME,
                     "source": None, "approx": False})
    return segs


def validate_polarity(segments, oldest_ma):
    errors = []
    if not segments:
        return ["polarity has no segments"]
    if segments[0]["top_ma"] != 0:
        errors.append("polarity must start at 0 Ma")
    for i, s in enumerate(segments):
        if s.get("polarity") not in POLARITIES:
            errors.append(f"segment {i} ({s.get('name')}): polarity must be one of {list(POLARITIES)}")
        if not s["base_ma"] > s["top_ma"]:
            errors.append(f"segment {i} ({s.get('name')}): base_ma must be older than top_ma")
    for i, (a, b) in enumerate(zip(segments, segments[1:])):
        if abs(a["base_ma"] - b["top_ma"]) > 1e-9:
            errors.append(f"gap or overlap between segment {i} and {i + 1} at {a['base_ma']} / {b['top_ma']} Ma")
    if abs(segments[-1]["base_ma"] - oldest_ma) > 1e-9:
        errors.append(f"polarity must end at {oldest_ma:g} Ma (base of the time scale)")
    return errors


def load_polarity(path):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
