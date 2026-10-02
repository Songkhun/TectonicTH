# Evidence ("How do we know?") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add evidence items (paleomagnetism, geophysics, dating and fossils, own surveys) to every event card, with a measured-versus-model paleolatitude comparison.

**Architecture:**
- A new `content/evidence.json` holds the items. Each item links to one or more events through `event_ids`.
- Python validates it (`build/evidence.py`), embeds it through `assemble.py`, exports it to a review CSV, and imports instructor rows from a CSV template.
- A new pure ES module, `src/evidence.js`, renders the card section as an HTML string. `card.js` appends that string through a callback passed in by `main.js`.

**Tech Stack:** unchanged (Python 3.12 + pytest, Node ≥ 20 `node:test`, D3 7.9.0 vendored).

**Spec:** `docs/2026-10-02-evidence-design.md` (base spec `docs/2026-10-01-deep-time-kanchanaburi-design.md`)

## Global Constraints

- **Methods (exact):** `paleomagnetism, geochronology, biostratigraphy, seismic, gravity, magnetic, seismicity, geodesy, field-survey`.
- **Source types (exact):** `peer-reviewed, government-report, thesis, conference, own-survey`.
- **New items:** every item starts with `verified: false`, and `--strict` fails on any unverified evidence.
- **Instructor notes:** `_`-prefixed fields never reach the page.
- **Data escaping:** every `<` in the embedded data is escaped as `<` (existing behaviour).
- **No runtime network requests.** Thai is the default language, with an English toggle.
- **Commit messages** end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01JZb5S9Kwceg4ZwkaKWtDPS`.

## Review Focus

1. **Evidence pointing to a removed or renamed event.** Expected: the build fails and names the item and the unknown id. Pinned in the Task 1 tests.
2. **HTML or Thai special characters in evidence text.** Expected: shown literally, never interpreted. Pinned in the Task 3 `evidenceHtml` escaping test.
3. **Southern paleolatitudes, stored as negative degrees.** Expected: shown as `32 ± 6°S` next to the model's `≈36°S`. Pinned in the Task 3 `formatPaleolatCompare` test.
4. **An event with no evidence.** Expected: no empty heading. Pinned in the Task 3 `evidenceHtml` empty test.
5. **An instructor CSV saved by Excel** (UTF-8 with BOM, Thai text, blank optional cells). Expected: it imports cleanly. Pinned in the Task 2 import test.

---

## File Structure

```
build/evidence.py           # METHODS, SOURCE_TYPES, load_evidence, validate_evidence, rows_to_items (Task 1–2)
build/import_evidence.py    # CLI: append template rows to content/evidence.json (Task 2)
build/assemble.py           # modify: load/validate/embed evidence, strict, MODULE_ORDER (Task 1, 4)
build/review_table.py       # modify: evidence review CSV/MD (Task 2)
content/evidence.json       # items (Task 5)
content/evidence_template.csv  # header + one example row (Task 2)
src/evidence.js             # evidenceFor, formatPaleolatCompare, evidenceHtml (Task 3)
src/i18n.js                 # modify: evidence strings + method labels (Task 3)
src/card.js, src/main.js, src/style.css  # modify: render section, About citations, styles (Task 4)
tests/test_evidence.py, tests/js/evidence.test.js  # new
```

---

### Task 1: Evidence schema and build integration

**Files:**
- Create: `build/evidence.py`, `tests/test_evidence.py`
- Modify: `build/assemble.py` (`build()`), `tests/test_assemble.py`

**Interfaces:**
- Produces:
  - `METHODS: tuple[str, ...]`, `SOURCE_TYPES: tuple[str, ...]`
  - `load_evidence(path) -> list[dict]`, which returns `[]` when the file is missing
  - `validate_evidence(items, event_ids: set[str]) -> list[str]`
  - `assemble.build` reads `content/evidence.json` and embeds `data.evidence`; `--strict` also lists unverified evidence ids.

- [ ] **Step 1: Write the failing tests** in `tests/test_evidence.py`:

```python
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
```

Append to `tests/test_assemble.py`:

```python
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
```

- [ ] **Step 2: Run to verify RED.** Run `python3 -m pytest -q tests/test_evidence.py tests/test_assemble.py`. Expected: `ModuleNotFoundError: No module named 'evidence'`.

- [ ] **Step 3: Implement `build/evidence.py`:**

```python
"""Evidence items: schema checks and loading. Validators return lists of error strings."""
import json
from pathlib import Path

