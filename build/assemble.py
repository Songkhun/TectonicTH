"""Build dist/index.html: one self-contained page. Usage: python3 build/assemble.py [--strict]"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

from evidence import EvidenceFileError, load_evidence, validate_evidence
from paleo import MODEL, check_present, load_slices
from polarity import load_polarity, validate_polarity
from fossils import load_fossils, validate_fossils
from validate import load_json, validate_events, validate_timescale

MODULE_ORDER = ["i18n.js", "format.js", "layout.js", "select.js", "geo.js", "evidence.js", "polarity.js",
                "globe.js", "timeline.js", "card.js", "main.js"]
MAX_HTML_BYTES = 3_000_000
IMPORT_RE = re.compile(r"^import\s+\{[\w\s,$]*\}\s+from\s+'\./[\w-]+\.js';\s*$")
EXPORT_RE = re.compile(r"^export\s+(?=(?:async\s+)?(?:function|const|let|class)\b)")
TOP_DECL_RE = re.compile(r"^(?:async\s+)?(?:function\*?|const|let|class)\s+([A-Za-z_$][\w$]*)", re.M)


class BuildError(Exception):
    pass


def strip_module_syntax(src, name):
    out = []
    for n, line in enumerate(src.splitlines(), 1):
        if line != line.lstrip() and re.match(r"(import|export)\b", line.lstrip()):
            raise BuildError(f"{name}:{n}: import/export must start at column 0")
        if line.startswith("import"):
            if IMPORT_RE.match(line) and not re.search(r"\bas\b", line.split("}")[0]):
                continue
            raise BuildError(f"{name}:{n}: unsupported import (use: import {{ a }} from './x.js';)")
        if line.startswith("export"):
            if EXPORT_RE.match(line):
                out.append(EXPORT_RE.sub("", line))
                continue
            raise BuildError(f"{name}:{n}: unsupported export (use: export function|const|let|class)")
        if re.search(r"\bimport\s*\(", line):
            raise BuildError(f"{name}:{n}: dynamic import is not supported")
        out.append(line)
    return "\n".join(out) + "\n"


def build(root, strict=False, module_order=MODULE_ORDER):
    root = Path(root)
    periods = load_json(root / "content/timescale.json")
    events = load_json(root / "content/events.json")
    slices = load_slices(root / "paleo")
    slice_ages = {float(k) for k in slices}
    try:
        evidence = load_evidence(root / "content/evidence.json")
    except EvidenceFileError as exc:
        raise BuildError(f"content/{exc}") from exc

    polarity = load_polarity(root / "content/polarity.json")
    fossils = load_fossils(root / "content/fossils.json")
    errors = (validate_timescale(periods) + validate_events(events, periods, slice_ages)
              + validate_evidence(evidence, {e.get("id") for e in events},
                                  {e.get("id"): e.get("age_ma") for e in events}))
    errors += validate_fossils(fossils, max(p["start_ma"] for p in periods))
    if polarity is not None:
        errors += validate_polarity(polarity.get("segments", []), max(p["start_ma"] for p in periods))
    if "0" not in slices:
        errors.append("paleo slice for 0 Ma is missing")
    else:
        present = check_present(slices)
        if present:
            errors.append(present)
    for key, sl in slices.items():
        if sl.get("model") != MODEL:
            errors.append(f"{key} Ma slice is from {sl.get('model')}, not {MODEL}; re-run build/fetch_paleo.py")
    if errors:
        raise BuildError("content errors:\n  " + "\n  ".join(errors))
    if strict:
        unverified = [e["id"] for e in events if not e["verified"]]
        if unverified:
            raise BuildError("--strict: unverified events: " + ", ".join(unverified))
        unverified_ev = [it["id"] for it in evidence if not it["verified"]]
        if unverified_ev:
            raise BuildError("--strict: unverified evidence: " + ", ".join(unverified_ev))
        unverified_fos = [f["id"] for f in fossils if not f["verified"]]
        if unverified_fos:
            raise BuildError("--strict: unverified fossils: " + ", ".join(unverified_fos))

    js_parts, seen = [], {}
    for name in module_order:
        code = strip_module_syntax((root / "src" / name).read_text(encoding="utf-8"), name)
        for decl in TOP_DECL_RE.findall(code):
            if decl in seen:
                raise BuildError(f"top-level name '{decl}' defined in both {seen[decl]} and {name}")
            seen[decl] = name
        js_parts.append(f"// ---- {name} ----\n{code}")
    js = "\n".join(js_parts)

    d3 = (root / "vendor/d3.min.js").read_text(encoding="utf-8")
    if "</script" in d3.lower() or "</script" in js.lower():
        raise BuildError("a script contains '</script' and cannot be inlined")

    public_events = [{k: v for k, v in e.items() if not k.startswith("_")} for e in events]
    public_evidence = [{k: v for k, v in it.items() if not k.startswith("_")} for it in evidence]
    public_fossils = [{k: v for k, v in f.items() if not k.startswith("_")} for f in fossils]
    data = json.dumps({"events": public_events, "fossils": public_fossils, "evidence": public_evidence, "polarity": polarity, "periods": periods, "slices": slices, "model": MODEL,
                       "built": dt.date.today().isoformat()},
                      ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

    html = (root / "src/index.html").read_text(encoding="utf-8")
    for ph in ("/*__CSS__*/", "<!--__DATA__-->", "<!--__SCRIPTS__-->"):
        if ph not in html:
            raise BuildError(f"template placeholder {ph} missing from src/index.html")
    css = (root / "src/style.css").read_text(encoding="utf-8")
    html = (html.replace("/*__CSS__*/", css)
                .replace("<!--__DATA__-->", f'<script id="dt-data" type="application/json">{data}</script>')
                .replace("<!--__SCRIPTS__-->", f"<script>{d3}</script>\n<script type=\"module\">\n{js}</script>"))

    if re.search(r"<script[^>]+\bsrc=", html) or re.search(r"<link[^>]+href=\"https?:", html):
        raise BuildError("page must not load external scripts or stylesheets")
    size = len(html.encode("utf-8"))
    if size > MAX_HTML_BYTES:
        raise BuildError(f"dist/index.html is {size} bytes, over the {MAX_HTML_BYTES} bytes limit")

    out = root / "dist/index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


WRAPPER_RE = re.compile(r"<!doctype[^>]*>|</?html[^>]*>|</?head>|</?body[^>]*>", re.I)


def build_artifact(root, strict=False, module_order=MODULE_ORDER):
    """Same page without document wrapper tags; the Artifact publisher adds its own skeleton."""
    full = build(root, strict=strict, module_order=module_order)
    out = full.with_name("artifact.html")
    out.write_text(WRAPPER_RE.sub("", full.read_text(encoding="utf-8")).strip() + "\n", encoding="utf-8")
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="refuse to build with unverified events")
    parser.add_argument("--artifact", action="store_true", help="also write dist/artifact.html for claude.ai publishing")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    try:
        out = (build_artifact if args.artifact else build)(root, strict=args.strict)
    except BuildError as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"built {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
