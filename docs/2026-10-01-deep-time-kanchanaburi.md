# Deep Time Kanchanaburi Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A single self-contained HTML teaching page that shows Kanchanaburi's geologic history in three timeline lanes next to a globe of ancient plate positions, in Thai and English.

**Architecture:**
- Python build scripts fetch paleo-coastlines and Kanchanaburi's ancient position from the GPlates Web Service once per fixed time slice, then simplify them and store them as JSON.
- A second script validates the content and inlines everything (CSS, vendored D3, the page's ES modules with import/export stripped, and the data JSON) into `dist/index.html`.
- The browser code is split into small ES modules. The pure-logic modules are unit-tested with `node --test`; the DOM modules are checked manually in a browser.

**Tech Stack:**
- Python 3.12 with `requests`, plus pytest 7
- Node ≥ 20 (`node:test`, no npm dependencies)
- D3 v7.9.0, vendored from cdnjs
- Canvas 2D

**Spec:** `docs/superpowers/specs/2026-10-01-deep-time-kanchanaburi-design.md`

**Deliberate deviations from the spec.** Each one simplifies without changing behaviour:
1. **Slice format:** slices are GeoJSON simplified with our own Douglas–Peucker code, not TopoJSON via mapshaper. This adds no dependency and drops the topojson-client library.
2. **Present-day coastlines:** these come from GPlates at 0 Ma rather than Natural Earth, so all slices come from one source.
3. **Time-axis heights:** each period's height is `max(minPeriodH, events × rowH)`, i.e. proportional to how many events it holds, not to its duration. The axis stays monotonic and readable, and empty periods still get a minimum height.
4. **Life-lane icons:** life-lane events get an `icon` field (an emoji), which the spec's "strip of icons" needs.
5. **Review table format:** the review table is CSV (UTF-8 with BOM, so Excel shows Thai correctly) plus Markdown, not .xlsx.
6. **Module APIs:** `card` also exposes `hide()` and `refresh()`, and `globe.showSlice()` returns `{age, exact, lonlat}` for the latitude readout.

## Global Constraints

- **Project root:** `/Users/songkhunboonchaisuk/Downloads/_Projects/MU/deep-time/`. It is its own git repo, because the parent folder is not a repo. All paths below are relative to it.
- **Page:** the page title is exactly `Deep Time Kanchanaburi`. Thai is the default language, with an English toggle; the choice is stored in `localStorage` key `dt-lang` and every access is wrapped in try/catch.
- **Plate model:** `MULLER2022` via `https://gws.gplates.org`. Present-day reference point: Kanchanaburi town, lon 99.53, lat 14.02.
- **Slice ages (fixed):** `[470, 430, 400, 360, 320, 290, 270, 250, 230, 200, 150, 100, 66, 40, 20, 5, 0]`.
- **Size limits:** each slice ≤ 100,000 bytes; `dist/index.html` ≤ 3,000,000 bytes.
- **No runtime network requests:** no `<script src>`, no external stylesheet and no web fonts. Thai uses the system font stack `"Noto Sans Thai","Thonburi","Leelawadee UI",system-ui,sans-serif`.
- **Time scale:** ICS chart v2024/12 boundaries in official ICS colours. The youngest period ends at 0 Ma.
- **Lecture mode:** about 8 events with `lecture_stop: true`, text scaled to 1.4×, arrow-key navigation.
- **Verification:** every event starts with `verified: false`. Unverified events show a "draft" (ร่าง) badge, and `assemble.py --strict` refuses to build while any remain.
- **Light and dark themes:** colours are defined as tokens on `:root`, redefined under `@media (prefers-color-scheme: dark)` with `:root:not([data-theme="light"])`, and again under `:root[data-theme="dark"]`. `body` has an explicit background.
- **Commits:** every commit message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Polygon winding.** GPlates returns standard GeoJSON winding (counter-clockwise exteriors), but d3-geo treats that as "everything except the land", so the globe would paint the oceans as land. Expected: land is filled. Pinned by the `normalizeWinding` tests in Task 3.
2. **Event text containing `</script>`, `<`, `&` or quotes.** Expected: the page still loads, and the text shows literally with no HTML injection. Pinned by the `</` escaping test in Task 4 and the `esc()` test in Task 3.
3. **Scrolling to the very first or last event.** Expected: the first or last event becomes active and is never skipped. Pinned by the `activeIndex` extreme-position tests in Task 3.
4. **Globe moving across the antimeridian** (for example from lon 170 to −170). Expected: it rotates 20° the short way, not 340°. Pinned by the `shortestLonDelta` tests in Task 3.
5. **Storage unavailable** (Safari private mode, or blocked site data, where `getItem` throws). Expected: the page loads in Thai and the language toggle still works. Pinned by the `initLang` throwing-storage test in Task 3.

---

## File Structure

```
deep-time/
  .gitignore
  package.json               # {"type":"module"} + "test" script for node --test
  pytest.ini                 # pythonpath = build
  content/
    timescale.json           # ICS periods (Task 1)
    events.json              # event content (starter in Task 1, full draft in Task 6)
  build/
    validate.py              # schema checks for events and timescale (Task 1)
    paleo.py                 # simplification + GPlates fetch + atomic write (Task 2)
    fetch_paleo.py           # CLI: fetch the missing slices (Task 2)
    paleo_report.py          # CLI: paleo-latitude table + 0 Ma sanity check (Task 2)
    assemble.py              # CLI: build dist/index.html (Task 4)
    review_table.py          # CLI: review CSV/MD for the instructor (Task 6)
  paleo/<age>.json           # generated slices (committed)
  vendor/d3.min.js           # D3 7.9.0 (Task 1)
  src/
    i18n.js                  # strings, t(), field(), language state (Task 3)
    format.js                # formatAge, formatLat, esc (Task 3)
    layout.js                # periodOf, layoutTimeline (Task 3)
    select.js                # activeIndex, nearestSlice (Task 3)
    geo.js                   # shortestLonDelta, normalizeWinding (Task 3)
    globe.js                 # canvas globe (Task 5)
    timeline.js              # lanes, scrolling, active event (Task 5)
    card.js                  # event card + lecture navigation (Task 5)
    main.js                  # glue (Task 5)
    index.html               # page template with placeholders (Task 5)
    style.css                # tokens, layout, light/dark (Task 5)
  tests/
    test_validate.py  test_paleo.py  test_assemble.py  test_review_table.py
    js/i18n.test.js  js/format.test.js  js/layout.test.js  js/select.test.js  js/geo.test.js
  review/                    # generated review table (git-ignored)
  dist/index.html            # build output (git-ignored)
```

Module concatenation order in `assemble.py`: `i18n.js, format.js, layout.js, select.js, geo.js, globe.js, timeline.js, card.js, main.js`.

Module rules, which `assemble.py` enforces:
- Imports must be single-line `import { a, b } from './x.js';`.
- Exports must be `export function|const|let|class` only.
- Top-level names must be unique across all modules.

---

### Task 1: Scaffold, time scale, starter content and validator

**Files:**
- Create: `.gitignore`, `package.json`, `pytest.ini`, `vendor/d3.min.js`, `content/timescale.json`, `content/events.json`, `build/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Produces:
  - `validate_timescale(periods: list[dict]) -> list[str]` returns error strings; empty means valid.
  - `validate_events(events: list[dict], periods: list[dict], slice_ages: set[float] | None = None) -> list[str]`
  - `load_json(path) -> Any`
  - Constant `LANES = {"local", "world", "life"}`
- Event fields:
  - `id`, `lane`, `age_ma`, `age_uncertainty_ma`, `title_th`, `title_en`
  - `body_th`, `body_en`, `rock_unit`, `visit_site` (`{name_th, name_en, lat, lon}` or null)
  - `citation` (`{text, url}` or null), `icon` (life lane only)
  - `paleo_age`, `lecture_stop`, `verified`
- Period fields: `id`, `name_th`, `name_en`, `start_ma`, `end_ma`, `color`.

- [ ] **Step 1: Scaffold the repo and vendor D3**

```bash
mkdir -p /Users/songkhunboonchaisuk/Downloads/_Projects/MU/deep-time/{content,build,paleo,vendor,src,tests/js,review,dist}
cd /Users/songkhunboonchaisuk/Downloads/_Projects/MU/deep-time
git init
curl -sL https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js -o vendor/d3.min.js
head -c 80 vendor/d3.min.js; echo; wc -c vendor/d3.min.js
```
Expected: the header mentions `d3js.org v7.9.0`, and the size is above 200,000 bytes.

Create `.gitignore`:
```
dist/
review/
__pycache__/
.pytest_cache/
*.json.tmp
.DS_Store
```

Create `package.json`:
```json
{
  "name": "deep-time-kanchanaburi",
  "private": true,
  "type": "module",
  "scripts": { "test": "node --test tests/js/" }
}
```

Create `pytest.ini`:
```ini
[pytest]
pythonpath = build
testpaths = tests
```

- [ ] **Step 2: Write `content/timescale.json`**

```json
[
  {"id": "ordovician", "name_th": "ยุคออร์โดวิเชียน", "name_en": "Ordovician", "start_ma": 486.85, "end_ma": 443.1, "color": "#009270"},
  {"id": "silurian", "name_th": "ยุคไซลูเรียน", "name_en": "Silurian", "start_ma": 443.1, "end_ma": 419.62, "color": "#B3E1B6"},
  {"id": "devonian", "name_th": "ยุคดีโวเนียน", "name_en": "Devonian", "start_ma": 419.62, "end_ma": 358.86, "color": "#CB8C37"},
  {"id": "carboniferous", "name_th": "ยุคคาร์บอนิเฟอรัส", "name_en": "Carboniferous", "start_ma": 358.86, "end_ma": 298.9, "color": "#67A599"},
  {"id": "permian", "name_th": "ยุคเพอร์เมียน", "name_en": "Permian", "start_ma": 298.9, "end_ma": 251.902, "color": "#F04028"},
  {"id": "triassic", "name_th": "ยุคไทรแอสซิก", "name_en": "Triassic", "start_ma": 251.902, "end_ma": 201.4, "color": "#812B92"},
  {"id": "jurassic", "name_th": "ยุคจูแรสซิก", "name_en": "Jurassic", "start_ma": 201.4, "end_ma": 143.1, "color": "#34B2C9"},
  {"id": "cretaceous", "name_th": "ยุคครีเทเชียส", "name_en": "Cretaceous", "start_ma": 143.1, "end_ma": 66.0, "color": "#7FC64E"},
  {"id": "paleogene", "name_th": "ยุคพาลีโอจีน", "name_en": "Paleogene", "start_ma": 66.0, "end_ma": 23.04, "color": "#FD9A52"},
  {"id": "neogene", "name_th": "ยุคนีโอจีน", "name_en": "Neogene", "start_ma": 23.04, "end_ma": 2.58, "color": "#FFE619"},
  {"id": "quaternary", "name_th": "ยุคควอเทอร์นารี", "name_en": "Quaternary", "start_ma": 2.58, "end_ma": 0, "color": "#F9F97F"}
]
```
Then check every boundary age and colour against the ICS chart v2024/12 (https://stratigraphy.org/chart) and correct any value that differs.

- [ ] **Step 3: Write `content/events.json` with three starter events**

```json
[
  {
    "id": "ratburi-limestone", "lane": "local", "age_ma": 270, "age_uncertainty_ma": 15,
    "title_th": "หินปูนกลุ่มราชบุรี", "title_en": "Ratburi limestone",
    "body_th": "หินปูนกลุ่มราชบุรีสะสมตัวในทะเลตื้นที่อบอุ่นในยุคเพอร์เมียน ขณะที่แผ่นซีบูมาสุ (Sibumasu) เคลื่อนออกจากขอบมหาทวีปกอนด์วานา ปัจจุบันหินปูนนี้เป็นภูเขาหินปูนและถ้ำจำนวนมากในกาญจนบุรี",
    "body_en": "Ratburi Group limestone built up in warm, shallow seas during the Permian, as the Sibumasu block drifted away from Gondwana. Today it forms many of Kanchanaburi's limestone hills and caves.",
    "rock_unit": "Ratburi Group (กลุ่มหินราชบุรี)", "visit_site": null,
    "citation": {"text": "Ridd, Barber & Crow (eds) 2011, The Geology of Thailand, Geological Society of London", "url": "https://doi.org/10.1144/GOTH"},
    "paleo_age": 270, "lecture_stop": true, "verified": false
  },
  {
    "id": "end-permian-extinction", "lane": "world", "age_ma": 251.94, "age_uncertainty_ma": 0.04,
    "title_th": "การสูญพันธุ์ครั้งใหญ่ปลายยุคเพอร์เมียน", "title_en": "End-Permian mass extinction",
    "body_th": "การสูญพันธุ์ครั้งใหญ่ที่สุดในประวัติโลก สิ่งมีชีวิตในทะเลราวร้อยละ 90 หายไป สัมพันธ์กับการปะทุของภูเขาไฟไซบีเรียนแทรปส์ (Siberian Traps)",
    "body_en": "The largest mass extinction in Earth's history: about 90% of marine species disappeared, linked to the Siberian Traps eruptions.",
    "rock_unit": null, "visit_site": null,
    "citation": {"text": "Burgess, Bowring & Shen 2014, PNAS 111:3316–3321", "url": "https://doi.org/10.1073/pnas.1317692111"},
    "paleo_age": 250, "lecture_stop": false, "verified": false
  },
  {
    "id": "first-dinosaurs", "lane": "life", "age_ma": 233, "age_uncertainty_ma": null,
    "title_th": "ไดโนเสาร์กลุ่มแรก", "title_en": "First dinosaurs",
    "body_th": "", "body_en": "", "icon": "🦕",
    "rock_unit": null, "visit_site": null, "citation": null,
    "paleo_age": 230, "lecture_stop": false, "verified": false
  }
]
```

- [ ] **Step 4: Write the failing tests `tests/test_validate.py`**

```python
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
    ({"age_ma": 500}, "age_ma"),
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
```

- [ ] **Step 5: Run the tests to verify they fail**

Run: `cd deep-time && python3 -m pytest tests/test_validate.py -q`
Expected: collection error `ModuleNotFoundError: No module named 'validate'`.

- [ ] **Step 6: Implement `build/validate.py`**

```python
"""Schema checks for Deep Time content. Each function returns a list of error strings."""
import json
import re
from pathlib import Path

LANES = {"local", "world", "life"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
URL_RE = re.compile(r"^https?://\S+$")
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _text(x):
    return isinstance(x, str) and x.strip() != ""


def validate_timescale(periods):
    if not periods:
        return ["timescale is empty"]
    errors, ids = [], set()
    for p in periods:
        pid = p.get("id", "?")
        for key in ("id", "name_th", "name_en", "color"):
            if not _text(p.get(key)):
                errors.append(f"period {pid}: missing {key}")
        if _text(p.get("color")) and not HEX_RE.match(p["color"]):
            errors.append(f"period {pid}: color must be #RRGGBB")
        if not (_num(p.get("start_ma")) and _num(p.get("end_ma")) and p["start_ma"] > p["end_ma"] >= 0):
            errors.append(f"period {pid}: start_ma must be > end_ma >= 0")
        if pid in ids:
            errors.append(f"period {pid}: duplicate id")
        ids.add(pid)
    ordered = sorted(
        (p for p in periods if _num(p.get("start_ma")) and _num(p.get("end_ma"))),
        key=lambda p: -p["start_ma"],
    )
    for older, younger in zip(ordered, ordered[1:]):
        if abs(older["end_ma"] - younger["start_ma"]) > 1e-9:
            errors.append(f"gap or overlap between {older['id']} and {younger['id']}")
    if ordered and ordered[-1]["end_ma"] != 0:
        errors.append("youngest period must end at 0 Ma")
    return errors


def validate_events(events, periods, slice_ages=None):
    errors, seen = [], set()
    oldest = max((p["start_ma"] for p in periods), default=541)
    for i, e in enumerate(events):
        eid = e.get("id", f"#{i}")

        def err(msg):
            errors.append(f"{eid}: {msg}")

        if not isinstance(e.get("id"), str) or not ID_RE.match(e["id"]):
            err("id must be kebab-case")
        elif e["id"] in seen:
            err("duplicate id")
        else:
            seen.add(e["id"])

        lane = e.get("lane")
        if lane not in LANES:
            err(f"lane must be one of {sorted(LANES)}")

        age = e.get("age_ma")
        if not _num(age) or age < 0 or age >= oldest:
            err(f"age_ma must be in [0, {oldest})")
        unc = e.get("age_uncertainty_ma")
        if unc is not None and (not _num(unc) or unc < 0):
            err("age_uncertainty_ma must be null or >= 0")

        for key in ("title_th", "title_en"):
            if not _text(e.get(key)):
                err(f"{key} is empty")

        if lane == "life":
            if not _text(e.get("icon")):
                err("life events need an icon")
        else:
            for key in ("body_th", "body_en"):
                if not _text(e.get(key)):
                    err(f"{key} is empty")
            c = e.get("citation")
            if not (isinstance(c, dict) and _text(c.get("text"))
                    and isinstance(c.get("url"), str) and URL_RE.match(c["url"])):
                err("citation needs text and an http(s) url")

        if e.get("rock_unit") is not None and not _text(e.get("rock_unit")):
            err("rock_unit must be null or text")

        site = e.get("visit_site")
        if site is not None:
            if not (isinstance(site, dict) and _text(site.get("name_th")) and _text(site.get("name_en"))):
                err("visit_site needs name_th and name_en")
            elif not (_num(site.get("lat")) and -90 <= site["lat"] <= 90
                      and _num(site.get("lon")) and -180 <= site["lon"] <= 180):
                err("visit_site lat/lon out of range")

        pa = e.get("paleo_age")
        if not _num(pa):
            err("paleo_age must be a number")
        elif slice_ages is not None and pa not in slice_ages:
            err(f"no paleo slice for paleo_age {pa}")

        for key in ("lecture_stop", "verified"):
            if not isinstance(e.get(key), bool):
                err(f"{key} must be true or false")
    return errors
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `python3 -m pytest tests/test_validate.py -q`
Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: scaffold project, ICS time scale, starter content and validator" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Paleo slices from GPlates

**Files:**
- Create: `build/paleo.py`, `build/fetch_paleo.py`, `build/paleo_report.py`, `paleo/*.json` (generated)
- Test: `tests/test_paleo.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces:
  - Constants: `SLICE_AGES: list[int]`, `KANCHANABURI = (99.53, 14.02)`, `MODEL = "MULLER2022"`, `MAX_SLICE_BYTES = 100_000`.
  - `simplify_line(points, tol) -> list[tuple]`
  - `simplify_geojson(fc, tol=0.5, ndigits=1) -> dict` returns a FeatureCollection of Polygon/MultiPolygon features.
  - `fetch_slice(age, session) -> dict` returns `{"age", "model", "kanchanaburi": [lon, lat], "coastlines": FeatureCollection}`.
  - `write_slice_atomic(path, slice_dict)`
  - `fetch_all(out_dir, session, ages) -> int` returns 0 on success, 1 on the first failure.
  - `load_slices(paleo_dir) -> dict[str, dict]`, keyed by `str(age)`.
  - `check_present(slices) -> str | None` returns an error message or None.
  - The slice file format is consumed by Task 4 (`assemble.py`) and Task 5 (`globe.js`).

- [ ] **Step 1: Write the failing tests `tests/test_paleo.py`**

```python
import json

import pytest

import paleo
from paleo import (KANCHANABURI, check_present, fetch_all, fetch_slice, load_slices,
                   simplify_geojson, simplify_line)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status = payload, status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    def json(self):
        return self.payload


SQUARE = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {
    "type": "Polygon", "coordinates": [[[0, 0], [5, 0.01], [10, 0], [10, 10], [0, 10], [0, 0]]]}}]}