from validate import ID_RE, URL_RE, _num, _text

METHODS = ("paleomagnetism", "geochronology", "biostratigraphy", "seismic", "gravity",
           "magnetic", "seismicity", "geodesy", "field-survey")
SOURCE_TYPES = ("peer-reviewed", "government-report", "thesis", "conference", "own-survey")


def load_evidence(path):
    path = Path(path)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def validate_evidence(items, event_ids):
    errors, seen = [], set()
    for i, it in enumerate(items):
        iid = it.get("id", f"#{i}")

        def err(msg):
            errors.append(f"{iid}: {msg}")

        if not isinstance(it.get("id"), str) or not ID_RE.match(it["id"]):
            err("id must be kebab-case")
        elif it["id"] in seen:
            err("duplicate id")
        else:
            seen.add(it["id"])

        ids = it.get("event_ids")
        if not isinstance(ids, list) or not ids:
            err("event_ids must be a non-empty list")
        else:
            for eid in ids:
                if eid not in event_ids:
                    err(f"unknown event id {eid}")

        if it.get("method") not in METHODS:
            err(f"method must be one of {list(METHODS)}")
        if it.get("source_type") not in SOURCE_TYPES:
            err(f"source_type must be one of {list(SOURCE_TYPES)}")
        for key in ("title_th", "title_en", "finding_th", "finding_en"):
            if not _text(it.get(key)):
                err(f"{key} is empty")
        if it.get("value") is not None and not _text(it.get("value")):
            err("value must be null or text")

        c = it.get("citation")
        if not (isinstance(c, dict) and _text(c.get("text"))
                and isinstance(c.get("url"), str) and URL_RE.match(c["url"])):
            err("citation needs text and an http(s) url")

        site = it.get("site")
        if site is not None:
            if not (isinstance(site, dict) and _text(site.get("name_th")) and _text(site.get("name_en"))):
                err("site needs name_th and name_en")
            elif not (_num(site.get("lat")) and -90 <= site["lat"] <= 90
                      and _num(site.get("lon")) and -180 <= site["lon"] <= 180):
                err("site lat/lon out of range")

        pl = it.get("paleolat")
        if pl is not None:
            if it.get("method") != "paleomagnetism":
                err("paleolat is only allowed on paleomagnetism items")
            elif not (isinstance(pl, dict) and _num(pl.get("deg")) and -90 <= pl["deg"] <= 90
                      and _num(pl.get("err")) and pl["err"] >= 0):
                err("paleolat needs deg in [-90, 90] and err >= 0")

        if not isinstance(it.get("verified"), bool):
            err("verified must be true or false")
    return errors
