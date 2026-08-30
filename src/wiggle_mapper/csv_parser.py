# License: GNU AGPLv3 (GNU Affero General Public License v3.0)
import csv
import io
import math
from typing import Any, Dict, List, Optional
from wiggle_mapper.models import DataPoint

def find_header_offset(csv_content: str) -> int:
    """Find character offset of CSV header, skipping leading metadata."""
    lowered = csv_content.lower()
    for pattern in ["mac,ssid", "mac, ssid", "bssid,ssid", "ssid,rssi"]:
        idx = lowered.find(pattern)
        if idx != -1:
            return idx
    
    # Fallback to scanning first lines
    sample = csv_content[:20000]
    offset = 0
    for line in sample.splitlines(keepends=True):
        l_low = line.lower().strip()
        if l_low.startswith("mac") or ("ssid" in l_low and "rssi" in l_low):
            return offset
        offset += len(line)
    return 0

def parse_wiggle_csv(csv_content: str, filename: str) -> List[DataPoint]:
    """Parse raw WiGLE CSV text into structured DataPoint instances."""
    offset = find_header_offset(csv_content)
    clean_csv = csv_content[offset:]
    reader = csv.DictReader(io.StringIO(clean_csv))
    points: List[DataPoint] = []

    try:
        for row in reader:
            point = _extract_point_from_row(row, filename)
            if point is not None:
                points.append(point)
    except csv.Error:
        pass
    return points

def _extract_point_from_row(row: Dict[Any, Any], filename: str) -> Optional[DataPoint]:
    """Extract and validate a single DataPoint from a CSV row dictionary."""
    row_type = str(row.get("Type") or row.get("type") or "WIFI").upper()
    if row_type != "WIFI":
        return None

    mac = str(row.get("MAC") or row.get("BSSID") or row.get("mac") or row.get("bssid") or "").strip()
    if not mac:
        return None

    lat_str = row.get("CurrentLatitude") or row.get("lat") or row.get("latitude")
    lng_str = row.get("CurrentLongitude") or row.get("lon") or row.get("lng") or row.get("longitude")
    if lat_str is None or lng_str is None:
        return None

    try:
        lat = float(lat_str)
        lng = float(lng_str)
    except (ValueError, TypeError):
        return None

    if math.isnan(lat) or math.isnan(lng):
        return None

    ssid = str(row.get("SSID") or row.get("ssid") or "Unknown").strip()
    rssi_val = row.get("RSSI") or row.get("rssi") or row.get("signal") or -100
    chan_val = row.get("Channel") or row.get("channel") or 0
    freq_val = row.get("Frequency") or row.get("frequency") or 0
    acc_val = row.get("AccuracyMeters") or row.get("accuracy") or 10.0

    return DataPoint(
        ssid=ssid,
        mac=mac,
        lat=lat,
        lng=lng,
        rssi=int(rssi_val),
        channel=int(chan_val),
        frequency=int(freq_val),
        accuracy=float(acc_val),
        source_file=filename
    )

def filter_data_points(
    points: List[DataPoint],
    target_ssid: str = "_ALL_",
    allow_24g: bool = True,
    allow_5g: bool = True
) -> List[DataPoint]:
    """Filter data points by target SSID and frequency band."""
    filtered: List[DataPoint] = []
    for p in points:
        if target_ssid != "_ALL_" and p.ssid != target_ssid:
            continue
        is_5g = (p.frequency >= 4900 and p.frequency <= 5900) or (p.channel > 14)
        is_24g = (p.frequency >= 2400 and p.frequency <= 2500) or (1 <= p.channel <= 14)
        if (is_5g and allow_5g) or (is_24g and allow_24g):
            filtered.append(p)
    return filtered

def get_rssi_color(rssi: int) -> str:
    """Return hex color representation for signal dBm strength."""
    if rssi >= -60:
        return "#10b981"
    if rssi >= -75:
        return "#f59e0b"
    return "#ef4444"