class FakeSession:
    def __init__(self, fail_age=None):
        self.fail_age, self.calls = fail_age, []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        if params["time"] == self.fail_age:
            return FakeResponse({}, status=503)
        if "reconstruct_points" in url:
            return FakeResponse({"type": "MultiPoint", "coordinates": [[88.1234, -37.4487]]})
        return FakeResponse(SQUARE)


def test_simplify_line_drops_near_collinear_points():
    pts = [(0, 0), (5, 0.01), (10, 0)]
    assert simplify_line(pts, 0.1) == [(0, 0), (10, 0)]


def test_simplify_line_keeps_far_points():
    pts = [(0, 0), (5, 3), (10, 0)]
    assert simplify_line(pts, 0.1) == pts


def test_simplify_geojson_keeps_closed_rings_and_rounds():
    out = simplify_geojson(SQUARE, tol=0.1, ndigits=1)
    ring = out["features"][0]["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]
    assert [5, 0.0] not in ring
    assert len(ring) == 5


def test_simplify_geojson_drops_degenerate_rings():
    tiny = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {
        "type": "Polygon", "coordinates": [[[0, 0], [0.01, 0], [0.01, 0.01], [0, 0]]]}}]}
    assert simplify_geojson(tiny, tol=0.5)["features"] == []


def test_simplify_geojson_handles_multipolygon():
    multi = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {
        "type": "MultiPolygon", "coordinates": [SQUARE["features"][0]["geometry"]["coordinates"]] * 2}}]}
    geom = simplify_geojson(multi, tol=0.1)["features"][0]["geometry"]
    assert geom["type"] == "MultiPolygon" and len(geom["coordinates"]) == 2


def test_fetch_slice_shape():
    s = fetch_slice(270, FakeSession())
    assert s["age"] == 270 and s["model"] == "MULLER2022"
    assert s["kanchanaburi"] == [88.12, -37.45]
    assert s["coastlines"]["type"] == "FeatureCollection"


def test_fetch_slice_queries_kanchanaburi():
    session = FakeSession()
    fetch_slice(270, session)
    point_call = [c for c in session.calls if "reconstruct_points" in c[0]][0]
    assert point_call[1]["points"] == f"{KANCHANABURI[0]},{KANCHANABURI[1]}"


def test_fetch_all_stops_on_failure_and_names_age(tmp_path, capsys):
    code = fetch_all(tmp_path, FakeSession(fail_age=250), [270, 250, 230])
    assert code == 1
    assert (tmp_path / "270.json").exists()
    assert not (tmp_path / "250.json").exists()
    assert not (tmp_path / "230.json").exists()
    assert "250" in capsys.readouterr().err


