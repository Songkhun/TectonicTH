import copy
import json
from pathlib import Path

import pytest

from validate import validate_events, validate_timescale

ROOT = Path(__file__).resolve().parent.parent
PERIODS = json.loads((ROOT / "content/timescale.json").read_text(encoding="utf-8"))

GOOD = {
    "id": "ratburi-limestone", "lane": "local", "age_ma": 270, "age_uncertainty_ma": 15,
    "title_th": "หินปูน", "title_en": "Limestone", "body_th": "ข้อความ", "body_en": "Text",
    "rock_unit": None, "visit_site": {"name_th": "ถ้ำ", "name_en": "Cave", "lat": 14.2, "lon": 99.1},
    "citation": {"text": "Ridd 2011", "url": "https://doi.org/10.1144/GOTH"},
    "paleo_age": 270, "lecture_stop": False, "verified": False,
}
LIFE = {
    "id": "first-dinosaurs", "lane": "life", "age_ma": 233, "age_uncertainty_ma": None,
    "title_th": "ไดโนเสาร์", "title_en": "Dinosaurs", "body_th": "", "body_en": "", "icon": "🦕",
    "rock_unit": None, "visit_site": None, "citation": None,
    "paleo_age": 230, "lecture_stop": False, "verified": False,
}


def ev(**changes):
    e = copy.deepcopy(GOOD)
    e.update(changes)
    return e


def test_real_timescale_is_valid():
    assert validate_timescale(PERIODS) == []


def test_timescale_gap_detected():
    broken = copy.deepcopy(PERIODS)
    broken[1]["start_ma"] = 440.0
    assert any("gap or overlap" in e for e in validate_timescale(broken))


def test_timescale_must_end_at_zero():
    broken = copy.deepcopy(PERIODS)
    broken[-1]["end_ma"] = 0.01
    assert any("end at 0" in e for e in validate_timescale(broken))


def test_good_events_pass():
    assert validate_events([GOOD, LIFE], PERIODS, {270, 230}) == []


def test_real_starter_content_is_valid():
    events = json.loads((ROOT / "content/events.json").read_text(encoding="utf-8"))
    assert validate_events(events, PERIODS) == []


@pytest.mark.parametrize("changes, fragment", [
    ({"id": "Bad Id"}, "kebab-case"),
    ({"lane": "ocean"}, "lane"),
    ({"age_ma": -1}, "age_ma"),
    ({"age_ma": 600}, "age_ma"),
    ({"age_uncertainty_ma": -2}, "age_uncertainty_ma"),
    ({"title_th": " "}, "title_th"),
    ({"body_en": ""}, "body_en"),
    ({"citation": None}, "citation"),
    ({"citation": {"text": "x", "url": "javascript:alert(1)"}}, "citation"),
    ({"visit_site": {"name_th": "a", "name_en": "b", "lat": 95, "lon": 0}}, "lat/lon"),
    ({"paleo_age": "270"}, "paleo_age"),
    ({"verified": "no"}, "verified"),
    ({"rock_unit": 5}, "rock_unit"),
])
def test_bad_fields_rejected(changes, fragment):
    errors = validate_events([ev(**changes)], PERIODS)
    assert any(fragment in e for e in errors), errors


def test_duplicate_id_rejected():
    assert any("duplicate" in e for e in validate_events([GOOD, GOOD], PERIODS))


def test_life_event_needs_icon():
    life = copy.deepcopy(LIFE)
    life["icon"] = ""
    assert any("icon" in e for e in validate_events([life], PERIODS))


def test_missing_slice_rejected():
    errors = validate_events([GOOD], PERIODS, {250})
    assert any("no paleo slice" in e for e in errors)


def test_age_zero_is_allowed():
    assert validate_events([ev(age_ma=0, paleo_age=0)], PERIODS, {0}) == []
