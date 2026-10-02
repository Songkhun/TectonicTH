"""Digitize the Mesozoic M-sequence from the GSA Geologic Time Scale v6.0 chart (vector PDF) into
content/msequence_gsa_v6.json. Normal chrons are drawn as thick horizontal strokes (and filled blocks)
in the polarity column; ages come from a least-squares fit of the chart's own 100–160 Ma tick labels.
Usage: python3 build/digitize_gsa_msequence.py path/to/timescl.pdf   (needs poppler: pdftocairo, pdftotext)"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from polarity import check_digitization, mseq_from_blocks, recalibrate

COLUMN_X = (249.5, 261.0)   # polarity column of the Mesozoic panel, in PDF points
TICKS = range(100, 170, 10)

# Stage-boundary ages printed on the GSA v6.0 chart (Aptian … Bajocian bases) paired with the same
# boundaries in ICS v2024/12 (GTS2020). Stage boundaries are tied to chrons (e.g. Aptian base = base of
# M0r), so mapping through them puts the chart's chrons on the time scale used by the rest of the page.
GSA_TO_ICS2024 = [(125.0, 121.4), (129.4, 125.77), (132.6, 132.6), (139.8, 137.05), (145.0, 143.1),
                  (152.1, 149.2), (157.3, 154.8), (163.5, 161.5), (166.1, 165.3), (168.3, 168.2), (170.3, 170.9)]


def _words(pdf):
    html = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    return [(float(a), float(b), float(c), float(d), t) for a, b, c, d, t in
            re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', html)]


def _age_fit(words, label_x):
    pts = [((w[1] + w[3]) / 2, int(w[4])) for w in words
           if w[4].isdigit() and int(w[4]) in TICKS and abs(w[0] - label_x) < 60]
    pts = sorted(dict((age, y) for y, age in pts).items())
    n = len(pts)
    sy = sum(y for _, y in pts); sa = sum(a for a, _ in pts)
    syy = sum(y * y for _, y in pts); sya = sum(a * y for a, y in pts)
    slope = (n * sya - sy * sa) / (n * syy - sy * sy)
    icpt = (sa - slope * sy) / n
    resid = max(abs(slope * y + icpt - a) for a, y in pts)
    return (lambda y: slope * y + icpt), resid, n


def digitize(pdf):
    words = _words(pdf)
    labels = [w for w in words if re.fullmatch(r"M\d+r?", w[4])]
    fit, resid, nticks = _age_fit(words, min(w[0] for w in labels))
    with tempfile.TemporaryDirectory() as tmp:
        svg_path = Path(tmp) / "chart.svg"
        subprocess.run(["pdftocairo", "-svg", str(pdf), str(svg_path)], check=True)
        svg = svg_path.read_text()
    normals, mixed, cns = [], [], None
    for m in re.finditer(r"<path ([^>]*?)/>", svg):
        p = m.group(1)
        t = re.search(r'transform="matrix\(([^)]+)\)"', p)
        a = b = 1.0
        e = f = 0.0
        if t:
            a, rot1, rot2, b, e, f = [float(x) for x in t.group(1).replace(",", " ").split()]
            if rot1 or rot2 or abs(abs(b) - 1) > 1e-6 or abs(abs(a) - 1) > 1e-6:
                raise ValueError("unexpected scaled or rotated drawing transform; the chart layout has changed")
        line = re.search(r' d="M ([-\d.]+) ([-\d.]+) L ([-\d.]+) ([-\d.]+) "', p)
        if line and "stroke-width" in p and 'fill="none"' in p:
            x0, x1 = a * float(line.group(1)) + e, a * float(line.group(3)) + e
            y = b * float(line.group(2)) + f
            w = float(re.search(r'stroke-width="([\d.]+)"', p).group(1))
            if COLUMN_X[0] <= min(x0, x1) <= COLUMN_X[0] + 3 and max(x0, x1) >= COLUMN_X[1] - 3:
                normals.append((fit(y - w / 2), fit(y + w / 2)))
            continue
        fill = re.search(r'fill="rgb\(([\d.]+)%', p)
        d = re.search(r' d="([^"]+)"', p)
        if not (fill and d):
            continue
        for sub in re.split(r"(?=M)", d.group(1)):
            nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", sub)]
            if len(nums) < 6:
                continue
            xs = [a * x + e for x in nums[0::2]]
            ys = [b * y + f for y in nums[1::2]]
            if not (COLUMN_X[0] <= min(xs) and max(xs) <= COLUMN_X[1] and max(xs) - min(xs) > 6):
                continue
            top, base = fit(min(ys)), fit(max(ys))
            dark = float(fill.group(1)) < 30
            if dark and top < 100 < base:
                cns = base                      # Cretaceous Normal Superchron block: its base starts the M-sequence
            elif dark and 115 < top < 170:
                normals.append((top, base))
            elif 40 <= float(fill.group(1)) <= 80 and 115 < top < 175:
                mixed.append((top, base))           # grey = poorly known
    normals = [(t, bse) for t, bse in normals if cns and t >= cns - 1e-6 and t < 175]
    check_digitization(nticks, resid, cns, len(normals), len(labels))
    base_ma = max(b for _, b in normals + mixed)
    # The Aptian base is defined at the base of M0r: tie it to the drawn M0r base rather than the
    # chart's rounded "~125" label.
    m0r_base = min(a for a, _ in normals)
    ties = [(m0r_base, 121.4)] + GSA_TO_ICS2024[1:]
    rc = lambda x: recalibrate(x, ties)  # noqa: E731
    out = mseq_from_blocks(rc(cns), [(rc(a), rc(b)) for a, b in normals], [(rc(a), rc(b)) for a, b in mixed],
                           [(w[4], rc(fit((w[1] + w[3]) / 2))) for w in labels], rc(base_ma))
    out["calibration"] = {"ticks_used": nticks, "max_tick_residual_myr": round(resid, 3),
                          "chart_cns_base_ma": round(cns, 3), "ties_gsa_to_ics2024": [[round(a, 3), b] for a, b in ties],
                          "note": "Chron pattern read from the GSA v6.0 chart's vector geometry, then rescaled "
                                  "piecewise-linearly from the chart's printed stage-boundary ages to ICS v2024/12 "
                                  "(GTS2020) ones. Ages are approximate."}
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    root = Path(__file__).resolve().parent.parent
    out = digitize(sys.argv[1])
    (root / "content/msequence_gsa_v6.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    segs = out["segments"]
    print(f"{len(segs)} M-sequence segments, {segs[0]['top_ma']}–{segs[-1]['base_ma']} Ma; "
          f"tick residual {out['calibration']['max_tick_residual_myr']} Myr")