def test_fetch_all_skips_existing(tmp_path):
    (tmp_path / "270.json").write_text("{}", encoding="utf-8")
    session = FakeSession()
    assert fetch_all(tmp_path, session, [270]) == 0
    assert session.calls == []


def test_slice_size_limit_enforced(monkeypatch):
    monkeypatch.setattr(paleo, "MAX_SLICE_BYTES", 10)
    with pytest.raises(paleo.SliceTooLargeError):
        fetch_slice(270, FakeSession())


def test_load_slices_and_check_present(tmp_path):
    for age, pt in [(0, [99.53, 14.02]), (270, [88.1, -37.4])]:
        (tmp_path / f"{age}.json").write_text(json.dumps({"age": age, "kanchanaburi": pt}), encoding="utf-8")
    slices = load_slices(tmp_path)
    assert set(slices) == {"0", "270"}
    assert check_present(slices) is None
    slices["0"]["kanchanaburi"] = [98.0, 14.02]
    assert "0 Ma" in check_present(slices)
    del slices["0"]
    assert "missing" in check_present(slices)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/test_paleo.py -q`
Expected: `ModuleNotFoundError: No module named 'paleo'`.

- [ ] **Step 3: Implement `build/paleo.py`**

```python
"""Fetch and simplify paleogeographic slices from the GPlates Web Service."""
import json
import math
import os
import sys
from pathlib import Path

GWS_URL = "https://gws.gplates.org"
MODEL = "MULLER2022"
KANCHANABURI = (99.53, 14.02)
SLICE_AGES = [470, 430, 400, 360, 320, 290, 270, 250, 230, 200, 150, 100, 66, 40, 20, 5, 0]
MAX_SLICE_BYTES = 100_000


class SliceTooLargeError(Exception):
    pass


def _seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def simplify_line(points, tol):
    """Douglas–Peucker in lon/lat degrees. Endpoints are always kept."""
    points = list(points)
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        dmax, idx = 0.0, None
        for i in range(start + 1, end):
            d = _seg_dist(points[i], points[start], points[end])
            if d > dmax:
                dmax, idx = d, i
        if idx is not None and dmax > tol:
            keep[idx] = True
            stack.extend([(start, idx), (idx, end)])
    return [p for p, k in zip(points, keep) if k]


def _clean_ring(ring, tol, ndigits):
    pts = simplify_line([(p[0], p[1]) for p in ring], tol)
    out = []
    for x, y in pts:
        q = [round(x, ndigits), round(y, ndigits)]
        if not out or out[-1] != q:
            out.append(q)
    if out and out[0] != out[-1]:
        out.append(list(out[0]))
    return out if len(out) >= 4 else None


def simplify_geojson(fc, tol=0.5, ndigits=1):
    features = []
    for f in fc.get("features", []):
        g = f.get("geometry") or {}
        if g.get("type") == "Polygon":
            polys = [g["coordinates"]]
        elif g.get("type") == "MultiPolygon":
            polys = g["coordinates"]
        else:
            continue
        out_polys = []
        for poly in polys:
            if not poly:
                continue
            outer = _clean_ring(poly[0], tol, ndigits)
            if outer is None:
                continue
            holes = [r for r in (_clean_ring(h, tol, ndigits) for h in poly[1:]) if r]
            out_polys.append([outer] + holes)
        if not out_polys:
            continue
        geom = ({"type": "Polygon", "coordinates": out_polys[0]} if len(out_polys) == 1
                else {"type": "MultiPolygon", "coordinates": out_polys})
        features.append({"type": "Feature", "properties": {}, "geometry": geom})
    return {"type": "FeatureCollection", "features": features}


def fetch_slice(age, session, base_url=GWS_URL, model=MODEL, timeout=90):
    lon, lat = KANCHANABURI
    r = session.get(f"{base_url}/reconstruct/reconstruct_points/",
                    params={"points": f"{lon},{lat}", "time": age, "model": model}, timeout=timeout)
    r.raise_for_status()
    px, py = r.json()["coordinates"][0]
    r = session.get(f"{base_url}/reconstruct/coastlines/",
                    params={"time": age, "model": model}, timeout=timeout)
    r.raise_for_status()
    raw = r.json()
    tol = 0.3
    for _ in range(8):
        sl = {"age": age, "model": model, "kanchanaburi": [round(px, 2), round(py, 2)],
              "coastlines": simplify_geojson(raw, tol=tol, ndigits=1)}
        if len(json.dumps(sl, separators=(",", ":")).encode("utf-8")) <= MAX_SLICE_BYTES:
            return sl
        tol *= 1.5
    raise SliceTooLargeError(f"slice {age} Ma is still over {MAX_SLICE_BYTES} bytes after simplification")


