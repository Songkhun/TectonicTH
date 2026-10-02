# Map tab and tectonic-models tab: design and plan

Date: 2026-10-03 · Status: design approved in chat ("approve"); build without further stops.

## Tabs
A tab bar under the header switches between Timeline, Map and Tectonic models. Tabs can be opened directly with `#timeline`, `#map` and `#models`. The map and models views are built the first time they're opened.

## Map tab
- **Base map:** Natural Earth 1:50 m land and land borders (public domain), pinned to a commit. Clipped to the region 85–125°E, 12°S–32°N with Sutherland–Hodgman clipping, then simplified and rounded. Stored in `content/basemap.json` by `build/make_basemap.py`.
- **World view:** uses the 0 Ma globe slice for coastlines, so it needs no extra data.
- **Faults:** GEM Global Active Faults Database (Styron & Pagani 2020, CC BY-SA 4.0), pinned to a commit and clipped to the region. Stored in `content/faults.json` by `build/make_faults.py`. Attribution and licence are shown in About.
- **Sutures and terranes:** `content/sutures.json`, schematic. Sutures are drawn as dashed lines through places a primary paper names, and terranes as labels. Both are clearly marked schematic, start `verified: false`, and are refused by `--strict` until verified.
- **Layers, each toggleable:**
  - evidence sites, coloured by method
  - fossils, shown with their group icons
  - event visit sites
  - active faults
  - sutures
  - terrane labels
- **Navigation:** zoom and pan (`d3.zoom`), plus "Thailand" and "World" buttons.
- **Tap a point:** opens the existing card (evidence, fossil or event).

## Tectonic models tab
- **Data:** `content/models.json`, a list of questions. Each question has:
  - `axis {base_ma, top_ma}` and `event_ids`
  - `models[]`, each with `id`, names, `citation`, summaries, and `phases[{labels, base_ma, top_ma}]`
  - `evidence[]`, each with `evidence_id`, `age_base_ma`/`age_top_ma`, `roles {model_id: supports|challenges|neutral}` and reasons
  - a bilingual `synthesis` and `verified`
- **Evidence:** new evidence found by the research goes into `content/evidence.json`, and the models refer to it by id.
- **View, per question:**
  - an age axis (older on the left), with one row of phase bars per model and a data row of evidence markers with their age ranges
  - a model × evidence table (✓ / ✗ / –, with reasons); clicking a row opens the evidence card
  - the synthesis
- **Build checks:** `build/models.py` `validate_models(models, evidence_ids, event_ids)` checks that ids exist, every role covers every model, ages lie inside the axis window, and citations are http(s). The models are embedded in the page, `--strict` refuses unverified ones, and they're exported to `review/models_review.csv`.

## Pure, tested units
- **Python:**
  - `clip_ring`, `clip_line` and `simplify_and_round`
  - `validate_models` and `validate_sutures`
- **JS:**
  - `mapPoints(data)`, which collects every located item with its kind, colour or icon, and a label
  - `modelLayout(question, width)`, which places bars and markers
  - `rolesTableHtml(question, evidence, lang)`, with everything escaped

## Tasks
1. Basemap and faults: clipping code and tests, the two CLIs, and the generated content.
2. Sutures and models: validation, embedding, strict mode and review export, with tests.
3. Pure JS units: `mapPoints`, `modelLayout` and `rolesTableHtml`, with tests.
4. UI: the tabs, the map tab and the models tab, with styles for light, dark and phone.
5. Content: merge the agents' output, validate, check links, browser QA, commit, merge and republish.
