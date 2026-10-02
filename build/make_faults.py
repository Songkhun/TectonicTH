"""Write content/faults.json: GEM Global Active Faults Database traces for the map region.
Usage: python3 build/make_faults.py   (needs network)"""
import json
from pathlib import Path

import requests

from basemap import clip_features
from make_basemap import BOX

GEM_COMMIT = "56816508ad92fd6846dad1163b1c8c01376a2cd1"
GEM_URL = (f"https://raw.githubusercontent.com/GEMScienceTools/gem-global-active-faults/{GEM_COMMIT}"
           "/geojson/gem_active_faults_harmonized.geojson")

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    fc = requests.get(GEM_URL, timeout=300).json()
    out = {"bbox": BOX, "source": {"text": "GEM Global Active Faults Database (Styron & Pagani 2020, Earthquake Spectra 36:160–180), CC BY-SA 4.0",
                                   "url": "https://doi.org/10.1177/8755293020944182", "commit": GEM_COMMIT,
                                   "license": "CC BY-SA 4.0"},
           "faults": clip_features(fc, BOX, tol=0.01, ndigits=3, keep=("slip_type", "catalog_name"))}
    path = root / "content/faults.json"
    path.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"faults: {len(out['faults']['features'])} traces, {path.stat().st_size // 1024} KB")