def write_slice_atomic(path, sl):
    path = Path(path)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(sl, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


def fetch_all(out_dir, session, ages):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for age in ages:
        path = out_dir / f"{age}.json"
        if path.exists():
            print(f"skip {age} Ma (exists)")
            continue
        try:
            sl = fetch_slice(age, session)
        except Exception as exc:  # noqa: BLE001 — report any failure with its age
            print(f"ERROR: slice {age} Ma failed: {exc}", file=sys.stderr)
            return 1
        write_slice_atomic(path, sl)
        print(f"wrote {age} Ma ({path.stat().st_size // 1024} KB), Kanchanaburi at {sl['kanchanaburi']}")
    return 0


def load_slices(paleo_dir):
    slices = {}
    for p in sorted(Path(paleo_dir).glob("*.json")):
        sl = json.loads(p.read_text(encoding="utf-8"))
        slices[str(sl["age"])] = sl
    return slices


def check_present(slices):
    present = slices.get("0")
    if present is None:
        return "0 Ma slice is missing"
    lon, lat = present["kanchanaburi"]
    if abs(lon - KANCHANABURI[0]) > 0.05 or abs(lat - KANCHANABURI[1]) > 0.05:
        return f"0 Ma Kanchanaburi position {present['kanchanaburi']} != {list(KANCHANABURI)}"
    return None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/test_paleo.py -q`
Expected: all pass.

- [ ] **Step 5: Add the CLIs**

`build/fetch_paleo.py`:
```python
"""Fetch any missing paleo slices into paleo/. Usage: python3 build/fetch_paleo.py"""
import sys
from pathlib import Path

import requests

from paleo import SLICE_AGES, fetch_all

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    sys.exit(fetch_all(root / "paleo", requests.Session(), SLICE_AGES))
```

`build/paleo_report.py`:
```python
"""Print Kanchanaburi's paleo-position per slice for the instructor's science check."""
import sys
from pathlib import Path

from paleo import check_present, load_slices

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    slices = load_slices(root / "paleo")
    print(f"{'age (Ma)':>9}  {'lon':>8}  {'lat':>7}  hemisphere")
    for key in sorted(slices, key=lambda k: -float(k)):
        lon, lat = slices[key]["kanchanaburi"]
        print(f"{key:>9}  {lon:>8.2f}  {lat:>7.2f}  {'S' if lat < 0 else 'N'}")
    problem = check_present(slices)
    if problem:
        print(f"FAIL: {problem}", file=sys.stderr)
        sys.exit(1)
    print("OK: 0 Ma position matches Kanchanaburi town")
```

The CLIs import `paleo` directly. Run them from the project root as `python3 build/<script>.py`; Python puts the script's own folder on `sys.path`, so the import resolves.

- [ ] **Step 6: Fetch the real slices and run the science check (needs network)**

Run: `python3 build/fetch_paleo.py && python3 build/paleo_report.py && du -ch paleo/*.json | tail -1`

Expected:
- 17 files are written, each ≤ 100 KB, totalling about 1.7 MB or less.
- The report ends with `OK`.

Check the latitude trend against the literature:
- southern mid-latitudes around 290–270 Ma (the 270 Ma value was ≈ −37° when the service was probed on 2026-10-01)
- moving north to near the equator by about 230–200 Ma
- 14.02°N at 0 Ma

If any slice fails, re-run; existing slices are skipped. If the trend looks wrong, stop and report it before continuing.

- [ ] **Step 7: Commit**

```bash
git add build/paleo.py build/fetch_paleo.py build/paleo_report.py tests/test_paleo.py paleo/
git commit -m "feat: fetch and simplify GPlates paleo slices with science check" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Pure browser logic (i18n, formatting, layout, selection, geo)

**Files:**
- Create: `src/i18n.js`, `src/format.js`, `src/layout.js`, `src/select.js`, `src/geo.js`
- Test: `tests/js/i18n.test.js`, `tests/js/format.test.js`, `tests/js/layout.test.js`, `tests/js/select.test.js`, `tests/js/geo.test.js`

**Interfaces:**
- Produces (exact exports):
  - **i18n.js:**
    - `initLang(storage) -> 'th'|'en'`, `getLang()`, `setLang(lang)`, `onLangChange(fn)`
    - `t(key) -> string`: current language, then English, then the key itself.
    - `field(obj, base) -> string`: `obj[base_<lang>]`, falling back to `obj[base_en]`, then `''`.
    - `I18N_STRINGS` (object `{th, en}`)
  - **format.js:**
    - `PRESENT_YEAR = 2026`
    - `formatAge(ma, unc, lang, presentYear = PRESENT_YEAR) -> string`
    - `formatLat(lat) -> string`
    - `esc(s) -> string`
  - **layout.js:**
    - `periodOf(age, periods) -> period | null`
    - `layoutTimeline(events, periods, {rowH, minPeriodH}) -> {rows: [{event, y}], bands: [{period, y, h}], height}`
  - **select.js:**
    - `activeIndex(rows, centerY, rowH) -> number` (−1 if there are no rows)
    - `nearestSlice(age, sliceAges) -> {age, exact}`
  - **geo.js:**
    - `shortestLonDelta(from, to) -> number` in (−180, 180]
    - `normalizeWinding(fc, geoArea) -> fc`, where `geoArea` is `d3.geoArea`

- [ ] **Step 1: Write the failing tests**

`tests/js/i18n.test.js`:
```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { initLang, getLang, setLang, onLangChange, t, field, I18N_STRINGS } from '../../src/i18n.js';

const memory = () => { const m = {}; return { getItem: k => m[k] ?? null, setItem: (k, v) => { m[k] = v; } }; };

test('defaults to Thai with no storage', () => {
  assert.equal(initLang(null), 'th');
});

test('throwing storage still loads in Thai and toggling works', () => {
  const bad = { getItem() { throw new Error('SecurityError'); }, setItem() { throw new Error('SecurityError'); } };
  assert.equal(initLang(bad), 'th');
  setLang('en');
  assert.equal(getLang(), 'en');
});

test('remembers language in storage', () => {
  const s = memory();
  initLang(s);
  setLang('en');
  assert.equal(initLang(s), 'en');
});

test('ignores unknown languages and notifies listeners', () => {
  initLang(null);
  let seen = null;
  onLangChange(l => { seen = l; });
  setLang('fr');
  assert.equal(getLang(), 'th');
  setLang('en');
  assert.equal(seen, 'en');
});

test('t falls back to the key for unknown strings', () => {
  initLang(null);
  assert.equal(t('no_such_key'), 'no_such_key');
});

test('every English key has a Thai string', () => {
  for (const k of Object.keys(I18N_STRINGS.en)) assert.ok(I18N_STRINGS.th[k], k);
});

test('field falls back to English when Thai is missing', () => {
  initLang(null);
  assert.equal(field({ title_en: 'Limestone' }, 'title'), 'Limestone');
  assert.equal(field({ title_th: 'หินปูน', title_en: 'Limestone' }, 'title'), 'หินปูน');
  assert.equal(field({}, 'title'), '');
});
```

`tests/js/format.test.js`:
```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { formatAge, formatLat, esc } from '../../src/format.js';

test('deep time ages in Ma', () => {
  assert.equal(formatAge(270, 15, 'en'), '270 ± 15 Ma');
  assert.equal(formatAge(270, 15, 'th'), '270 ± 15 ล้านปีก่อน');
  assert.equal(formatAge(251.94, null, 'en'), '251.9 Ma');
});

test('prehistoric ages in years ago', () => {
  assert.equal(formatAge(0.004, null, 'en'), '≈4,000 years ago');
  assert.equal(formatAge(0.004, null, 'th'), '≈4,000 ปีก่อน');
});

test('historic ages as calendar years', () => {
  assert.equal(formatAge(0.000083, null, 'en', 2026), '1943 CE');
  assert.equal(formatAge(0.000083, null, 'th', 2026), 'พ.ศ. 2486 (ค.ศ. 1943)');
});

test('present', () => {
  assert.equal(formatAge(0, null, 'en'), 'Present');
  assert.equal(formatAge(0, null, 'th'), 'ปัจจุบัน');
});

test('latitude readout', () => {
  assert.equal(formatLat(-37.45), '≈37°S');
  assert.equal(formatLat(14.02), '≈14°N');
});

test('esc neutralises HTML', () => {
  assert.equal(esc('<script>"a" & \'b\'</script>'), '&lt;script&gt;&quot;a&quot; &amp; &#39;b&#39;&lt;/script&gt;');
  assert.equal(esc(null), '');
});
```

`tests/js/layout.test.js`:
```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { periodOf, layoutTimeline } from '../../src/layout.js';

const periods = JSON.parse(readFileSync(new URL('../../content/timescale.json', import.meta.url), 'utf8'));
const ev = (id, age) => ({ id, age_ma: age });

test('periodOf boundaries: base age belongs to the older period', () => {
  assert.equal(periodOf(251.94, periods).id, 'permian');
  assert.equal(periodOf(251.902, periods).id, 'permian');
  assert.equal(periodOf(251.9, periods).id, 'triassic');
  assert.equal(periodOf(0, periods).id, 'quaternary');
  assert.equal(periodOf(500, periods), null);
});

test('layout orders oldest first and never overlaps', () => {
  const events = [ev('b', 270), ev('a', 470), ev('c', 0.004), ev('d', 0), ev('e', 280)];
  const { rows, bands, height } = layoutTimeline(events, periods, { rowH: 50, minPeriodH: 120 });
  assert.deepEqual(rows.map(r => r.event.id), ['a', 'e', 'b', 'c', 'd']);
  for (let i = 1; i < rows.length; i++) assert.ok(rows[i].y >= rows[i - 1].y + 50);
  assert.equal(bands.length, periods.length);
  assert.ok(bands.every(b => b.h >= 120));
  assert.equal(height, bands.reduce((s, b) => s + b.h, 0));
});

test('busy period grows beyond the minimum', () => {
  const events = [ev('p1', 290), ev('p2', 280), ev('p3', 270)];
  const { bands } = layoutTimeline(events, periods, { rowH: 50, minPeriodH: 120 });
  assert.equal(bands.find(b => b.period.id === 'permian').h, 150);
});

test('event outside the time scale throws with its id', () => {
  assert.throws(() => layoutTimeline([ev('too-old', 600)], periods), /too-old/);
});
```

`tests/js/select.test.js`:
```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { activeIndex, nearestSlice } from '../../src/select.js';

const rows = [{ y: 0 }, { y: 50 }, { y: 100 }];

test('activeIndex picks the row whose centre is nearest', () => {
  assert.equal(activeIndex(rows, 74, 50), 1);
  assert.equal(activeIndex(rows, 126, 50), 2);
});

test('activeIndex clamps at the extremes', () => {
  assert.equal(activeIndex(rows, -500, 50), 0);
  assert.equal(activeIndex(rows, 99999, 50), 2);
  assert.equal(activeIndex([], 10, 50), -1);
});

test('nearestSlice exact and approximate', () => {
  const ages = [0, 5, 20, 270, 290];
  assert.deepEqual(nearestSlice(270, ages), { age: 270, exact: true });
  assert.deepEqual(nearestSlice(275, ages), { age: 270, exact: false });
  assert.deepEqual(nearestSlice(0.004, ages), { age: 0, exact: false });
  assert.throws(() => nearestSlice(10, []));
});
```

`tests/js/geo.test.js`:
```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { shortestLonDelta, normalizeWinding } from '../../src/geo.js';

// d3.min.js is a UMD script; run it as a classic script so it sets `d3` on the sandbox global.
const sandbox = vm.createContext({});
vm.runInContext(readFileSync(new URL('../../vendor/d3.min.js', import.meta.url), 'utf8'), sandbox);
const d3 = sandbox.d3;

test('shortestLonDelta takes the short way across the antimeridian', () => {
  assert.equal(shortestLonDelta(170, -170), 20);
  assert.equal(shortestLonDelta(-170, 170), -20);
  assert.equal(shortestLonDelta(0, 90), 90);
  assert.equal(shortestLonDelta(10, 10), 0);
});

const ccw = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]];
const fc = ring => ({ type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [ring] } }] });

test('normalizeWinding flips RFC 7946 rings so d3 fills the land, not the ocean', () => {
  assert.ok(d3.geoArea(fc(ccw)) > 2 * Math.PI);
  const fixed = normalizeWinding(fc(ccw), d3.geoArea);
  assert.ok(d3.geoArea(fixed) < 0.1);
});

test('normalizeWinding leaves correct rings and handles MultiPolygon', () => {
  const cw = [...ccw].reverse();
  assert.deepEqual(normalizeWinding(fc(cw), d3.geoArea).features[0].geometry.coordinates[0], cw);
  const multi = { type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: { type: 'MultiPolygon', coordinates: [[ccw], [cw]] } }] };
  assert.ok(d3.geoArea(normalizeWinding(multi, d3.geoArea)) < 0.2);
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test`
Expected: FAIL with `Cannot find module '.../src/i18n.js'` (and similarly for the others).

- [ ] **Step 3: Implement `src/i18n.js`**

```js
export const I18N_STRINGS = {
  th: {
    app_title: 'ย้อนเวลาธรณีกาญจนบุรี',
    app_subtitle: 'ประวัติธรณีวิทยากาญจนบุรีเทียบกับโลก บนลูกโลกยุคโบราณ',
    btn_lecture: 'โหมดบรรยาย',
    btn_about: 'เกี่ยวกับ',
    btn_lang: 'English',
    lane_period: 'ยุค',
    lane_local: 'กาญจนบุรี',
    lane_world: 'เอเชียตะวันออกเฉียงใต้และโลก',
    lane_life: 'ชีวิต',
    draft: 'ร่าง',
    visit: 'ดูของจริงได้ที่',
    source: 'ที่มา',
    approx_slice: 'ตำแหน่งจากแบบจำลองช่วงอายุใกล้เคียง',
    paleo_label: 'กาญจนบุรีอยู่ที่',
    ma_short: 'ล้านปีก่อน',
    prev: 'ก่อนหน้า',
    next: 'ถัดไป',
    close: 'ปิด',
    globe_label: 'ลูกโลกแสดงตำแหน่งกาญจนบุรีในอดีต',
    about_title: 'เกี่ยวกับหน้านี้',
    about_intro: 'สื่อการสอนของสาขาวิชาธรณีศาสตร์ มหาวิทยาลัยมหิดล วิทยาเขตกาญจนบุรี เลื่อนเส้นเวลาเพื่อดูว่ากาญจนบุรีอยู่ที่ใดบนโลกในแต่ละยุค',
    credit_model: 'แบบจำลองแผ่นธรณี: Müller et al. (2022) ผ่าน GPlates Web Service (EarthByte)',
    credit_timescale: 'ตารางธรณีกาล: International Commission on Stratigraphy (ICS)',
    credit_inspiration: 'แรงบันดาลใจ: เว็บ “สยามและโลก เส้นเวลาคู่ขนาน”',
    citations_heading: 'แหล่งอ้างอิงของเหตุการณ์',
  },
  en: {
    app_title: 'Deep Time Kanchanaburi',
    app_subtitle: "Kanchanaburi's geologic history beside the world's, on an ancient globe",
    btn_lecture: 'Lecture mode',
    btn_about: 'About',
    btn_lang: 'ไทย',
    lane_period: 'Period',
    lane_local: 'Kanchanaburi',
    lane_world: 'SE Asia & world',
    lane_life: 'Life',
    draft: 'Draft',
    visit: 'See it at',
    source: 'Source',
    approx_slice: '≈ position from nearest reconstruction',
    paleo_label: 'Kanchanaburi at',
    ma_short: 'Ma',
    prev: 'Previous',
    next: 'Next',
    close: 'Close',
    globe_label: "Globe showing Kanchanaburi's past position",
    about_title: 'About this page',
    about_intro: 'A teaching resource from the Geoscience Division, Mahidol University Kanchanaburi Campus. Scroll the timeline to see where Kanchanaburi was on Earth at each time.',
    credit_model: 'Plate model: Müller et al. (2022), via the GPlates Web Service (EarthByte)',
    credit_timescale: 'Time scale: International Commission on Stratigraphy (ICS)',
    credit_inspiration: 'Inspired by the “Siam & World parallel timeline”',
    citations_heading: 'Event sources',
  },
};

const STORAGE_KEY = 'dt-lang';
let lang = 'th';
let store = null;
const listeners = [];

export function initLang(storage) {
  store = storage;
  let saved = null;
  try { saved = storage ? storage.getItem(STORAGE_KEY) : null; } catch (_) { saved = null; }
  lang = saved === 'en' ? 'en' : 'th';
  return lang;
}

export function getLang() { return lang; }

export function setLang(next) {
  if (next !== 'th' && next !== 'en') return;
  lang = next;
  try { if (store) store.setItem(STORAGE_KEY, next); } catch (_) { /* storage blocked */ }
  listeners.forEach(fn => fn(next));
}

export function onLangChange(fn) { listeners.push(fn); }

export function t(key) {
  return I18N_STRINGS[lang][key] ?? I18N_STRINGS.en[key] ?? key;
}

export function field(obj, base) {
  return obj[`${base}_${lang}`] || obj[`${base}_en`] || '';
}
```

- [ ] **Step 4: Implement `src/format.js`**

```js
export const PRESENT_YEAR = 2026;

function num(x) {
  return Number.isInteger(x) ? String(x) : String(Math.round(x * 10) / 10);
}

export function formatAge(ma, unc, lang, presentYear = PRESENT_YEAR) {
  const th = lang === 'th';
  if (ma === 0) return th ? 'ปัจจุบัน' : 'Present';
  const yearsAgo = ma * 1e6;
  if (yearsAgo < 1000) {
    const ce = Math.round(presentYear - yearsAgo);
    return th ? `พ.ศ. ${ce + 543} (ค.ศ. ${ce})` : `${ce} CE`;
  }
  if (ma < 1) {
    const s = (Math.round(yearsAgo / 100) * 100).toLocaleString('en-US');
    return th ? `≈${s} ปีก่อน` : `≈${s} years ago`;
  }
  const u = unc ? ` ± ${num(unc)}` : '';
  return th ? `${num(ma)}${u} ล้านปีก่อน` : `${num(ma)}${u} Ma`;
}

