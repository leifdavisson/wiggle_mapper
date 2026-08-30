import math
import pytest
from hypothesis import given, strategies as st
from tests.conftest import verifies
from models import DataPoint
from csv_parser import (
    parse_wiggle_csv,
    filter_data_points,
    get_rssi_color,
    find_header_offset,
    _extract_point_from_row
)

@verifies("REQ-WIG-001")
def test_parse_wiggle_csv_standard():
    raw_csv = """WigleWifi-1.4,appRelease=2.66,model=Pixel7,release=14,device=cheetah
MAC,SSID,AuthMode,FirstSeen,Channel,Frequency,RSSI,CurrentLatitude,CurrentLongitude,AltitudeMeters,AccuracyMeters,Type
00:11:22:33:44:55,School-WiFi,[WPA2-PSK],2026-08-10 10:00:00,6,2437,-65,37.422,-122.084,10.5,4.2,WIFI
00:11:22:33:44:56,School-5G,[WPA2-PSK],2026-08-10 10:00:01,36,5180,-55,37.423,-122.085,10.5,3.8,WIFI
00:11:22:33:44:57,BluetoothDev,[BLE],2026-08-10 10:00:02,0,0,-80,37.424,-122.086,10.5,5.0,BT
"""
    points = parse_wiggle_csv(raw_csv, "test.csv")
    assert len(points) == 2
    assert points[0].ssid == "School-WiFi"
    assert points[0].mac == "00:11:22:33:44:55"
    assert points[0].lat == pytest.approx(37.422)
    assert points[0].lng == pytest.approx(-122.084)
    assert points[0].rssi == -65
    assert points[0].channel == 6
    assert points[0].frequency == 2437
    assert points[0].accuracy == pytest.approx(4.2)
    assert points[0].source_file == "test.csv"
    assert points[1].ssid == "School-5G"

@verifies("REQ-WIG-001")
def test_parse_wiggle_csv_alternate_headers_and_invalid_rows():
    raw_csv = """bssid,ssid,signal,lat,lon,channel,frequency,accuracy,type
00:AA:BB:CC:DD:EE,LibGuest,-72,37.425,-122.087,1,2412,5.0,WIFI
,NoMAC,-70,37.425,-122.087,1,2412,5.0,WIFI
00:AA:BB:CC:DD:EF,BadLat,-70,NaN,-122.087,1,2412,5.0,WIFI
00:AA:BB:CC:DD:F0,BadLon,-70,37.425,NaN,1,2412,5.0,WIFI
"""
    points = parse_wiggle_csv(raw_csv, "alt.csv")
    assert len(points) == 1
    assert points[0].ssid == "LibGuest"
    assert points[0].mac == "00:AA:BB:CC:DD:EE"
    assert points[0].rssi == -72

@verifies("REQ-WIG-001")
def test_parse_wiggle_csv_fallback_offset():
    # Header appears after some garbage metadata without mac,ssid immediately
    raw_csv = "METADATA_LINE_1\nMETADATA_LINE_2\nMAC,SSID,RSSI,CurrentLatitude,CurrentLongitude,Channel,Frequency,AccuracyMeters,Type\n00:01:02:03:04:05,AdminNet,-60,37.1,-122.1,11,2462,3.0,WIFI\n"
    points = parse_wiggle_csv(raw_csv, "offset.csv")
    assert len(points) == 1
    assert points[0].ssid == "AdminNet"

@verifies("REQ-WIG-001")
def test_parse_wiggle_csv_header_patterns():
    # Pattern: "mac, ssid" (with space) offset detection
    csv_space = "META_PREHEADER\nMAC, SSID,CurrentLatitude,CurrentLongitude\nAA:BB:CC:DD:EE:01,SpacedNet,37.0,-122.0\n"
    assert find_header_offset(csv_space) > 0

    # Pattern: "ssid,rssi"
    csv_ssid_rssi = "SSID,RSSI,MAC,CurrentLatitude,CurrentLongitude\nRSSIHeaderNet,-50,AA:BB:CC:DD:EE:02,37.0,-122.0\n"
    pts_rssi = parse_wiggle_csv(csv_ssid_rssi, "rssi.csv")
    assert len(pts_rssi) == 1
    assert pts_rssi[0].ssid == "RSSIHeaderNet"

    # Fallback line scanning: line starting with mac (case-insensitive)
    csv_mac_start = "GARBAGE_LINE\nmac_address,ssid,latitude,longitude\nAA:BB:CC:DD:EE:03,MacStartNet,37.0,-122.0\n"
    assert find_header_offset(csv_mac_start) > 0

    # Fallback line scanning: line containing ssid and rssi
    csv_contain = "META1\nfoo,ssid_name,rssi_val,mac,latitude,longitude\n1,ContainNet,-60,AA:BB:CC:DD:EE:04,37.0,-122.0\n"
    assert find_header_offset(csv_contain) > 0

