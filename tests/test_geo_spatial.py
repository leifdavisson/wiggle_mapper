import math
import pytest
from hypothesis import given, strategies as st
from tests.conftest import verifies
from models import LatLng
from geo_spatial import (
    calculate_degree_steps,
    calculate_distance_meters,
    is_point_in_polygon,
    convex_hull
)

@verifies("REQ-WIG-003")
def test_calculate_degree_steps():
    # Test at equator
    lat_step_eq, lng_step_eq = calculate_degree_steps(grid_meters=10.0, avg_lat=0.0)
    assert lat_step_eq == pytest.approx(10.0 / 111320)
    assert lng_step_eq == pytest.approx(10.0 / 111320)

    # Test at latitude 60 degrees (cos(60 deg) = 0.5)
    lat_step_60, lng_step_60 = calculate_degree_steps(grid_meters=10.0, avg_lat=60.0)
    assert lat_step_60 == pytest.approx(10.0 / 111320)
    assert lng_step_60 == pytest.approx(10.0 / (111320 * 0.5))

@verifies("REQ-WIG-003")
@given(
    lat=st.floats(min_value=-85.0, max_value=85.0),
    meters=st.floats(min_value=1.0, max_value=1000.0)
)
def test_calculate_degree_steps_property(lat: float, meters: float):
    lat_step, lng_step = calculate_degree_steps(grid_meters=meters, avg_lat=lat)
    assert lat_step > 0
    assert lng_step > 0
    # Step in degrees longitude should be >= step in degrees latitude for any lat
    assert lng_step >= lat_step - 1e-9

@verifies("REQ-WIG-003")
def test_calculate_distance_meters():
    p1 = LatLng(37.4220, -122.0840)
    p2 = LatLng(37.4220, -122.0840)
    assert calculate_distance_meters(p1, p2, 37.4220) == 0.0

    # Moving exactly 1 degree North at lat 0 should be approx 111,320m
    d = calculate_distance_meters(LatLng(0.0, 0.0), LatLng(1.0, 0.0), 0.0)
    assert d == pytest.approx(111320.0, rel=1e-3)

@verifies("REQ-WIG-004")
def test_is_point_in_polygon_rectangle():
    poly = [
        LatLng(10.0, 10.0),
        LatLng(10.0, 20.0),
        LatLng(20.0, 20.0),
        LatLng(20.0, 10.0)
    ]
    # Inside
    assert is_point_in_polygon(LatLng(15.0, 15.0), poly) is True
    # Outside
    assert is_point_in_polygon(LatLng(5.0, 15.0), poly) is False
    assert is_point_in_polygon(LatLng(25.0, 15.0), poly) is False
    assert is_point_in_polygon(LatLng(15.0, 5.0), poly) is False
    assert is_point_in_polygon(LatLng(15.0, 25.0), poly) is False

@verifies("REQ-WIG-004")
def test_is_point_in_polygon_triangle():
    triangle = [
        LatLng(0.0, 0.0),
        LatLng(10.0, 0.0),
        LatLng(0.0, 10.0)
    ]
    assert is_point_in_polygon(LatLng(2.0, 2.0), triangle) is True
    assert is_point_in_polygon(LatLng(8.0, 8.0), triangle) is False

@verifies("REQ-WIG-005")
def test_convex_hull_standard():
    pts = [
        LatLng(0.0, 0.0),
        LatLng(10.0, 0.0),
        LatLng(10.0, 10.0),
        LatLng(0.0, 10.0),
        LatLng(5.0, 5.0) # Internal point
    ]
    hull = convex_hull(pts)
    assert len(hull) == 4
    # Check that (5,5) is not in the hull
    assert not any(p.lat == 5.0 and p.lng == 5.0 for p in hull)

@verifies("REQ-WIG-005")
def test_convex_hull_few_points_or_collinear():
    pts_two = [LatLng(0.0, 0.0), LatLng(1.0, 1.0)]
    assert len(convex_hull(pts_two)) <= 2

    # Collinear points
    collinear = [LatLng(0.0, 0.0), LatLng(1.0, 1.0), LatLng(2.0, 2.0)]
    hull_collinear = convex_hull(collinear)
    assert len(hull_collinear) <= 3

@verifies("REQ-WIG-004")
def test_is_point_in_polygon_less_than_3_vertices():
    # Degenerate polygon with fewer than 3 vertices
    assert is_point_in_polygon(LatLng(10.0, 10.0), []) is False
    assert is_point_in_polygon(LatLng(10.0, 10.0), [LatLng(0.0, 0.0), LatLng(1.0, 1.0)]) is False

@verifies("REQ-WIG-003")
def test_calculate_degree_steps_polar_extremes():
    # Extreme north latitude (89 degrees)
    lat_step_89, lng_step_89 = calculate_degree_steps(grid_meters=10.0, avg_lat=89.0)
    assert lat_step_89 == pytest.approx(10.0 / 111320.0)
    cos_89 = math.cos(math.radians(89.0))
    assert lng_step_89 == pytest.approx(10.0 / (111320.0 * cos_89))
    assert lng_step_89 > lat_step_89 * 50  # Longitude degrees shrink near poles

    # Extreme south latitude (-89.5 degrees)
    lat_step_s, lng_step_s = calculate_degree_steps(grid_meters=5.0, avg_lat=-89.5)
    cos_s = math.cos(math.radians(-89.5))
    assert lat_step_s == pytest.approx(5.0 / 111320.0)
    assert lng_step_s == pytest.approx(5.0 / (111320.0 * cos_s))

