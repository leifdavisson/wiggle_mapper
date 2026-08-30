# License: GNU AGPLv3 (GNU Affero General Public License v3.0)
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass(frozen=True)
class LatLng:
    lat: float
    lng: float

@dataclass
class DataPoint:
    ssid: str
    mac: str
    lat: float
    lng: float
    rssi: int
    channel: int
    frequency: int
    accuracy: float
    source_file: str

@dataclass
class GridCell:
    lat_idx: int
    lng_idx: int
    sum_rssi: float = 0.0
    count: int = 0
    min_lat: float = 0.0
    max_lat: float = 0.0
    min_lng: float = 0.0
    max_lng: float = 0.0

    @property
    def avg_rssi(self) -> float:
        return (self.sum_rssi / self.count) if self.count > 0 else -100.0

@dataclass
class GridResult:
    cells: List[GridCell]
    dead_zone_pct: int
    gaps_pct: int
    total_cells: int
    active_cells: int
    resolution_adjusted: bool = False
    effective_grid_meters: float = 0.0

@dataclass
class Alert:
    alert_type: str  # "danger", "warning", "info", "success"
    message: str

@dataclass
class ProjectConfig:
    boundary: List[LatLng] = field(default_factory=list)
    loaded_files: List[str] = field(default_factory=list)
    data_points: List[DataPoint] = field(default_factory=list)