```

Modify `build/assemble.py`:
- `from evidence import load_evidence, validate_evidence`
- In `build()`, after `slice_ages = ...`, add `evidence = load_evidence(root / "content/evidence.json")`.
- Change the error line to `errors = validate_timescale(periods) + validate_events(events, periods, slice_ages) + validate_evidence(evidence, {e.get("id") for e in events})`.
- In the strict block, add after the events check:
  ```python
          unverified_ev = [it["id"] for it in evidence if not it["verified"]]
          if unverified_ev:
              raise BuildError("--strict: unverified evidence: " + ", ".join(unverified_ev))
  ```
- Next to `public_events`, add `public_evidence = [{k: v for k, v in it.items() if not k.startswith("_")} for it in evidence]`, and add `"evidence": public_evidence` to the data dict.

- [ ] **Step 4: Run to verify GREEN.** Run `python3 -m pytest -q`. Expected: all pass.

- [ ] **Step 5: Commit.** Run `git add build/evidence.py build/assemble.py tests/test_evidence.py tests/test_assemble.py`, then `git commit -m "feat: evidence schema, validation and embedding"` with the attribution lines.

---

### Task 2: Review export, template and CSV import

**Files:**
- Modify: `build/review_table.py`, `tests/test_review_table.py`, `build/evidence.py`
- Create: `build/import_evidence.py`, `content/evidence_template.csv`
- Test: append to `tests/test_evidence.py`

**Interfaces:**
- Consumes: `validate_evidence`, `load_evidence` (Task 1)
- Produces:
  - `TEMPLATE_COLUMNS: list[str]`
  - `rows_to_items(rows: list[dict]) -> list[dict]`
  - `import_rows(csv_path, evidence_path, event_ids) -> list[str]`, which returns errors; empty means it was written
  - `write_evidence_review(items, out_dir) -> tuple[Path, Path]`

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_evidence.py`:

```python
import csv as csvmod

from evidence import TEMPLATE_COLUMNS, import_rows, rows_to_items


def test_rows_to_items_handles_blanks_and_lists():
    row = {c: "" for c in TEMPLATE_COLUMNS}
    row.update({"id": "ert-sai-yok-2024", "event_ids": "ratburi-limestone; indosinian-collision",
                "method": "field-survey", "title_th": "ERT ไทรโยค", "title_en": "ERT Sai Yok",
                "finding_th": "พบโพรง", "finding_en": "Cavity found", "citation_text": "Division report 2024",
                "citation_url": "https://example.org/r.pdf", "site_lat": "14.4", "site_lon": "98.85",
                "site_name_th": "ไทรโยค", "site_name_en": "Sai Yok", "notes": "line 3"})
    it = rows_to_items([row])[0]
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
    it = rows_to_items([row])[0]
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
```

Append to `tests/test_review_table.py`:

```python
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
```

- [ ] **Step 2: Run to verify RED.** Run `python3 -m pytest -q`. Expected: ImportError for `TEMPLATE_COLUMNS` and `EVIDENCE_COLUMNS`.

- [ ] **Step 3: Implement.** Append to `build/evidence.py`:

```python
import csv

TEMPLATE_COLUMNS = ["id", "event_ids", "method", "title_th", "title_en", "finding_th", "finding_en", "value",
                    "paleolat_deg", "paleolat_err", "site_name_th", "site_name_en", "site_lat", "site_lon",
                    "citation_text", "citation_url", "source_type", "notes"]


def _cell(row, key):
    return (row.get(key) or "").strip()


def rows_to_items(rows):
    items = []
    for row in rows:
        deg, err = _cell(row, "paleolat_deg"), _cell(row, "paleolat_err")
        lat, lon = _cell(row, "site_lat"), _cell(row, "site_lon")
        items.append({
            "id": _cell(row, "id"),
            "event_ids": [s.strip() for s in _cell(row, "event_ids").split(";") if s.strip()],
            "method": _cell(row, "method"),
            "title_th": _cell(row, "title_th"), "title_en": _cell(row, "title_en"),
            "finding_th": _cell(row, "finding_th"), "finding_en": _cell(row, "finding_en"),
            "value": _cell(row, "value") or None,
            "paleolat": {"deg": float(deg), "err": float(err or 0)} if deg else None,
            "site": ({"name_th": _cell(row, "site_name_th"), "name_en": _cell(row, "site_name_en"),
                      "lat": float(lat), "lon": float(lon)} if lat and lon else None),
            "citation": {"text": _cell(row, "citation_text"), "url": _cell(row, "citation_url")},
            "source_type": _cell(row, "source_type") or "own-survey",
            "verified": False,
            "_notes": _cell(row, "notes"),
        })
    return items


def import_rows(csv_path, evidence_path, event_ids):
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as f:
        new = rows_to_items(list(csv.DictReader(f)))
    existing = load_evidence(evidence_path)
    errors = validate_evidence(existing + new, event_ids)
    if errors:
        return errors
    Path(evidence_path).write_text(json.dumps(existing + new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return []
```

