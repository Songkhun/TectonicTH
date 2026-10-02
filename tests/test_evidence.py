import copy
import json

import pytest

from evidence import load_evidence, validate_evidence

EVENTS = {"ratburi-limestone", "indosinian-collision"}
GOOD = {
    "id": "pmag-ratburi", "event_ids": ["ratburi-limestone"], "method": "paleomagnetism",
    "title_th": "แม่เหล็กบรรพกาล", "title_en": "Paleomagnetic pole", "finding_th": "ผล", "finding_en": "Result",
    "value": "paleolatitude 32 ± 6°S", "paleolat": {"deg": -32, "err": 6},
    "site": {"name_th": "ถ้ำ", "name_en": "Cave", "lat": 14.2, "lon": 99.1},
    "citation": {"text": "Someone 2020", "url": "https://doi.org/10.1/x"},
    "source_type": "peer-reviewed", "verified": False,
}


def item(**changes):
    e = copy.deepcopy(GOOD)
    e.update(changes)
    return e


def test_good_item_passes():
    assert validate_evidence([GOOD], EVENTS) == []


def test_missing_file_is_empty(tmp_path):
    assert load_evidence(tmp_path / "nope.json") == []


def test_load_reads_json(tmp_path):
    p = tmp_path / "e.json"
    p.write_text(json.dumps([GOOD], ensure_ascii=False), encoding="utf-8")
    assert load_evidence(p)[0]["id"] == "pmag-ratburi"


@pytest.mark.parametrize("changes, fragment", [
    ({"id": "Bad Id"}, "kebab-case"),
    ({"event_ids": []}, "event_ids"),
    ({"event_ids": ["renamed-event"]}, "renamed-event"),
    ({"method": "dowsing"}, "method"),
    ({"source_type": "blog"}, "source_type"),
    ({"title_en": ""}, "title_en"),
    ({"finding_th": " "}, "finding_th"),
    ({"citation": None}, "citation"),
    ({"citation": {"text": "x", "url": "javascript:alert(1)"}}, "citation"),
    ({"site": {"name_th": "a", "name_en": "b", "lat": 91, "lon": 0}}, "lat/lon"),
    ({"paleolat": {"deg": -95, "err": 5}}, "paleolat"),
    ({"paleolat": {"deg": -30, "err": -1}}, "paleolat"),
    ({"method": "seismic"}, "paleolat"),
    ({"verified": "no"}, "verified"),
    ({"value": 5}, "value"),
])
def test_bad_items_rejected(changes, fragment):
    errors = validate_evidence([item(**changes)], EVENTS)
    assert any(fragment in e for e in errors), errors


def test_unknown_event_error_names_item_and_id():
    errors = validate_evidence([item(event_ids=["renamed-event"])], EVENTS)
    assert errors == ["pmag-ratburi: unknown event id renamed-event"]


def test_duplicate_id_rejected():
    assert any("duplicate" in e for e in validate_evidence([GOOD, GOOD], EVENTS))


def test_non_paleomag_item_without_paleolat_passes():
    assert validate_evidence([item(id="seis", method="seismic", paleolat=None, value=None, site=None)], EVENTS) == []


import csv as csvmod

from evidence import TEMPLATE_COLUMNS, import_rows, rows_to_items


def test_rows_to_items_handles_blanks_and_lists():
    row = {c: "" for c in TEMPLATE_COLUMNS}
    row.update({"id": "ert-sai-yok-2024", "event_ids": "ratburi-limestone; indosinian-collision",
                "method": "field-survey", "title_th": "ERT ไทรโยค", "title_en": "ERT Sai Yok",
                "finding_th": "พบโพรง", "finding_en": "Cavity found", "citation_text": "Division report 2024",
                "citation_url": "https://example.org/r.pdf", "site_lat": "14.4", "site_lon": "98.85",
                "site_name_th": "ไทรโยค", "site_name_en": "Sai Yok", "notes": "line 3"})
    it = rows_to_items([row])[0]
    assert it["event_ids"] == ["ratburi-limestone", "indosinian-collision"]
    assert it["source_type"] == "own-survey" and it["verified"] is False
    assert it["paleolat"] is None and it["value"] is None
    assert it["site"] == {"name_th": "ไทรโยค", "name_en": "Sai Yok", "lat": 14.4, "lon": 98.85}
    assert it["_notes"] == "line 3"


def test_rows_to_items_reads_paleolat_and_ignores_verified_column():
    row = {c: "" for c in TEMPLATE_COLUMNS}
    row.update({"id": "pm", "event_ids": "ratburi-limestone", "method": "paleomagnetism",
                "paleolat_deg": "-32", "paleolat_err": "6", "source_type": "peer-reviewed"})
    row["verified"] = "yes"
    it = rows_to_items([row])[0]
    assert it["paleolat"] == {"deg": -32.0, "err": 6.0}
    assert it["source_type"] == "peer-reviewed" and it["verified"] is False


def _write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csvmod.DictWriter(f, fieldnames=TEMPLATE_COLUMNS)
        w.writeheader()
        w.writerows(rows)


def test_import_rows_appends_excel_csv(tmp_path):
    ev_path = tmp_path / "evidence.json"
    ev_path.write_text(json.dumps([GOOD], ensure_ascii=False), encoding="utf-8")
    row = {c: "" for c in TEMPLATE_COLUMNS}
    row.update({"id": "ert-1", "event_ids": "ratburi-limestone", "method": "field-survey",
                "title_th": "ก", "title_en": "A", "finding_th": "ข", "finding_en": "B",
                "citation_text": "Report", "citation_url": "https://example.org/x"})
    csv_path = tmp_path / "rows.csv"
    _write_csv(csv_path, [row])
    assert import_rows(csv_path, ev_path, EVENTS) == []
    ids = [it["id"] for it in json.loads(ev_path.read_text(encoding="utf-8"))]
    assert ids == ["pmag-ratburi", "ert-1"]


def test_import_rows_refuses_duplicates_and_invalid_rows_without_writing(tmp_path):
    ev_path = tmp_path / "evidence.json"
    ev_path.write_text(json.dumps([GOOD], ensure_ascii=False), encoding="utf-8")
    row = {c: "" for c in TEMPLATE_COLUMNS}
    row.update({"id": "pmag-ratburi", "event_ids": "nope", "method": "field-survey"})
    csv_path = tmp_path / "rows.csv"
    _write_csv(csv_path, [row])
    errors = import_rows(csv_path, ev_path, EVENTS)
    assert any("duplicate" in e for e in errors) and any("unknown event id nope" in e for e in errors)
    assert len(json.loads(ev_path.read_text(encoding="utf-8"))) == 1


def test_template_file_has_template_columns():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    with (root / "content/evidence_template.csv").open(encoding="utf-8-sig") as f:
        assert next(csvmod.reader(f)) == TEMPLATE_COLUMNS


def test_paleolat_without_stated_error_is_allowed():
    assert validate_evidence([item(paleolat={"deg": -13.0, "err": None})], EVENTS) == []


def test_electrical_method_is_allowed():
    assert validate_evidence([item(id="mt", method="electrical", paleolat=None)], EVENTS) == []
