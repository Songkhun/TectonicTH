"""Export events to review/review.csv and review/review.md for the instructor."""
import csv
import sys
from pathlib import Path

from validate import load_json

COLUMNS = ["id", "lane", "age_ma", "age_uncertainty_ma", "title_th", "title_en", "body_th", "body_en",
           "rock_unit", "visit_site", "citation", "lecture_stop", "verified", "notes", "corrections"]


def _row(e):
    site = e.get("visit_site")
    cite = e.get("citation")
    return {
        "id": e["id"], "lane": e["lane"], "age_ma": e["age_ma"],
        "age_uncertainty_ma": "" if e.get("age_uncertainty_ma") is None else e["age_uncertainty_ma"],
        "title_th": e["title_th"], "title_en": e["title_en"],
        "body_th": e.get("body_th", ""), "body_en": e.get("body_en", ""),
        "rock_unit": e.get("rock_unit") or "",
        "visit_site": f"{site['name_en']} ({site['lat']}, {site['lon']})" if site else "",
        "citation": f"{cite['text']} — {cite['url']}" if cite else "",
        "lecture_stop": "yes" if e["lecture_stop"] else "no",
        "verified": "yes" if e["verified"] else "no",
        "notes": e.get("_notes", ""),
        "corrections": "",
    }


def write_review(events, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [_row(e) for e in sorted(events, key=lambda e: -e["age_ma"])]
    csv_path = out_dir / "review.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    md_path = out_dir / "review.md"
    cell = lambda v: str(v).replace("|", "\\|").replace("\n", " ")  # noqa: E731
    lines = ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    lines += ["| " + " | ".join(cell(r[c]) for c in COLUMNS) + " |" for r in rows]
    md_path.write_text("# Deep Time Kanchanaburi — content review\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    paths = write_review(load_json(root / "content/events.json"), root / "review")
    print("\n".join(str(p) for p in paths))
    sys.exit(0)
