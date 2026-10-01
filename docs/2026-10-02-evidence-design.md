# Deep Time Kanchanaburi: evidence ("How do we know?") design

Date: 2026-10-02 · Status: design approved in chat, awaiting written-spec review
Builds on: `docs/2026-10-01-deep-time-kanchanaburi-design.md`

## 1. Purpose

Students should see that each claim on the timeline rests on data. Every event card gets a **"หลักฐาน / How do we know?"** section listing the evidence for that event: paleomagnetism, geophysics, radiometric dating and fossils, and later the Geoscience Division's own field surveys.

**Success criteria**
1. Each of the 8 lecture stops has at least one evidence item. Overall there are about 30–40 items.
2. Each paleomagnetic item shows the measured paleolatitude next to the plate model's latitude for that age.
3. Every item has a citation and has been checked by the instructor before students see it. `--strict` refuses unverified evidence.
4. The instructor can add the division's surveys later by filling in a CSV template, with no code changes.

**Out of scope:** images and figures, a paleolatitude chart, and a separate evidence lane on the timeline.

## 2. Data model: `content/evidence.json`

This is a separate file. `events.json` does not change. One item can support several events.

| Field | Type | Notes |
|---|---|---|
| `id` | string | kebab-case, unique |
| `event_ids` | string[] | Must be non-empty, and every id must exist in `events.json` |
| `method` | enum | `paleomagnetism`, `geochronology`, `biostratigraphy`, `seismic`, `gravity`, `magnetic`, `seismicity`, `geodesy`, `field-survey` |
| `title_th`, `title_en` | string | Short, e.g. "Paleomagnetic pole, Ratburi limestone" |
| `finding_th`, `finding_en` | string | 1–2 sentences: what was measured and what it shows |
| `value` | string \| null | The key result exactly as the source states it, e.g. "paleolatitude 32 ± 6°S", "U–Pb 242 ± 2 Ma" |
| `paleolat` | `{deg, err}` \| null | Paleomagnetism only: the numeric paleolatitude in degrees, negative for south. This drives the comparison with the model. |
| `site` | `{name_th, name_en, lat, lon}` \| null | |
| `citation` | `{text, url}` | Required, with an http(s) url |
| `source_type` | enum | `peer-reviewed`, `government-report`, `thesis`, `conference`, `own-survey` |
| `verified` | boolean | Starts `false` |
| `_notes` | string | Optional and instructor-only. It is stripped from the page and shown in the review table. |

## 3. Page

- **Card:** below the event's citation, a heading `หลักฐาน · How do we know?` (localised), then one row per evidence item linked to that event. Each row shows:
  - a method chip, in its own colour and labelled in Thai or English
  - the title, the finding and the value
  - a site link to Google Maps, if the item has a site
  - the citation
  - a draft badge, if the item is unverified
- **Paleomagnetic comparison:** for items with `paleolat`, the row also shows `วัดได้ 32 ± 6°S · แบบจำลอง ≈36°S` (`measured … · model …`). The model value is Kanchanaburi's latitude in the event's `paleo_age` slice.
- An event with no evidence shows no section.
- **About panel:** evidence citations are added to the citation list.
- **Lecture mode:** the evidence section scrolls inside the card, and Previous/Next stay pinned.

## 4. Build and validation

- **`validate_evidence(items, event_ids)` rejects:**
  - a bad or duplicate id, or an unknown or empty `event_ids`
  - an unknown `method` or `source_type`
  - an empty title or finding
  - a missing citation, or a citation url that isn't http(s)
  - a site whose lat/lon is out of range
  - a `paleolat` outside ±90, a negative err, or `paleolat` on a non-paleomagnetic item
  - a non-boolean `verified`
- **`assemble.py`:**
  - loads the evidence and validates it against the event ids
  - strips `_` fields and embeds it as `data.evidence`
  - `--strict` also fails on unverified evidence
  - a missing `evidence.json` counts as an empty list
- **`review_table.py`** also writes `review/evidence_review.csv` and `review/evidence_review.md`.
- **Instructor template:** `content/evidence_template.csv` has the same columns, with `event_ids` separated by `;` and site and citation split into plain columns. `build/import_evidence.py <csv>` converts the rows and appends them to `evidence.json`. It always sets `verified: false` and `source_type: own-survey` unless the row states another type. It refuses duplicate ids, then validates.

## 5. Content workflow

1. **Research:** three background research agents (paleomagnetism, geophysics, dating & fossils) draft items under the same rules as the events:
   - no invented citation or value
   - every DOI checked on Crossref
   - `_notes` records exactly what the source states
2. **Merge:** I merge their output, validate it, check every link, and put the results in the evidence review CSV.
3. **Instructor review:** you mark corrections and verify items, then the build runs with `--strict`.

## 6. Testing

- **Python:**
  - `validate_evidence` cases
  - assemble embedding, stripping and `--strict`
  - a missing file is treated as empty
  - the review CSV columns
  - `import_evidence` round-trip, rejection of duplicate ids, and forced `verified: false`
- **JS:**
  - `evidenceFor(eventId, items)` keeps the given order and filters by event
  - `formatPaleolatCompare(measured, modelLat, lang)` gives the expected strings in Thai and English
  - method labels exist in both languages
- **Browser** (`tools/browser_check.mjs`):
  - an event card with evidence shows the section
  - the paleomagnetic comparison text appears
  - no JavaScript errors
