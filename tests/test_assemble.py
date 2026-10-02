import json
import shutil
from pathlib import Path

import pytest

import assemble
from assemble import BuildError, build, strip_module_syntax

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = "<!doctype html><title>Deep Time Kanchanaburi</title><style>/*__CSS__*/</style><!--__DATA__--><!--__SCRIPTS__-->"


def make_root(tmp_path, events=None):
    root = tmp_path / "site"
    for d in ("content", "paleo", "src", "vendor"):
        (root / d).mkdir(parents=True)
    shutil.copy(ROOT / "content/timescale.json", root / "content/timescale.json")
    starter = json.loads((ROOT / "tests/fixtures/starter_events.json").read_text(encoding="utf-8"))
    (root / "content/events.json").write_text(json.dumps(events if events is not None else starter, ensure_ascii=False), encoding="utf-8")
    for age in (270, 250, 230, 0):
        (root / f"paleo/{age}.json").write_text(json.dumps({"age": age, "model": assemble.MODEL, "kanchanaburi": [99.53, 14.02], "coastlines": {"type": "FeatureCollection", "features": []}}), encoding="utf-8")
    (root / "src/index.html").write_text(TEMPLATE, encoding="utf-8")
    (root / "src/style.css").write_text("body{background:#fff}", encoding="utf-8")
    (root / "src/a.js").write_text("export function hello() { return 1; }\n", encoding="utf-8")
    (root / "src/b.js").write_text("import { hello } from './a.js';\nexport const two = hello() + 1;\n", encoding="utf-8")
    (root / "vendor/d3.min.js").write_text("var d3={};", encoding="utf-8")
    return root


def test_strip_module_syntax():
    out = strip_module_syntax("import { a } from './a.js';\nexport function f() {}\nexport const x = 1;\n", "t.js")
    assert "import" not in out and "export" not in out
    assert "function f()" in out and "const x = 1" in out


@pytest.mark.parametrize("src", ["export default 1;\n", "import x from './a.js';\n", "export { a };\n", "import('./a.js');\n",
                                 "  import { a } from './a.js';\n", "  export function f() {}\n",
                                 "import { a as b } from './a.js';\n"])
def test_strip_rejects_unsupported(src):
    with pytest.raises(BuildError):
        strip_module_syntax(src, "bad.js")


def test_build_inlines_everything(tmp_path):
    root = make_root(tmp_path)
    out = build(root, module_order=["a.js", "b.js"])
    html = out.read_text(encoding="utf-8")
    assert "/*__CSS__*/" not in html and "<!--__DATA__-->" not in html
    assert "body{background:#fff}" in html and "var d3={};" in html
    assert "function hello()" in html and "<script src" not in html
    data = json.loads(html.split('<script id="dt-data" type="application/json">')[1].split("</script>")[0])
    assert {"events", "periods", "slices", "model", "built"} <= set(data)
    assert set(data["slices"]) == {"0", "230", "250", "270"}


def test_build_escapes_script_close_in_content(tmp_path):
    starter = json.loads((ROOT / "tests/fixtures/starter_events.json").read_text(encoding="utf-8"))
    starter[0]["body_en"] = "Danger </script><b>bold</b>"
    root = make_root(tmp_path, starter)
    html = build(root, module_order=["a.js", "b.js"]).read_text(encoding="utf-8")
    assert "Danger </script>" not in html
    block = html.split('<script id="dt-data" type="application/json">')[1].split("</script>")[0]
    assert json.loads(block)["events"][0]["body_en"] == "Danger </script><b>bold</b>"


def test_build_fails_on_invalid_content(tmp_path):
    starter = json.loads((ROOT / "tests/fixtures/starter_events.json").read_text(encoding="utf-8"))
    starter[0]["citation"] = None
    root = make_root(tmp_path, starter)
    with pytest.raises(BuildError, match="citation"):
        build(root, module_order=["a.js", "b.js"])


def test_build_fails_on_missing_slice(tmp_path):
    root = make_root(tmp_path)
    (root / "paleo/250.json").unlink()
    with pytest.raises(BuildError, match="no paleo slice"):
        build(root, module_order=["a.js", "b.js"])


def test_strict_refuses_unverified(tmp_path):
    root = make_root(tmp_path)
    with pytest.raises(BuildError, match="ratburi-limestone"):
        build(root, strict=True, module_order=["a.js", "b.js"])


