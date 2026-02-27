#!/usr/bin/env python3
"""
Compute per-basin daily mean soil moisture timeseries.

Loads basins.geojson (11 basins with polygon geometry) and
soil-moisture-frames.json (77 frames × 256 points), performs
point-in-polygon assignment, and outputs per-basin daily means
for 5 key basins (Minho-Lima, Douro, Mondego, Tejo, Sado).

Output: data/frontend/sm-basin-timeseries.json
"""

import json
from pathlib import Path
from shapely.geometry import shape, Point

ROOT = Path(__file__).resolve().parent.parent
BASINS_PATH = ROOT / "assets" / "basins.geojson"
SM_FRAMES_PATH = ROOT / "data" / "frontend" / "soil-moisture-frames.json"
OUTPUT_PATH = ROOT / "data" / "frontend" / "sm-basin-timeseries.json"

KEY_BASINS = ["Minho-Lima", "Douro", "Mondego", "Tejo", "Sado"]


def main():
    # Load basins
    with open(BASINS_PATH) as f:
        basins_geojson = json.load(f)

    basins = {}
    for feat in basins_geojson["features"]:
        river = feat["properties"]["river"]
        if river in KEY_BASINS:
            basins[river] = shape(feat["geometry"])

    print(f"Loaded {len(basins)} key basins: {list(basins.keys())}")

    # Load soil moisture frames
    with open(SM_FRAMES_PATH) as f:
        frames = json.load(f)

    print(f"Loaded {len(frames)} frames, {len(frames[0]['points'])} points each")

    # Pre-compute point-to-basin assignment (once, using first frame's points)
    points = frames[0]["points"]
    point_basin_map = {}  # index -> basin name
    for i, pt in enumerate(points):
        p = Point(pt["lon"], pt["lat"])
        for basin_name, basin_geom in basins.items():
            if basin_geom.contains(p):
                point_basin_map[i] = basin_name
                break

    # Count points per basin
    basin_point_counts = {}
    for basin_name in point_basin_map.values():
        basin_point_counts[basin_name] = basin_point_counts.get(basin_name, 0) + 1
    print(f"Point assignments: {basin_point_counts}")

    # Compute per-basin daily means
    result = []
    for basin_name in KEY_BASINS:
        dates = []
        values = []
        for frame in frames:
            dates.append(frame["date"])
            # Collect SM values for points in this basin
            basin_values = []
            for i, pt in enumerate(frame["points"]):
                if point_basin_map.get(i) == basin_name:
                    basin_values.append(pt["value"])
            if basin_values:
                mean_val = round(sum(basin_values) / len(basin_values), 3)
            else:
                mean_val = None
            values.append(mean_val)

        result.append({
            "basin": basin_name,
            "dates": dates,
            "values": values,
        })

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, separators=(",", ":"))

    print(f"Written {OUTPUT_PATH} ({len(result)} basins, {len(result[0]['dates'])} dates each)")

    # Summary
    for entry in result:
        vals = [v for v in entry["values"] if v is not None]
        if vals:
            print(f"  {entry['basin']:12s}: min={min(vals):.3f}  max={max(vals):.3f}  range={max(vals)-min(vals):.3f}")


if __name__ == "__main__":
    main()
