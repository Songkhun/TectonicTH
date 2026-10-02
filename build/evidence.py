"""Evidence items: schema checks, loading and CSV import. Validators return lists of error strings."""
import csv
import json
from pathlib import Path

from validate import ID_RE, URL_RE, _num, _text

METHODS = ("paleomagnetism", "geochronology", "biostratigraphy", "seismic", "gravity",
           "magnetic", "electrical", "seismicity", "geodesy", "field-survey")
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
                      and (pl.get("err") is None or (_num(pl["err"]) and pl["err"] >= 0))):
                err("paleolat needs deg in [-90, 90] and err null or >= 0")

        if not isinstance(it.get("verified"), bool):
            err("verified must be true or false")
    return errors


TEMPLATE_COLUMNS = ["id", "event_ids", "method", "title_th", "title_en", "finding_th", "finding_en", "value",
                    "paleolat_deg", "paleolat_err", "site_name_th", "site_name_en", "site_lat", "site_lon",
                    "citation_text", "citation_url", "source_type", "notes"]


def _cell(row, key):
    return (row.get(key) or "").strip()


def rows_to_items(rows):
    """Convert template rows to evidence items. New items are always unverified."""
    items = []
    for row in rows:
        deg, err = _cell(row, "paleolat_deg"), _cell(row, "paleolat_err")
        lat, lon = _cell(row, "site_lat"), _cell(row, "site_lon")
        items.append({
            "id": _cell(row, "id"),
            "event_ids": [s.strip() for s in _cell(row, "event_ids").split(";") if s.strip()],
            "method": _cell(row, "method"),
            "title_th": _cell(row, "title_th"), "title_en": _cell(row, "title_en"),
            "finding_th": _cell(row, "finding_th"), "finding_en": _cell(row, "finding_en"),
            "value": _cell(row, "value") or None,
            "paleolat": {"deg": float(deg), "err": float(err or 0)} if deg else None,
            "site": ({"name_th": _cell(row, "site_name_th"), "name_en": _cell(row, "site_name_en"),
                      "lat": float(lat), "lon": float(lon)} if lat and lon else None),
            "citation": {"text": _cell(row, "citation_text"), "url": _cell(row, "citation_url")},
            "source_type": _cell(row, "source_type") or "own-survey",
            "verified": False,
            "_notes": _cell(row, "notes"),
        })
    return items


def import_rows(csv_path, evidence_path, event_ids):
    """Append CSV rows to evidence.json. Returns errors; nothing is written unless all rows are valid."""
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as f:
        new = rows_to_items(list(csv.DictReader(f)))
    existing = load_evidence(evidence_path)
    errors = validate_evidence(existing + new, event_ids)
    if errors:
        return errors
    Path(evidence_path).write_text(json.dumps(existing + new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return []