@verifies("REQ-WIG-001")
def test_parse_wiggle_csv_column_aliases_and_defaults():
    # Test aliases: "latitude", "longitude", "lng", "bssid"
    csv_aliases = """bssid,ssid,latitude,longitude
00:12:34:56:78:9A,AliasNet1,37.5,-122.5
"""
    pts1 = parse_wiggle_csv(csv_aliases, "alias1.csv")
    assert len(pts1) == 1
    assert pts1[0].mac == "00:12:34:56:78:9A"
    assert pts1[0].ssid == "AliasNet1"
    assert pts1[0].lat == pytest.approx(37.5)
    assert pts1[0].lng == pytest.approx(-122.5)
    assert pts1[0].rssi == -100  # Default RSSI
    assert pts1[0].channel == 0  # Default Channel
    assert pts1[0].frequency == 0  # Default Frequency
    assert pts1[0].accuracy == pytest.approx(10.0)  # Default Accuracy

    # Test "lat", "lng", and empty SSID defaulting to "Unknown"
    csv_aliases2 = """mac,lat,lng
00:12:34:56:78:9B,37.6,-122.6
"""
    pts2 = parse_wiggle_csv(csv_aliases2, "alias2.csv")
    assert len(pts2) == 1
    assert pts2[0].ssid == "Unknown"
    assert pts2[0].lat == pytest.approx(37.6)
    assert pts2[0].lng == pytest.approx(-122.6)

@verifies("REQ-WIG-001")
def test_parse_wiggle_csv_corrupted_and_adversarial_rows():
    # Completely empty CSV
    assert parse_wiggle_csv("", "empty.csv") == []
    assert parse_wiggle_csv("   \n\n\t  ", "blank.csv") == []

    # Non-WIFI types (BLE, GSM, LTE, etc.)
    row_bt = {"Type": "BT", "MAC": "00:11:22:33:44:55", "CurrentLatitude": "37.0", "CurrentLongitude": "-122.0"}
    assert _extract_point_from_row(row_bt, "f.csv") is None

    row_gsm = {"type": "gsm", "MAC": "00:11:22:33:44:55", "CurrentLatitude": "37.0", "CurrentLongitude": "-122.0"}
    assert _extract_point_from_row(row_gsm, "f.csv") is None

    # Missing or blank MAC
    row_no_mac = {"Type": "WIFI", "MAC": "   ", "CurrentLatitude": "37.0", "CurrentLongitude": "-122.0"}
    assert _extract_point_from_row(row_no_mac, "f.csv") is None

    # Missing coordinates (None)
    row_no_lat = {"Type": "WIFI", "MAC": "00:11:22:33:44:55", "CurrentLongitude": "-122.0"}
    assert _extract_point_from_row(row_no_lat, "f.csv") is None
    row_no_lng = {"Type": "WIFI", "MAC": "00:11:22:33:44:55", "CurrentLatitude": "37.0"}
    assert _extract_point_from_row(row_no_lng, "f.csv") is None

    # Non-float coordinate strings
    row_bad_lat = {"Type": "WIFI", "MAC": "00:11:22:33:44:55", "CurrentLatitude": "invalid_num", "CurrentLongitude": "-122.0"}
    assert _extract_point_from_row(row_bad_lat, "f.csv") is None
    row_bad_lng = {"Type": "WIFI", "MAC": "00:11:22:33:44:55", "CurrentLatitude": "37.0", "CurrentLongitude": "invalid_num"}
    assert _extract_point_from_row(row_bad_lng, "f.csv") is None

    # NaN in longitude
    row_nan_lng = {"Type": "WIFI", "MAC": "00:11:22:33:44:55", "CurrentLatitude": "37.0", "CurrentLongitude": "nan"}
    assert _extract_point_from_row(row_nan_lng, "f.csv") is None

@verifies("REQ-WIG-001")
def test_csv_parser_fallback_scanner_and_empty_coordinates():
    # Trigger fallback line-by-line scanner where header has no mac,ssid pattern match
    raw = "INFO_LINE_NO_MATCH\nMAC_ONLY_LINE\nSOME_OTHER_LINE\n"
    pts = parse_wiggle_csv(raw, "empty.csv")
    assert len(pts) == 0

    # Trigger empty/none lat/lng
    csv_missing_coords = "MAC,SSID,Type\n00:11:22:33:44:55,Net,WIFI\n"
    pts_missing = parse_wiggle_csv(csv_missing_coords, "missing.csv")
    assert len(pts_missing) == 0