export function formatLat(lat) {
  return `≈${Math.round(Math.abs(lat))}°${lat < 0 ? 'S' : 'N'}`;
}

const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

export function esc(s) {
  return s == null ? '' : String(s).replace(/[&<>"']/g, c => ESC[c]);
}
```

- [ ] **Step 5: Implement `src/layout.js`**

```js
export function periodOf(age, periods) {
  for (const p of periods) {
    if (age >= p.end_ma && age < p.start_ma) return p;
  }
  return null;
}

export function layoutTimeline(events, periods, { rowH = 64, minPeriodH = 140 } = {}) {
  const ordered = [...periods].sort((a, b) => b.start_ma - a.start_ma);
  const groups = new Map(ordered.map(p => [p.id, []]));
  for (const e of events) {
    const p = periodOf(e.age_ma, ordered);
    if (!p) throw new Error(`Event ${e.id} (age ${e.age_ma} Ma) is outside the time scale`);
    groups.get(p.id).push(e);
  }
  const rows = [];
  const bands = [];
  let y = 0;
  for (const p of ordered) {
    const evs = groups.get(p.id).sort((a, b) => b.age_ma - a.age_ma || a.id.localeCompare(b.id));
    const h = Math.max(minPeriodH, evs.length * rowH);
    bands.push({ period: p, y, h });
    evs.forEach((e, i) => rows.push({ event: e, y: y + i * rowH }));
    y += h;
  }
  return { rows, bands, height: y };
}
```

- [ ] **Step 6: Implement `src/select.js`**

```js
export function activeIndex(rows, centerY, rowH) {
  let best = -1;
  let bestDist = Infinity;
  rows.forEach((r, i) => {
    const d = Math.abs(r.y + rowH / 2 - centerY);
    if (d < bestDist) { bestDist = d; best = i; }
  });
  return best;
}

export function nearestSlice(age, sliceAges) {
  if (!sliceAges.length) throw new Error('No paleo slices available');
  let best = sliceAges[0];
  for (const a of sliceAges) {
    if (Math.abs(a - age) < Math.abs(best - age)) best = a;
  }
  return { age: best, exact: best === age };
}
```

- [ ] **Step 7: Implement `src/geo.js`**

```js
export function shortestLonDelta(from, to) {
  return ((to - from + 540) % 360) - 180;
}

function fixPolygon(rings, geoArea) {
  const area = geoArea({ type: 'Polygon', coordinates: rings });
  return area > 2 * Math.PI ? rings.map(r => [...r].reverse()) : rings;
}

export function normalizeWinding(fc, geoArea) {
  return {
    type: 'FeatureCollection',
    features: fc.features.map(f => {
      const g = f.geometry;
      const coordinates = g.type === 'Polygon'
        ? fixPolygon(g.coordinates, geoArea)
        : g.coordinates.map(poly => fixPolygon(poly, geoArea));
      return { type: 'Feature', properties: {}, geometry: { type: g.type, coordinates } };
    }),
  };
}
```

- [ ] **Step 8: Run the tests to verify they pass**

Run: `npm test`
Expected: all JS tests pass. If `shortestLonDelta(10, 10)` returns `-0`, `assert.equal` still passes, because `-0 == 0`.

- [ ] **Step 9: Commit**

```bash
git add src/i18n.js src/format.js src/layout.js src/select.js src/geo.js tests/js package.json
git commit -m "feat: pure browser logic for language, formatting, layout, selection and winding" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Single-file assembler

**Files:**
- Create: `build/assemble.py`
- Test: `tests/test_assemble.py`

**Interfaces:**
- Consumes:
  - from Task 1: `validate_events`, `validate_timescale`, `load_json`
  - from Task 2: `load_slices`
- Produces:
  - `MODULE_ORDER: list[str]`
  - `strip_module_syntax(src: str, name: str) -> str` raises `BuildError` on unsupported syntax
  - `build(root: Path, strict: bool = False, module_order: list[str] = MODULE_ORDER) -> Path` raises `BuildError`
  - CLI: `python3 build/assemble.py [--strict]`
  - Placeholders it expects in `src/index.html`: `/*__CSS__*/`, `<!--__DATA__-->`, `<!--__SCRIPTS__-->`
  - The data JSON sits in `<script id="dt-data" type="application/json">` with shape `{events, periods, slices, model, built}`.

- [ ] **Step 1: Write the failing tests `tests/test_assemble.py`**

```python
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
    starter = json.loads((ROOT / "content/events.json").read_text(encoding="utf-8"))
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
    starter = json.loads((ROOT / "content/events.json").read_text(encoding="utf-8"))
    starter[0]["body_en"] = "Danger </script><b>bold</b>"
    root = make_root(tmp_path, starter)
    html = build(root, module_order=["a.js", "b.js"]).read_text(encoding="utf-8")
    assert "Danger </script>" not in html
    assert "Danger <\\/script>" in html


def test_build_fails_on_invalid_content(tmp_path):
    starter = json.loads((ROOT / "content/events.json").read_text(encoding="utf-8"))
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/test_assemble.py -q`
Expected: `ModuleNotFoundError: No module named 'assemble'`.

- [ ] **Step 3: Implement `build/assemble.py`**

```python
"""Build dist/index.html: one self-contained page. Usage: python3 build/assemble.py [--strict]"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

from paleo import MODEL, load_slices
from validate import load_json, validate_events, validate_timescale

MODULE_ORDER = ["i18n.js", "format.js", "layout.js", "select.js", "geo.js",
                "globe.js", "timeline.js", "card.js", "main.js"]
MAX_HTML_BYTES = 3_000_000
IMPORT_RE = re.compile(r"^import\s+\{[^}]*\}\s+from\s+'\./[\w-]+\.js';\s*$")
EXPORT_RE = re.compile(r"^export\s+(?=(?:async\s+)?(?:function|const|let|class)\b)")
TOP_DECL_RE = re.compile(r"^(?:async\s+)?(?:function\*?|const|let|class)\s+([A-Za-z_$][\w$]*)", re.M)


class BuildError(Exception):
    pass


def strip_module_syntax(src, name):
    out = []
    for n, line in enumerate(src.splitlines(), 1):
        if line.startswith("import"):
            if IMPORT_RE.match(line):
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

    errors = validate_timescale(periods) + validate_events(events, periods, slice_ages)
    if "0" not in slices:
        errors.append("paleo slice for 0 Ma is missing")
    if errors:
        raise BuildError("content errors:\n  " + "\n  ".join(errors))
    if strict:
        unverified = [e["id"] for e in events if not e["verified"]]
        if unverified:
            raise BuildError("--strict: unverified events: " + ", ".join(unverified))

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

    data = json.dumps({"events": events, "periods": periods, "slices": slices, "model": MODEL,
                       "built": dt.date.today().isoformat()},
                      ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="refuse to build with unverified events")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    try:
        out = build(root, strict=args.strict)
    except BuildError as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"built {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest -q`
Expected: every Python test passes (validate, paleo, assemble).

- [ ] **Step 5: Commit**

```bash
git add build/assemble.py tests/test_assemble.py
git commit -m "feat: single-file assembler with validation, strict mode and size checks" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Page shell, globe, timeline, card and glue

**Files:**
- Create: `src/index.html`, `src/style.css`, `src/globe.js`, `src/timeline.js`, `src/card.js`, `src/main.js`

**Interfaces:**
- Consumes:
  - from Task 3: `t`, `field`, `getLang`, `setLang`, `initLang`, `onLangChange`, `formatAge`, `formatLat`, `esc`, `layoutTimeline`, `activeIndex`, `nearestSlice`, `shortestLonDelta`, `normalizeWinding`
  - the global `d3`
  - the data JSON from Task 4
- Produces:
  - `createGlobe(canvas, slices, {reducedMotion}) -> {showSlice(age) -> {age, exact, lonlat}, resize()}`
  - `createTimeline(container, events, periods, {onActive, onSelect}) -> {scrollToEvent(id), refresh()}`
  - `createCard(el, {onPrev, onNext, onClose}) -> {show(event), hide(), refresh(), lectureMode(on)}`

- [ ] **Step 1: Write `src/index.html`**

```html
<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Deep Time Kanchanaburi</title>
<meta name="description" content="Kanchanaburi's geologic history alongside world events, on a globe of ancient plate positions.">
<style>/*__CSS__*/</style>
</head>
<body>
<header class="topbar">
  <h1><span data-i18n="app_title"></span><span class="sub" data-i18n="app_subtitle"></span></h1>
  <button type="button" id="btn-lecture" aria-pressed="false" data-i18n="btn_lecture"></button>
  <button type="button" id="btn-about" data-i18n="btn_about"></button>
  <button type="button" id="btn-lang" data-i18n="btn_lang"></button>
</header>
<main class="main">
  <section class="globe-pane">
    <canvas id="globe" role="img"></canvas>
    <div id="readout" aria-live="polite"></div>
  </section>
  <section class="tl-pane">
    <div class="lanes" aria-hidden="true">
      <span data-i18n="lane_period"></span><span data-i18n="lane_local"></span><span data-i18n="lane_world"></span><span data-i18n="lane_life"></span>
    </div>
    <div id="timeline" tabindex="0"></div>
    <article id="card" hidden aria-live="polite"></article>
  </section>
</main>
<dialog id="about">
  <div id="about-body"></div>
  <form method="dialog"><button data-i18n="close"></button></form>
</dialog>
<!--__DATA__-->
<!--__SCRIPTS__-->
</body>
</html>
```

- [ ] **Step 2: Write `src/style.css`**

```css
:root {
  --bg: #f7f5f0; --surface: #ffffff; --text: #1d1b18; --muted: #6b665d; --border: #e2ddd3;
  --accent: #b4471f; --row-active: #fbe9df; --badge-bg: #fff1c2; --badge-text: #6a4d00;
  --globe-ocean: #dbe7ef; --globe-land: #c9b48a; --globe-grid: rgba(40, 60, 80, .18);
  --globe-edge: #8aa0b0; --globe-marker: #d13b1c;
  --font: "Noto Sans Thai", "Thonburi", "Leelawadee UI", system-ui, -apple-system, "Segoe UI", sans-serif;
  --scale: 1;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #15171a; --surface: #1f2226; --text: #ece8e1; --muted: #a39d92; --border: #33373d;
    --accent: #f08a5d; --row-active: #3a2a22; --badge-bg: #4a3a0a; --badge-text: #ffe08a;
    --globe-ocean: #16283a; --globe-land: #6e6046; --globe-grid: rgba(200, 220, 240, .12);
    --globe-edge: #3e5568; --globe-marker: #ff7a50;
  }
}
:root[data-theme="dark"] {
  --bg: #15171a; --surface: #1f2226; --text: #ece8e1; --muted: #a39d92; --border: #33373d;
  --accent: #f08a5d; --row-active: #3a2a22; --badge-bg: #4a3a0a; --badge-text: #ffe08a;
  --globe-ocean: #16283a; --globe-land: #6e6046; --globe-grid: rgba(200, 220, 240, .12);
  --globe-edge: #3e5568; --globe-marker: #ff7a50;
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; }
body { background: var(--bg); color: var(--text); font-family: var(--font); font-size: calc(16px * var(--scale));
  line-height: 1.55; display: flex; flex-direction: column; overflow: hidden; }
body.lecture { --scale: 1.4; }
.topbar { display: flex; align-items: center; gap: 8px; padding: 10px 16px; border-bottom: 1px solid var(--border); background: var(--surface); }
.topbar h1 { font-size: 1.05em; margin: 0; flex: 1; min-width: 0; }
.topbar .sub { display: block; font-size: .72em; color: var(--muted); font-weight: 400; }
.topbar button { font: inherit; font-size: .8em; padding: 6px 10px; border: 1px solid var(--border); border-radius: 8px;
  background: var(--bg); color: var(--text); cursor: pointer; white-space: nowrap; }
.topbar button[aria-pressed="true"] { background: var(--accent); color: #fff; border-color: var(--accent); }
.main { flex: 1; display: grid; grid-template-columns: 45% 55%; min-height: 0; }
.globe-pane { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 16px;
  border-right: 1px solid var(--border); min-height: 0; }
#globe { width: 100%; max-width: 640px; aspect-ratio: 1; touch-action: none; cursor: grab; }
#readout { margin-top: 8px; font-variant-numeric: tabular-nums; color: var(--muted); font-size: .9em; text-align: center; }
.tl-pane { display: flex; flex-direction: column; min-height: 0; position: relative; }
.lanes { display: grid; grid-template-columns: 80px 1fr 1fr 40px; gap: 8px; padding: 8px 16px; font-size: .72em;
  color: var(--muted); border-bottom: 1px solid var(--border); background: var(--surface); }
#timeline { flex: 1; overflow-y: auto; position: relative; overscroll-behavior: contain; }
.tl-inner { position: relative; margin: 0 16px; }
.tl-band { position: absolute; left: 0; width: 72px; border-radius: 6px; opacity: .85; display: flex;
  justify-content: center; padding-top: 8px; }
.tl-band span { writing-mode: vertical-rl; font-size: .72em; color: #1d1b18; font-weight: 600; }
.tl-row { position: absolute; display: flex; flex-direction: column; justify-content: center; align-items: flex-start;
  gap: 2px; padding: 4px 10px; border: 1px solid transparent; border-radius: 8px; background: none; color: var(--text);
  font: inherit; text-align: left; cursor: pointer; overflow: hidden; }
.tl-row:hover, .tl-row:focus-visible { border-color: var(--border); background: var(--surface); }
.tl-row.is-active { background: var(--row-active); border-color: var(--accent); }
.lane-local { left: 80px; width: calc(50% - 64px); }
.lane-world { left: calc(50% + 24px); width: calc(50% - 72px); }
.lane-life { right: 0; width: 40px; align-items: center; padding: 0; }
.tl-age { font-size: .7em; color: var(--muted); font-variant-numeric: tabular-nums; }
.tl-title { font-size: .86em; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.tl-icon { font-size: 1.3em; }
.badge { display: inline-block; font-size: .66em; padding: 1px 6px; border-radius: 999px; background: var(--badge-bg); color: var(--badge-text); }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
#card { position: absolute; left: 16px; right: 16px; bottom: 16px; max-height: 60%; overflow-y: auto; background: var(--surface);
  border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; box-shadow: 0 8px 28px rgba(0, 0, 0, .18); z-index: 5; }
#card h2 { margin: 4px 0 6px; font-size: 1.1em; }
#card p { margin: 6px 0; font-size: .92em; }
#card a { color: var(--accent); }
.card-head { display: flex; align-items: center; gap: 8px; }
.card-age { font-size: .8em; color: var(--muted); flex: 1; }
.card-close { border: 0; background: none; font-size: 1.4em; line-height: 1; color: var(--muted); cursor: pointer; padding: 0 4px; }
.card-unit { color: var(--muted); }
#card .card-cite { font-size: .8em; color: var(--muted); }
.card-nav { display: flex; justify-content: space-between; margin-top: 10px; }
.card-nav button, dialog#about button { font: inherit; font-size: .85em; padding: 6px 12px; border-radius: 8px;
  border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; }
dialog#about { max-width: min(680px, calc(100vw - 32px)); max-height: calc(100vh - 64px); border: 1px solid var(--border);
  border-radius: 12px; background: var(--surface); color: var(--text); padding: 20px; }
dialog#about::backdrop { background: rgba(0, 0, 0, .4); }
dialog#about ol, dialog#about ul { padding-left: 20px; font-size: .85em; }
@media (max-width: 767px) {
  .main { grid-template-columns: 1fr; grid-template-rows: 33vh 1fr; }
  .globe-pane { border-right: 0; border-bottom: 1px solid var(--border); padding: 8px; }
  #globe { height: calc(33vh - 44px); width: auto; max-width: 100%; }
  #readout { margin-top: 2px; font-size: .8em; }
  .topbar .sub { display: none; }
  .lanes { grid-template-columns: 56px 1fr 1fr 28px; }
  .tl-band { width: 48px; }
  .lane-local { left: 56px; width: calc(50% - 44px); }
  .lane-world { left: calc(50% + 16px); width: calc(50% - 48px); }
  .lane-life { width: 28px; }
  #card { max-height: 70%; }
}
```

- [ ] **Step 3: Write `src/globe.js`**

```js
import { nearestSlice } from './select.js';
import { shortestLonDelta, normalizeWinding } from './geo.js';

export function createGlobe(canvas, slices, { reducedMotion = false } = {}) {
  const ctx = canvas.getContext('2d');
  const projection = d3.geoOrthographic().clipAngle(90).precision(0.5);
  const path = d3.geoPath(projection, ctx);
  const graticule = d3.geoGraticule10();
  const prepared = {};
  for (const [k, s] of Object.entries(slices)) {
    prepared[k] = { ...s, coastlines: normalizeWinding(s.coastlines, d3.geoArea) };
  }
  const ages = Object.keys(prepared).map(Number);
  let current = null;
  let previous = null;
  let fade = 1;
  let rotation = [0, 0];
  let anim = null;
  let dragged = false;
  let width = 0;
  let height = 0;

  function colors() {
    const cs = getComputedStyle(canvas);
    const v = name => cs.getPropertyValue(name).trim();
    return { ocean: v('--globe-ocean'), land: v('--globe-land'), grid: v('--globe-grid'), edge: v('--globe-edge'), marker: v('--globe-marker') };
  }

  function drawLand(slice, c) {
    ctx.beginPath();
    path(slice.coastlines);
    ctx.fillStyle = c.land;
    ctx.fill();
  }

  function drawMarker(lonlat, c, now) {
    if (d3.geoDistance(lonlat, [-rotation[0], -rotation[1]]) > Math.PI / 2) return;
    const p = projection(lonlat);
    if (!p) return;
    ctx.beginPath();
    ctx.arc(p[0], p[1], 5, 0, 2 * Math.PI);
    ctx.fillStyle = c.marker;
    ctx.fill();
    if (!reducedMotion) {
      const k = (now % 1600) / 1600;
      ctx.beginPath();
      ctx.arc(p[0], p[1], 5 + k * 14, 0, 2 * Math.PI);
      ctx.strokeStyle = c.marker;
      ctx.lineWidth = 2;
      ctx.globalAlpha = 1 - k;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
  }

  function draw(now) {
    if (!width) return;
    const c = colors();
    projection.rotate(rotation);
    ctx.clearRect(0, 0, width, height);
    ctx.beginPath(); path({ type: 'Sphere' }); ctx.fillStyle = c.ocean; ctx.fill();
    ctx.beginPath(); path(graticule); ctx.strokeStyle = c.grid; ctx.lineWidth = 0.5; ctx.stroke();
    if (previous && fade < 1) { ctx.globalAlpha = 1 - fade; drawLand(previous, c); }
    if (current) { ctx.globalAlpha = previous ? fade : 1; drawLand(current, c); }
    ctx.globalAlpha = 1;
    if (current) drawMarker(current.kanchanaburi, c, now);
    ctx.beginPath(); path({ type: 'Sphere' }); ctx.strokeStyle = c.edge; ctx.lineWidth = 1; ctx.stroke();
  }

  function frame(now) {
    if (anim) anim(now);
    draw(now);
    if (!reducedMotion || anim) requestAnimationFrame(frame);
  }

  function animateTo(target, withFade) {
    if (reducedMotion) {
      rotation = target; previous = null; fade = 1; draw(performance.now());
      return;
    }
    const start = rotation.slice();
    const dLon = shortestLonDelta(start[0], target[0]);
    const dLat = target[1] - start[1];
    const t0 = performance.now();
    fade = withFade ? 0 : 1;
    anim = now => {
      const k = Math.min(1, (now - t0) / 600);
      const e = d3.easeCubicInOut(k);
      rotation = [start[0] + dLon * e, start[1] + dLat * e];
      if (withFade) fade = e;
      if (k >= 1) { anim = null; previous = null; fade = 1; }
    };
  }

  function showSlice(age) {
    const { age: a, exact } = nearestSlice(age, ages);
    const next = prepared[String(a)];
    const info = { age: a, exact, lonlat: next.kanchanaburi };
    const target = [-next.kanchanaburi[0], -next.kanchanaburi[1]];
    if (current === next) {
      if (dragged) { dragged = false; animateTo(target, false); }
      return info;
    }
    const first = current === null;
    previous = current;
    current = next;
    dragged = false;
    if (first) { rotation = target; previous = null; draw(performance.now()); } else { animateTo(target, true); }
    return info;
  }

  function resize() {
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    width = rect.width; height = rect.height;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    projection.translate([width / 2, height / 2]).scale(Math.min(width, height) / 2 - 4);
    draw(performance.now());
  }

  d3.select(canvas).call(d3.drag().on('drag', ev => {
    dragged = true;
    anim = null;
    rotation = [rotation[0] + ev.dx * 0.4, Math.max(-90, Math.min(90, rotation[1] - ev.dy * 0.4))];
    draw(performance.now());
  }));

  requestAnimationFrame(frame);
  return { showSlice, resize };
}
```

With reduced motion, `frame` stops after its first pass; every later draw is triggered explicitly by `showSlice`, by drag or by `resize`.

- [ ] **Step 4: Write `src/timeline.js`**

```js
import { layoutTimeline } from './layout.js';
import { activeIndex } from './select.js';
import { t, field, getLang } from './i18n.js';
import { formatAge, esc } from './format.js';

const ROW_H = 64;
const MIN_PERIOD_H = 140;

export function createTimeline(container, events, periods, { onActive, onSelect }) {
  const layout = layoutTimeline(events, periods, { rowH: ROW_H, minPeriodH: MIN_PERIOD_H });
  const inner = document.createElement('div');
  inner.className = 'tl-inner';
  container.appendChild(inner);
  let pad = 0;
  let active = -1;
  let rowEls = [];

  function rowHtml(e) {
    if (e.lane === 'life') {
      return `<span class="tl-icon" aria-hidden="true">${esc(e.icon)}</span><span class="sr">${esc(field(e, 'title'))}</span>`;
    }
    const badge = e.verified ? '' : ` <span class="badge">${esc(t('draft'))}</span>`;
    return `<span class="tl-age">${esc(formatAge(e.age_ma, null, getLang()))}${badge}</span><span class="tl-title">${esc(field(e, 'title'))}</span>`;
  }

  function render() {
    pad = Math.round(container.clientHeight / 2);
    inner.innerHTML = '';
    inner.style.height = `${layout.height + 2 * pad}px`;
    for (const b of layout.bands) {
      const el = document.createElement('div');
      el.className = 'tl-band';
      el.style.top = `${pad + b.y}px`;
      el.style.height = `${b.h - 4}px`;
      el.style.background = b.period.color;
      el.innerHTML = `<span>${esc(field(b.period, 'name'))}</span>`;
      inner.appendChild(el);
    }
    rowEls = layout.rows.map(r => {
      const el = document.createElement('button');
      el.type = 'button';
      el.className = `tl-row lane-${r.event.lane}`;
      el.style.top = `${pad + r.y + 2}px`;
      el.style.height = `${ROW_H - 4}px`;
      el.title = field(r.event, 'title');
      el.innerHTML = rowHtml(r.event);
      el.addEventListener('click', () => onSelect(r.event));
      inner.appendChild(el);
      return el;
    });
    active = -1;
    update();
  }

  function update() {
    const i = activeIndex(layout.rows, container.scrollTop + container.clientHeight / 2 - pad, ROW_H);
    if (i < 0 || i === active) return;
    if (rowEls[active]) rowEls[active].classList.remove('is-active');
    rowEls[i].classList.add('is-active');
    active = i;
    onActive(layout.rows[i].event);
  }

  let ticking = false;
  container.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { ticking = false; update(); });
  }, { passive: true });

  function scrollToEvent(id) {
    const r = layout.rows.find(row => row.event.id === id);
    if (!r) return;
    const smooth = !matchMedia('(prefers-reduced-motion: reduce)').matches;
    container.scrollTo({ top: r.y + ROW_H / 2, behavior: smooth ? 'smooth' : 'auto' });
  }

  render();
  return { scrollToEvent, refresh: render };
}
```

`scrollTop = r.y + ROW_H/2` puts the row's centre at the viewport centre, because `pad` equals half the viewport height.

- [ ] **Step 5: Write `src/card.js`**

```js
import { t, field, getLang } from './i18n.js';
import { formatAge, esc } from './format.js';