Create `build/import_evidence.py`:

```python
"""Append rows from an evidence CSV (see content/evidence_template.csv) to content/evidence.json.
Usage: python3 build/import_evidence.py path/to/rows.csv"""
import sys
from pathlib import Path

from evidence import import_rows
from validate import load_json

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    root = Path(__file__).resolve().parent.parent
    event_ids = {e["id"] for e in load_json(root / "content/events.json")}
    errors = import_rows(sys.argv[1], root / "content/evidence.json", event_ids)
    if errors:
        print("NOT IMPORTED:\n  " + "\n  ".join(errors), file=sys.stderr)
        sys.exit(1)
    print("imported; all new items are verified: false")
```

Create `content/evidence_template.csv` with UTF-8 BOM, the header row `TEMPLATE_COLUMNS`, and one example row (`field-survey`, linked to `ratburi-limestone`, example ERT survey text marked "EXAMPLE — replace", citation url `https://example.org/report.pdf`). Write it with Python `csv` using `utf-8-sig`.

Modify `build/review_table.py`:
- Add `EVIDENCE_COLUMNS = ["id", "event_ids", "method", "title_th", "title_en", "finding_th", "finding_en", "value", "paleolat", "site", "citation", "source_type", "verified", "notes", "corrections"]`.
- Add `write_evidence_review(items, out_dir)`. It mirrors `write_review`:
  - `event_ids` is joined with `"; "`
  - `paleolat` is shown as `f"{deg:g} ± {err:g}"`
  - `site` uses the same format as events
  - the files are named `evidence_review.csv` and `evidence_review.md`
  - Markdown cells have `|` escaped
- In `__main__`, also call `write_evidence_review(load_evidence(root / "content/evidence.json"), root / "review")`, importing `load_evidence` from `evidence`.

- [ ] **Step 4: Run to verify GREEN.** Run `python3 -m pytest -q`. Expected: all pass.

- [ ] **Step 5: Commit** with the message `feat: evidence review export, CSV template and importer`.

---

### Task 3: Pure rendering module and strings

**Files:**
- Create: `src/evidence.js`, `tests/js/evidence.test.js`
- Modify: `src/i18n.js`

**Interfaces:**
- Consumes: `t`, `field`, `getLang`, `I18N_STRINGS` (from i18n.js); `esc`, `formatLat` (from format.js)
- Produces:
  - `EVIDENCE_METHODS` (array of method ids)
  - `evidenceFor(eventId, items) -> item[]`, keeping file order
  - `formatPaleolatCompare(paleolat {deg, err}, modelLat number|null, lang) -> string`
  - `evidenceHtml(eventId, items, modelLat) -> string`, which returns `''` when the event has no items
  - i18n keys: `evidence_heading`, `measured`, `model`, `method_<id>` for every method

- [ ] **Step 1: Write the failing test** `tests/js/evidence.test.js`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { initLang, setLang, I18N_STRINGS } from '../../src/i18n.js';
import { EVIDENCE_METHODS, evidenceFor, formatPaleolatCompare, evidenceHtml } from '../../src/evidence.js';

const items = [
  { id: 'a', event_ids: ['x'], method: 'paleomagnetism', title_th: 'ขั้วแม่เหล็ก', title_en: 'Pole', finding_th: 'ผล', finding_en: 'Result',
    value: '32 ± 6°S', paleolat: { deg: -32, err: 6 }, site: null, citation: { text: 'S 2020', url: 'https://doi.org/10.1/x' }, source_type: 'peer-reviewed', verified: false },
  { id: 'b', event_ids: ['y', 'x'], method: 'seismic', title_th: 'สำรวจ <b>', title_en: 'Survey <b>', finding_th: 'พบ & "ชั้น"', finding_en: 'Found & "layer"',
    value: null, paleolat: null, site: { name_th: 'ไทรโยค', name_en: 'Sai Yok', lat: 14.4, lon: 98.85 }, citation: { text: 'T 2010', url: 'https://doi.org/10.2/y' }, source_type: 'peer-reviewed', verified: true },
];

