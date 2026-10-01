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
