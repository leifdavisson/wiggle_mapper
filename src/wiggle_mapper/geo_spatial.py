# License: GNU AGPLv3 (GNU Affero General Public License v3.0)
import math
from typing import List, Tuple
from wiggle_mapper.models import LatLng

def calculate_degree_steps(grid_meters: float, avg_lat: float) -> Tuple[float, float]:
    """Calculate latitude and longitude degree offsets for a given meter grid spacing."""
    lat_step = grid_meters / 111320.0
    rad = math.radians(avg_lat)
    lng_step = grid_meters / (111320.0 * math.cos(rad))
    return lat_step, lng_step

def calculate_distance_meters(p1: LatLng, p2: LatLng, ref_lat: float) -> float:
    """Calculate approximate Euclidean distance in meters on the spherical plane."""
    dist_y = (p2.lat - p1.lat) * 111320.0
    dist_x = (p2.lng - p1.lng) * (111320.0 * math.cos(math.radians(ref_lat)))
    return math.sqrt(dist_x * dist_x + dist_y * dist_y)

def is_point_in_polygon(point: LatLng, polygon: List[LatLng]) -> bool:
    """Ray-casting algorithm to determine if point is inside a polygon."""
    x = point.lat
    y = point.lng
    inside = False
    n = len(polygon)
    if n < 3:
        return False

    j = n - 1
    for i in range(n):
        xi, yi = polygon[i].lat, polygon[i].lng
        xj, yj = polygon[j].lat, polygon[j].lng
        
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside

def _cross_product(o: LatLng, a: LatLng, b: LatLng) -> float:
    """2D cross product of OA and OB vectors."""
    return (a.lng - o.lng) * (b.lat - o.lat) - (a.lat - o.lat) * (b.lng - o.lng)

def convex_hull(points: List[LatLng]) -> List[LatLng]:
    """Compute the convex hull of a set of 2D points using Andrew's Monotone Chain."""
    if len(points) <= 2:
        return list(points)

    sorted_pts = sorted(points, key=lambda p: (p.lat, p.lng))

    lower: List[LatLng] = []
    for p in sorted_pts:
        while len(lower) >= 2 and _cross_product(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper: List[LatLng] = []
    for p in reversed(sorted_pts):
        while len(upper) >= 2 and _cross_product(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]