@verifies("REQ-WIG-003")
def test_calculate_distance_meters_polar_and_axes():
    # East-West distance at latitude 60
    p1 = LatLng(60.0, 10.0)
    p2 = LatLng(60.0, 11.0)
    d = calculate_distance_meters(p1, p2, ref_lat=60.0)
    expected_ew = 1.0 * 111320.0 * math.cos(math.radians(60.0))
    assert d == pytest.approx(expected_ew, rel=1e-4)

    # North-South distance across equator
    p_s = LatLng(-1.0, 0.0)
    p_n = LatLng(1.0, 0.0)
    d_ns = calculate_distance_meters(p_s, p_n, ref_lat=0.0)
    assert d_ns == pytest.approx(2.0 * 111320.0, rel=1e-4)

@verifies("REQ-WIG-004")
def test_is_point_in_polygon_boundary_and_concave():
    # Boundary and vertex edge cases on a square [0, 10] x [0, 10]
    poly = [
        LatLng(0.0, 0.0),
        LatLng(0.0, 10.0),
        LatLng(10.0, 10.0),
        LatLng(10.0, 0.0)
    ]
    # Center is unambiguously inside
    assert is_point_in_polygon(LatLng(5.0, 5.0), poly) is True
    # Far outside points in 4 cardinal directions
    assert is_point_in_polygon(LatLng(-5.0, 5.0), poly) is False
    assert is_point_in_polygon(LatLng(15.0, 5.0), poly) is False
    assert is_point_in_polygon(LatLng(5.0, -5.0), poly) is False
    assert is_point_in_polygon(LatLng(5.0, 15.0), poly) is False

    # Concave (U-shaped / cavity) polygon
    u_poly = [
        LatLng(0.0, 0.0),
        LatLng(0.0, 30.0),
        LatLng(30.0, 30.0),
        LatLng(30.0, 20.0),
        LatLng(10.0, 20.0),
        LatLng(10.0, 10.0),
        LatLng(30.0, 10.0),
        LatLng(30.0, 0.0)
    ]
    # Inside one of the arms
    assert is_point_in_polygon(LatLng(20.0, 5.0), u_poly) is True
    assert is_point_in_polygon(LatLng(5.0, 15.0), u_poly) is True
    # Inside the cavity (exterior to the polygon)
    assert is_point_in_polygon(LatLng(20.0, 15.0), u_poly) is False

@verifies("REQ-WIG-005")
def test_convex_hull_collinear_edges_and_line():
    # Square with intermediate collinear points on every side
    pts_with_collinear = [
        LatLng(0.0, 0.0), LatLng(0.0, 5.0), LatLng(0.0, 10.0),
        LatLng(5.0, 10.0), LatLng(10.0, 10.0),
        LatLng(10.0, 5.0), LatLng(10.0, 0.0),
        LatLng(5.0, 0.0),
        LatLng(5.0, 5.0)  # Internal point
    ]
    hull = convex_hull(pts_with_collinear)
    assert len(hull) == 4
    hull_coords = {(p.lat, p.lng) for p in hull}
    assert hull_coords == {(0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0)}

    # Purely 1D collinear points
    line_pts = [
        LatLng(0.0, 0.0),
        LatLng(3.0, 3.0),
        LatLng(1.0, 1.0),
        LatLng(4.0, 4.0),
        LatLng(2.0, 2.0)
    ]
    line_hull = convex_hull(line_pts)
    line_hull_coords = {(p.lat, p.lng) for p in line_hull}
    assert line_hull_coords == {(0.0, 0.0), (4.0, 4.0)}

@verifies("REQ-WIG-005")
def test_convex_hull_input_ordering_invariance():
    # CCW order
    ccw_pts = [
        LatLng(0.0, 0.0),
        LatLng(10.0, 0.0),
        LatLng(10.0, 10.0),
        LatLng(0.0, 10.0),
        LatLng(5.0, 5.0)
    ]
    # CW order
    cw_pts = [
        LatLng(0.0, 0.0),
        LatLng(0.0, 10.0),
        LatLng(10.0, 10.0),
        LatLng(10.0, 0.0),
        LatLng(5.0, 5.0)
    ]
    # Permuted order
    permuted_pts = [
        LatLng(5.0, 5.0),
        LatLng(10.0, 10.0),
        LatLng(0.0, 0.0),
        LatLng(0.0, 10.0),
        LatLng(10.0, 0.0)
    ]

    hull_ccw = convex_hull(ccw_pts)
    hull_cw = convex_hull(cw_pts)
    hull_perm = convex_hull(permuted_pts)

    assert [(p.lat, p.lng) for p in hull_ccw] == [(p.lat, p.lng) for p in hull_cw]
    assert [(p.lat, p.lng) for p in hull_ccw] == [(p.lat, p.lng) for p in hull_perm]

@verifies("REQ-WIG-005")
def test_convex_hull_empty_and_single():
    assert convex_hull([]) == []
    single = [LatLng(37.0, -122.0)]
    assert convex_hull(single) == single
