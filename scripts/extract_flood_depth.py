#!/usr/bin/env python3
"""
Extract CEMS flood depth TIFs → COGs for Salvaterra de Magos (EMSR864 AOI03).

Clips each TIF to the Salvaterra bbox, converts to COG with LZW compression,
256x256 tiles, and overviews at 2x/4x/8x reduction.

Output: data/flood-depth/{salvaterra-depth-monit01,monit02,product}.tif + manifest.json
"""

import json
import os
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

BASE = Path("/home/nls/Documents/dev/cheias-pt")

SOURCES = [
    {
        "key": "monit01",
        "output": "salvaterra-depth-monit01.tif",
        "src": BASE / "data/flood-extent/EMSR864_AOI03_DEL_MONIT01_v2/EMSR864_AOI03_DEL_MONIT01_floodDepthA_v2.tif",
        "label": "EMSR864 AOI03 MONIT01 v2",
    },
    {
        "key": "monit02",
        "output": "salvaterra-depth-monit02.tif",
        "src": BASE / "data/flood-extent/EMSR864_AOI03_DEL_MONIT02_v1/EMSR864_AOI03_DEL_MONIT02_floodDepthA_v1.tif",
        "label": "EMSR864 AOI03 MONIT02 v1",
    },
    {
        "key": "product",
        "output": "salvaterra-depth-product.tif",
        "src": BASE / "data/flood-extent/EMSR864_AOI03_DEL_PRODUCT_v1/EMSR864_AOI03_DEL_PRODUCT_floodDepthA_v1.tif",
        "label": "EMSR864 AOI03 DEL PRODUCT v1",
    },
]

# Salvaterra de Magos clip bbox: [west, south, east, north]
BBOX = [-8.85, 38.85, -8.55, 39.15]
WEST, SOUTH, EAST, NORTH = BBOX

OUT_DIR = BASE / "data/flood-depth"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COG_PROFILE = {
    "driver": "GTiff",
    "compress": "lzw",
    "tiled": True,
    "blockxsize": 256,
    "blockysize": 256,
    "interleave": "band",
}

OVERVIEW_LEVELS = [2, 4, 8]
ATTRIBUTION = "Contains modified Copernicus Emergency Management Service information [2026]"


def clip_and_write_cog(src_path: Path, out_path: Path) -> dict:
    """Clip src to BBOX, write COG, return stats dict."""
    with rasterio.open(src_path) as src:
        # Compute window for clip bbox
        window = from_bounds(WEST, SOUTH, EAST, NORTH, src.transform)
        # Read clipped data
        data = src.read(1, window=window)
        nodata = src.nodata  # -9999.0
        transform = src.window_transform(window)
        crs = src.crs
        dtype = src.dtypes[0]

    # Mask nodata for stats
    valid = data[data != nodata]
    if valid.size > 0:
        depth_min = float(np.nanmin(valid))
        depth_max = float(np.nanmax(valid))
    else:
        depth_min = None
        depth_max = None

    total_pixels = data.size
    nodata_pixels = int(np.sum(data == nodata))
    nodata_pct = round(100.0 * nodata_pixels / total_pixels, 2)

    # Write temp unoptimized GeoTIFF then build COG in-place
    tmp_path = out_path.with_suffix(".tmp.tif")

    profile = {
        **COG_PROFILE,
        "dtype": dtype,
        "width": data.shape[1],
        "height": data.shape[0],
        "count": 1,
        "crs": crs,
        "transform": transform,
        "nodata": nodata,
    }

    with rasterio.open(tmp_path, "w", **profile) as dst:
        dst.write(data, 1)
        dst.build_overviews(OVERVIEW_LEVELS, Resampling.nearest)
        dst.update_tags(ns="rio_overview", resampling="nearest")

    # Copy to COG (copy_files + GDAL_TIFF_INTERNAL_MASK pattern via rasterio copy)
    from rasterio.shutil import copy as rio_copy
    rio_copy(tmp_path, out_path, copy_src_overviews=True, **COG_PROFILE)
    tmp_path.unlink()

    stats = {
        "output_file": str(out_path),
        "source_file": str(src_path),
        "crs": str(crs),
        "bbox": BBOX,
        "depth_min_m": depth_min,
        "depth_max_m": depth_max,
        "nodata_pct": nodata_pct,
        "width": int(data.shape[1]),
        "height": int(data.shape[0]),
    }
    return stats


def main():
    manifest = {
        "attribution": ATTRIBUTION,
        "clip_bbox": BBOX,
        "files": {},
    }

    for spec in SOURCES:
        src_path = spec["src"]
        out_path = OUT_DIR / spec["output"]
        print(f"Processing {spec['key']} ...")
        print(f"  src: {src_path}")
        print(f"  out: {out_path}")

        if not src_path.exists():
            print(f"  ERROR: source file not found: {src_path}")
            continue

        stats = clip_and_write_cog(src_path, out_path)
        print(f"  depth range: {stats['depth_min_m']:.2f} – {stats['depth_max_m']:.2f} m")
        print(f"  nodata: {stats['nodata_pct']}%")
        print(f"  size: {stats['width']} x {stats['height']} px")
        manifest["files"][spec["key"]] = {**stats, "label": spec["label"]}

    manifest_path = OUT_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest written: {manifest_path}")


if __name__ == "__main__":
    main()
