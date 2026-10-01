# Deep Time Kanchanaburi — Design

Date: 2026-10-01 · Status: approved in chat, awaiting written-spec review
Owner: Geoscience Division, Mahidol University Kanchanaburi Campus

## 1. Purpose

An interactive teaching page that shows Kanchanaburi's geologic history next to Southeast Asian and world events, on a globe showing where Kanchanaburi was at each age. Inspired by [Siam & World parallel timeline](https://timemaphistory.netlify.app).

- **Audience:** undergraduate geoscience students. The instructor projects it in lecture (historical/physical geology); students explore it on their phones afterwards.
- **Relationship to GeoGuard:** separate teaching tool, not a challenge entry. No Kiro or AWS requirement.
- **Success criteria:**
  1. Students can tell, for any major Kanchanaburi rock unit, its age, how it formed and where on Earth the area was at the time.
  2. The instructor can run a lecture from the eight lecture stops without any other slides.
  3. Every event has a citation and has been checked by the instructor before students see it.
  4. The page works offline once loaded and is usable on a phone.

## 2. Scope

**In:** about 35 events from the Ordovician (≈485 Ma) to the present, including a short human tail (Ban Kao prehistory, the Death Railway). Thai primary, English toggle, English technical terms shown in brackets in Thai mode. Single static HTML page.

**Out (for now):** quizzes, user accounts, analytics, live GPlates queries, continuous (unstepped) globe animation, 3D relief, LMS integration.

## 3. User experience

### Layout
- **Desktop/projector:** globe on the left (≈45% width), scrolling timeline on the right.
- **Phone (<768 px):** globe pinned at the top third; timeline scrolls underneath. No horizontal page scroll.

### Timeline
Three parallel lanes:
1. **Kanchanaburi** (about 20 events). Draft list:
   - Ordovician limestone deposition
   - Silurian–Devonian Kanchanaburi Group (กลุ่มหินกาญจนบุรี)
   - Permian Ratburi limestone and its caves
   - Sibumasu docking with Indochina and the Indosinian granites
   - Cretaceous tin–tungsten granites (the Pilok mineralisation)
   - Cenozoic Three Pagodas and Si Sawat fault movement
   - Bo Phloi basalt and sapphires
   - Ban Kao and the Death Railway
2. **Southeast Asia and the world** (about 15 events). Examples:
   - Great Ordovician Biodiversification
   - Pangaea assembly
   - End-Permian extinction
   - K–Pg impact
   - India–Asia collision
3. **Life:** a thin strip of icons only, with no text.

**Time axis:** an ICS geologic time scale bar in official colours, with Thai and English period names. The axis is non-linear so that short periods stay readable: each period gets a minimum height, and the rest of the space is proportional to its duration.

### Globe
- D3 orthographic projection drawn on canvas.
- Shows the paleo-coastlines of the active slice.
- Rotates to centre Kanchanaburi's ancient position, marked by a pulsing dot.
- Shows a latitude readout such as "≈37°S".
- Moves in steps between slices with a short (≈600 ms) eased rotation, and the coastlines cross-fade.
- The active slice is the one for the event nearest the middle of the timeline viewport.
- Drag to rotate by hand; the globe snaps back on the next scroll.

### Event card
Tap or click an event to open a card with:
- the title
- the age ± uncertainty (Ma)
- a 2–3 sentence explanation
- the rock unit, if one exists
- **where to see it today**: a site name with a link that opens the coordinates in Google Maps
- one citation
- a "draft" badge if the event is not yet verified

### Lecture mode
- A toolbar button switches it on.
- Arrow keys or on-screen buttons step through the events marked `lecture_stop: true` (about 8).
- Text is about 1.4× larger.
- The active card stays open.

### Language
- The TH/EN toggle swaps every label and event text.
- The choice is remembered in `localStorage`, wrapped in try/catch; the default is Thai.

## 4. Architecture

```
deep-time/
  content/
    events.json        # instructor-verified content
    timescale.json     # ICS periods: start/end Ma, colour, name_th, name_en
  build/
    fetch_paleo.py     # one-off: GPlates → paleo/<age>.json
    assemble.py        # content + paleo + src → dist/index.html
    review_table.py    # events.json → review .xlsx/.md for the instructor
  paleo/
    <age>.json         # simplified coastlines + Kanchanaburi paleo-point per slice
  src/
    index.html         # page shell, CSS tokens, light/dark
    globe.js           # globe rendering and slice transitions
    timeline.js        # lanes, axis, scroll → active event
    card.js            # event detail and lecture mode
    i18n.js            # TH/EN strings and toggle
  dist/
    index.html         # single self-contained output
```

### Units and interfaces
- **globe.js:** `createGlobe(el, slices)` returns `{ showSlice(age), resize() }`. It knows nothing about events.
- **timeline.js:** `createTimeline(el, events, timescale, onActive)`. It calls `onActive(event)` when the event nearest the viewport centre changes.
- **card.js:** `createCard(el)` returns `{ show(event, lang), lectureMode(on, stops) }`.
- **i18n.js:** `t(key)`, `setLang(lang)`, `onLangChange(fn)`.
- **main glue (in index.html):** wires `onActive` to `globe.showSlice(event.paleo_age)` and to card updates.

