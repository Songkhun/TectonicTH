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
    items, errs = rows_to_items([row])
    assert errs == []
    it = items[0]
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
    items, errs = rows_to_items([row])
    assert errs == []
    it = items[0]
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


def test_preprint_source_type_is_allowed():
    assert validate_evidence([item(source_type="preprint")], EVENTS) == []


def test_model_paleolat_is_validated():
    ok = {"deg": -35.6, "age_ma": 270, "model": "TorsvikCocks2017"}
    assert validate_evidence([item(model_paleolat=ok)], EVENTS) == []
    assert any("model_paleolat" in e for e in validate_evidence([item(model_paleolat={**ok, "deg": 99})], EVENTS))
    assert any("model_paleolat" in e for e in validate_evidence([item(model_paleolat=ok, site=None)], EVENTS))


class _Resp:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class _Session:
    def __init__(self):
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append(params)
        return _Resp({"type": "MultiPoint", "coordinates": [[88.0, -36.42]]})


def test_add_model_paleolat_queries_site_at_event_age():
    from evidence import add_model_paleolat
    items = [item(), item(id="nosite", site=None), item(id="seis", method="seismic", paleolat=None)]
    session = _Session()
    out = add_model_paleolat(items, {"ratburi-limestone": 270.0}, session)
    assert out[0]["model_paleolat"] == {"deg": -36.42, "age_ma": 270.0, "model": "TorsvikCocks2017"}
    assert session.calls == [{"points": "99.1,14.2", "time": 270.0, "model": "TorsvikCocks2017"}]
    assert "model_paleolat" not in out[1] and "model_paleolat" not in out[2]


def _row(**kw):
    row = {c: "" for c in TEMPLATE_COLUMNS}
    row.update({"id": "ert-1", "event_ids": "ratburi-limestone", "method": "field-survey", "title_th": "ก",
                "title_en": "A", "finding_th": "ข", "finding_en": "B", "citation_text": "Report",
                "citation_url": "https://example.org/x"})
    row.update(kw)
    return row


def test_bad_numbers_are_reported_not_crashing(tmp_path):
    ev_path = tmp_path / "evidence.json"
    csv_path = tmp_path / "rows.csv"
    _write_csv(csv_path, [_row(site_lat="14,4", site_lon="98.85", site_name_th="ก", site_name_en="A")])
    errors = import_rows(csv_path, ev_path, EVENTS)
    assert errors == ["row 2 (ert-1): site_lat must be a number, got '14,4'"]
    assert not ev_path.exists()


def test_blank_paleolat_error_is_null_not_zero():
    items, errs = rows_to_items([_row(method="paleomagnetism", paleolat_deg="-32")])
    assert errs == [] and items[0]["paleolat"] == {"deg": -32.0, "err": None}


def test_partial_site_is_an_error():
    _, errs = rows_to_items([_row(site_lat="14.4")])
    assert errs == ["row 2 (ert-1): site needs site_name_th, site_name_en, site_lat and site_lon together"]


def test_non_utf8_csv_gives_a_clear_message(tmp_path):
    csv_path = tmp_path / "rows.csv"
    csv_path.write_bytes(",".join(TEMPLATE_COLUMNS).encode() + b"\n" + "ert-1,ratburi-limestone,field-survey,ไทย".encode("cp874") + b"\n")
    errors = import_rows(csv_path, tmp_path / "evidence.json", EVENTS)
    assert len(errors) == 1 and "CSV UTF-8" in errors[0]


def test_example_rows_are_refused():
    _, errs = rows_to_items([_row(id="example-ert-sai-yok")])
    assert errs == ["row 2 (example-ert-sai-yok): this is the template's example row; delete it or give it a real id"]


def test_stale_model_paleolat_is_reported():
    mp = {"deg": -35.6, "age_ma": 270, "model": "TorsvikCocks2017"}
    errors = validate_evidence([item(model_paleolat=mp)], EVENTS, {"ratburi-limestone": 260.5})
    assert errors == ["pmag-ratburi: model_paleolat was computed for 270 Ma but ratburi-limestone is now 260.5 Ma; "
                      "run python3 build/model_paleolat.py"]
    assert validate_evidence([item(model_paleolat=mp)], EVENTS, {"ratburi-limestone": 270}) == []


def test_unplaceable_site_removes_old_model_value():
    from evidence import add_model_paleolat

    class S(_Session):
        def get(self, url, params=None, timeout=None):
            return _Resp({"type": "MultiPoint", "coordinates": [[999.99, 999.99]]})

    old = item(model_paleolat={"deg": -35.6, "age_ma": 200, "model": "TorsvikCocks2017"})
    out = add_model_paleolat([old], {"ratburi-limestone": 270.0}, S())
    assert "model_paleolat" not in out[0]


def test_wrong_types_are_reported_not_crashing():
    errors = validate_evidence(["not an item", item(id="nested", event_ids=[["ratburi-limestone"]])], EVENTS)
    assert any("#0: item must be an object" in e for e in errors)
    assert any("nested: event_ids must be a list of ids" in e for e in errors)


def test_malformed_evidence_file_names_file_and_line(tmp_path):
    from evidence import EvidenceFileError
    p = tmp_path / "evidence.json"
    p.write_text('[\n {"id": "a",\n  oops }\n]', encoding="utf-8")
    with pytest.raises(EvidenceFileError, match=r"evidence\.json line 3"):
        load_evidence(p)


def test_add_model_paleolat_skips_items_whose_event_was_removed():
    from evidence import add_model_paleolat
    out = add_model_paleolat([item(event_ids=["gone"])], {"ratburi-limestone": 270.0}, _Session())
    assert "model_paleolat" not in out[0]
