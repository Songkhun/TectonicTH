"""Write content/basemap.json: Natural Earth 1:50m land and land borders for the map tab.
Usage: python3 build/make_basemap.py   (needs network)"""
import json
from pathlib import Path

import requests

from basemap import clip_features

NE_COMMIT = "ca96624a56bd078437bca8184e78163e5039ad19"
NE = f"https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{NE_COMMIT}/geojson"
BOX = (85.0, -12.0, 125.0, 32.0)

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    land = requests.get(f"{NE}/ne_50m_land.geojson", timeout=120).json()
    borders = requests.get(f"{NE}/ne_50m_admin_0_boundary_lines_land.geojson", timeout=120).json()
    out = {"bbox": BOX, "source": {"text": "Natural Earth 1:50m land and boundary lines (public domain)",
                                   "url": "https://www.naturalearthdata.com/", "commit": NE_COMMIT},
           "land": clip_features(land, BOX, tol=0.02, ndigits=3),
           "borders": clip_features(borders, BOX, tol=0.02, ndigits=3)}
    path = root / "content/basemap.json"
    path.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"basemap: {len(out['land']['features'])} land, {len(out['borders']['features'])} border features, "
          f"{path.stat().st_size // 1024} KB")