export function createCard(el, { onPrev, onNext, onClose } = {}) {
  let shown = null;
  let lecture = false;

  function hide() {
    shown = null;
    el.hidden = true;
  }

  function render() {
    if (!shown) { el.hidden = true; return; }
    const e = shown;
    const badge = e.verified ? '' : `<span class="badge">${esc(t('draft'))}</span>`;
    const body = field(e, 'body') ? `<p>${esc(field(e, 'body'))}</p>` : '';
    const unit = e.rock_unit ? `<p class="card-unit">${esc(e.rock_unit)}</p>` : '';
    const site = e.visit_site
      ? `<p><strong>${esc(t('visit'))}:</strong> <a href="https://www.google.com/maps?q=${e.visit_site.lat},${e.visit_site.lon}" target="_blank" rel="noopener">${esc(field(e.visit_site, 'name'))}</a></p>`
      : '';
    const cite = e.citation
      ? `<p class="card-cite"><strong>${esc(t('source'))}:</strong> <a href="${esc(e.citation.url)}" target="_blank" rel="noopener">${esc(e.citation.text)}</a></p>`
      : '';
    const nav = lecture
      ? `<div class="card-nav"><button type="button" class="prev">← ${esc(t('prev'))}</button><button type="button" class="next">${esc(t('next'))} →</button></div>`
      : '';
    el.innerHTML = `<div class="card-head"><span class="card-age">${esc(formatAge(e.age_ma, e.age_uncertainty_ma, getLang()))}</span>${badge}<button type="button" class="card-close" aria-label="${esc(t('close'))}">×</button></div><h2>${esc(field(e, 'title'))}</h2>${body}${unit}${site}${cite}${nav}`;
    el.hidden = false;
    el.querySelector('.card-close').addEventListener('click', () => { hide(); if (onClose) onClose(); });
    if (lecture) {
      el.querySelector('.prev').addEventListener('click', () => onPrev && onPrev());
      el.querySelector('.next').addEventListener('click', () => onNext && onNext());
    }
  }

  function show(e) { shown = e; render(); }
  function lectureMode(on) { lecture = on; render(); }

  return { show, hide, refresh: render, lectureMode };
}
```

- [ ] **Step 6: Write `src/main.js`**

```js
import { t, initLang, getLang, setLang, onLangChange } from './i18n.js';
import { formatLat, esc } from './format.js';
import { createGlobe } from './globe.js';
import { createTimeline } from './timeline.js';
import { createCard } from './card.js';

