import json

import pytest

import paleo
from paleo import (KANCHANABURI, check_present, fetch_all, fetch_slice, load_slices,
                   simplify_geojson, simplify_line)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status = payload, status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    def json(self):
        return self.payload


SQUARE = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {
    "type": "Polygon", "coordinates": [[[0, 0], [5, 0.01], [10, 0], [10, 10], [0, 10], [0, 0]]]}}]}


class FakeSession:
    def __init__(self, fail_age=None):
        self.fail_age, self.calls = fail_age, []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        if params["time"] == self.fail_age:
            return FakeResponse({}, status=503)
        if "reconstruct_points" in url:
            return FakeResponse({"type": "MultiPoint", "coordinates": [[88.1234, -37.4487]]})
        return FakeResponse(SQUARE)


def test_simplify_line_drops_near_collinear_points():
    pts = [(0, 0), (5, 0.01), (10, 0)]
    assert simplify_line(pts, 0.1) == [(0, 0), (10, 0)]


def test_simplify_line_keeps_far_points():
    pts = [(0, 0), (5, 3), (10, 0)]
    assert simplify_line(pts, 0.1) == pts


def test_simplify_geojson_keeps_closed_rings_and_rounds():
    out = simplify_geojson(SQUARE, tol=0.1, ndigits=1)
    ring = out["features"][0]["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]
    assert [5, 0.0] not in ring
    assert len(ring) == 5


def test_simplify_geojson_drops_degenerate_rings():
    tiny = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {
        "type": "Polygon", "coordinates": [[[0, 0], [0.01, 0], [0.01, 0.01], [0, 0]]]}}]}
    assert simplify_geojson(tiny, tol=0.5)["features"] == []


def test_simplify_geojson_handles_multipolygon():
    multi = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {
        "type": "MultiPolygon", "coordinates": [SQUARE["features"][0]["geometry"]["coordinates"]] * 2}}]}
    geom = simplify_geojson(multi, tol=0.1)["features"][0]["geometry"]
    assert geom["type"] == "MultiPolygon" and len(geom["coordinates"]) == 2


def test_fetch_slice_shape():
    s = fetch_slice(270, FakeSession())
    assert s["age"] == 270 and s["model"] == paleo.MODEL
    assert s["kanchanaburi"] == [88.12, -37.45]
    assert s["coastlines"]["type"] == "FeatureCollection"


def test_fetch_slice_queries_kanchanaburi():
    session = FakeSession()
    fetch_slice(270, session)
    point_call = [c for c in session.calls if "reconstruct_points" in c[0]][0]
    assert point_call[1]["points"] == f"{KANCHANABURI[0]},{KANCHANABURI[1]}"


def test_fetch_all_stops_on_failure_and_names_age(tmp_path, capsys):
    code = fetch_all(tmp_path, FakeSession(fail_age=250), [270, 250, 230])
    assert code == 1
    assert (tmp_path / "270.json").exists()
    assert not (tmp_path / "250.json").exists()
    assert not (tmp_path / "230.json").exists()
    assert "250" in capsys.readouterr().err


def test_fetch_all_skips_existing(tmp_path):
    (tmp_path / "270.json").write_text("{}", encoding="utf-8")
    session = FakeSession()
    assert fetch_all(tmp_path, session, [270]) == 0
    assert session.calls == []


def test_slice_size_limit_enforced(monkeypatch):
    monkeypatch.setattr(paleo, "MAX_SLICE_BYTES", 10)
    with pytest.raises(paleo.SliceTooLargeError):
        fetch_slice(270, FakeSession())


def test_load_slices_and_check_present(tmp_path):
    for age, pt in [(0, [99.53, 14.02]), (270, [88.1, -37.4])]:
        (tmp_path / f"{age}.json").write_text(json.dumps({"age": age, "kanchanaburi": pt}), encoding="utf-8")
    slices = load_slices(tmp_path)
    assert set(slices) == {"0", "270"}
    assert check_present(slices) is None
    slices["0"]["kanchanaburi"] = [98.0, 14.02]
    assert "0 Ma" in check_present(slices)
    del slices["0"]
    assert "missing" in check_present(slices)


class UnplacedSession(FakeSession):
    def get(self, url, params=None, timeout=None):
        if "reconstruct_points" in url:
            return FakeResponse({"type": "MultiPoint", "coordinates": [[999.99, 999.99]]})
        return super().get(url, params, timeout)


def test_fetch_slice_rejects_unplaced_point():
    with pytest.raises(paleo.UnplacedPointError, match="470"):
        fetch_slice(470, UnplacedSession())


def test_fetch_slice_uses_model_constant():
    session = FakeSession()
    s = fetch_slice(270, session)
    assert s["model"] == paleo.MODEL
    assert all(c[1]["model"] == paleo.MODEL for c in session.calls)


def test_present_day_coastlines_use_one_ma_from_same_model(tmp_path):
    session = FakeSession()
    assert fetch_all(tmp_path, session, [0]) == 0
    coast_call = [c for c in session.calls if "coastlines" in c[0]][0]
    point_call = [c for c in session.calls if "reconstruct_points" in c[0]][0]
    assert coast_call[1]["model"] == paleo.MODEL
    assert coast_call[1]["time"] == paleo.PRESENT_COAST_TIME == 1
    assert point_call[1]["time"] == 0
    saved = json.loads((tmp_path / "0.json").read_text(encoding="utf-8"))
    assert saved["coast_time"] == 1 and saved["age"] == 0
