"""Schema checks for Deep Time content. Each function returns a list of error strings."""
import json
import re
from pathlib import Path

LANES = {"local", "world", "life"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
URL_RE = re.compile(r"^https?://\S+$")
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _text(x):
    return isinstance(x, str) and x.strip() != ""


def validate_timescale(periods):
    if not periods:
        return ["timescale is empty"]
    errors, ids = [], set()
    for p in periods:
        pid = p.get("id", "?")
        for key in ("id", "name_th", "name_en", "color"):
            if not _text(p.get(key)):
                errors.append(f"period {pid}: missing {key}")
        if _text(p.get("color")) and not HEX_RE.match(p["color"]):
            errors.append(f"period {pid}: color must be #RRGGBB")
        if not (_num(p.get("start_ma")) and _num(p.get("end_ma")) and p["start_ma"] > p["end_ma"] >= 0):
            errors.append(f"period {pid}: start_ma must be > end_ma >= 0")
        if pid in ids:
            errors.append(f"period {pid}: duplicate id")
        ids.add(pid)
    ordered = sorted(
        (p for p in periods if _num(p.get("start_ma")) and _num(p.get("end_ma"))),
        key=lambda p: -p["start_ma"],
    )
    for older, younger in zip(ordered, ordered[1:]):
        if abs(older["end_ma"] - younger["start_ma"]) > 1e-9:
            errors.append(f"gap or overlap between {older['id']} and {younger['id']}")
    if ordered and ordered[-1]["end_ma"] != 0:
        errors.append("youngest period must end at 0 Ma")
    return errors


def validate_events(events, periods, slice_ages=None):
    errors, seen = [], set()
    oldest = max((p["start_ma"] for p in periods), default=541)
    for i, e in enumerate(events):
        eid = e.get("id", f"#{i}")

        def err(msg):
            errors.append(f"{eid}: {msg}")

        if not isinstance(e.get("id"), str) or not ID_RE.match(e["id"]):
            err("id must be kebab-case")
        elif e["id"] in seen:
            err("duplicate id")
        else:
            seen.add(e["id"])

        lane = e.get("lane")
        if lane not in LANES:
            err(f"lane must be one of {sorted(LANES)}")

        age = e.get("age_ma")
        if not _num(age) or age < 0 or age >= oldest:
            err(f"age_ma must be in [0, {oldest})")
        unc = e.get("age_uncertainty_ma")
        if unc is not None and (not _num(unc) or unc < 0):
            err("age_uncertainty_ma must be null or >= 0")

        for key in ("title_th", "title_en"):
            if not _text(e.get(key)):
                err(f"{key} is empty")

        if lane == "life":
            if not _text(e.get("icon")):
                err("life events need an icon")
        else:
            for key in ("body_th", "body_en"):
                if not _text(e.get(key)):
                    err(f"{key} is empty")
            c = e.get("citation")
            if not (isinstance(c, dict) and _text(c.get("text"))
                    and isinstance(c.get("url"), str) and URL_RE.match(c["url"])):
                err("citation needs text and an http(s) url")

        if e.get("rock_unit") is not None and not _text(e.get("rock_unit")):
            err("rock_unit must be null or text")

        site = e.get("visit_site")
        if site is not None:
            if not (isinstance(site, dict) and _text(site.get("name_th")) and _text(site.get("name_en"))):
                err("visit_site needs name_th and name_en")
            elif not (_num(site.get("lat")) and -90 <= site["lat"] <= 90
                      and _num(site.get("lon")) and -180 <= site["lon"] <= 180):
                err("visit_site lat/lon out of range")

        pa = e.get("paleo_age")
        if not _num(pa):
            err("paleo_age must be a number")
        elif slice_ages is not None and pa not in slice_ages:
            err(f"no paleo slice for paleo_age {pa}")

        for key in ("lecture_stop", "verified"):
            if not isinstance(e.get(key), bool):
                err(f"{key} must be true or false")
    return errors
