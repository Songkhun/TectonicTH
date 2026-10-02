import copy

import pytest

from fossils import GROUPS, validate_fossils

GOOD = {
    "id": "fos-sinoceras-thong-pha-phum", "taxon": "Sinoceras chinense", "group": "nautiloid",
    "age_top_ma": 449.0, "age_base_ma": 458.0, "stage": "Late Ordovician (Sandbian)",
    "formation_en": "Pa Kae Formation", "formation_th": "หมวดหินป่าแก่",
    "locality": {"name_en": "Ban Tha Kradan", "name_th": "บ้านท่ากระดาน", "tambon_th": "ท่ากระดาน",
                 "amphoe_th": "ศรีสวัสดิ์", "province_th": "กาญจนบุรี", "province_en": "Kanchanaburi",
                 "lat": 14.6, "lon": 99.1, "precision": "area"},
    "significance_th": "ฟอสซิลดัชนี", "significance_en": "Index fossil",
    "citation": {"text": "Fang et al. 2021", "url": "https://doi.org/10.1/x"},
    "source_type": "peer-reviewed", "verified": False,
}


def fos(**changes):
    f = copy.deepcopy(GOOD)
    f.update(changes)
    return f


def loc(**changes):
    return fos(locality={**GOOD["locality"], **changes})


def test_good_fossil_passes():
    assert validate_fossils([GOOD], 486.85) == []


def test_groups_include_classic_index_fossils():
    for g in ("trilobite", "graptolite", "conodont", "fusulinid", "ammonoid", "dinosaur", "primate"):
        assert g in GROUPS


@pytest.mark.parametrize("f, fragment", [
    (fos(id="Bad"), "kebab-case"),
    (fos(taxon=""), "taxon"),
    (fos(group="unicorn"), "group"),
    (fos(age_top_ma=460), "age_base_ma"),
    (fos(age_base_ma=500), "age range"),
    (fos(age_top_ma=-1), "age range"),
    (fos(stage=""), "stage"),
    (fos(formation_en=5), "formation_en"),
    (loc(province_th=""), "province"),
    (loc(lat=95), "lat/lon"),
    (loc(lon="99"), "lat/lon"),
    (loc(precision="exact"), "precision"),
    (loc(tambon_th=""), "tambon_th"),
    (fos(locality=None), "locality"),
    (fos(significance_en=""), "significance_en"),
    (fos(citation={"text": "x", "url": "ftp://x"}), "citation"),
    (fos(source_type="blog"), "source_type"),
    (fos(verified=1), "verified"),
])
def test_bad_fossils_rejected(f, fragment):
    errors = validate_fossils([f], 486.85)
    assert any(fragment in e for e in errors), errors


def test_unknown_tambon_and_amphoe_may_be_null():
    assert validate_fossils([loc(tambon_th=None, amphoe_th=None, precision="district")], 486.85) == []


def test_duplicate_id_and_non_object_rejected():
    errors = validate_fossils([GOOD, GOOD, "x"], 486.85)
    assert any("duplicate" in e for e in errors) and any("must be an object" in e for e in errors)


def test_amphibian_group_is_allowed():
    assert validate_fossils([fos(group="amphibian")], 486.85) == []


def test_locality_thai_name_may_be_null_but_english_is_required():
    assert validate_fossils([loc(name_th=None)], 486.85) == []
    assert any("name_en" in e for e in validate_fossils([loc(name_en="")], 486.85))
