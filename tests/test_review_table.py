import csv

from review_table import COLUMNS, write_review

EVENTS = [{
    "id": "ratburi-limestone", "lane": "local", "age_ma": 270, "age_uncertainty_ma": 15,
    "title_th": "หินปูนกลุ่มราชบุรี", "title_en": "Ratburi limestone", "body_th": "ข้อความ | มีขีด", "body_en": "Text",
    "rock_unit": None, "visit_site": None, "citation": {"text": "Ridd 2011", "url": "https://doi.org/10.1144/GOTH"},
    "paleo_age": 270, "lecture_stop": True, "verified": False,
    "_notes": "Age from Ridd 2011 table 5.1",
}]


def test_csv_has_bom_columns_and_thai(tmp_path):
    csv_path, md_path = write_review(EVENTS, tmp_path)
    raw = csv_path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    assert list(rows[0].keys()) == COLUMNS
    assert rows[0]["title_th"] == "หินปูนกลุ่มราชบุรี"
    assert rows[0]["verified"] == "no" and rows[0]["corrections"] == ""


def test_markdown_escapes_pipes(tmp_path):
    _, md_path = write_review(EVENTS, tmp_path)
    text = md_path.read_text(encoding="utf-8")
    assert "ข้อความ \\| มีขีด" in text
    assert text.count("\n|") >= 3


def test_notes_column_carries_research_notes(tmp_path):
    csv_path, _ = write_review(EVENTS, tmp_path)
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    assert rows[0]["notes"] == "Age from Ridd 2011 table 5.1"


from review_table import EVIDENCE_COLUMNS, write_evidence_review


def test_evidence_review_csv(tmp_path):
    items = [{"id": "pm", "event_ids": ["a", "b"], "method": "paleomagnetism", "title_th": "ก", "title_en": "Pole",
              "finding_th": "ข", "finding_en": "F", "value": "32 ± 6°S", "paleolat": {"deg": -32, "err": 6},
              "site": None, "citation": {"text": "S 2020", "url": "https://doi.org/10.1/x"},
              "source_type": "peer-reviewed", "verified": False, "_notes": "n"}]
    csv_path, md_path = write_evidence_review(items, tmp_path)
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    assert list(rows[0].keys()) == EVIDENCE_COLUMNS
    assert rows[0]["event_ids"] == "a; b" and rows[0]["paleolat"] == "-32 ± 6" and rows[0]["notes"] == "n"
    assert md_path.name == "evidence_review.md"


from review_table import FOSSIL_COLUMNS, write_fossil_review


def test_fossil_review_csv(tmp_path):
    f = {"id": "fos-a", "taxon": "Sinoceras chinense", "group": "nautiloid", "age_top_ma": 449.0, "age_base_ma": 458.0,
         "stage": "Sandbian", "formation_en": "Pa Kae Fm", "formation_th": "หมวดหินป่าแก่",
         "locality": {"name_en": "Ban Tha Kradan", "name_th": "บ้านท่ากระดาน", "tambon_th": "ท่ากระดาน", "amphoe_th": "ศรีสวัสดิ์",
                      "province_th": "กาญจนบุรี", "province_en": "Kanchanaburi", "lat": 14.6, "lon": 99.1, "precision": "area"},
         "significance_th": "ก", "significance_en": "A", "citation": {"text": "F 2021", "url": "https://doi.org/10.1/x"},
         "source_type": "peer-reviewed", "verified": False, "_notes": "n"}
    csv_path, md_path = write_fossil_review([f], tmp_path)
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    assert list(rows[0].keys()) == FOSSIL_COLUMNS
    assert rows[0]["locality"] == "บ้านท่ากระดาน ต.ท่ากระดาน อ.ศรีสวัสดิ์ จ.กาญจนบุรี"
    assert rows[0]["lat_lon"] == "14.6, 99.1 (area)" and rows[0]["age"] == "449–458 Ma"
    assert md_path.name == "fossil_review.md"


from review_table import MODEL_COLUMNS, write_models_review


def test_models_review_has_one_row_per_model_and_evidence_link(tmp_path):
    from test_models import Q, SUT
    csv_path, _ = write_models_review([Q], SUT, tmp_path)
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    assert list(rows[0].keys()) == MODEL_COLUMNS
    kinds = [r["kind"] for r in rows]
    assert kinds.count("model") == 2 and kinds.count("evidence-role") == 1 and kinds.count("suture") == 1 and kinds.count("terrane") == 1
    role = next(r for r in rows if r["kind"] == "evidence-role")
    assert role["detail"] == "inthanon: supports; nan: challenges"
