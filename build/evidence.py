"""Evidence items: schema checks, loading and CSV import. Validators return lists of error strings."""
import csv
import json
from pathlib import Path

from validate import ID_RE, URL_RE, _num, _text

METHODS = ("paleomagnetism", "geochronology", "biostratigraphy", "seismic", "gravity",
           "magnetic", "seismicity", "geodesy", "field-survey")
SOURCE_TYPES = ("peer-reviewed", "government-report", "thesis", "conference", "own-survey")


def load_evidence(path):
    path = Path(path)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def validate_evidence(items, event_ids):
    errors, seen = [], set()
    for i, it in enumerate(items):
        iid = it.get("id", f"#{i}")

        def err(msg):
            errors.append(f"{iid}: {msg}")

        if not isinstance(it.get("id"), str) or not ID_RE.match(it["id"]):
            err("id must be kebab-case")
        elif it["id"] in seen:
            err("duplicate id")
        else:
            seen.add(it["id"])

        ids = it.get("event_ids")
        if not isinstance(ids, list) or not ids:
            err("event_ids must be a non-empty list")
        else:
            for eid in ids:
                if eid not in event_ids:
                    err(f"unknown event id {eid}")

        if it.get("method") not in METHODS:
            err(f"method must be one of {list(METHODS)}")
        if it.get("source_type") not in SOURCE_TYPES:
            err(f"source_type must be one of {list(SOURCE_TYPES)}")
        for key in ("title_th", "title_en", "finding_th", "finding_en"):
            if not _text(it.get(key)):
                err(f"{key} is empty")
        if it.get("value") is not None and not _text(it.get("value")):
            err("value must be null or text")

        c = it.get("citation")
        if not (isinstance(c, dict) and _text(c.get("text"))
                and isinstance(c.get("url"), str) and URL_RE.match(c["url"])):
            err("citation needs text and an http(s) url")

        site = it.get("site")
        if site is not None:
            if not (isinstance(site, dict) and _text(site.get("name_th")) and _text(site.get("name_en"))):
                err("site needs name_th and name_en")
            elif not (_num(site.get("lat")) and -90 <= site["lat"] <= 90
                      and _num(site.get("lon")) and -180 <= site["lon"] <= 180):
                err("site lat/lon out of range")

        pl = it.get("paleolat")
        if pl is not None:
            if it.get("method") != "paleomagnetism":
                err("paleolat is only allowed on paleomagnetism items")
            elif not (isinstance(pl, dict) and _num(pl.get("deg")) and -90 <= pl["deg"] <= 90
                      and _num(pl.get("err")) and pl["err"] >= 0):
                err("paleolat needs deg in [-90, 90] and err >= 0")

        if not isinstance(it.get("verified"), bool):
            err("verified must be true or false")
    return errors