### Data model: `events.json`
Each event:

| Field | Type | Notes |
|---|---|---|
| `id` | string | kebab-case, unique |
| `lane` | `"local"` \| `"world"` \| `"life"` | |
| `age_ma` | number | 0 for the present; human events use fractional Ma (for example 0.004) |
| `age_uncertainty_ma` | number \| null | |
| `title_th`, `title_en` | string | |
| `body_th`, `body_en` | string | 2–3 sentences; empty for the `life` lane |
| `rock_unit` | string \| null | Formal name with its Thai name |
| `visit_site` | `{name_th, name_en, lat, lon}` \| null | |
| `citation` | `{text, url}` | One per event; required for `local` and `world` |
| `paleo_age` | number | Slice age used for the globe; defaults to `age_ma` rounded to the nearest available slice |
| `lecture_stop` | boolean | |
| `verified` | boolean | Starts `false` |

### Paleo slices: `paleo/<age>.json`
```json
{ "age": 270, "model": "MULLER2022",
  "kanchanaburi": [88.17, -37.45],
  "coastlines": <TopoJSON, simplified> }
```
- **Source:** the GPlates Web Service (`gws.gplates.org`), using `reconstruct/coastlines` and `reconstruct/reconstruct_points`.
- **Model:** Müller et al. 2022. Present-day reference point: Kanchanaburi town (99.53 E, 14.02 N).
- **Simplification:** Visvalingam simplification to ≤100 KB per slice, using the `mapshaper` CLI via npx or Python `topojson`.
- **Slices:** one per distinct `paleo_age`, about 15–20 in total. The present-day slice uses Natural Earth 110 m coastlines.

### Build
1. `fetch_paleo.py`: reads `events.json`, collects the distinct `paleo_age` values, and fetches and simplifies any slice that is missing. It is idempotent and skips slices that already exist. If any request fails, it exits with a non-zero code and names the failing age; it never writes a partial slice.
2. `assemble.py`: inlines the CSS, the JS, the D3 and topojson-client libraries (vendored copies from cdnjs, pinned versions), `events.json`, `timescale.json` and every slice into `dist/index.html`.
   - With `--strict`, it fails if any event has `verified: false`.
   - It fails if any event is missing a citation (except in the `life` lane), or if its `paleo_age` has no matching slice.
3. **Target size:** `dist/index.html` ≤ 3 MB.

### Publishing
`dist/index.html` is published as a private claude.ai Artifact. The same file can later be copied unchanged to GitHub Pages or MU web hosting.

## 5. Content workflow

1. Claude drafts `events.json` from published literature, with one citation per event. Priority sources:
   - DMR geological maps and the Kanchanaburi geology explanation
   - Ridd et al., *The Geology of Thailand* (2011)
   - Metcalfe's papers on Sibumasu and Indochina
   - published work on Bo Phloi basalt and sapphires
   - ICS chart v2024 for period ages
2. `review_table.py` exports a review table (event, age, text, citation, verified column).
3. The instructor marks corrections; Claude applies them and sets `verified: true` on approved events.
4. Before students see the page, build with `--strict`.
5. Until then, draft builds show the "draft" badge on unverified events.

## 6. Error handling

| Situation | Behaviour |
|---|---|
| GPlates request fails during the build | The build stops and names the failing age; existing slices are kept |
| An event has no matching slice | `assemble.py` fails; nothing is published with gaps |
| A slice is missing at runtime (should not happen) | Use the nearest slice and show "≈ position from nearest reconstruction" |
| `localStorage` is unavailable | Default to Thai; nothing else breaks |
| Very small screen or reduced-motion preference | Turn off the rotation animation and jump straight to the slice |

## 7. Testing

- **Data checks**, run automatically in `assemble.py`:
  - the schema of every event
  - unique ids
  - ages within 0–541 Ma
  - every `paleo_age` has a slice
  - citations present
  - Thai and English fields both non-empty
- **Science checks:** a script prints Kanchanaburi's paleo-latitude for each slice. The instructor checks the trend against the literature: southern mid-latitudes on the Gondwana margin in the Early Permian, near the equator by the Triassic collision, and the present position at 0 Ma. The 0 Ma slice must return 99.53 E, 14.02 N.
- **Unit tests (JS):**
  - nearest-event selection
  - the non-linear axis mapping is monotonic and every period gets at least the minimum height
  - nearest-slice fallback
  - i18n fallback to English when a Thai string is missing
- **Manual checks:**
  - phone (iOS Safari, Android Chrome) at 375 px width
  - projector at 1920×1080
  - lecture-mode keyboard navigation
  - offline after the first load
  - light and dark themes

## 8. Credits shown in the page

- **Plate model:** Müller et al. (2022), via the GPlates Web Service (EarthByte).
- **Present-day coastlines:** Natural Earth.
- **Time scale:** International Commission on Stratigraphy chart.
- **Inspiration:** the Siam & World parallel timeline.
- **Event citations:** listed on each card, and all of them on an "About" panel.

## 9. Open items

- Lecture-stop selection: Claude proposes 8; the instructor confirms them at review.
- Which near-campus outcrops count as visit sites: the instructor supplies coordinates for any sites not in the literature.
