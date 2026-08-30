# License: GNU AGPLv3 (GNU Affero General Public License v3.0)
"""Command-line interface for Wiggle Mapper."""
import argparse
import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path
from typing import List, Optional

from wiggle_mapper import __version__
from wiggle_mapper.csv_parser import filter_data_points, parse_wiggle_csv
from wiggle_mapper.diagnostics import generate_channel_histogram, generate_diagnostic_alerts
from wiggle_mapper.grid_analyzer import calculate_grid_overlay

def get_web_root() -> Path:
    """Return path to directory containing index.html."""
    # Check current directory, then parent directory of package
    candidate1 = Path(__file__).resolve().parent.parent.parent
    if (candidate1 / "index.html").exists():
        return candidate1
    candidate2 = Path.cwd()
    if (candidate2 / "index.html").exists():
        return candidate2
    return candidate1

def cmd_serve(args: argparse.Namespace) -> int:
    """Serve the Wiggle Mapper SPA web application locally."""
    web_dir = get_web_root()
    port = args.port
    host = args.host

    os.chdir(str(web_dir))
    handler = http.server.SimpleHTTPRequestHandler

    print(f"==================================================")
    print(f"  Wiggle Mapper Web App Server v{__version__}")
    print(f"==================================================")
    print(f"Serving from: {web_dir}")
    print(f"URL:          http://{host}:{port}/")
    print(f"Press Ctrl+C to stop the server.")
    print(f"--------------------------------------------------")

    if not args.no_browser:
        webbrowser.open(f"http://localhost:{port}/")

    try:
        with socketserver.TCPServer((host, port), handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Wiggle Mapper server...")
    return 0

def cmd_parse(args: argparse.Namespace) -> int:
    """Parse a WiGLE CSV file and display dataset summary."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    content = file_path.read_text(encoding="utf-8", errors="replace")
    points = parse_wiggle_csv(content, file_path.name)

    print(f"==================================================")
    print(f"  Wiggle Mapper Parse Summary: {file_path.name}")
    print(f"==================================================")
    print(f"Valid Wi-Fi Points: {len(points)}")

    if not points:
        print("No valid Wi-Fi points found.")
        return 0

    unique_ssids = sorted(list({p.ssid for p in points}))
    unique_macs = set(p.mac for p in points)
    rssi_vals = [p.rssi for p in points]
    avg_rssi = sum(rssi_vals) / len(rssi_vals)

    print(f"Unique SSIDs:       {len(unique_ssids)}")
    print(f"Unique BSSIDs/APs:  {len(unique_macs)}")
    print(f"RSSI Range:         {min(rssi_vals)} dBm to {max(rssi_vals)} dBm (Avg: {avg_rssi:.1f} dBm)")
    print("--------------------------------------------------")
    print("Top SSIDs:")
    ssid_counts = {}
    for p in points:
        ssid_counts[p.ssid] = ssid_counts.get(p.ssid, 0) + 1
    for ssid, count in sorted(ssid_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {ssid or '[Hidden]'}: {count} points")
    return 0

def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyze signal health, dead zones, and channel congestion."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    content = file_path.read_text(encoding="utf-8", errors="replace")
    points = parse_wiggle_csv(content, file_path.name)
    filtered = filter_data_points(points, target_ssid=args.ssid, allow_24g=not args.no_24g, allow_5g=not args.no_5g)

    grid_res = calculate_grid_overlay(filtered, boundary=None, grid_meters=args.grid_meters, conf_threshold=args.conf)
    alerts = generate_diagnostic_alerts(grid_res.dead_zone_pct, grid_res.gaps_pct, grid_res.resolution_adjusted, filtered)

    print(f"==================================================")
    print(f"  Wiggle Mapper Coverage & Diagnostic Analysis")
    print(f"==================================================")
    print(f"Target SSID:        {args.ssid}")
    print(f"Grid Resolution:    {grid_res.effective_grid_meters}m")
    print(f"Active Grid Cells:  {grid_res.active_cells}")
    print(f"Dead Zone Area:     {grid_res.dead_zone_pct}%")
    print(f"Survey Gaps:        {grid_res.gaps_pct}%")
    print("--------------------------------------------------")
    print("Diagnostic Alerts:")
    for a in alerts:
        icon = "[!]" if a.alert_type == "danger" else "[*]" if a.alert_type == "warning" else "[i]"
        print(f"  {icon} ({a.alert_type.upper()}) {a.message}")
    return 0

def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="wiggle-mapper",
        description="Wiggle Mapper: School Wi-Fi Coverage & Interference Analyst"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start local web server for Wiggle Mapper SPA")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind server to (default: 8000)")
    serve_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface to bind to (default: 127.0.0.1)")
    serve_parser.add_argument("--no-browser", action="store_true", help="Do not automatically open web browser")

    # parse command
    parse_parser = subparsers.add_parser("parse", help="Parse and summarize a WiGLE CSV scan")
    parse_parser.add_argument("file", type=str, help="Path to WiGLE CSV file")

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze signal health and dead zones")
    analyze_parser.add_argument("file", type=str, help="Path to WiGLE CSV file")
    analyze_parser.add_argument("--ssid", type=str, default="_ALL_", help="Filter by specific SSID (default: _ALL_)")
    analyze_parser.add_argument("--grid-meters", type=float, default=10.0, help="Grid cell size in meters (default: 10)")
    analyze_parser.add_argument("--conf", type=int, default=3, help="Confidence threshold count (default: 3)")
    analyze_parser.add_argument("--no-24g", action="store_true", help="Exclude 2.4 GHz band")
    analyze_parser.add_argument("--no-5g", action="store_true", help="Exclude 5 GHz band")

    return parser

def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint."""
    parser = create_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    if args.command == "serve":
        return cmd_serve(args)
    elif args.command == "parse":
        return cmd_parse(args)
    elif args.command == "analyze":
        return cmd_analyze(args)
    return 0

if __name__ == "__main__":
    sys.exit(main())
