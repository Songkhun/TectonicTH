"""Export events to review/review.csv and review/review.md for the instructor."""
import csv
import sys
from pathlib import Path

from evidence import load_evidence
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


EVIDENCE_COLUMNS = ["id", "event_ids", "method", "title_th", "title_en", "finding_th", "finding_en", "value",
                    "paleolat", "site", "citation", "source_type", "verified", "notes", "corrections"]


def _evidence_row(it):
    site, cite, pl = it.get("site"), it.get("citation"), it.get("paleolat")
    return {
        "id": it["id"], "event_ids": "; ".join(it["event_ids"]), "method": it["method"],
        "title_th": it["title_th"], "title_en": it["title_en"],
        "finding_th": it["finding_th"], "finding_en": it["finding_en"],
        "value": it.get("value") or "",
        "paleolat": (f"{pl['deg']:g}" + (f" ± {pl['err']:g}" if pl.get("err") is not None else "")) if pl else "",
        "site": f"{site['name_en']} ({site['lat']}, {site['lon']})" if site else "",
        "citation": f"{cite['text']} — {cite['url']}" if cite else "",
        "source_type": it["source_type"],
        "verified": "yes" if it["verified"] else "no",
        "notes": it.get("_notes", ""),
        "corrections": "",
    }


def write_evidence_review(items, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [_evidence_row(it) for it in items]
    csv_path = out_dir / "evidence_review.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EVIDENCE_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    md_path = out_dir / "evidence_review.md"
    cell = lambda v: str(v).replace("|", "\\|").replace("\n", " ")  # noqa: E731
    lines = ["| " + " | ".join(EVIDENCE_COLUMNS) + " |", "|" + "---|" * len(EVIDENCE_COLUMNS)]
    lines += ["| " + " | ".join(cell(r[c]) for c in EVIDENCE_COLUMNS) + " |" for r in rows]
    md_path.write_text("# Deep Time Kanchanaburi — evidence review\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    paths = write_review(load_json(root / "content/events.json"), root / "review")
    paths += write_evidence_review(load_evidence(root / "content/evidence.json"), root / "review")
    print("\n".join(str(p) for p in paths))
    sys.exit(0)
