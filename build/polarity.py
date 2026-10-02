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
    "gsa_v6": {"text": "Walker & Geissman (compilers) 2022, GSA Geologic Time Scale v6.0 — M-sequence pattern digitized from the chart, then rescaled to ICS v2024/12 (GTS2020) stage-boundary ages, piecewise linear; ages approximate",
               "url": "https://doi.org/10.1130/2022.CTS006C"},
    "moyero": {"text": "Pavlov & Gallet 2005, A third superchron during the Early Paleozoic, Episodes 28:78–84 (~20 Myr, Lower–Middle Ordovician; boundaries approximate)",
               "url": "https://doi.org/10.18814/epiiugs/2005/v28i2/001"},
}


def recalibrate(age, ties):
    """Piecewise-linear map from one time-scale calibration to another through (old, new) tie ages;
    beyond the outermost ties the nearest segment's slope is extended."""
    ties = sorted(ties)
    i = 0
    while i < len(ties) - 2 and age > ties[i + 1][0]:
        i += 1
    (a0, b0), (a1, b1) = ties[i], ties[i + 1]
    return b0 + (age - a0) * (b1 - b0) / (a1 - a0)


def check_digitization(nticks, resid, cns, n_normals, n_labels):
    """Fail loudly when a different chart layout would otherwise give silent garbage."""
    if nticks != 7:
        raise ValueError(f"expected 7 age ticks (100–160 Ma) next to the polarity column, found {nticks}")
    if resid > 0.3:
        raise ValueError(f"age-axis fit residual {resid:.2f} Myr is too large; the tick labels were not read correctly")
    if cns is None or not 118 <= cns <= 128:
        raise ValueError(f"Cretaceous Normal Superchron block not found where expected (got {cns})")
    if n_normals < 20:
        raise ValueError(f"only {n_normals} normal chrons found; the polarity column was not read correctly")
    if n_labels < 1:
        raise ValueError("no M-chron labels found next to the polarity column")


def mseq_from_blocks(cns_base, normals, mixed, labels, base_ma, source="gsa_v6"):
    """Contiguous M-sequence segments from digitized normal blocks and poorly known intervals;
    gaps between them are reversed. A chron label whose age falls inside a segment names it."""
    spans = sorted([(a, b, "normal") for a, b in normals] + [(a, b, "mixed") for a, b in mixed])
    merged = []
    for a, b, kind in spans:
        if merged and merged[-1][2] == kind and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]), kind)
        else:
            merged.append((max(a, merged[-1][1]) if merged else a, b, kind))
    segs, cursor = [], cns_base
    for a, b, kind in merged + [(base_ma, base_ma, None)]:
        if a > cursor:
            segs.append((cursor, a, "reversed"))
        if kind:
            segs.append((a, b, kind))
        cursor = max(cursor, b)

    segs = [(t, b, pol) for t, b, pol in segs if b > t]
    names = ["M-sequence (poorly known)" if pol == "mixed" else "M-sequence" for _, _, pol in segs]
    # Chart labels sit beside the column; give "M12" to the nearest normal segment and "M12r" to the
    # nearest reversed one, so a normal-chron name never lands on a reversed interval.
    for label, age in labels:
        want = "reversed" if label.endswith("r") else "normal"
        cands = [(0 if t <= age < b else min(abs(age - t), abs(age - b)), i)
                 for i, (t, b, pol) in enumerate(segs) if pol == want and names[i] == "M-sequence"]
        if cands:
            names[min(cands)[1]] = f"M-sequence (≈{label})"
    return {"source": source, "segments": [
        {"top_ma": round(t, 3), "base_ma": round(b, 3), "polarity": pol, "name": n, "source": source, "approx": True}
        for (t, b, pol), n in zip(segs, names)]}


def build_segments(ts, labels, superchrons, oldest_ma, mseq=None):
    """ts: chron boundaries from 0 Ma (GTS2020 C-sequence); polarity alternates from normal at 0.
    labels: [name, start_ma] pairs; each segment takes the latest label starting at or before it."""
    segs = []
    for i, (top, base) in enumerate(zip(ts, ts[1:])):
        name = [n for n, start in labels if start <= top + 1e-9][-1]
        segs.append({"top_ma": top, "base_ma": base, "polarity": "normal" if i % 2 == 0 else "reversed",
                     "name": name, "source": "gts2020", "approx": False})
    cursor = ts[-1]
    for sc in superchrons:
        if mseq and sc["name"].startswith("Cretaceous Normal"):
            sc = {**sc, "base_ma": mseq["segments"][0]["top_ma"], "approx": True}
            segs.append({**sc, "top_ma": cursor})
            segs.extend(mseq["segments"])
            cursor = mseq["segments"][-1]["base_ma"]
            continue
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
