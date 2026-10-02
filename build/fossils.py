"""Index fossils of Thailand: schema checks and loading."""
import json
from pathlib import Path

from validate import ID_RE, URL_RE, _num, _text

GROUPS = ("trilobite", "nautiloid", "graptolite", "conodont", "tentaculitid", "brachiopod", "fusulinid", "coral",
          "ammonoid", "bivalve", "gastropod", "radiolarian", "crinoid", "fish", "reptile", "dinosaur", "mammal",
          "primate", "plant", "other")
PRECISIONS = ("site", "area", "district")
SOURCE_TYPES = ("peer-reviewed", "government-report", "thesis", "conference", "preprint")


def load_fossils(path):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def _optional_text(value):
    return value is None or _text(value)


def validate_fossils(items, oldest_ma):
    errors, seen = [], set()
    for i, f in enumerate(items):
        if not isinstance(f, dict):
            errors.append(f"#{i}: fossil must be an object")
            continue
        fid = f.get("id", f"#{i}")

        def err(msg):
            errors.append(f"{fid}: {msg}")

        if not isinstance(f.get("id"), str) or not ID_RE.match(f["id"]):
            err("id must be kebab-case")
        elif f["id"] in seen:
            err("duplicate id")
        else:
            seen.add(f["id"])
        if not _text(f.get("taxon")):
            err("taxon is empty")
        if f.get("group") not in GROUPS:
            err(f"group must be one of {list(GROUPS)}")
        top, base = f.get("age_top_ma"), f.get("age_base_ma")
        if not (_num(top) and _num(base)):
            err("age_top_ma and age_base_ma must be numbers")
        elif not base > top:
            err("age_base_ma must be older (larger) than age_top_ma")
        elif top < 0 or base > oldest_ma:
            err(f"age range must lie within 0–{oldest_ma:g} Ma")
        if not _text(f.get("stage")):
            err("stage is empty")
        for key in ("formation_en", "formation_th"):
            if not _optional_text(f.get(key)):
                err(f"{key} must be null or text")
        loc = f.get("locality")
        if not isinstance(loc, dict):
            err("locality is required")
        else:
            for key in ("name_en", "name_th", "province_th", "province_en"):
                if not _text(loc.get(key)):
                    err(f"locality {key} is empty (province is required)")
            for key in ("tambon_th", "amphoe_th"):
                if not _optional_text(loc.get(key)):
                    err(f"locality {key} must be null or text")
            if not (_num(loc.get("lat")) and -90 <= loc["lat"] <= 90 and _num(loc.get("lon")) and -180 <= loc["lon"] <= 180):
                err("locality lat/lon out of range")
            if loc.get("precision") not in PRECISIONS:
                err(f"locality precision must be one of {list(PRECISIONS)}")
        for key in ("significance_th", "significance_en"):
            if not _text(f.get(key)):
                err(f"{key} is empty")
        c = f.get("citation")
        if not (isinstance(c, dict) and _text(c.get("text")) and isinstance(c.get("url"), str) and URL_RE.match(c["url"])):
            err("citation needs text and an http(s) url")
        if f.get("source_type") not in SOURCE_TYPES:
            err(f"source_type must be one of {list(SOURCE_TYPES)}")
        if not isinstance(f.get("verified"), bool):
            err("verified must be true or false")
    return errors