test('evidenceFor filters by event and keeps file order', () => {
  assert.deepEqual(evidenceFor('x', items).map(i => i.id), ['a', 'b']);
  assert.deepEqual(evidenceFor('y', items).map(i => i.id), ['b']);
  assert.deepEqual(evidenceFor('z', items), []);
});

test('paleolatitude comparison shows hemisphere for measured and model', () => {
  assert.equal(formatPaleolatCompare({ deg: -32, err: 6 }, -35.6, 'th'), 'วัดได้ 32 ± 6°S · แบบจำลอง ≈36°S');
  assert.equal(formatPaleolatCompare({ deg: 12.5, err: 3 }, 6.6, 'en'), 'measured 12.5 ± 3°N · model ≈7°N');
  assert.equal(formatPaleolatCompare({ deg: -32, err: 6 }, null, 'en'), 'measured 32 ± 6°S');
});

test('evidenceHtml is empty for an event without evidence', () => {
  initLang(null);
  assert.equal(evidenceHtml('z', items, null), '');
});

test('evidenceHtml escapes text and includes heading, chips, comparison and links', () => {
  initLang(null);
  setLang('en');
  const html = evidenceHtml('x', items, -35.6);
  assert.ok(html.includes('How do we know?'));
  assert.ok(html.includes('Survey &lt;b&gt;') && !html.includes('Survey <b>'));
  assert.ok(html.includes('Found &amp; &quot;layer&quot;'));
  assert.ok(html.includes('measured 32 ± 6°S · model ≈36°S'));
  assert.ok(html.includes('ev-paleomagnetism') && html.includes('ev-seismic'));
  assert.ok(html.includes('https://www.google.com/maps?q=14.4,98.85'));
  assert.ok(html.includes('https://doi.org/10.1/x'));
  setLang('th');
});

test('every method has a label in both languages', () => {
  for (const m of EVIDENCE_METHODS) {
    assert.ok(I18N_STRINGS.th[`method_${m}`], m);
    assert.ok(I18N_STRINGS.en[`method_${m}`], m);
  }
});
```

- [ ] **Step 2: Run to verify RED.** Run `npm test`. Expected: `Cannot find module .../src/evidence.js`.

- [ ] **Step 3: Implement `src/evidence.js`:**

```js
import { t, field, getLang } from './i18n.js';
import { esc, formatLat } from './format.js';

export const EVIDENCE_METHODS = ['paleomagnetism', 'geochronology', 'biostratigraphy', 'seismic', 'gravity',
  'magnetic', 'seismicity', 'geodesy', 'field-survey'];

export function evidenceFor(eventId, items) {
  return items.filter(it => it.event_ids.includes(eventId));
}

function hemi(deg) {
  return `${Math.abs(deg)}`.replace(/\.0+$/, '');
}

export function formatPaleolatCompare(paleolat, modelLat, lang) {
  const th = lang === 'th';
  const measured = `${hemi(paleolat.deg)} ± ${paleolat.err}°${paleolat.deg < 0 ? 'S' : 'N'}`;
  const head = `${th ? 'วัดได้' : 'measured'} ${measured}`;
  if (modelLat == null) return head;
  return `${head} · ${th ? 'แบบจำลอง' : 'model'} ${formatLat(modelLat)}`;
}

