"""Write content/polarity.json from the GTS2020 chron table in PmagPy (pinned commit) plus superchrons.
Usage: python3 build/make_polarity.py   (needs network)"""
import ast
import json
from pathlib import Path

import requests

from polarity import SOURCES, SUPERCHRONS, build_segments, validate_polarity
from validate import load_json

PMAGPY_COMMIT = "3264d53d5475f94c051c7eb1c4209d42653b7fb9"
PMAG_URL = f"https://raw.githubusercontent.com/PmagPy/PmagPy/{PMAGPY_COMMIT}/pmagpy/pmag.py"


def gts2020_from_pmagpy(src):
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_ts")
    ns = {}
    exec("import numpy as np\n" + ast.get_source_segment(src, fn), ns)  # noqa: S102 — pinned upstream source
    ts, labels = ns["get_ts"]("gts20")
    return [float(x) for x in ts], [[str(n), float(a)] for n, a in labels]


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    oldest = max(p["start_ma"] for p in load_json(root / "content/timescale.json"))
    ts, labels = gts2020_from_pmagpy(requests.get(PMAG_URL, timeout=60).text)
    segs = build_segments(ts, labels, SUPERCHRONS, oldest)
    errors = validate_polarity(segs, oldest)
    if errors:
        raise SystemExit("\n".join(errors))
    out = {"sources": SOURCES, "pmagpy_commit": PMAGPY_COMMIT, "segments": segs}
    (root / "content/polarity.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(segs)} polarity segments (C-sequence back to {ts[-1]} Ma)")
