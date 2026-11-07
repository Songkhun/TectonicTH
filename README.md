# Deep Time Kanchanaburi

A teaching page on the geologic and tectonic history of Kanchanaburi, Thailand, in Thai and English. It is a single self-contained HTML file with no network requests at run time.

The page has three tabs:

- **Timeline:** geologic, tectonic and life events in three lanes on the ICS time scale, with a globe showing where Kanchanaburi sat at each time slice (470 Ma to today) and a magnetic polarity column.
- **Map:** a base map of the region with active faults, field evidence, fossil sites and visit sites.
- **Tectonic models:** competing tectonic models for the region, each linked to the evidence for and against it, with schematic sutures and terrane labels.

A lecture mode (larger text, arrow-key navigation) steps through the key events in class.

## Build

Needs Python 3.12 (with `requests`) and Node 20 or later. There are no npm dependencies.

```sh
python3 build/assemble.py            # writes dist/index.html
python3 build/assemble.py --strict   # refuses to build while any event is unverified
```

Open `dist/index.html` in a browser.

## Tests

```sh
python3 -m pytest   # build scripts
npm test            # browser logic (node --test)
```

## Layout

| Folder | Contents |
| --- | --- |
| `src/` | Page HTML, CSS and ES modules (timeline, globe, map, models, fossils, i18n) |
| `content/` | Events, evidence, fossils, models, faults, base map, time scale and polarity data (JSON) |
| `paleo/` | Paleo-coastline slices, one per age in Ma |
| `build/` | Python scripts that fetch, validate and assemble the data into `dist/index.html` |
| `tests/` | pytest and `node --test` suites |
| `docs/` | Design notes and implementation plans |
| `vendor/` | D3 v7 |

To add evidence, fill rows in `content/evidence_template.csv` and run `python3 build/import_evidence.py rows.csv`. To make a review table for the instructor, run `python3 build/review_table.py`.

## Data sources

- Paleogeography: [GPlates Web Service](https://gws.gplates.org), TorsvikCocks2017 model
- Time scale: International Chronostratigraphic Chart (ICS) v2024/12
- Magnetic polarity: GTS2020 chrons via [PmagPy](https://github.com/PmagPy/PmagPy); Mesozoic M-sequence from the GSA Geologic Time Scale v6.0
- Active faults: [GEM Global Active Faults Database](https://github.com/GEMScienceTools/gem-global-active-faults)
- Base map: [Natural Earth](https://www.naturalearthdata.com/) 1:50m

## License

[MIT](LICENSE). Third-party data and D3 (`vendor/d3.min.js`, ISC licence) keep their own licences; see Data sources.

## Author

Songkhun Boonchaisuk, Mahidol University
