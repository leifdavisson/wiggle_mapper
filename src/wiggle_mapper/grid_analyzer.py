import math
from typing import Dict, List, Optional, Tuple
from wiggle_mapper.models import DataPoint, GridCell, GridResult, LatLng
from wiggle_mapper.geo_spatial import calculate_degree_steps, is_point_in_polygon

def _get_bounding_box(coords: List[LatLng]) -> Tuple[float, float, float, float]:
    """Return min_lat, max_lat, min_lng, max_lng for a list of coordinates."""
    if not coords:
        return (0.0, 0.0, 0.0, 0.0)
    lats = [p.lat for p in coords]
    lngs = [p.lng for p in coords]
    return (min(lats), max(lats), min(lngs), max(lngs))

def _scale_resolution_if_needed(boundary: List[LatLng], grid_meters: float, avg_lat: float) -> Tuple[float, bool]:
    """Scale grid resolution up if total potential cells exceed 40,000."""
    b_min_lat, b_max_lat, b_min_lng, b_max_lng = _get_bounding_box(boundary)
    lat_step, lng_step = calculate_degree_steps(grid_meters, avg_lat)
    lat_range = math.ceil((b_max_lat - b_min_lat) / lat_step) if lat_step > 0 else 0
    lng_range = math.ceil((b_max_lng - b_min_lng) / lng_step) if lng_step > 0 else 0
    total_cells = lat_range * lng_range
    if total_cells > 40000:
        area_m2 = (b_max_lat - b_min_lat) * 111320.0 * (b_max_lng - b_min_lng) * 111320.0 * math.cos(math.radians(avg_lat))
        adjusted = math.ceil(math.sqrt(area_m2 / 40000.0))
        return (max(grid_meters, adjusted), True)
    return (grid_meters, False)

def calculate_grid_overlay(points: List[DataPoint], boundary: Optional[List[LatLng]]=None, grid_meters: float=10.0, conf_threshold: int=3) -> GridResult:
    """Group points into grid cells and compute dead-zone and confidence metrics."""
    if not points and (not boundary):
        return GridResult(cells=[], dead_zone_pct=0, gaps_pct=0, total_cells=0, active_cells=0)
    all_coords = [LatLng(p.lat, p.lng) for p in points]
    if boundary:
        all_coords.extend(boundary)
    min_lat, max_lat, min_lng, max_lng = _get_bounding_box(all_coords)
    avg_lat = (min_lat + max_lat) / 2.0
    res_adjusted = False
    effective_meters = grid_meters
    if boundary:
        effective_meters, res_adjusted = _scale_resolution_if_needed(boundary, grid_meters, avg_lat)
    lat_step, lng_step = calculate_degree_steps(effective_meters, avg_lat)
    grid_dict: Dict[Tuple[int, int], GridCell] = {}
    for p in points:
        l_idx = math.floor((p.lat - min_lat) / lat_step)
        g_idx = math.floor((p.lng - min_lng) / lng_step)
        key = (l_idx, g_idx)
        if key not in grid_dict:
            c_min_lat = min_lat + l_idx * lat_step
            c_min_lng = min_lng + g_idx * lng_step
            grid_dict[key] = GridCell(lat_idx=l_idx, lng_idx=g_idx, min_lat=c_min_lat, max_lat=c_min_lat + lat_step, min_lng=c_min_lng, max_lng=c_min_lng + lng_step)
        grid_dict[key].sum_rssi += p.rssi
        grid_dict[key].count += 1
    if boundary:
        return _calculate_with_boundary(grid_dict, boundary, min_lat, min_lng, lat_step, lng_step, conf_threshold, res_adjusted, effective_meters)
    return _calculate_without_boundary(grid_dict, conf_threshold, res_adjusted, effective_meters)

def _calculate_without_boundary(grid_dict: Dict[Tuple[int, int], GridCell], conf_threshold: int, res_adjusted: bool, effective_meters: float) -> GridResult:
    """Calculate metrics without boundary polygon."""
    active_cells = list(grid_dict.values())
    total = len(active_cells)
    if total == 0:
        return GridResult(cells=[], dead_zone_pct=0, gaps_pct=0, total_cells=0, active_cells=0)
    dead_count = sum((1 for c in active_cells if c.avg_rssi <= -75.0))
    gap_count = sum((1 for c in active_cells if c.count < conf_threshold))
    return GridResult(cells=active_cells, dead_zone_pct=round(dead_count / total * 100), gaps_pct=round(gap_count / total * 100), total_cells=total, active_cells=total, resolution_adjusted=res_adjusted, effective_grid_meters=effective_meters)

def _calculate_with_boundary(grid_dict: Dict[Tuple[int, int], GridCell], boundary: List[LatLng], min_lat: float, min_lng: float, lat_step: float, lng_step: float, conf_threshold: int, res_adjusted: bool, effective_meters: float) -> GridResult:
    """Calculate metrics with boundary polygon containment."""
    if not boundary:
        return GridResult(cells=[], dead_zone_pct=0, gaps_pct=0, total_cells=0, active_cells=0)
    b_min_lat, b_max_lat, b_min_lng, b_max_lng = _get_bounding_box(boundary)
    lat_min_idx = math.floor((b_min_lat - min_lat) / lat_step)
    lat_max_idx = math.ceil((b_max_lat - min_lat) / lat_step)
    lng_min_idx = math.floor((b_min_lng - min_lng) / lng_step)
    lng_max_idx = math.ceil((b_max_lng - min_lng) / lng_step)
    inside_cells: List[GridCell] = []
    dead_count = 0
    gap_count = 0
    inside_total = 0
    for l in range(lat_min_idx - 1, lat_max_idx + 2):
        for g in range(lng_min_idx - 1, lng_max_idx + 2):
            cell_lat = min_lat + l * lat_step + lat_step / 2.0
            cell_lng = min_lng + g * lng_step + lng_step / 2.0
            if is_point_in_polygon(LatLng(cell_lat, cell_lng), boundary):
                inside_total += 1
                cell = grid_dict.get((l, g))
                if cell is not None:
                    inside_cells.append(cell)
                    if cell.avg_rssi <= -75.0:
                        dead_count += 1
                    if cell.count < conf_threshold:
                        gap_count += 1
                else:
                    dead_count += 1
                    gap_count += 1
    if inside_total == 0:
        return GridResult(cells=[], dead_zone_pct=0, gaps_pct=0, total_cells=0, active_cells=0)
    return GridResult(cells=inside_cells, dead_zone_pct=round(dead_count / inside_total * 100), gaps_pct=round(gap_count / inside_total * 100), total_cells=inside_total, active_cells=len(inside_cells), resolution_adjusted=res_adjusted, effective_grid_meters=effective_meters)