function start() {
  const data = JSON.parse(document.getElementById('dt-data').textContent);
  let storage = null;
  try { storage = window.localStorage; } catch (_) { storage = null; }
  initLang(storage);

  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const globeEl = document.getElementById('globe');
  const globe = createGlobe(globeEl, data.slices, { reducedMotion });
  const readout = document.getElementById('readout');
  const lectureBtn = document.getElementById('btn-lecture');
  const stops = data.events.filter(e => e.lecture_stop).sort((a, b) => b.age_ma - a.age_ma);
  let stopIndex = -1;
  let lecture = false;
  let lastInfo = null;

  function showReadout(info) {
    lastInfo = info;
    const approx = info.exact ? '' : ` · ${t('approx_slice')}`;
    readout.textContent = `${t('paleo_label')} ${formatLat(info.lonlat[1])} · ${info.age} ${t('ma_short')}${approx}`;
  }

  const card = createCard(document.getElementById('card'), {
    onPrev: () => goStop(stopIndex - 1),
    onNext: () => goStop(stopIndex + 1),
  });

  const timeline = createTimeline(document.getElementById('timeline'), data.events, data.periods, {
    onActive: e => showReadout(globe.showSlice(e.paleo_age)),
    onSelect: e => card.show(e),
  });

  function goStop(i) {
    if (!stops.length) return;
    stopIndex = Math.max(0, Math.min(stops.length - 1, i));
    const e = stops[stopIndex];
    timeline.scrollToEvent(e.id);
    card.show(e);
  }

  function setLecture(on) {
    lecture = on;
    document.body.classList.toggle('lecture', on);
    lectureBtn.setAttribute('aria-pressed', String(on));
    card.lectureMode(on);
    requestAnimationFrame(() => { globe.resize(); timeline.refresh(); if (on) goStop(stopIndex < 0 ? 0 : stopIndex); });
  }

  function renderAbout() {
    const seen = new Set();
    const cites = data.events
      .filter(e => e.citation && !seen.has(e.citation.text) && seen.add(e.citation.text))
      .map(e => `<li><a href="${esc(e.citation.url)}" target="_blank" rel="noopener">${esc(e.citation.text)}</a></li>`)
      .join('');
    document.getElementById('about-body').innerHTML =
      `<h2>${esc(t('about_title'))}</h2><p>${esc(t('about_intro'))}</p>` +
      `<ul><li>${esc(t('credit_model'))}</li><li>${esc(t('credit_timescale'))}</li><li>${esc(t('credit_inspiration'))}</li></ul>` +
      `<h3>${esc(t('citations_heading'))}</h3><ol>${cites}</ol>`;
  }

  function applyStaticText() {
    document.documentElement.lang = getLang();
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    globeEl.setAttribute('aria-label', t('globe_label'));
  }

  lectureBtn.addEventListener('click', () => setLecture(!lecture));
  document.getElementById('btn-lang').addEventListener('click', () => setLang(getLang() === 'th' ? 'en' : 'th'));
  document.getElementById('btn-about').addEventListener('click', () => document.getElementById('about').showModal());
  document.addEventListener('keydown', ev => {
    if (!lecture) return;
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(ev.key)) { ev.preventDefault(); goStop(stopIndex + 1); }
    if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(ev.key)) { ev.preventDefault(); goStop(stopIndex - 1); }
    if (ev.key === 'Escape') setLecture(false);
  });
  onLangChange(() => {
    applyStaticText();
    renderAbout();
    timeline.refresh();
    card.refresh();
    if (lastInfo) showReadout(lastInfo);
  });
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { globe.resize(); timeline.refresh(); }, 120);
  });

  applyStaticText();
  renderAbout();
  globe.resize();
  timeline.refresh();
}

start();
```

- [ ] **Step 7: Build and check in a browser**

Run:
```bash
python3 -m pytest -q && npm test && python3 build/assemble.py && open dist/index.html
```
Expected: the build prints `built .../dist/index.html (… KB)` under 3,000 KB, and the page opens. Check each of these:
1. **Globe:** land is filled and the oceans are blue (Review Focus 1). With the three starter events, scrolling moves the marker between the 270, 250 and 230 Ma slices with a smooth rotation and a cross-fade.
2. **Readout:** shows `กาญจนบุรีอยู่ที่ ≈37°S · 270 ล้านปีก่อน` (the latitude comes from the real slice).
3. **Event card:** tapping a row opens the card. The draft badge, the citation link and the close button all work.
4. **Language toggle:** EN ↔ ไทย swaps every label, the card and the period names. Reloading keeps the choice.
5. **Lecture mode:** the text gets larger, the arrow keys step between stops, and Escape exits.
6. **About:** lists the credits and citations.
7. **Phone layout:** in DevTools at 375 px, the globe is in the top third, the timeline scrolls underneath, and there is no horizontal scroll.
8. **Dark theme:** switch the OS appearance to dark; the colours flip and the text stays readable.
9. **Dragging the globe:** it rotates, then snaps back on the next scroll.

Fix any failure before you commit.

- [ ] **Step 8: Commit**

```bash
git add src/
git commit -m "feat: page shell, canvas globe, timeline lanes, event card and lecture mode" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Draft the full content and the review table

**Files:**
- Modify: `content/events.json` (replace the starter content with the full draft)
- Create: `build/review_table.py`
- Test: `tests/test_review_table.py`

**Interfaces:**
- Consumes: from Task 1, `load_json`; from Task 4, `build` (to confirm the content passes).
- Produces: `write_review(events: list[dict], out_dir: Path) -> tuple[Path, Path]`, which writes `review.csv` (utf-8-sig) and `review.md`. CLI: `python3 build/review_table.py`.

- [ ] **Step 1: Write the failing test `tests/test_review_table.py`**

```python
import csv

from review_table import COLUMNS, write_review

EVENTS = [{
    "id": "ratburi-limestone", "lane": "local", "age_ma": 270, "age_uncertainty_ma": 15,
    "title_th": "หินปูนกลุ่มราชบุรี", "title_en": "Ratburi limestone", "body_th": "ข้อความ | มีขีด", "body_en": "Text",
    "rock_unit": None, "visit_site": None, "citation": {"text": "Ridd 2011", "url": "https://doi.org/10.1144/GOTH"},
    "paleo_age": 270, "lecture_stop": True, "verified": False,
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/test_review_table.py -q`
Expected: `ModuleNotFoundError: No module named 'review_table'`.

- [ ] **Step 3: Implement `build/review_table.py`**