export function evidenceHtml(eventId, items, modelLat) {
  const list = evidenceFor(eventId, items);
  if (!list.length) return '';
  const lang = getLang();
  const rows = list.map(it => {
    const badge = it.verified ? '' : ` <span class="badge">${esc(t('draft'))}</span>`;
    const value = it.value ? `<span class="ev-value">${esc(it.value)}</span>` : '';
    const compare = it.paleolat ? `<span class="ev-compare">${esc(formatPaleolatCompare(it.paleolat, modelLat, lang))}</span>` : '';
    const site = it.site
      ? ` · <a href="https://www.google.com/maps?q=${it.site.lat},${it.site.lon}" target="_blank" rel="noopener">${esc(field(it.site, 'name'))}</a>`
      : '';
    return `<li class="ev-item"><div class="ev-head"><span class="ev-chip ev-${esc(it.method)}">${esc(t(`method_${it.method}`))}</span>` +
      `<strong>${esc(field(it, 'title'))}</strong>${badge}</div>` +
      `<p>${esc(field(it, 'finding'))}</p>${value || compare ? `<p class="ev-data">${value}${value && compare ? ' · ' : ''}${compare}</p>` : ''}` +
      `<p class="ev-cite"><a href="${esc(it.citation.url)}" target="_blank" rel="noopener">${esc(it.citation.text)}</a>${site}</p></li>`;
  }).join('');
  return `<section class="evidence"><h3>${esc(t('evidence_heading'))}</h3><ul>${rows}</ul></section>`;
}
```

Add to `I18N_STRINGS.th`:
```js
    evidence_heading: 'หลักฐาน · เรารู้ได้อย่างไร',
    method_paleomagnetism: 'แม่เหล็กบรรพกาล',
    method_geochronology: 'การหาอายุ',
    method_biostratigraphy: 'ฟอสซิล/ลำดับชั้นชีวภาพ',
    method_seismic: 'คลื่นไหวสะเทือน',
    method_gravity: 'ความโน้มถ่วง',
    method_magnetic: 'สนามแม่เหล็ก',
    method_seismicity: 'แผ่นดินไหว',
    method_geodesy: 'GPS/มาตรวิทยาธรณี',
    'method_field-survey': 'สำรวจภาคสนามของเรา',
```

Add to `I18N_STRINGS.en`:
```js
    evidence_heading: 'How do we know?',
    method_paleomagnetism: 'Paleomagnetism',
    method_geochronology: 'Dating',
    method_biostratigraphy: 'Fossils',
    method_seismic: 'Seismic',
    method_gravity: 'Gravity',
    method_magnetic: 'Magnetics',
    method_seismicity: 'Earthquakes',
    method_geodesy: 'GPS/geodesy',
    'method_field-survey': 'Our field survey',
