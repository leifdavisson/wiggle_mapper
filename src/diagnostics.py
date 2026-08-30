# License: GNU AGPLv3 (GNU Affero General Public License v3.0)
import json
from typing import Dict, List, Set
from models import Alert, DataPoint, LatLng, ProjectConfig

def generate_channel_histogram(points: List[DataPoint]) -> Dict[int, int]:
    """Generate map of channel to distinct BSSID / MAC count."""
    channel_aps: Dict[int, Set[str]] = {}
    for p in points:
        if p.channel > 0:
            channel_aps.setdefault(p.channel, set()).add(p.mac)
    return {ch: len(macs) for ch, macs in channel_aps.items()}

def generate_diagnostic_alerts(
    dead_zone_pct: int,
    gaps_pct: int,
    is_resolution_adjusted: bool,
    points: List[DataPoint]
) -> List[Alert]:
    """Generate diagnostic alerts based on network metrics and channel congestion."""
    alerts: List[Alert] = []

    # 1. Dead zone alerts
    if dead_zone_pct > 25:
        alerts.append(Alert(
            alert_type="danger",
            message=f"Critical Dead Zones: {dead_zone_pct}% of the campus area has weak/poor coverage. Consider adding a booster or AP near weak spots."
        ))
    elif dead_zone_pct > 5:
        alerts.append(Alert(
            alert_type="warning",
            message=f"Moderate Dead Zones: {dead_zone_pct}% of campus coverage is weak. Check boundary spots."
        ))

    # 2. Coverage confidence gaps
    if gaps_pct > 30:
        alerts.append(Alert(
            alert_type="info",
            message=f"Low Survey Confidence: {gaps_pct}% of campus is unscanned or lacks sufficient points. Send students to walk the pink zones."
        ))

    # 3. Dynamic resolution adjustment notification
    if is_resolution_adjusted:
        alerts.append(Alert(
            alert_type="warning",
            message="Resolution Adjusted: The boundary spans a very large area. Grid cell size has been scaled up locally to protect rendering speed."
        ))

    # 4. 2.4 GHz channel congestion
    channel_histogram = generate_channel_histogram(points)
    for ch in [1, 6, 11]:
        count = channel_histogram.get(ch, 0)
        if count > 5:
            alerts.append(Alert(
                alert_type="warning",
                message=f"Channel Congestion: Channel {ch} is highly congested with {count} active transmitters. Recommend changing router frequencies."
            ))

    if not alerts:
        alerts.append(Alert(
            alert_type="success",
            message="Networks are running smoothly. Keep scanning!"
        ))

    return alerts

def serialize_project_config(config: ProjectConfig) -> str:
    """Serialize project configuration to JSON string."""
    data = {
        "boundary": [[p.lat, p.lng] for p in config.boundary],
        "loadedFiles": config.loaded_files,
        "dataPoints": [
            {
                "ssid": p.ssid,
                "mac": p.mac,
                "lat": p.lat,
                "lng": p.lng,
                "rssi": p.rssi,
                "channel": p.channel,
                "frequency": p.frequency,
                "accuracy": p.accuracy,
                "file": p.source_file
            }
            for p in config.data_points
        ]
    }
    return json.dumps(data, indent=2)

def deserialize_project_config(json_str: str) -> ProjectConfig:
    """Deserialize project configuration from JSON string."""
    try:
        raw = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON configuration: {e}") from e

    boundary = [LatLng(c[0], c[1]) for c in raw.get("boundary", []) if len(c) >= 2]
    loaded_files = raw.get("loadedFiles", [])
    data_points = []
    for row in raw.get("dataPoints", []):
        data_points.append(DataPoint(
            ssid=str(row.get("ssid", "")),
            mac=str(row.get("mac", "")),
            lat=float(row.get("lat", 0.0)),
            lng=float(row.get("lng", 0.0)),
            rssi=int(row.get("rssi", -100)),
            channel=int(row.get("channel", 0)),
            frequency=int(row.get("frequency", 0)),
            accuracy=float(row.get("accuracy", 10.0)),
            source_file=str(row.get("file", ""))
        ))

    return ProjectConfig(
        boundary=boundary,
        loaded_files=loaded_files,
        data_points=data_points
    )
