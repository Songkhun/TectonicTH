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
        (root / f"paleo/{age}.json").write_text(json.dumps({"age": age, "kanchanaburi": [99.53, 14.02], "coastlines": {"type": "FeatureCollection", "features": []}}), encoding="utf-8")
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


@pytest.mark.parametrize("src", ["export default 1;\n", "import x from './a.js';\n", "export { a };\n", "import('./a.js');\n"])
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