@verifies("REQ-WIG-001")
def test_csv_parser_nan_and_unmatched_header_offset():
    # Header offset fallback returns 0 if nothing matches in sample
    assert find_header_offset("NO_MATCH_AT_ALL\nJUST_TEXT\n") == 0

    # Row with NaN latitude
    row_nan = {"Type": "WIFI", "MAC": "00:11:22:33:44:55", "CurrentLatitude": "nan", "CurrentLongitude": "-122.0"}
    assert _extract_point_from_row(row_nan, "test.csv") is None

@verifies("REQ-WIG-001")
def test_csv_parser_invalid_coordinate_type_error():
    row_invalid = {"Type": "WIFI", "MAC": "00:11:22:33:44:55", "CurrentLatitude": "INVALID_FLOAT", "CurrentLongitude": "-122.0"}
    assert _extract_point_from_row(row_invalid, "test.csv") is None

@verifies("REQ-WIG-001")
@given(st.text())
def test_parse_wiggle_csv_fuzzing(fuzz_text: str):
    # Parser should handle arbitrary strings gracefully without uncaught exceptions
    try:
        points = parse_wiggle_csv(fuzz_text, "fuzz.csv")
        assert isinstance(points, list)
        for p in points:
            assert isinstance(p, DataPoint)
            assert not math.isnan(p.lat)
            assert not math.isnan(p.lng)
    except (ValueError, TypeError, KeyError):
        pytest.fail("parse_wiggle_csv raised unexpected exception on fuzzed input")

@verifies("REQ-WIG-002")
def test_filter_data_points_by_ssid_and_band():
    pts = [
        DataPoint("School-24", "00:01", 37.42, -122.08, -60, 6, 2437, 5.0, "f1.csv"),
        DataPoint("School-5", "00:02", 37.42, -122.08, -55, 36, 5180, 5.0, "f1.csv"),
        DataPoint("Guest-24", "00:03", 37.42, -122.08, -75, 1, 2412, 5.0, "f1.csv"),
        DataPoint("Guest-5", "00:04", 37.42, -122.08, -80, 40, 5200, 5.0, "f1.csv"),
    ]
    # Filter by specific SSID
    res_school = filter_data_points(pts, target_ssid="School-24", allow_24g=True, allow_5g=True)
    assert len(res_school) == 1
    assert res_school[0].ssid == "School-24"

    # Filter ALL SSIDs, 5GHz only
    res_5g = filter_data_points(pts, target_ssid="_ALL_", allow_24g=False, allow_5g=True)
    assert len(res_5g) == 2
    assert {p.ssid for p in res_5g} == {"School-5", "Guest-5"}

    # Filter ALL SSIDs, 2.4GHz only
    res_24g = filter_data_points(pts, target_ssid="_ALL_", allow_24g=True, allow_5g=False)
    assert len(res_24g) == 2
    assert {p.ssid for p in res_24g} == {"School-24", "Guest-24"}

    # Filter none enabled
    res_none = filter_data_points(pts, target_ssid="_ALL_", allow_24g=False, allow_5g=False)
    assert len(res_none) == 0

