import pytest

from polarity import SUPERCHRONS, build_segments, validate_polarity

TS = [0.0, 0.773, 0.99, 1.07, 82.875]
LABELS = [["C1n", 0.0], ["C1r", 0.773], ["C33r", 1.07]]


def test_c_sequence_alternates_from_normal_and_takes_labels():
    segs = build_segments(TS, LABELS, SUPERCHRONS, 486.85)
    first = segs[:4]
    assert [s["polarity"] for s in first] == ["normal", "reversed", "normal", "reversed"]
    assert [s["name"] for s in first] == ["C1n", "C1r", "C1r", "C33r"]
    assert first[0]["top_ma"] == 0.0 and first[0]["base_ma"] == 0.773
    assert all(s["source"] == "gts2020" for s in first)


def test_older_record_uses_superchrons_and_mixed_gaps():
    segs = build_segments(TS, LABELS, SUPERCHRONS, 486.85)
    older = [(s["top_ma"], s["base_ma"], s["polarity"], s["name"]) for s in segs[4:]]
    assert older[0] == (82.875, 121.4, "normal", "Cretaceous Normal Superchron (C34n)")
    assert (265.0, 318.0, "reversed", "Kiaman Reverse Superchron") in older
    assert older[-1][1] == 486.85
    assert any(p == "mixed" for _, _, p, _ in older)


def test_built_segments_validate():
    segs = build_segments(TS, LABELS, SUPERCHRONS, 486.85)
    assert validate_polarity(segs, 486.85) == []


@pytest.mark.parametrize("mutate, fragment", [
    (lambda s: s.__setitem__(1, {**s[1], "top_ma": 0.8}), "gap or overlap"),
    (lambda s: s.__setitem__(0, {**s[0], "polarity": "sideways"}), "polarity"),
    (lambda s: s.__setitem__(0, {**s[0], "top_ma": 0.5}), "start at 0"),
    (lambda s: s.pop(), "end at 486.85"),
    (lambda s: s.__setitem__(2, {**s[2], "base_ma": s[2]["top_ma"]}), "base_ma"),
])
def test_bad_segments_rejected(mutate, fragment):
    segs = build_segments(TS, LABELS, SUPERCHRONS, 486.85)
    mutate(segs)
    assert any(fragment in e for e in validate_polarity(segs, 486.85))


MSEQ = {"source": "gsa_v6", "segments": [
    {"top_ma": 124.1, "base_ma": 124.8, "polarity": "reversed", "name": "M-sequence (≈M0r)", "source": "gsa_v6", "approx": True},
    {"top_ma": 124.8, "base_ma": 127.0, "polarity": "normal", "name": "M-sequence (≈M1)", "source": "gsa_v6", "approx": True},
    {"top_ma": 127.0, "base_ma": 154.3, "polarity": "reversed", "name": "M-sequence", "source": "gsa_v6", "approx": True},
    {"top_ma": 154.3, "base_ma": 165.2, "polarity": "mixed", "name": "M-sequence (poorly known)", "source": "gsa_v6", "approx": True},
]}


def test_m_sequence_replaces_mixed_after_the_cretaceous_superchron():
    segs = build_segments(TS, LABELS, SUPERCHRONS, 486.85, mseq=MSEQ)
    cns = next(s for s in segs if s["name"].startswith("Cretaceous Normal"))
    assert cns["base_ma"] == 124.1
    i = segs.index(cns)
    assert [s["name"] for s in segs[i + 1:i + 5]] == [s["name"] for s in MSEQ["segments"]]
    assert segs[i + 5]["top_ma"] == 165.2 and segs[i + 5]["polarity"] == "mixed"
    assert validate_polarity(segs, 486.85) == []


def test_without_m_sequence_cns_base_stays_gts2020():
    segs = build_segments(TS, LABELS, SUPERCHRONS, 486.85)
    assert next(s for s in segs if s["name"].startswith("Cretaceous Normal"))["base_ma"] == 121.4


def test_digitized_strokes_become_contiguous_segments():
    from polarity import mseq_from_blocks
    out = mseq_from_blocks(cns_base=124.1, normals=[(124.8, 127.0), (127.7, 128.2)], mixed=[(154.3, 164.8)],
                           labels=[("M0r", 124.2), ("M1", 125.7)], base_ma=165.2)
    names = [(s["top_ma"], s["base_ma"], s["polarity"], s["name"]) for s in out["segments"]]
    assert names[0] == (124.1, 124.8, "reversed", "M-sequence (≈M0r)")
    assert names[1] == (124.8, 127.0, "normal", "M-sequence (≈M1)")
    assert names[2][2] == "reversed" and names[3][2] == "normal"
    assert (154.3, 164.8, "mixed", "M-sequence (poorly known)") in names
    assert names[-1][1] == 165.2
    assert all(a["base_ma"] == b["top_ma"] for a, b in zip(out["segments"], out["segments"][1:]))
