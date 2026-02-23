#!/usr/bin/env python3
"""
Generate clipped grid cell polygons for MapLibre fill layers.

Converts the 256-point Open-Meteo grid (0.25° spacing) into polygon cells
clipped to continental Portugal. Output is a GeoJSON file with stable cell
indices matching the soil-moisture-frames.json point order.

Usage:
    source .venv/bin/activate
    python3 scripts/generate_grid_cells.py
"""

import json
import geopandas as gpd
from shapely.geometry import box, mapping
from shapely.ops import unary_union

HALF_CELL = 0.25 / 2  # Half of 0.25° grid spacing

def main():
    # 1. Load grid points from first soil moisture frame (defines the point order)
    print("Loading grid points...")
    with open("data/frontend/soil-moisture-frames.json") as f:
        frames = json.load(f)
    points = frames[0]["points"]
    print(f"  {len(points)} grid points")

    # 2. Load Portugal continental boundary (merge 18 districts)
    print("Loading Portugal boundary...")
    districts = gpd.read_file("assets/districts.geojson")
    portugal = unary_union(districts.geometry)
    # Buffer slightly to avoid edge artifacts at the coast
    portugal_buffered = portugal.buffer(0.02)
    print(f"  Merged {len(districts)} districts into continental boundary")

    # 3. Create grid cell polygons and clip to Portugal
    print("Creating grid cells...")
    cells = []
    cell_indices = []  # Track which point indices have valid (non-empty) cells

    for i, pt in enumerate(points):
        lat, lon = pt["lat"], pt["lon"]
        # Create a square cell centered on the grid point
        cell = box(
            lon - HALF_CELL,  # minx
            lat - HALF_CELL,  # miny
            lon + HALF_CELL,  # maxx
            lat + HALF_CELL,  # maxy
        )
        # Clip to Portugal boundary
        clipped = cell.intersection(portugal_buffered)
        if not clipped.is_empty and clipped.area > 0:
            cells.append(clipped)
            cell_indices.append(i)

    print(f"  {len(cells)} cells after clipping (discarded {len(points) - len(cells)} ocean/outside cells)")

    # 4. Build GeoJSON output
    features = []
    for j, (cell, idx) in enumerate(zip(cells, cell_indices)):
        pt = points[idx]
        features.append({
            "type": "Feature",
            "geometry": mapping(cell),
            "properties": {
                "cell_id": idx,  # Maps to index in frames[n].points[idx]
                "lat": pt["lat"],
                "lon": pt["lon"],
            },
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    # 5. Write output
    out_path = "data/frontend/grid-cells.geojson"
    with open(out_path, "w") as f:
        json.dump(geojson, f)
    
    import os
    size_kb = os.path.getsize(out_path) / 1024
    print(f"\nOutput: {out_path} ({size_kb:.0f} KB, {len(features)} cells)")

    # 6. Also output the cell index mapping for the frontend
    # This tells the frontend which points[] indices have valid geometry
    mapping_path = "data/frontend/grid-cell-mapping.json"
    with open(mapping_path, "w") as f:
        json.dump({"valid_indices": cell_indices, "total_points": len(points)}, f)
    print(f"Mapping: {mapping_path} ({len(cell_indices)} valid of {len(points)} points)")

    # 7. Quick stats
    print(f"\nGrid extent:")
    lats = [pt["lat"] for pt in points]
    lons = [pt["lon"] for pt in points]
    print(f"  Lat: {min(lats)} to {max(lats)}")
    print(f"  Lon: {min(lons)} to {max(lons)}")
    print(f"  Cell size: {HALF_CELL*2}° × {HALF_CELL*2}°")


if __name__ == "__main__":
    main()
