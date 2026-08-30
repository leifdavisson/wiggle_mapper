import pytest
from tests.conftest import verifies
from models import DataPoint, LatLng, ProjectConfig
from diagnostics import (
    generate_channel_histogram,
    generate_diagnostic_alerts,
    serialize_project_config,
    deserialize_project_config
)

@verifies("REQ-WIG-008")
def test_generate_channel_histogram():
    pts = [
        DataPoint("Net1", "00:01", 37.42, -122.08, -60, 1, 2412, 5.0, "f1"),
        DataPoint("Net2", "00:02", 37.42, -122.08, -60, 1, 2412, 5.0, "f1"),
        DataPoint("Net1", "00:01", 37.42, -122.08, -65, 1, 2412, 5.0, "f1"), # duplicate MAC on same ch
        DataPoint("Net3", "00:03", 37.42, -122.08, -50, 6, 2437, 5.0, "f1"),
    ]
    hist = generate_channel_histogram(pts)
    assert hist[1] == 2 # 2 distinct BSSIDs
    assert hist[6] == 1 # 1 distinct BSSID
    assert 11 not in hist

@verifies("REQ-WIG-008")
def test_generate_diagnostic_alerts_dead_zones_and_gaps():
    # Danger dead zone (> 25%)
    alerts_danger = generate_diagnostic_alerts(dead_zone_pct=26, gaps_pct=10, is_resolution_adjusted=False, points=[])
    assert any(a.alert_type == "danger" and "Critical Dead Zones" in a.message for a in alerts_danger)

    # Moderate dead zone (6% -> warning)
    alerts_mod = generate_diagnostic_alerts(dead_zone_pct=6, gaps_pct=10, is_resolution_adjusted=False, points=[])
    assert any(a.alert_type == "warning" and "Moderate Dead Zones" in a.message for a in alerts_mod)

    # Survey confidence gaps (> 30% -> info)
    alerts_gap = generate_diagnostic_alerts(dead_zone_pct=0, gaps_pct=35, is_resolution_adjusted=False, points=[])
    assert any(a.alert_type == "info" and "Low Survey Confidence" in a.message for a in alerts_gap)

    # Resolution adjusted warning
    alerts_res = generate_diagnostic_alerts(dead_zone_pct=0, gaps_pct=0, is_resolution_adjusted=True, points=[])
    assert any(a.alert_type == "warning" and "Resolution Adjusted" in a.message for a in alerts_res)

@verifies("REQ-WIG-008")
def test_exact_threshold_boundary_dead_zones():
    # Boundary: dead_zone_pct == 25 should trigger warning ("Moderate Dead Zones"), NOT danger ("Critical Dead Zones")
    alerts_25 = generate_diagnostic_alerts(dead_zone_pct=25, gaps_pct=0, is_resolution_adjusted=False, points=[])
    assert not any(a.alert_type == "danger" for a in alerts_25)
    assert any(a.alert_type == "warning" and "Moderate Dead Zones" in a.message for a in alerts_25)

    # Boundary: dead_zone_pct == 26 should trigger danger ("Critical Dead Zones")
    alerts_26 = generate_diagnostic_alerts(dead_zone_pct=26, gaps_pct=0, is_resolution_adjusted=False, points=[])
    assert any(a.alert_type == "danger" and "Critical Dead Zones" in a.message for a in alerts_26)
    assert not any("Moderate Dead Zones" in a.message for a in alerts_26)

    # Boundary: dead_zone_pct == 5 should NOT trigger warning
    alerts_5 = generate_diagnostic_alerts(dead_zone_pct=5, gaps_pct=0, is_resolution_adjusted=False, points=[])
    assert not any(a.alert_type == "warning" for a in alerts_5)
    assert any(a.alert_type == "success" for a in alerts_5)

    # Boundary: dead_zone_pct == 6 should trigger warning
    alerts_6 = generate_diagnostic_alerts(dead_zone_pct=6, gaps_pct=0, is_resolution_adjusted=False, points=[])
    assert any(a.alert_type == "warning" and "Moderate Dead Zones" in a.message for a in alerts_6)

@verifies("REQ-WIG-008")
def test_exact_threshold_boundary_confidence_gaps():
    # Boundary: gaps_pct == 30 should NOT trigger info alert
    alerts_30 = generate_diagnostic_alerts(dead_zone_pct=0, gaps_pct=30, is_resolution_adjusted=False, points=[])
    assert not any(a.alert_type == "info" for a in alerts_30)
    assert any(a.alert_type == "success" for a in alerts_30)

    # Boundary: gaps_pct == 31 should trigger info alert
    alerts_31 = generate_diagnostic_alerts(dead_zone_pct=0, gaps_pct=31, is_resolution_adjusted=False, points=[])
    assert any(a.alert_type == "info" and "Low Survey Confidence" in a.message for a in alerts_31)

@verifies("REQ-WIG-008")
def test_exact_threshold_boundary_channel_congestion():
    # Test channels 1, 6, 11 boundaries (count <= 5 -> no alert, count > 5 -> warning)
    for ch in [1, 6, 11]:
        pts_5 = [DataPoint(f"Net_{i}", f"00:0{ch}:{i}", 37.42, -122.08, -60, ch, 2400 + ch * 5, 5.0, "f1") for i in range(5)]
        alerts_5 = generate_diagnostic_alerts(dead_zone_pct=0, gaps_pct=0, is_resolution_adjusted=False, points=pts_5)
        assert not any(f"Channel {ch} is highly congested" in a.message for a in alerts_5)

        pts_6 = [DataPoint(f"Net_{i}", f"00:0{ch}:{i}", 37.42, -122.08, -60, ch, 2400 + ch * 5, 5.0, "f1") for i in range(6)]
        alerts_6 = generate_diagnostic_alerts(dead_zone_pct=0, gaps_pct=0, is_resolution_adjusted=False, points=pts_6)
        assert any(a.alert_type == "warning" and f"Channel {ch} is highly congested with 6 active transmitters" in a.message for a in alerts_6)

    # Other channel with > 5 APs (e.g. channel 2 or 36) should not trigger 2.4GHz congestion alert
    pts_other = [DataPoint(f"Net_{i}", f"00:02:{i}", 37.42, -122.08, -60, 2, 2417, 5.0, "f1") for i in range(10)]
    alerts_other = generate_diagnostic_alerts(dead_zone_pct=0, gaps_pct=0, is_resolution_adjusted=False, points=pts_other)
    assert not any("congested" in a.message for a in alerts_other)

