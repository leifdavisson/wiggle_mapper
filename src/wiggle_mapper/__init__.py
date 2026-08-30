# License: GNU AGPLv3 (GNU Affero General Public License v3.0)
"""Wiggle Mapper: School Wi-Fi Coverage & Interference Analysis Engine."""

from wiggle_mapper.models import (
    Alert,
    DataPoint,
    GridCell,
    GridResult,
    LatLng,
    ProjectConfig,
)
from wiggle_mapper.csv_parser import (
    filter_data_points,
    find_header_offset,
    get_rssi_color,
    parse_wiggle_csv,
)
from wiggle_mapper.geo_spatial import (
    calculate_degree_steps,
    calculate_distance_meters,
    convex_hull,
    is_point_in_polygon,
)
from wiggle_mapper.grid_analyzer import calculate_grid_overlay
from wiggle_mapper.diagnostics import (
    deserialize_project_config,
    generate_channel_histogram,
    generate_diagnostic_alerts,
    serialize_project_config,
)

__version__ = "1.0.0"

__all__ = [
    "Alert",
    "DataPoint",
    "GridCell",
    "GridResult",
    "LatLng",
    "ProjectConfig",
    "calculate_degree_steps",
    "calculate_distance_meters",
    "calculate_grid_overlay",
    "convex_hull",
    "deserialize_project_config",
    "filter_data_points",
    "find_header_offset",
    "generate_channel_histogram",
    "generate_diagnostic_alerts",
    "get_rssi_color",
    "is_point_in_polygon",
    "parse_wiggle_csv",
    "serialize_project_config",
]
