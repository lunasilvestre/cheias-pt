#!/usr/bin/env python3
"""
P1.B1: Extract automated storm tracks from MSLP minima.

For each hourly timestep in data/cog/mslp/, find the grid cell with minimum
MSLP within the Atlantic+Iberia domain. Track minima per storm within known
date windows (storm cluster: Kristin, Leonardo, Marta). Apply Savitzky-Golay
smoothing to the resulting lon/lat trajectories.

Output:
  data/qgis/storm-tracks-auto.geojson — 3 LineString features
  data/qgis/storm-tracks-auto.md      — method documentation
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.signal import savgol_filter

# --- Configuration ---
MSLP_DIR = Path("data/cog/mslp")
OUT_GEOJSON = Path("data/qgis/storm-tracks-auto.geojson")
OUT_MD = Path("data/qgis/storm-tracks-auto.md")

# COGs are EPSG:4326, bounds: -60.125W to 5.125E, 35.875N to 60.125N
# Search domain: Atlantic + Iberia
DOMAIN = {"west": -40.0, "east": 5.0, "south": 35.875, "north": 60.0}

THRESHOLD_HPA = 990.0  # only track minima below this value
SAVGOL_WINDOW = 11     # Savitzky-Golay window length
SAVGOL_POLY = 3        # Savitzky-Golay polynomial order

# Named storm windows based on ECMWF/ERA5 data and project context.
# These match the known storm cluster timeline for the January-February 2026
# Portugal flood crisis. Windows are inclusive on both ends.
STORM_WINDOWS = [
    {
        "name": "Kristin",
        "start": "2026-01-25T00",
        "end":   "2026-01-30T06",
    },
    {
        "name": "Leonardo",
        "start": "2026-02-03T00",
        "end":   "2026-02-08T00",
    },
    {
        "name": "Marta",
        "start": "2026-02-08T00",
        "end":   "2026-02-13T06",
    },
]


def parse_timestamp(filename: str) -> datetime | None:
    """Parse datetime from filename like '2026-01-28T14.tif'."""
    m = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2})\.tif$", filename)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)


def get_min_in_domain(filepath: Path, domain: dict) -> tuple[float, float, float] | None:
    """
    Return (lon, lat, pressure_hpa) of the MSLP minimum within the domain.
    Returns None if no valid data in domain.
    """
    with rasterio.open(filepath) as src:
        bounds = src.bounds
        transform = src.transform
        data = src.read(1)

        # Compute pixel slices for the domain
        col_left  = max(0, int((domain["west"] - bounds.left) / transform.a))
        col_right = min(src.width, int((domain["east"] - bounds.left) / transform.a) + 1)
        row_top    = max(0, int((bounds.top - domain["north"]) / abs(transform.e)))
        row_bottom = min(src.height, int((bounds.top - domain["south"]) / abs(transform.e)) + 1)

        if col_right <= col_left or row_bottom <= row_top:
            return None

        subset = data[row_top:row_bottom, col_left:col_right]
        if np.all(np.isnan(subset)):
            return None

        min_idx = np.nanargmin(subset)
        r, c = divmod(int(min_idx), subset.shape[1])

        col_abs = col_left + c
        row_abs = row_top + r
        lon = bounds.left + (col_abs + 0.5) * transform.a
        lat = bounds.top  + (row_abs + 0.5) * transform.e  # e is negative

        pressure_hpa = float(np.nanmin(subset)) / 100.0
        return (lon, lat, pressure_hpa)


def extract_storm_track(files: list[Path], window: dict) -> list[dict]:
    """
    Extract storm track for a given time window.
    Returns list of {dt, lon, lat, pressure_hpa} dicts.
    Only includes timesteps where pressure < THRESHOLD_HPA.
    """
    start = datetime.strptime(window["start"], "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
    end   = datetime.strptime(window["end"],   "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)

    track = []
    for f in files:
        dt = parse_timestamp(f.name)
        if dt is None or dt < start or dt > end:
            continue

        result = get_min_in_domain(f, DOMAIN)
        if result is None:
            continue

        lon, lat, pressure_hpa = result
        if pressure_hpa < THRESHOLD_HPA:
            track.append({"dt": dt, "lon": lon, "lat": lat, "pressure_hpa": pressure_hpa})

    return sorted(track, key=lambda x: x["dt"])


def smooth_track(track: list[dict], window: int, poly: int) -> list[dict]:
    """Apply Savitzky-Golay smoothing to lon/lat of a track."""
    n = len(track)
    if n < 3:
        return track

    w = min(window, n)
    if w % 2 == 0:
        w -= 1
    if w < 3:
        return track

    p = min(poly, w - 1)

    lons = np.array([pt["lon"] for pt in track])
    lats = np.array([pt["lat"] for pt in track])

    lons_smooth = savgol_filter(lons, w, p)
    lats_smooth = savgol_filter(lats, w, p)

    smoothed = []
    for i, pt in enumerate(track):
        smoothed.append({**pt, "lon": float(lons_smooth[i]), "lat": float(lats_smooth[i])})
    return smoothed


def track_to_feature(track: list[dict], name: str) -> dict:
    """Convert a track to a GeoJSON LineString feature."""
    coords    = [[round(pt["lon"], 4), round(pt["lat"], 4)] for pt in track]
    pressures = [pt["pressure_hpa"] for pt in track]
    dts       = [pt["dt"].strftime("%Y-%m-%dT%H:%M:%SZ") for pt in track]

    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coords,
        },
        "properties": {
            "name": name,
            "min_pressure_hpa": round(min(pressures), 1),
            "start_datetime": dts[0],
            "end_datetime": dts[-1],
            "duration_hours": round(
                (track[-1]["dt"] - track[0]["dt"]).total_seconds() / 3600, 1
            ),
            "vertex_datetimes": dts,
            "vertex_pressures_hpa": [round(p, 1) for p in pressures],
        },
    }


def write_method_doc(tracks: list[list[dict]], windows: list[dict], n_cogs: int) -> None:
    """Write method documentation markdown."""
    lines = [
        "# Storm Track Extraction Method",
        "",
        "## Source",
        "Script: `scripts/extract_storm_tracks.py`",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "## Input Data",
        f"- **COGs:** `data/cog/mslp/` — {n_cogs} files",
        "- **Variable:** Mean Sea Level Pressure (MSLP) in Pa (stored), converted to hPa",
        "- **Resolution:** 0.25° grid, EPSG:4326",
        f"- **Domain:** {DOMAIN['west']}°W to {DOMAIN['east']}°E, {DOMAIN['south']}°N to {DOMAIN['north']}°N",
        "",
        "## Algorithm",
        "1. For each timestep **within the named storm's date window**, find the grid cell "
        "   with minimum MSLP within the domain.",
        f"2. Retain only timesteps where min MSLP < {THRESHOLD_HPA} hPa.",
        "3. Named storm windows are derived from the ERA5 data and project storm timeline:",
    ]
    for w in windows:
        lines.append(f"   - **{w['name']}**: {w['start']} → {w['end']} UTC")
    lines += [
        f"4. Smooth lon/lat with Savitzky-Golay filter (window={SAVGOL_WINDOW}, polyorder={SAVGOL_POLY}).",
        "",
        "## Results",
    ]
    for track, w in zip(tracks, windows):
        name = w["name"]
        if not track:
            lines += [f"### {name}", "- No sub-threshold points found.", ""]
            continue
        pressures = [pt["pressure_hpa"] for pt in track]
        lines += [
            f"### {name}",
            f"- Points: {len(track)}",
            f"- Min pressure: {min(pressures):.1f} hPa",
            f"- Period: {track[0]['dt'].strftime('%Y-%m-%d %H:%M UTC')} "
            f"→ {track[-1]['dt'].strftime('%Y-%m-%d %H:%M UTC')}",
            f"- Duration: {(track[-1]['dt'] - track[0]['dt']).total_seconds()/3600:.1f} h",
            "",
        ]
    lines += [
        "## Comparison with Hand-Drawn Tracks",
        "Hand-drawn tracks in `data/qgis/storm-tracks.geojson` were created manually",
        "as rough approximations. Automated tracks are derived from ERA5 MSLP minima",
        "and are physically grounded but domain-constrained (COG bounds: 35.875°N–60.125°N,",
        "60.125°W–5.125°E — storms appearing west of -40°W are at the western edge).",
        "",
        "## Limitations",
        "- Southern COG boundary (35.875°N) may clip tracks when storms are south of Iberia.",
        "- Western COG boundary (-60.125°W) clips storms that originate far in the Atlantic.",
        "- The script tracks the absolute MSLP minimum per timestep — near simultaneous",
        "  systems, the tracker can jump between two distinct low-pressure centers.",
        "- Savitzky-Golay smoothing reduces noise but slightly displaces track near endpoints.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Written: {OUT_MD}")


def main() -> None:
    os.chdir(Path(__file__).parent.parent)  # project root

    files = sorted(MSLP_DIR.glob("*.tif"))
    print(f"Found {len(files)} MSLP COGs")

    all_tracks = []
    for w in STORM_WINDOWS:
        print(f"\nProcessing {w['name']} ({w['start']} → {w['end']}) ...")
        raw_track = extract_storm_track(files, w)
        print(f"  {len(raw_track)} sub-threshold points")

        if len(raw_track) >= 2:
            smoothed = smooth_track(raw_track, SAVGOL_WINDOW, SAVGOL_POLY)
        else:
            smoothed = raw_track
            print(f"  WARNING: too few points to smooth")

        all_tracks.append((smoothed, raw_track, w))

    # Build GeoJSON
    features = []
    for smoothed, raw_track, w in all_tracks:
        if not smoothed:
            print(f"WARNING: {w['name']} has no track points — skipping feature")
            continue
        features.append(track_to_feature(smoothed, w["name"]))

    geojson = {"type": "FeatureCollection", "features": features}
    OUT_GEOJSON.write_text(json.dumps(geojson, indent=2))
    print(f"\nWritten: {OUT_GEOJSON}")

    # Validation
    print("\n--- Validation ---")
    for f in features:
        p = f["properties"]
        print(
            f"{p['name']}: min={p['min_pressure_hpa']} hPa | "
            f"{p['start_datetime']} → {p['end_datetime']} | "
            f"{p['duration_hours']}h | {len(f['geometry']['coordinates'])} vertices"
        )

    if len(features) != 3:
        print(f"\nWARNING: Expected 3 features, got {len(features)}")
    else:
        print("\nOK: 3 features produced")

    # Method doc (using raw tracks for accurate stats before smoothing)
    raw_tracks_list = [rt for _, rt, _ in all_tracks]
    write_method_doc(raw_tracks_list, STORM_WINDOWS, len(files))

    print(f"\nDone. {len(features)} storm tracks written to {OUT_GEOJSON}")


if __name__ == "__main__":
    main()