```python
"""Export events to review/review.csv and review/review.md for the instructor."""
import csv
import sys
from pathlib import Path

from validate import load_json

COLUMNS = ["id", "lane", "age_ma", "age_uncertainty_ma", "title_th", "title_en", "body_th", "body_en",
           "rock_unit", "visit_site", "citation", "lecture_stop", "verified", "corrections"]


def _row(e):
    site = e.get("visit_site")
    cite = e.get("citation")
    return {
        "id": e["id"], "lane": e["lane"], "age_ma": e["age_ma"],
        "age_uncertainty_ma": "" if e.get("age_uncertainty_ma") is None else e["age_uncertainty_ma"],
        "title_th": e["title_th"], "title_en": e["title_en"],
        "body_th": e.get("body_th", ""), "body_en": e.get("body_en", ""),
        "rock_unit": e.get("rock_unit") or "",
        "visit_site": f"{site['name_en']} ({site['lat']}, {site['lon']})" if site else "",
        "citation": f"{cite['text']} — {cite['url']}" if cite else "",
        "lecture_stop": "yes" if e["lecture_stop"] else "no",
        "verified": "yes" if e["verified"] else "no",
        "corrections": "",
    }


def write_review(events, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [_row(e) for e in sorted(events, key=lambda e: -e["age_ma"])]
    csv_path = out_dir / "review.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    md_path = out_dir / "review.md"
    cell = lambda v: str(v).replace("|", "\\|").replace("\n", " ")  # noqa: E731
    lines = ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    lines += ["| " + " | ".join(cell(r[c]) for c in COLUMNS) + " |" for r in rows]
    md_path.write_text("# Deep Time Kanchanaburi — content review\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    paths = write_review(load_json(root / "content/events.json"), root / "review")
    print("\n".join(str(p) for p in paths))
    sys.exit(0)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/test_review_table.py -q`
Expected: pass.

- [ ] **Step 5: Draft the full `content/events.json` (research step)**

Replace the starter file with about 40 events. Use the seed list below. For each event:
- Find a real primary or authoritative source, and prefer a DOI link.
- Read the source's statement of the age, and use the source's age when it differs from the seed age.
- Write 2–3 sentences in Thai and in English (life lane: title + icon only). Put English technical terms in brackets in the Thai text, e.g. `แผ่นซีบูมาสุ (Sibumasu)`.
- Set `paleo_age` to the nearest value in `SLICE_AGES`; use `0` for every event younger than 2.5 Ma.
- Keep `verified: false`.
- Never invent a citation. If no source can be found, drop the event and note it in the handoff.

Seed list:

| id | lane | seed age (Ma) | topic | where to look first | lecture_stop |
|---|---|---|---|---|---|
| ordovician-limestone | local | 470 | Ordovician carbonate platform (Thung Song Group) in Kanchanaburi; Sibumasu on the Gondwana margin | Ridd et al. 2011 *Geology of Thailand* (doi:10.1144/GOTH); DMR 1:250,000 Kanchanaburi sheet explanation | yes |
| kanchanaburi-group | local | 425 | Silurian–Devonian Kanchanaburi Group shales and graptolites | Ridd et al. 2011 | no |
| kaeng-krachan-diamictite | local | 295 | Late Carboniferous–Early Permian glaciomarine diamictites (Kaeng Krachan Group): ice-rafted debris from Gondwana | Ridd et al. 2011; Metcalfe 2013 | yes |
| sibumasu-rifting | local | 285 | Sibumasu rifts off Gondwana; the Meso-Tethys opens | Metcalfe 2013, *J. Asian Earth Sci.* 66:1–33 | no |
| ratburi-limestone | local | 270 | (keep the starter event; add a visit site such as a Ratburi-limestone cave near campus, coordinates checked on a map) | Ridd et al. 2011 | yes |
| indosinian-collision | local | 230 | Sibumasu–Indochina collision closes the Paleo-Tethys (Indosinian orogeny) | Metcalfe 2013; Sone & Metcalfe 2008 | yes |
| western-granites | local | 80 | Cretaceous–Paleogene granites of the Western Province | Ridd et al. 2011; Searle et al. 2012 | no |
| pilok-tin-tungsten | local | 60 | Tin–tungsten veins at Pilok, Thong Pha Phum; mined in the 20th century | Ridd et al. 2011; DMR mineral resources reports | yes |
| india-asia-faults | local | 40 | India–Asia collision starts strike-slip motion on the Three Pagodas and Si Sawat faults | Lacassin et al. 1997, *JGR* (doi:10.1029/97JB00894); Morley 2004 | yes |
| fault-reversal | local | 23 | The faults switch from sinistral to dextral motion in the Neogene | Lacassin et al. 1997 | no |
| bo-phloi-basalt | local | 3 | Bo Phloi basalt eruption brings sapphire-bearing magma up (use the source's dated age) | Barr & Macdonald 1981, *GSA Bulletin*; recent Bo Phloi geochronology | yes |
| sapphire-gravels | local | 1 | Weathering concentrates sapphires into gravels that are mined at Bo Phloi | Ridd et al. 2011 | no |
| erawan-travertine | local | 0.01 | Travertine terraces of Erawan Falls built from limestone-dissolved water | Peer-reviewed study of Erawan travertine (search Google Scholar) | no |
| ban-kao-neolithic | local | 0.004 | Ban Kao Neolithic people at the Kwai Noi | Sørensen 1967/1988 excavation reports | yes |
| death-railway | local | 0.000083 | The Thailand–Burma Railway follows the Kwai Noi valley, cut through limestone and granite (1943) | Authoritative history source, e.g. Commonwealth War Graves Commission or a peer-reviewed account | no |
| kanchanaburi-1983-quake | local | 0.000043 | M5.9 earthquake near the Srinagarind reservoir (1983); the reservoir-triggering debate | USGS/ISC event record; published RTS study | no |
| hin-dat-hot-spring | local | 0 | Hin Dat hot spring on the active fault zones today; it heated up after the 2004 Sumatra earthquake | doi:10.3390/atmos17080777 | no |
| gobe | world | 470 | Great Ordovician Biodiversification Event | Servais et al. 2010 | no |
| end-ordovician-extinction | world | 444 | End-Ordovician glaciation and mass extinction | Harper et al. 2014 | no |
| late-devonian-extinction | world | 372 | Late Devonian (Kellwasser) extinction | McGhee 1996 / a review paper | no |
| late-paleozoic-ice-age | world | 300 | Late Paleozoic Ice Age at its peak on Gondwana | Montañez & Poulsen 2013 | no |
| pangaea-assembled | world | 300 | Pangaea assembled | a standard review | no |
| end-permian-extinction | world | 251.94 | (keep the starter event) | Burgess et al. 2014 | no |
| end-triassic-extinction | world | 201.4 | End-Triassic extinction and the CAMP volcanism | Blackburn et al. 2013 | no |
| pangaea-breakup | world | 180 | Pangaea breaks up; the Atlantic opens | a standard review | no |
| k-pg-impact | world | 66 | The Chicxulub impact ends the age of non-avian dinosaurs | Renne et al. 2013 | no |
| india-asia-collision | world | 50 | India collides with Asia and the Himalaya rises | Hu et al. 2016 | no |
| asian-monsoon | world | 25 | The Asian monsoon strengthens | a review paper | no |
| quaternary-ice-ages | world | 2.58 | The Quaternary ice ages begin; sea level falls and Sundaland is exposed | a review paper | no |
| toba-eruption | world | 0.074 | The Toba super-eruption spreads ash over Southeast Asia | Chesner 1991 / Storey et al. 2012 | no |
| myanmar-2025-earthquake | world | 0.000001 | The M7.7 Sagaing fault earthquake (28 Mar 2025) is felt in Kanchanaburi and Bangkok | USGS event page | no |
| first-jawed-fish | life | 430 | 🐟 jawed fishes | — | no |
| first-forests | life | 385 | 🌳 first forests | — | no |
| first-reptiles | life | 312 | 🦎 first reptiles | — | no |
| first-dinosaurs | life | 233 | 🦕 (keep the starter event) | — | no |
| first-mammals | life | 200 | 🐁 early mammals | — | no |
| first-birds | life | 150 | 🐦 first birds | — | no |
| flowering-plants | life | 130 | 🌸 flowering plants | — | no |
| first-primates | life | 55 | 🐒 early primates | — | no |
| homo-sapiens | life | 0.3 | 🧍 *Homo sapiens* | — | no |

The `lecture_stop` column must mark exactly these 8 ids:
- `ordovician-limestone`
- `kaeng-krachan-diamictite`
- `ratburi-limestone`
- `indosinian-collision`
- `pilok-tin-tungsten`
- `india-asia-faults`
- `bo-phloi-basalt`
- `ban-kao-neolithic`

- [ ] **Step 6: Validate, build and export the review table**

Run:
```bash
python3 -m pytest -q && python3 build/assemble.py && python3 build/review_table.py
python3 -c "import json;e=json.load(open('content/events.json'));print(len(e),'events;',sum(x['lecture_stop'] for x in e),'stops;',sum(x['verified'] for x in e),'verified')"
```
Expected: the build succeeds, and the last line prints `≈40 events; 8 stops; 0 verified`.

Then check every citation URL:
```bash
python3 -c "
import json,requests
for e in json.load(open('content/events.json')):
    c=e.get('citation')
    if c:
        try: s=requests.head(c['url'],allow_redirects=True,timeout=20).status_code
        except Exception as x: s=str(x)
        print(s, e['id'], c['url'])"
```
Expected: every line shows 200, or 403/405, which publishers sometimes return to HEAD requests; open those in a browser to confirm. Fix or replace any 404.

- [ ] **Step 7: Commit**

```bash
git add content/events.json build/review_table.py tests/test_review_table.py
git commit -m "content: draft ~40 cited events and review-table export" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Full QA and draft publish

**Files:**
- No new code. Output: `dist/index.html`, published as a private claude.ai Artifact; `review/review.csv` handed to the instructor.

- [ ] **Step 1: Run every automated check**

Run: `python3 -m pytest -q && npm test && python3 build/paleo_report.py && python3 build/assemble.py`
Expected: everything passes, the report says `OK`, and the build is under 3,000 KB.

- [ ] **Step 2: Manual QA on the full content**

Open `dist/index.html` and repeat the 9 checks from Task 5 Step 7. In addition:
- All 17 slices appear while scrolling from the Ordovician to the present.
- At 0 Ma the marker sits on western Thailand.
- No Thai title overflows its row at 375 px; titles clamp to two lines.
- Lecture mode visits exactly the 8 stops in age order.
- Turn off Wi-Fi and reload the file: it still works.
- Events younger than 1,000 years show Buddhist and Common Era years, e.g. `พ.ศ. 2486 (ค.ศ. 1943)`.

- [ ] **Step 3: Publish the draft**

Publish `dist/index.html` with the Artifact tool:
- Title: `Deep Time Kanchanaburi`
- Icon: `globe`
- Description: "Kanchanaburi's geologic history beside world events on a globe of ancient plate positions (draft — content under instructor review)."

The page shows draft badges on every event until the review is done.

- [ ] **Step 4: Hand over for review**

Give the instructor:
- the artifact link
- `review/review.csv`, which opens in Excel with Thai intact (fill in the `corrections` column, and set `verified` to `yes` for each approved event)
- the paleo-latitude table from `paleo_report.py`, to check against the literature

After the review comes back:
1. Apply the corrections to `events.json` and set `verified: true` on approved events.
2. Run `python3 build/assemble.py --strict`.
3. Republish to the same artifact.
4. Commit with `content: apply instructor review`.