def test_duplicate_top_level_names_rejected(tmp_path):
    root = make_root(tmp_path)
    (root / "src/b.js").write_text("export function hello() { return 2; }\n", encoding="utf-8")
    with pytest.raises(BuildError, match="hello"):
        build(root, module_order=["a.js", "b.js"])


def test_size_limit(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    monkeypatch.setattr(assemble, "MAX_HTML_BYTES", 100)
    with pytest.raises(BuildError, match="bytes"):
        build(root, module_order=["a.js", "b.js"])


def test_build_strips_private_note_fields(tmp_path):
    starter = json.loads((ROOT / "tests/fixtures/starter_events.json").read_text(encoding="utf-8"))
    starter[0]["_notes"] = "instructor-only note"
    root = make_root(tmp_path, starter)
    html = build(root, module_order=["a.js", "b.js"]).read_text(encoding="utf-8")
    assert "instructor-only note" not in html
    assert "_notes" not in html


def test_artifact_variant_has_no_document_wrapper(tmp_path):
    root = make_root(tmp_path)
    (root / "src/index.html").write_text(
        '<!doctype html>\n<html lang="th">\n<head>\n<meta charset="utf-8">\n<title>Deep Time Kanchanaburi</title>\n'
        '<style>/*__CSS__*/</style>\n</head>\n<body>\n<main>hi</main>\n<!--__DATA__-->\n<!--__SCRIPTS__-->\n</body>\n</html>\n',
        encoding="utf-8")
    out = assemble.build_artifact(root, module_order=["a.js", "b.js"])
    html = out.read_text(encoding="utf-8")
    assert out.name == "artifact.html"
    for tag in ("<!doctype", "<html", "<head", "<body", "</body>", "</html>", "</head>"):
        assert tag not in html.lower()
    assert html.lstrip().startswith("<meta charset")
    assert html.index("<title>") < 8192 and "<main>hi</main>" in html and 'id="dt-data"' in html


def test_build_survives_html_comment_openers_in_content(tmp_path):
    starter = json.loads((ROOT / "tests/fixtures/starter_events.json").read_text(encoding="utf-8"))
    starter[0]["body_en"] = "odd <!--<script> text <body> here"
    root = make_root(tmp_path, starter)
    out = assemble.build_artifact(root, module_order=["a.js", "b.js"])
    html = out.read_text(encoding="utf-8")
    block = html.split('<script id="dt-data" type="application/json">')[1].split("</script>")[0]
    assert "<" not in block
    assert json.loads(block)["events"][0]["body_en"] == "odd <!--<script> text <body> here"


def write_evidence(root, items):
    (root / "content/evidence.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


EV = {"id": "pmag-ratburi", "event_ids": ["ratburi-limestone"], "method": "paleomagnetism",
      "title_th": "ก", "title_en": "Pole", "finding_th": "ข", "finding_en": "Finding", "value": None,
      "paleolat": {"deg": -32, "err": 6}, "site": None,
      "citation": {"text": "S 2020", "url": "https://doi.org/10.1/x"}, "source_type": "peer-reviewed",
      "verified": True, "_notes": "private evidence note"}


def test_build_embeds_evidence_without_private_fields(tmp_path):
    root = make_root(tmp_path)
    write_evidence(root, [EV])
    html = build(root, module_order=["a.js", "b.js"]).read_text(encoding="utf-8")
    block = html.split('<script id="dt-data" type="application/json">')[1].split("</script>")[0]
    data = json.loads(block)
    assert data["evidence"][0]["id"] == "pmag-ratburi"
    assert "private evidence note" not in html


def test_build_without_evidence_file_embeds_empty_list(tmp_path):
    root = make_root(tmp_path)
    html = build(root, module_order=["a.js", "b.js"]).read_text(encoding="utf-8")
    block = html.split('<script id="dt-data" type="application/json">')[1].split("</script>")[0]
    assert json.loads(block)["evidence"] == []


def test_build_rejects_evidence_for_unknown_event(tmp_path):
    root = make_root(tmp_path)
    write_evidence(root, [{**EV, "event_ids": ["gone"]}])
    with pytest.raises(BuildError, match="unknown event id gone"):
        build(root, module_order=["a.js", "b.js"])


def test_strict_refuses_unverified_evidence(tmp_path):
    starter = json.loads((ROOT / "tests/fixtures/starter_events.json").read_text(encoding="utf-8"))
    for e in starter:
        e["verified"] = True
    root = make_root(tmp_path, starter)
    write_evidence(root, [{**EV, "verified": False}])
    with pytest.raises(BuildError, match="unverified evidence: pmag-ratburi"):
        build(root, strict=True, module_order=["a.js", "b.js"])


def test_build_rejects_slices_from_another_model(tmp_path):
    root = make_root(tmp_path)
    p = root / "paleo/250.json"
    sl = json.loads(p.read_text(encoding="utf-8"))
    sl["model"] = "SOMEOTHER2020"
    p.write_text(json.dumps(sl), encoding="utf-8")
    with pytest.raises(BuildError, match="250 Ma slice is from SOMEOTHER2020"):
        build(root, module_order=["a.js", "b.js"])


def test_build_rejects_wrong_present_day_position(tmp_path):
    root = make_root(tmp_path)
    p = root / "paleo/0.json"
    sl = json.loads(p.read_text(encoding="utf-8"))
    sl["kanchanaburi"] = [90.0, 14.02]
    p.write_text(json.dumps(sl), encoding="utf-8")
    with pytest.raises(BuildError, match="0 Ma Kanchanaburi position"):
        build(root, module_order=["a.js", "b.js"])


def test_build_embeds_polarity_when_present(tmp_path):
    from polarity import SUPERCHRONS, build_segments
    root = make_root(tmp_path)
    segs = build_segments([0.0, 0.773, 82.875], [["C1n", 0.0], ["C1r", 0.773]], SUPERCHRONS, 486.85)
    (root / "content/polarity.json").write_text(json.dumps({"sources": {"gts2020": {"text": "Ogg 2020", "url": "https://doi.org/10.1/x"}}, "segments": segs}), encoding="utf-8")
    html = build(root, module_order=["a.js", "b.js"]).read_text(encoding="utf-8")
    data = json.loads(html.split('<script id="dt-data" type="application/json">')[1].split("</script>")[0])
    assert data["polarity"]["segments"][0]["name"] == "C1n"


def test_build_without_polarity_file_embeds_null(tmp_path):
    root = make_root(tmp_path)
    html = build(root, module_order=["a.js", "b.js"]).read_text(encoding="utf-8")
    data = json.loads(html.split('<script id="dt-data" type="application/json">')[1].split("</script>")[0])
    assert data["polarity"] is None


FOS = {"id": "fos-a", "taxon": "Sinoceras chinense", "group": "nautiloid", "age_top_ma": 260.0, "age_base_ma": 270.0,
       "stage": "Permian", "formation_en": None, "formation_th": None,
       "locality": {"name_en": "A", "name_th": "ก", "tambon_th": None, "amphoe_th": None, "province_th": "กาญจนบุรี",
                    "province_en": "Kanchanaburi", "lat": 14.0, "lon": 99.5, "precision": "district"},
       "significance_th": "ก", "significance_en": "A", "citation": {"text": "S", "url": "https://doi.org/10.1/x"},
       "source_type": "peer-reviewed", "verified": False, "_notes": "secret fossil note"}


def test_build_embeds_fossils_without_private_fields(tmp_path):
    root = make_root(tmp_path)
    (root / "content/fossils.json").write_text(json.dumps([FOS], ensure_ascii=False), encoding="utf-8")
    html = build(root, module_order=["a.js", "b.js"]).read_text(encoding="utf-8")
    data = json.loads(html.split('<script id="dt-data" type="application/json">')[1].split("</script>")[0])
    assert data["fossils"][0]["taxon"] == "Sinoceras chinense"
    assert "secret fossil note" not in html


def test_strict_refuses_unverified_fossils(tmp_path):
    starter = json.loads((ROOT / "tests/fixtures/starter_events.json").read_text(encoding="utf-8"))
    for e in starter:
        e["verified"] = True
    root = make_root(tmp_path, starter)
    (root / "content/fossils.json").write_text(json.dumps([FOS], ensure_ascii=False), encoding="utf-8")
    with pytest.raises(BuildError, match="unverified fossils: fos-a"):
        build(root, strict=True, module_order=["a.js", "b.js"])


def test_build_without_fossils_embeds_empty_list(tmp_path):
    root = make_root(tmp_path)
    html = build(root, module_order=["a.js", "b.js"]).read_text(encoding="utf-8")
    data = json.loads(html.split('<script id="dt-data" type="application/json">')[1].split("</script>")[0])
    assert data["fossils"] == []
