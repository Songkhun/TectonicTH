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
