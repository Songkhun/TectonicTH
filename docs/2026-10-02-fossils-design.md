# Index fossils of Thailand: design and plan

Date: 2026-10-02 · Status: design approved in chat ("yes"); user asked for build without further stops.

## Goal
Show index fossils found in Thailand (about 40–60, all periods and provinces, Kanchanaburi first). Each fossil carries its age range, its formation and its locality: place, ตำบล, อำเภอ, จังหวัด, lat/lon and a precision flag.

## Data: `content/fossils.json`
Schema as in `.superpowers/content/FOSSIL_SCHEMA.md`, kept in this repo as `docs/fossil-schema.md`:
- `id`, `taxon`, `group` (20 groups)
- `age_top_ma` < `age_base_ma`, `stage`, `formation_en`/`formation_th`
- `locality {name_en, name_th, tambon_th|null, amphoe_th|null, province_th, province_en, lat, lon, precision: site|area|district}`
- `significance_th`/`significance_en`
- `citation {text, url}`, `source_type`, `verified`, `_notes`

## Page
- **Fossil column:** a 🐚 lane between "SE Asia & world" and "Life". Each icon sits at the midpoint of its age range, linear inside its period band. Overlapping icons go to a second column (desktop only), then are pushed down. Kanchanaburi fossils get a ring.
- **Fossil card:** tapping an icon opens it, showing:
  - the taxon in italics and its group
  - the age range and stage
  - the formation
  - the locality line: "ต.… อ.… จ.…" or "Tambon …, Amphoe …, … Province"
  - lat/lon with a Google Maps link and the precision
  - the significance and the citation
  - a draft badge until verified
- **Toolbar button "ฟอสซิลดัชนี / Index fossils":** opens a dialog containing:
  - a search box, and filters for period, province and group
  - a sortable-by-age table with columns: taxon · group · age · formation · locality · lat, lon · source
  - clicking a row closes the dialog, scrolls the timeline to that age and opens the card

## Build
- `build/fossils.py`: `load_fossils`, `validate_fossils(items, oldest_ma)`.
- `assemble.py`: embeds the fossils with `_` fields stripped; `--strict` refuses unverified fossils.
- `review_table.py`: also writes `review/fossil_review.csv` and `review/fossil_review.md`.

## Pure JS (`src/fossils.js`), tested with node:test
- `FOSSIL_GROUPS`: icon, Thai label and English label for each group
- `fossilMidAge`
- `placeFossils(bands, fossils, {size, columns})` → `[{x, y, fossil}]`, with no overlaps inside a column
- `localityText(loc, lang)`
- `filterFossils(list, {q, period, province, group}, periods)`
- `fossilCardHtml(f, lang)`, with everything escaped
- `ageToY(age, bands)` in `layout.js`, used for jumping from a table row to the timeline

## Tasks
1. Python schema, validation, embedding, strict mode and review export, with tests.
2. JS pure module and strings, with tests.
3. UI: lane, card dispatch, dialog with filters and row jump, styles for light/dark and phone.
4. Content: merge the three research files, validate, check links, browser QA, commit, merge and republish.
