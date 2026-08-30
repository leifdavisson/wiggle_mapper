import pytest
from pathlib import Path
from tests.conftest import verifies
from wiggle_mapper.cli import main, get_web_root

@verifies("REQ-WIG-009")
def test_cli_help_and_version(capsys):
    assert main([]) == 0
    captured = capsys.readouterr()
    assert "usage: wiggle-mapper" in captured.out

    assert get_web_root().exists()

@verifies("REQ-WIG-001")
def test_cli_parse_command(tmp_path, capsys):
    csv_file = tmp_path / "scan.csv"
    csv_file.write_text("""MAC,SSID,CurrentLatitude,CurrentLongitude,RSSI,Channel,Frequency,AccuracyMeters,Type
00:11:22:33:44:55,SchoolNet,37.42,-122.08,-60,6,2437,5.0,WIFI
""", encoding="utf-8")

    code = main(["parse", str(csv_file)])
    assert code == 0
    captured = capsys.readouterr()
    assert "Valid Wi-Fi Points: 1" in captured.out
    assert "SchoolNet" in captured.out

    # Missing file
    assert main(["parse", str(tmp_path / "non_existent.csv")]) == 1

@verifies("REQ-WIG-008")
def test_cli_analyze_command(tmp_path, capsys):
    csv_file = tmp_path / "scan.csv"
    csv_file.write_text("""MAC,SSID,CurrentLatitude,CurrentLongitude,RSSI,Channel,Frequency,AccuracyMeters,Type
00:11:22:33:44:55,SchoolNet,37.42,-122.08,-80,6,2437,5.0,WIFI
""", encoding="utf-8")

    code = main(["analyze", str(csv_file), "--ssid", "SchoolNet", "--grid-meters", "10"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Dead Zone Area:" in captured.out

    # Missing file
    assert main(["analyze", str(tmp_path / "non_existent.csv")]) == 1
from unittest.mock import patch, MagicMock
from wiggle_mapper.cli import cmd_serve

@verifies("REQ-WIG-009")
def test_cli_serve_mocked(tmp_path):
    args = MagicMock()
    args.port = 8999
    args.host = "127.0.0.1"
    args.no_browser = False

    with patch("webbrowser.open") as mock_open, \
         patch("socketserver.TCPServer") as mock_server:
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.serve_forever.side_effect = KeyboardInterrupt
        mock_server.return_value = mock_instance

        code = cmd_serve(args)
        assert code == 0
        mock_open.assert_called_once()
