"""Evidence items: schema checks, loading and CSV import. Validators return lists of error strings."""
import csv
import json
from pathlib import Path

from validate import ID_RE, URL_RE, _num, _text

METHODS = ("paleomagnetism", "geochronology", "thermochronology", "biostratigraphy", "geochemistry", "mapping", "seismic", "gravity",
           "magnetic", "electrical", "seismicity", "geodesy", "field-survey")
SOURCE_TYPES = ("peer-reviewed", "government-report", "thesis", "conference", "preprint", "own-survey")


class EvidenceFileError(ValueError):
    pass


def load_evidence(path):
    path = Path(path)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceFileError(f"{path.name} line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def validate_evidence(items, event_ids, event_ages=None):
    errors, seen = [], set()
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            errors.append(f"#{i}: item must be an object")
            continue
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
        elif not all(isinstance(x, str) for x in ids):
            err("event_ids must be a list of ids")
            ids = None
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

        mp = it.get("model_paleolat")
        if mp is not None:
            if it.get("method") != "paleomagnetism" or it.get("site") is None:
                err("model_paleolat needs a paleomagnetism item with a site")
            elif not (isinstance(mp, dict) and _num(mp.get("deg")) and -90 <= mp["deg"] <= 90
                      and _num(mp.get("age_ma")) and _text(mp.get("model"))):
                err("model_paleolat needs deg in [-90, 90], age_ma and model")
            elif event_ages is not None and isinstance(ids, list) and ids and ids[0] in event_ages \
                    and mp["age_ma"] != event_ages[ids[0]]:
                err(f"model_paleolat was computed for {mp['age_ma']:g} Ma but {ids[0]} is now "
                    f"{event_ages[ids[0]]:g} Ma; run python3 build/model_paleolat.py")

        if not isinstance(it.get("verified"), bool):
            err("verified must be true or false")
    return errors


TEMPLATE_COLUMNS = ["id", "event_ids", "method", "title_th", "title_en", "finding_th", "finding_en", "value",
                    "paleolat_deg", "paleolat_err", "site_name_th", "site_name_en", "site_lat", "site_lon",
                    "citation_text", "citation_url", "source_type", "notes"]


def _cell(row, key):
    return (row.get(key) or "").strip()


def _number(row, key, label, errors):
    raw = _cell(row, key)
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        errors.append(f"{label}: {key} must be a number, got '{raw}'")
        return None


def rows_to_items(rows):
    """Convert template rows to evidence items (always unverified). Returns (items, errors).
    Row numbers in errors count the header as row 1, as Excel does."""
    items, errors = [], []
    site_keys = ("site_name_th", "site_name_en", "site_lat", "site_lon")
    for n, row in enumerate(rows, start=2):
        label = f"row {n} ({_cell(row, 'id')})"
        if _cell(row, "id").startswith("example-"):
            errors.append(f"{label}: this is the template's example row; delete it or give it a real id")
            continue
        deg = _number(row, "paleolat_deg", label, errors)
        err = _number(row, "paleolat_err", label, errors)
        lat = _number(row, "site_lat", label, errors)
        lon = _number(row, "site_lon", label, errors)
        filled = [bool(_cell(row, k)) for k in site_keys]
        if any(filled) and not all(filled):
            errors.append(f"{label}: site needs site_name_th, site_name_en, site_lat and site_lon together")
        items.append({
            "id": _cell(row, "id"),
            "event_ids": [x.strip() for x in _cell(row, "event_ids").split(";") if x.strip()],
            "method": _cell(row, "method"),
            "title_th": _cell(row, "title_th"), "title_en": _cell(row, "title_en"),
            "finding_th": _cell(row, "finding_th"), "finding_en": _cell(row, "finding_en"),
            "value": _cell(row, "value") or None,
            "paleolat": {"deg": deg, "err": err} if deg is not None else None,
            "site": ({"name_th": _cell(row, "site_name_th"), "name_en": _cell(row, "site_name_en"),
                      "lat": lat, "lon": lon} if all(filled) and lat is not None and lon is not None else None),
            "citation": {"text": _cell(row, "citation_text"), "url": _cell(row, "citation_url")},
            "source_type": _cell(row, "source_type") or "own-survey",
            "verified": False,
            "_notes": _cell(row, "notes"),
        })
    return items, errors


def import_rows(csv_path, evidence_path, event_ids):
    """Append CSV rows to evidence.json. Returns errors; nothing is written unless all rows are valid."""
    try:
        with Path(csv_path).open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except UnicodeDecodeError:
        return [f"{csv_path}: not UTF-8. In Excel use File > Save As > 'CSV UTF-8 (Comma delimited)'"]
    new, errors = rows_to_items(rows)
    if errors:
        return errors
    existing = load_evidence(evidence_path)
    errors = validate_evidence(existing + new, event_ids)
    if errors:
        return errors
    Path(evidence_path).write_text(json.dumps(existing + new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return []


def add_model_paleolat(items, event_ages, session):
    """For paleomagnetism items with a measured paleolatitude and a sampling site, store the plate
    model's latitude of that site at the age of the item's first event (the fair data-vs-model test)."""
    from paleo import GWS_URL, MODEL
    out = []
    for it in items:
        it = dict(it)
        if (it.get("method") == "paleomagnetism" and it.get("paleolat") and it.get("site")
                and it["event_ids"] and it["event_ids"][0] in event_ages):
            age = event_ages[it["event_ids"][0]]
            r = session.get(f"{GWS_URL}/reconstruct/reconstruct_points/",
                            params={"points": f"{it['site']['lon']},{it['site']['lat']}", "time": age, "model": MODEL},
                            timeout=90)
            r.raise_for_status()
            lon, lat = r.json()["coordinates"][0]
            if abs(lat) <= 90:
                it["model_paleolat"] = {"deg": round(lat, 2), "age_ma": age, "model": MODEL}
            else:
                it.pop("model_paleolat", None)
        out.append(it)
    return out
