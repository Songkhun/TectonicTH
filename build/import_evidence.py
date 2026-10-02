"""Append rows from an evidence CSV (see content/evidence_template.csv) to content/evidence.json.
Usage: python3 build/import_evidence.py path/to/rows.csv"""
import sys
from pathlib import Path

from evidence import import_rows
from validate import load_json

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    root = Path(__file__).resolve().parent.parent
    event_ids = {e["id"] for e in load_json(root / "content/events.json")}
    errors = import_rows(sys.argv[1], root / "content/evidence.json", event_ids)
    if errors:
        print("NOT IMPORTED:\n  " + "\n  ".join(errors), file=sys.stderr)
        sys.exit(1)
    print("imported; all new items are verified: false")