@verifies("REQ-WIG-002")
def test_filter_data_points_frequency_and_channel_boundaries():
    # Exact frequency boundaries for 2.4 GHz [2400, 2500]
    p_2400 = DataPoint("Net", "01", 37.0, -122.0, -60, 0, 2400, 5.0, "f.csv")
    p_2500 = DataPoint("Net", "02", 37.0, -122.0, -60, 0, 2500, 5.0, "f.csv")
    p_2399 = DataPoint("Net", "03", 37.0, -122.0, -60, 0, 2399, 5.0, "f.csv")
    p_2501 = DataPoint("Net", "04", 37.0, -122.0, -60, 0, 2501, 5.0, "f.csv")

    assert filter_data_points([p_2400], allow_24g=True, allow_5g=False) == [p_2400]
    assert filter_data_points([p_2500], allow_24g=True, allow_5g=False) == [p_2500]
    assert filter_data_points([p_2399], allow_24g=True, allow_5g=False) == []
    assert filter_data_points([p_2501], allow_24g=True, allow_5g=False) == []

    # Exact channel boundaries for 2.4 GHz [1, 14]
    p_chan1 = DataPoint("Net", "05", 37.0, -122.0, -60, 1, 0, 5.0, "f.csv")
    p_chan14 = DataPoint("Net", "06", 37.0, -122.0, -60, 14, 0, 5.0, "f.csv")
    p_chan0 = DataPoint("Net", "07", 37.0, -122.0, -60, 0, 0, 5.0, "f.csv")
    p_chan_neg = DataPoint("Net", "08", 37.0, -122.0, -60, -5, 0, 5.0, "f.csv")

    assert filter_data_points([p_chan1], allow_24g=True, allow_5g=False) == [p_chan1]
    assert filter_data_points([p_chan14], allow_24g=True, allow_5g=False) == [p_chan14]
    assert filter_data_points([p_chan0], allow_24g=True, allow_5g=False) == []
    assert filter_data_points([p_chan_neg], allow_24g=True, allow_5g=False) == []

    # Exact frequency boundaries for 5 GHz [4900, 5900]
    p_4900 = DataPoint("Net", "09", 37.0, -122.0, -60, 0, 4900, 5.0, "f.csv")
    p_5900 = DataPoint("Net", "10", 37.0, -122.0, -60, 0, 5900, 5.0, "f.csv")
    p_4899 = DataPoint("Net", "11", 37.0, -122.0, -60, 0, 4899, 5.0, "f.csv")
    p_5901 = DataPoint("Net", "12", 37.0, -122.0, -60, 0, 5901, 5.0, "f.csv")

    assert filter_data_points([p_4900], allow_24g=False, allow_5g=True) == [p_4900]
    assert filter_data_points([p_5900], allow_24g=False, allow_5g=True) == [p_5900]
    assert filter_data_points([p_4899], allow_24g=False, allow_5g=True) == []
    assert filter_data_points([p_5901], allow_24g=False, allow_5g=True) == []

    # Channel boundary for 5 GHz (channel > 14)
    p_chan15 = DataPoint("Net", "13", 37.0, -122.0, -60, 15, 0, 5.0, "f.csv")
    assert filter_data_points([p_chan15], allow_24g=False, allow_5g=True) == [p_chan15]
    assert filter_data_points([p_chan15], allow_24g=True, allow_5g=False) == []

@verifies("REQ-WIG-002")
def test_get_rssi_color_exact_boundaries():
    # Boundary at -60 dBm
    assert get_rssi_color(0) == "#10b981"
    assert get_rssi_color(-59) == "#10b981"
    assert get_rssi_color(-60) == "#10b981"
    assert get_rssi_color(-61) == "#f59e0b"

    # Boundary at -75 dBm
    assert get_rssi_color(-74) == "#f59e0b"
    assert get_rssi_color(-75) == "#f59e0b"
    assert get_rssi_color(-76) == "#ef4444"
    assert get_rssi_color(-100) == "#ef4444"

@verifies("REQ-WIG-002")
@given(
    rssi=st.integers(min_value=-120, max_value=0)
)
def test_rssi_color_mapping_invariant(rssi: int):
    color = get_rssi_color(rssi)
    if rssi >= -60:
        assert color == "#10b981"  # Green
    elif rssi >= -75:
        assert color == "#f59e0b"  # Yellow/Amber
    else:
        assert color == "#ef4444"  # Red

@verifies("REQ-WIG-002")
@given(
    ssids=st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=10),
    channels=st.lists(st.integers(min_value=-5, max_value=165), min_size=0, max_size=10),
    frequencies=st.lists(st.integers(min_value=0, max_value=6000), min_size=0, max_size=10),
    target_ssid=st.text(min_size=1, max_size=10),
    allow_24g=st.booleans(),
    allow_5g=st.booleans()
)
def test_filter_data_points_property(ssids, channels, frequencies, target_ssid, allow_24g, allow_5g):
    pts = [
        DataPoint(
            ssid=s,
            mac=f"00:00:00:00:00:{i:02x}",
            lat=37.0,
            lng=-122.0,
            rssi=-70,
            channel=ch if i < len(channels) else 0,
            frequency=fq if i < len(frequencies) else 0,
            accuracy=5.0,
            source_file="prop.csv"
        )
        for i, (s, ch, fq) in enumerate(zip(ssids, channels, frequencies))
    ]
    filtered = filter_data_points(pts, target_ssid=target_ssid, allow_24g=allow_24g, allow_5g=allow_5g)
    assert len(filtered) <= len(pts)
    for p in filtered:
        assert p in pts
        if target_ssid != "_ALL_":
            assert p.ssid == target_ssid
        is_5g = (p.frequency >= 4900 and p.frequency <= 5900) or (p.channel > 14)
        is_24g = (p.frequency >= 2400 and p.frequency <= 2500) or (1 <= p.channel <= 14)
        assert (is_5g and allow_5g) or (is_24g and allow_24g)
