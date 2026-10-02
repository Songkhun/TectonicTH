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
