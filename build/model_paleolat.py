"""Add the plate model's paleolatitude at each paleomagnetic sampling site to content/evidence.json.
Usage: python3 build/model_paleolat.py   (needs network; GPlates Web Service)"""
import json
import sys
from pathlib import Path

import requests

from evidence import add_model_paleolat, load_evidence
from validate import load_json

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    ages = {e["id"]: e["age_ma"] for e in load_json(root / "content/events.json")}
    path = root / "content/evidence.json"
    items = add_model_paleolat(load_evidence(path), ages, requests.Session())
    path.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    done = [it["id"] for it in items if it.get("model_paleolat")]
    print(f"model paleolatitude added for {len(done)} item(s): {', '.join(done) or 'none'}")
    sys.exit(0)