```

- [ ] **Step 4: Run to verify GREEN.** Run `npm test`. Expected: all pass.

- [ ] **Step 5: Commit** with the message `feat: evidence rendering module and strings`.

---

### Task 4: Card, About and styles

**Files:**
- Modify: `src/card.js`, `src/main.js`, `src/style.css`, `build/assemble.py` (`MODULE_ORDER`)

**Interfaces:**
- Consumes: `evidenceHtml` (Task 3), `data.evidence` (Task 1)
- Produces: `createCard(el, {onPrev, onNext, onClose, extraHtml})`, where `extraHtml(event) -> string` is inserted after the citation and before the lecture nav.

- [ ] **Step 1: Wire it up.**
  - **`build/assemble.py`:** insert `"evidence.js"` into `MODULE_ORDER` after `"geo.js"`.
  - **`card.js`:** the destructuring becomes `{ onPrev, onNext, onClose, extraHtml } = {}`. Add `const extra = extraHtml ? extraHtml(e) : '';` and append `${extra}` after `${cite}` in `el.innerHTML`.
  - **`main.js`:**
    - `import { evidenceHtml } from './evidence.js';`
    - `const evidence = data.evidence || [];`
    - pass `extraHtml: e => evidenceHtml(e.id, evidence, data.slices[String(e.paleo_age)]?.kanchanaburi?.[1] ?? null)` to `createCard`
    - in `renderAbout`, iterate `[...data.events, ...evidence]` when collecting citations
  - **`style.css`:** add the tokens below to `:root` and to both dark blocks:

```css
/* light (:root) */
--ev-paleomag: #6a3fb5; --ev-dating: #a5531a; --ev-geophys: #1f6f8b; --ev-field: #2f7d32; --ev-chip-text: #ffffff;
/* dark (both dark blocks) */
--ev-paleomag: #b79cf0; --ev-dating: #f0a36b; --ev-geophys: #7cc7e0; --ev-field: #8fd18f; --ev-chip-text: #15171a;
```

  Then the rules:

```css
.evidence { margin-top: 10px; border-top: 1px solid var(--border); padding-top: 8px; }
.evidence h3 { font-size: .9em; margin: 0 0 6px; }
.evidence ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.ev-head { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: .88em; }
.ev-chip { font-size: .72em; padding: 1px 8px; border-radius: 999px; color: var(--ev-chip-text); background: var(--ev-geophys); }
.ev-paleomagnetism { background: var(--ev-paleomag); }
.ev-geochronology, .ev-biostratigraphy { background: var(--ev-dating); }
.ev-field-survey { background: var(--ev-field); }
#card .ev-item p { margin: 2px 0; font-size: .85em; }
#card .ev-data { font-variant-numeric: tabular-nums; color: var(--text); font-weight: 600; }
#card .ev-cite { font-size: .76em; color: var(--muted); }
```

- [ ] **Step 2: Verify.** Run `python3 -m pytest -q && npm test && python3 build/assemble.py`. Expected: everything passes and the build succeeds; with no evidence file, the cards show no section.

- [ ] **Step 3: Commit** with the message `feat: show evidence on event cards and in About`.

---

### Task 5: Draft evidence content, review, QA and publish

**Files:**
- Create: `content/evidence.json`
- Modify: `tools/browser_check.mjs` (add the evidence check)

- [ ] **Step 1: Research.** Three background research agents write `.superpowers/content/evidence-{paleomag,geophys,dating}.json` using the Task 1 schema and the real event ids from `content/events.json`. They work under the same rules as the events:
  - no invented citation or value
  - DOIs checked on Crossref
  - `_notes` states exactly what the source gives
  - `verified: false`

  The targets are about 10–15 items each, with every lecture stop covered by at least one item.
  - **Paleomagnetism:** Sibumasu and western Thailand paleolatitudes for the Ordovician, Permian, Triassic and Cretaceous, plus Cenozoic rotations, each with numeric `paleolat`.
  - **Geophysics:** seismic, gravity and aeromagnetic data, earthquake catalogues and GPS for the Three Pagodas and Si Sawat faults, the Kanchanaburi basins, Srinagarind seismicity and the 2025 earthquake.
  - **Dating and fossils:** U–Pb, Ar–Ar and K–Ar ages, fossils such as conodonts, fusulinids and graptolites, and radiocarbon dates behind each event.

- [ ] **Step 2: Merge and validate.** Merge the three files into `content/evidence.json`, renaming any duplicate ids with a suffix. Run `python3 build/assemble.py` and fix validation errors. Check every citation URL (HEAD/GET, then Crossref for 403/404 responses) and add the result to `_notes`. Confirm every lecture stop has at least one item.

- [ ] **Step 3: Browser check.** In `tools/browser_check.mjs`, after the card step, add:

```js
await ev("document.getElementById('btn-lecture').click()"); await sleep(1200);
report.evidence_section = await ev("!!document.querySelector('#card .evidence')");
report.evidence_compare = await ev("document.querySelector('#card .ev-compare')?.textContent || null");
await ev("document.getElementById('btn-lecture').click()"); await sleep(400);
```

  Run it and confirm that `evidence_section` is true on the first lecture stop, that a paleomagnetic comparison appears for at least one stop, and that there are no logs. Take one screenshot of a card with evidence.

- [ ] **Step 4: Build, export, commit and republish.** Run `python3 -m pytest -q && npm test && python3 build/assemble.py --artifact && python3 build/review_table.py`. Commit with the message `content: draft cited evidence items`. Republish `dist/artifact.html` to https://claude.ai/artifact/K2x7rtU1n7qBZ3uferxjLb.
