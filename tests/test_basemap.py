from basemap import clip_line, clip_ring, clip_features

BOX = (0.0, 0.0, 10.0, 10.0)  # lon_min, lat_min, lon_max, lat_max


def test_ring_inside_is_unchanged():
    ring = [[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]]
    assert clip_ring(ring, BOX) == ring


def test_ring_crossing_the_box_is_cut_at_the_edge():
    ring = [[5, 5], [15, 5], [15, 8], [5, 8], [5, 5]]
    out = clip_ring(ring, BOX)
    assert out[0] == out[-1]
    assert max(p[0] for p in out) == 10.0 and min(p[0] for p in out) == 5
    assert all(0 <= p[0] <= 10 and 0 <= p[1] <= 10 for p in out)


def test_ring_outside_is_dropped():
    assert clip_ring([[20, 20], [21, 20], [21, 21], [20, 20]], BOX) is None


def test_line_leaving_and_reentering_splits_into_parts():
    line = [[1, 1], [5, 1], [12, 1], [12, 5], [5, 5], [2, 5]]
    parts = clip_line(line, BOX)
    assert len(parts) == 2
    assert parts[0][0] == [1, 1] and parts[0][-1] == [10.0, 1.0]
    assert parts[1][0] == [10.0, 5.0] and parts[1][-1] == [2, 5]


def test_line_outside_is_dropped():
    assert clip_line([[20, 1], [30, 1]], BOX) == []


def test_clip_features_keeps_properties_and_drops_empty():
    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"slip_type": "Dextral"}, "geometry": {"type": "LineString", "coordinates": [[1, 1], [3, 3], [4, 4]]}},
        {"type": "Feature", "properties": {}, "geometry": {"type": "LineString", "coordinates": [[50, 50], [51, 51]]}},
        {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [[[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]]]}},
    ]}
    out = clip_features(fc, BOX, tol=0.0, ndigits=2, keep=("slip_type",))
    assert len(out["features"]) == 2
    assert out["features"][0]["properties"] == {"slip_type": "Dextral"}
    assert out["features"][1]["geometry"]["type"] == "Polygon"
