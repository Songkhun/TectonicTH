import copy

import pytest

from models import validate_models, validate_sutures

EVID = {"pmag-a", "date-b"}
EVENTS = {"indosinian-collision"}
Q = {
    "id": "paleo-tethys-suture", "title_th": "ก", "title_en": "Suture", "question_th": "ข", "question_en": "Where?",
    "axis": {"base_ma": 300, "top_ma": 190}, "event_ids": ["indosinian-collision"],
    "models": [
        {"id": "inthanon", "name_th": "ก", "name_en": "Inthanon suture", "citation": {"text": "Sone & Metcalfe 2008", "url": "https://doi.org/10.1/x"},
         "summary_th": "ก", "summary_en": "S", "phases": [{"label_th": "ก", "label_en": "Collision", "base_ma": 240, "top_ma": 230}]},
        {"id": "nan", "name_th": "ข", "name_en": "Nan suture", "citation": {"text": "Barr 1991", "url": "https://doi.org/10.2/y"},
         "summary_th": "ข", "summary_en": "T", "phases": [{"label_th": "ข", "label_en": "Closure", "base_ma": 260, "top_ma": 250}]},
    ],
    "evidence": [
        {"evidence_id": "pmag-a", "age_base_ma": 245, "age_top_ma": 235, "roles": {"inthanon": "supports", "nan": "challenges"},
         "reason_th": "ก", "reason_en": "R"},
    ],
    "synthesis_th": "ก", "synthesis_en": "Syn", "verified": False,
}


def q(**changes):
    x = copy.deepcopy(Q)
    x.update(changes)
    return x


def test_good_question_passes():
    assert validate_models([Q], EVID, EVENTS) == []


@pytest.mark.parametrize("mutate, fragment", [
    (lambda x: x.update(id="Bad Id"), "kebab-case"),
    (lambda x: x["models"].pop(), "at least 2 models"),
    (lambda x: x["models"][1].update(id="inthanon"), "duplicate model id"),
    (lambda x: x["models"][0]["phases"][0].update(top_ma=250), "phase"),
    (lambda x: x["models"][0]["phases"][0].update(base_ma=400), "inside the axis"),
    (lambda x: x["models"][0].update(citation={"text": "x", "url": "javascript:1"}), "citation"),
    (lambda x: x["evidence"][0].update(evidence_id="missing"), "unknown evidence id missing"),
    (lambda x: x["evidence"][0]["roles"].pop("nan"), "role for every model"),
    (lambda x: x["evidence"][0]["roles"].update(nan="maybe"), "supports|challenges|neutral"),
    (lambda x: x["evidence"][0].update(age_top_ma=250), "evidence age"),
    (lambda x: x.update(event_ids=["nope"]), "unknown event id nope"),
    (lambda x: x.update(axis={"base_ma": 100, "top_ma": 200}), "axis"),
    (lambda x: x.update(synthesis_en=""), "synthesis_en"),
    (lambda x: x.update(verified="no"), "verified"),
])
def test_bad_questions_rejected(mutate, fragment):
    x = copy.deepcopy(Q)
    mutate(x)
    errors = validate_models([x], EVID, EVENTS)
    assert any(fragment in e for e in errors), errors


SUT = {"sutures": [{"id": "nan-uttaradit", "name_th": "ก", "name_en": "Nan–Uttaradit suture",
                    "points": [{"place": "Nan", "lat": 18.78, "lon": 100.78, "basis": "x"}, {"place": "Uttaradit", "lat": 17.62, "lon": 100.1, "basis": "y"}],
                    "citation": {"text": "Metcalfe 2013", "url": "https://doi.org/10.1/x"}, "schematic": True, "verified": False}],
       "terranes": [{"id": "sibumasu", "name_th": "ซีบูมาสุ", "name_en": "Sibumasu", "label_lat": 15, "label_lon": 99,
                     "citation": {"text": "Metcalfe 2013", "url": "https://doi.org/10.1/x"}, "schematic": True, "verified": False}]}


def test_good_sutures_pass():
    assert validate_sutures(SUT) == []


def test_bad_sutures_rejected():
    bad = copy.deepcopy(SUT)
    bad["sutures"][0]["points"] = bad["sutures"][0]["points"][:1]
    bad["sutures"][0]["schematic"] = False
    bad["terranes"][0]["label_lat"] = 99
    errors = validate_sutures(bad)
    assert any("2 points" in e for e in errors)
    assert any("schematic" in e for e in errors)
    assert any("label" in e for e in errors)
