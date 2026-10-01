"""Print Kanchanaburi's paleo-position per slice for the instructor's science check."""
import sys
from pathlib import Path

from paleo import check_present, load_slices

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    slices = load_slices(root / "paleo")
    print(f"{'age (Ma)':>9}  {'lon':>8}  {'lat':>7}  hemisphere")
    for key in sorted(slices, key=lambda k: -float(k)):
        lon, lat = slices[key]["kanchanaburi"]
        print(f"{key:>9}  {lon:>8.2f}  {lat:>7.2f}  {'S' if lat < 0 else 'N'}")
    problem = check_present(slices)
    if problem:
        print(f"FAIL: {problem}", file=sys.stderr)
        sys.exit(1)
    print("OK: 0 Ma position matches Kanchanaburi town")
