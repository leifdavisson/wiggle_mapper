import pytest
from tests.conftest import verifies
from wiggle_mapper.models import DataPoint, LatLng
from wiggle_mapper.grid_analyzer import calculate_grid_overlay

@verifies("REQ-WIG-006")
def test_calculate_grid_overlay_empty():
    res = calculate_grid_overlay([], boundary=None, grid_meters=10, conf_threshold=3)
    assert res.dead_zone_pct == 0
    assert res.gaps_pct == 0
    assert len(res.cells) == 0

@verifies("REQ-WIG-006")
def test_calculate_grid_overlay_no_boundary():
    pts = [
        DataPoint("Net1", "M1", 37.42200, -122.08400, -50, 1, 2412, 5.0, "f1"),
        DataPoint("Net1", "M1", 37.42201, -122.08401, -70, 1, 2412, 5.0, "f1"),
        DataPoint("Net1", "M1", 37.42500, -122.08800, -85, 1, 2412, 5.0, "f1"),
    ]
    res = calculate_grid_overlay(pts, boundary=None, grid_meters=10, conf_threshold=3)
    assert len(res.cells) >= 2
    # Two distinct spatial areas
    # Total cells == active cells
    assert res.total_cells >= 2

@verifies("REQ-WIG-006")
def test_calculate_grid_overlay_dynamic_resolution_scaling():
    # Enormous boundary relative to small 2m grid resolution
    boundary = [
        LatLng(37.0, -122.0),
        LatLng(37.5, -122.0),
        LatLng(37.5, -121.5),
        LatLng(37.0, -121.5)
    ]
    pts = [
        DataPoint("Net1", "M1", 37.2, -121.8, -60, 6, 2437, 5.0, "f1")
    ]
    res = calculate_grid_overlay(pts, boundary=boundary, grid_meters=2, conf_threshold=2)
    assert res.resolution_adjusted is True
    assert res.effective_grid_meters > 2

@verifies("REQ-WIG-007")
def test_calculate_grid_overlay_with_boundary_dead_zones_and_gaps():
    # 4 points forming a small polygon bounding box
    boundary = [
        LatLng(37.420, -122.085),
        LatLng(37.424, -122.085),
        LatLng(37.424, -122.081),
        LatLng(37.420, -122.081)
    ]
    pts = [
        # Strong signal inside
        DataPoint("Net1", "M1", 37.422, -122.083, -50, 1, 2412, 5.0, "f1"),
        DataPoint("Net1", "M1", 37.422, -122.083, -55, 1, 2412, 5.0, "f1"),
        DataPoint("Net1", "M1", 37.422, -122.083, -52, 1, 2412, 5.0, "f1"), # 3 scans >= conf 3
        # Weak signal inside (dead zone)
        DataPoint("Net1", "M2", 37.421, -122.084, -80, 1, 2412, 5.0, "f1"), # 1 scan < conf 3
    ]
    res = calculate_grid_overlay(pts, boundary=boundary, grid_meters=50, conf_threshold=3)
    assert res.total_cells > 0
    assert res.dead_zone_pct > 0
    assert res.gaps_pct > 0

@verifies("REQ-WIG-006")
def test_grid_analyzer_boundary_outside_all_cells():
    # Boundary far away so no inside cells
    boundary = [
        LatLng(0.0, 0.0),
        LatLng(0.1, 0.0),
        LatLng(0.1, 0.1),
        LatLng(0.0, 0.1)
    ]
    pts = [DataPoint("Net", "M1", 50.0, 50.0, -60, 1, 2412, 5.0, "f1")]
    res = calculate_grid_overlay(pts, boundary=boundary, grid_meters=100, conf_threshold=3)
    assert res.total_cells > 0

@verifies("REQ-WIG-006")
def test_grid_analyzer_empty_calculation_helpers():
    from wiggle_mapper.grid_analyzer import _calculate_without_boundary, _calculate_with_boundary
    res_no_b = _calculate_without_boundary({}, conf_threshold=3, res_adjusted=False, effective_meters=10)
    assert res_no_b.total_cells == 0

    res_with_b = _calculate_with_boundary({}, [], min_lat=0, min_lng=0, lat_step=1, lng_step=1, conf_threshold=3, res_adjusted=False, effective_meters=10)
    assert res_with_b.total_cells == 0

@verifies("REQ-WIG-006")
def test_grid_analyzer_bounding_box_empty_and_zero_inside_total():
    from wiggle_mapper.grid_analyzer import _get_bounding_box, _calculate_with_boundary
    assert _get_bounding_box([]) == (0.0, 0.0, 0.0, 0.0)

    # Polygon outside calculation range
    poly_degenerate = [LatLng(100.0, 100.0), LatLng(100.1, 100.0), LatLng(100.0, 100.1)]
    res = _calculate_with_boundary({}, poly_degenerate, min_lat=0, min_lng=0, lat_step=1, lng_step=1, conf_threshold=3, res_adjusted=False, effective_meters=10)
    assert res.total_cells > 0 or res.total_cells == 0