@verifies("REQ-WIG-008")
def test_generate_diagnostic_alerts_channel_congestion():
    # 7 distinct MACs on channel 6
    pts = [
        DataPoint("Net", f"00:0{i}", 37.42, -122.08, -60, 6, 2437, 5.0, "f1")
        for i in range(7)
    ]
    alerts = generate_diagnostic_alerts(dead_zone_pct=0, gaps_pct=0, is_resolution_adjusted=False, points=pts)
    assert any("Channel 6 is highly congested" in a.message for a in alerts)

    # Clean state
    clean_alerts = generate_diagnostic_alerts(dead_zone_pct=0, gaps_pct=0, is_resolution_adjusted=False, points=[])
    assert len(clean_alerts) == 1
    assert clean_alerts[0].alert_type == "success"

@verifies("REQ-WIG-009")
def test_project_config_serialization_roundtrip():
    cfg = ProjectConfig(
        boundary=[LatLng(37.42, -122.08), LatLng(37.43, -122.08), LatLng(37.43, -122.07)],
        loaded_files=["walk1.csv", "walk2.csv"],
        data_points=[
            DataPoint("School-WiFi", "00:11:22:33:44:55", 37.422, -122.084, -60, 6, 2437, 4.5, "walk1.csv")
        ]
    )
    json_str = serialize_project_config(cfg)
    deserialized = deserialize_project_config(json_str)

    assert len(deserialized.boundary) == 3
    assert deserialized.boundary[0].lat == pytest.approx(37.42)
    assert deserialized.loaded_files == ["walk1.csv", "walk2.csv"]
    assert len(deserialized.data_points) == 1
    assert deserialized.data_points[0].ssid == "School-WiFi"
    assert deserialized.data_points[0].rssi == -60

@verifies("REQ-WIG-009")
def test_project_config_serialization_stability_and_field_fidelity():
    original_cfg = ProjectConfig(
        boundary=[
            LatLng(37.421, -122.081),
            LatLng(37.425, -122.081),
            LatLng(37.425, -122.075),
            LatLng(37.421, -122.075)
        ],
        loaded_files=["survey_east.csv", "survey_west.csv"],
        data_points=[
            DataPoint(
                ssid="Campus-Guest",
                mac="aa:bb:cc:dd:ee:01",
                lat=37.4225,
                lng=-122.0785,
                rssi=-55,
                channel=1,
                frequency=2412,
                accuracy=3.5,
                source_file="survey_east.csv"
            ),
            DataPoint(
                ssid="Campus-Secure",
                mac="aa:bb:cc:dd:ee:02",
                lat=37.4230,
                lng=-122.0790,
                rssi=-72,
                channel=11,
                frequency=2462,
                accuracy=4.0,
                source_file="survey_west.csv"
            )
        ]
    )

    json_1 = serialize_project_config(original_cfg)
    cfg_roundtrip_1 = deserialize_project_config(json_1)
    json_2 = serialize_project_config(cfg_roundtrip_1)

    # Exact byte/string stability across cycles
    assert json_1 == json_2

    # Detailed field-by-field verification
    assert len(cfg_roundtrip_1.boundary) == 4
    for orig_b, rt_b in zip(original_cfg.boundary, cfg_roundtrip_1.boundary):
        assert rt_b.lat == pytest.approx(orig_b.lat)
        assert rt_b.lng == pytest.approx(orig_b.lng)

    assert cfg_roundtrip_1.loaded_files == original_cfg.loaded_files
    assert len(cfg_roundtrip_1.data_points) == 2
    for orig_dp, rt_dp in zip(original_cfg.data_points, cfg_roundtrip_1.data_points):
        assert rt_dp.ssid == orig_dp.ssid
        assert rt_dp.mac == orig_dp.mac
        assert rt_dp.lat == pytest.approx(orig_dp.lat)
        assert rt_dp.lng == pytest.approx(orig_dp.lng)
        assert rt_dp.rssi == orig_dp.rssi
        assert rt_dp.channel == orig_dp.channel
        assert rt_dp.frequency == orig_dp.frequency
        assert rt_dp.accuracy == pytest.approx(orig_dp.accuracy)
        assert rt_dp.source_file == orig_dp.source_file

@verifies("REQ-WIG-009")
def test_deserialize_invalid_payload():
    with pytest.raises(ValueError):
        deserialize_project_config("not a json string")

    # Missing keys handled gracefully
    empty_cfg = deserialize_project_config("{}")
    assert empty_cfg.boundary == []
    assert empty_cfg.data_points == []

@verifies("REQ-WIG-008")
def test_generate_channel_histogram_zero_channel():
    # Points with channel <= 0 are ignored in channel histogram
    pts = [
        DataPoint("Net1", "00:01", 37.42, -122.08, -60, 0, 0, 5.0, "f1"),
        DataPoint("Net2", "00:02", 37.42, -122.08, -60, -1, 0, 5.0, "f1")
    ]
    hist = generate_channel_histogram(pts)
    assert len(hist) == 0
