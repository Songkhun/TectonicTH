"""Tectonic-model questions and schematic sutures: schema checks and loading."""
import json
from pathlib import Path

from validate import ID_RE, URL_RE, _num, _text

ROLES = ("supports", "challenges", "neutral")


def load_json_or(path, default):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _cite_ok(c):
    return isinstance(c, dict) and _text(c.get("text")) and isinstance(c.get("url"), str) and URL_RE.match(c["url"])


def _range_ok(base, top):
    return _num(base) and _num(top) and base >= top >= 0


def validate_models(questions, evidence_ids, event_ids):
    errors, seen = [], set()
    for i, qn in enumerate(questions):
        if not isinstance(qn, dict):
            errors.append(f"#{i}: question must be an object")
            continue
        qid = qn.get("id", f"#{i}")

        def err(msg):
            errors.append(f"{qid}: {msg}")

        if not isinstance(qn.get("id"), str) or not ID_RE.match(qn["id"]):
            err("id must be kebab-case")
        elif qn["id"] in seen:
            err("duplicate question id")
        else:
            seen.add(qn["id"])
        for key in ("title_th", "title_en", "question_th", "question_en", "synthesis_th", "synthesis_en"):
            if not _text(qn.get(key)):
                err(f"{key} is empty")
        axis = qn.get("axis") or {}
        if not (_range_ok(axis.get("base_ma"), axis.get("top_ma")) and axis["base_ma"] > axis["top_ma"]):
            err("axis needs base_ma older than top_ma")
            axis = None
        for eid in qn.get("event_ids", []):
            if eid not in event_ids:
                err(f"unknown event id {eid}")
        models = qn.get("models") or []
        if len(models) < 2:
            err("needs at least 2 models to compare")
        mids = []
        for m in models:
            mid = m.get("id")
            if not isinstance(mid, str) or not ID_RE.match(mid):
                err("model id must be kebab-case")
            elif mid in mids:
                err(f"duplicate model id {mid}")
            mids.append(mid)
            for key in ("name_th", "name_en", "summary_th", "summary_en"):
                if not _text(m.get(key)):
                    err(f"model {mid}: {key} is empty")
            if not _cite_ok(m.get("citation")):
                err(f"model {mid}: citation needs text and an http(s) url")
            phases = m.get("phases") or []
            if not phases:
                err(f"model {mid}: needs at least one phase")
            for ph in phases:
                if not (_range_ok(ph.get("base_ma"), ph.get("top_ma")) and _text(ph.get("label_en")) and _text(ph.get("label_th"))):
                    err(f"model {mid}: phase needs labels and base_ma >= top_ma")
                elif axis and not (axis["base_ma"] >= ph["base_ma"] and ph["top_ma"] >= axis["top_ma"]):
                    err(f"model {mid}: phase {ph['label_en']} must lie inside the axis window")
        for ev in qn.get("evidence") or []:
            eid = ev.get("evidence_id")
            if eid not in evidence_ids:
                err(f"unknown evidence id {eid}")
            if not _range_ok(ev.get("age_base_ma"), ev.get("age_top_ma")):
                err(f"evidence {eid}: evidence age needs age_base_ma >= age_top_ma")
            roles = ev.get("roles") or {}
            if set(roles) != set(mids):
                err(f"evidence {eid}: needs a role for every model ({', '.join(map(str, mids))})")
            if any(r not in ROLES for r in roles.values()):
                err(f"evidence {eid}: roles must be supports|challenges|neutral")
            for key in ("reason_th", "reason_en"):
                if not _text(ev.get(key)):
                    err(f"evidence {eid}: {key} is empty")
        if not isinstance(qn.get("verified"), bool):
            err("verified must be true or false")
    return errors


def validate_sutures(data):
    errors = []
    for s in data.get("sutures", []):
        sid = s.get("id", "?")
        pts = s.get("points") or []
        if len(pts) < 2:
            errors.append(f"{sid}: a suture needs at least 2 points")
        for p in pts:
            if not (_num(p.get("lat")) and -90 <= p["lat"] <= 90 and _num(p.get("lon")) and -180 <= p["lon"] <= 180):
                errors.append(f"{sid}: point {p.get('place')} lat/lon out of range")
        for key in ("id", "name_th", "name_en"):
            if not _text(s.get(key)):
                errors.append(f"{sid}: {key} is empty")
        if s.get("schematic") is not True:
            errors.append(f"{sid}: sutures must be marked schematic")
        if not _cite_ok(s.get("citation")):
            errors.append(f"{sid}: citation needs text and an http(s) url")
        if not isinstance(s.get("verified"), bool):
            errors.append(f"{sid}: verified must be true or false")
    for t in data.get("terranes", []):
        tid = t.get("id", "?")
        if not (_num(t.get("label_lat")) and -90 <= t["label_lat"] <= 90 and _num(t.get("label_lon")) and -180 <= t["label_lon"] <= 180):
            errors.append(f"{tid}: terrane label position out of range")
        for key in ("id", "name_th", "name_en"):
            if not _text(t.get(key)):
                errors.append(f"{tid}: {key} is empty")
        if t.get("schematic") is not True:
            errors.append(f"{tid}: terranes must be marked schematic")
        if not _cite_ok(t.get("citation")):
            errors.append(f"{tid}: citation needs text and an http(s) url")
        if not isinstance(t.get("verified"), bool):
            errors.append(f"{tid}: verified must be true or false")
    return errors