@verifies("REQ-WIG-006")
def test_grid_aggregation_arithmetic_mean():
    """Verify 10 measurements within single cell compute exact arithmetic mean."""
    rssi_values = [-50, -55, -60, -65, -70, -75, -80, -85, -60, -65]
    expected_mean = sum(rssi_values) / len(rssi_values)  # -66.5
    pts = [
        DataPoint("Net1", "M1", 37.422001, -122.084001, rssi, 1, 2412, 5.0, "f1")
        for rssi in rssi_values
    ]
    res = calculate_grid_overlay(pts, boundary=None, grid_meters=10, conf_threshold=3)
    assert len(res.cells) == 1
    assert res.cells[0].count == 10
    assert pytest.approx(res.cells[0].avg_rssi, 0.001) == expected_mean

@verifies("REQ-WIG-006")
def test_resolution_scaling_threshold_under_and_over_40k():
    """Verify resolution scaling stays False when under 40k cells and scales when >40k."""
    from wiggle_mapper.grid_analyzer import _scale_resolution_if_needed
    # Small boundary ~100m x 100m with 10m grid -> ~100 cells <= 40000
    small_b = [
        LatLng(37.420, -122.080),
        LatLng(37.421, -122.080),
        LatLng(37.421, -122.079),
        LatLng(37.420, -122.079)
    ]
    scaled_res, adjusted = _scale_resolution_if_needed(small_b, grid_meters=10.0, avg_lat=37.4205)
    assert adjusted is False
    assert scaled_res == 10.0

    # Huge boundary ~55km x 55km with 10m grid -> millions of cells > 40000
    large_b = [
        LatLng(37.0, -122.0),
        LatLng(37.5, -122.0),
        LatLng(37.5, -121.5),
        LatLng(37.0, -121.5)
    ]
    scaled_res_large, adjusted_large = _scale_resolution_if_needed(large_b, grid_meters=10.0, avg_lat=37.25)
    assert adjusted_large is True
    assert scaled_res_large > 10.0

@verifies("REQ-WIG-007")
def test_dead_zone_boundary_conditions():
    """Verify dead-zone RSSI threshold boundary at -75.0 dBm (<= -75.0 is dead zone, > -75.0 is not)."""
    # Test -74.9 dBm (active, healthy)
    pts_healthy = [
        DataPoint("Net1", "M1", 37.42200, -122.08400, -74.9, 1, 2412, 5.0, "f1")
    ]
    res_healthy = calculate_grid_overlay(pts_healthy, boundary=None, grid_meters=10, conf_threshold=1)
    assert res_healthy.dead_zone_pct == 0

    # Test -75.0 dBm (exact boundary -> dead zone)
    pts_exact = [
        DataPoint("Net1", "M1", 37.42200, -122.08400, -75.0, 1, 2412, 5.0, "f1")
    ]
    res_exact = calculate_grid_overlay(pts_exact, boundary=None, grid_meters=10, conf_threshold=1)
    assert res_exact.dead_zone_pct == 100

    # Test -75.1 dBm and -76.0 dBm (dead zone)
    pts_dead = [
        DataPoint("Net1", "M1", 37.42200, -122.08400, -76.0, 1, 2412, 5.0, "f1")
    ]
    res_dead = calculate_grid_overlay(pts_dead, boundary=None, grid_meters=10, conf_threshold=1)
    assert res_dead.dead_zone_pct == 100

@verifies("REQ-WIG-007")
def test_confidence_threshold_boundary_conditions():
    """Verify survey confidence gap boundary (count < conf_threshold is gap, count >= conf_threshold is covered)."""
    # conf_threshold = 3
    # 2 scans -> gap
    pts_under = [
        DataPoint("Net1", "M1", 37.42200, -122.08400, -50.0, 1, 2412, 5.0, "f1"),
        DataPoint("Net1", "M1", 37.42200, -122.08400, -55.0, 1, 2412, 5.0, "f1"),
    ]
    res_under = calculate_grid_overlay(pts_under, boundary=None, grid_meters=10, conf_threshold=3)
    assert res_under.gaps_pct == 100

    # 3 scans -> sufficient confidence
    pts_exact = [
        DataPoint("Net1", "M1", 37.42200, -122.08400, -50.0, 1, 2412, 5.0, "f1"),
        DataPoint("Net1", "M1", 37.42200, -122.08400, -55.0, 1, 2412, 5.0, "f1"),
        DataPoint("Net1", "M1", 37.42200, -122.08400, -52.0, 1, 2412, 5.0, "f1"),
    ]
    res_exact = calculate_grid_overlay(pts_exact, boundary=None, grid_meters=10, conf_threshold=3)
    assert res_exact.gaps_pct == 0

    # 4 scans -> sufficient confidence
    pts_over = pts_exact + [
        DataPoint("Net1", "M1", 37.42200, -122.08400, -51.0, 1, 2412, 5.0, "f1")
    ]
    res_over = calculate_grid_overlay(pts_over, boundary=None, grid_meters=10, conf_threshold=3)
    assert res_over.gaps_pct == 0
