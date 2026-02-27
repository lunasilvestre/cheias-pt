#!/usr/bin/env python3
"""
Fetch Sentinel-2 L2A before/after flood imagery via Earth Search STAC.

Searches the Element 84 Earth Search STAC catalog for cloud-free Sentinel-2
scenes over the Salvaterra de Magos floodplain (Tejo/Tagus valley) to produce
true-color composites and NDWI flood-detection products.

Data source: Earth Search v1 (https://earth-search.aws.element84.com/v1)
Collection: sentinel-2-l2a (Sentinel-2 L2A, atmospherically corrected)
Resolution: 10 m (B02, B03, B04, B08)
Access: S3 requester-pays / HTTPS (unsigned for public access via Earth Search)

Products generated:
  1. True-color composites (B04/B03/B02, uint8, percentile-stretched)
  2. NDWI per-scene: (B03 - B08) / (B03 + B08)
  3. NDWI difference: after - before (positive = new water / flooding)
  4. STAC Item JSON per scene (1.0.0 spec)
  5. Full search results JSON

Output: data/sentinel-2/

Usage:
  python scripts/fetch_sentinel2_stac.py                  # Default search
  python scripts/fetch_sentinel2_stac.py --output-dir data/sentinel-2
  python scripts/fetch_sentinel2_stac.py --max-cloud-before 10  # Stricter cloud filter

Attribution:
  Contains modified Copernicus Sentinel data 2026, processed by ESA.
  Accessed via Element 84 Earth Search (https://earth-search.aws.element84.com/v1).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
from rasterio.windows import from_bounds as window_from_bounds
from pystac_client import Client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

STAC_URL = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-l2a"

# Salvaterra de Magos floodplain — lower Tejo valley
BBOX = [-9.16, 38.65, -8.05, 39.48]

# Date ranges for scene search
BEFORE_START = "2026-01-01"
BEFORE_END = "2026-01-26"
AFTER_START = "2026-02-06"
AFTER_END = "2026-02-20"

# Cloud cover thresholds (percent)
MAX_CLOUD_BEFORE = 15
MAX_CLOUD_AFTER = 30

# Bands for true-color composite (10 m resolution)
TRUE_COLOR_BANDS = ["red", "green", "blue"]  # B04, B03, B02
# Bands for NDWI
NDWI_GREEN = "green"  # B03
NDWI_NIR = "nir"      # B08

# Percentile stretch for true-color
STRETCH_LOW = 2
STRETCH_HIGH = 98

# Output CRS (Web Mercator for tiling compatibility)
OUTPUT_CRS = CRS.from_epsg(32629)  # UTM 29N — native for Portugal

OUTPUT_DIR = Path("data/sentinel-2")


# ---------------------------------------------------------------------------
# STAC search
# ---------------------------------------------------------------------------

def search_scenes(
    catalog: Client,
    date_start: str,
    date_end: str,
    max_cloud: int,
    max_items: int = 10,
) -> list[dict[str, Any]]:
    """Search STAC catalog for Sentinel-2 scenes within date range and cloud cover."""
    search = catalog.search(
        collections=[COLLECTION],
        bbox=BBOX,
        datetime=f"{date_start}/{date_end}",
        query={"eo:cloud_cover": {"lt": max_cloud}},
        max_items=max_items,
        sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
    )
    items = list(search.items())
    log.info(
        "Found %d scenes for %s to %s (cloud < %d%%)",
        len(items), date_start, date_end, max_cloud,
    )
    for item in items:
        cc = item.properties.get("eo:cloud_cover", "?")
        log.info("  %s  cloud=%.1f%%  date=%s", item.id, cc, item.datetime.isoformat())
    return items


def select_best_scene(items: list) -> Any:
    """Select the scene with the lowest cloud cover."""
    if not items:
        return None
    return min(items, key=lambda x: x.properties.get("eo:cloud_cover", 100))


# ---------------------------------------------------------------------------
# Raster I/O
# ---------------------------------------------------------------------------

def read_band_clipped(
    href: str,
    bbox: list[float],
    target_crs: CRS = OUTPUT_CRS,
) -> tuple[np.ndarray, rasterio.transform.Affine, CRS]:
    """Read a single band from a COG href, clipped to bbox.

    The bbox is in EPSG:4326. We read the native window and reproject
    to the target CRS, returning the clipped array and its transform.
    """
    os.environ["AWS_NO_SIGN_REQUEST"] = "YES"

    with rasterio.open(href) as src:
        # Compute window in source CRS (should be UTM for Sentinel-2)
        # First, transform bbox to source CRS
        from rasterio.warp import transform_bounds
        src_bounds = transform_bounds(CRS.from_epsg(4326), src.crs, *bbox)
        window = window_from_bounds(*src_bounds, transform=src.transform)

        # Read windowed data
        data = src.read(1, window=window)
        win_transform = rasterio.windows.transform(window, src.transform)

        if src.crs == target_crs:
            return data, win_transform, target_crs

        # Reproject if needed
        dst_transform, dst_width, dst_height = rasterio.warp.calculate_default_transform(
            src.crs, target_crs, data.shape[1], data.shape[0],
            *src_bounds,
        )
        dst_data = np.zeros((dst_height, dst_width), dtype=data.dtype)
        reproject(
            source=data,
            destination=dst_data,
            src_transform=win_transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=target_crs,
            resampling=Resampling.bilinear,
        )
        return dst_data, dst_transform, target_crs


def build_true_color(
    item: Any,
    bbox: list[float],
    output_path: Path,
    stretch_low: int = STRETCH_LOW,
    stretch_high: int = STRETCH_HIGH,
) -> None:
    """Build a 3-band uint8 true-color COG from a STAC item."""
    bands = []
    transform = None
    crs = None

    for band_name in TRUE_COLOR_BANDS:
        href = item.assets[band_name].href
        log.info("  Reading %s: %s", band_name, href.split("/")[-1])
        data, transform, crs = read_band_clipped(href, bbox)
        bands.append(data.astype(np.float32))

    # Stack into (3, H, W)
    height, width = bands[0].shape
    # Handle potential size mismatches from different band resolutions
    min_h = min(b.shape[0] for b in bands)
    min_w = min(b.shape[1] for b in bands)
    stack = np.stack([b[:min_h, :min_w] for b in bands])

    # Percentile stretch to uint8
    valid = stack[stack > 0]
    if valid.size > 0:
        low_val = np.percentile(valid, stretch_low)
        high_val = np.percentile(valid, stretch_high)
    else:
        low_val, high_val = 0, 10000

    stretched = np.clip((stack - low_val) / (high_val - low_val) * 255, 0, 255).astype(np.uint8)

    # Write COG
    output_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "dtype": "uint8",
        "width": min_w,
        "height": min_h,
        "count": 3,
        "crs": crs,
        "transform": transform,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.open(output_path, "w", **profile) as dst:
        for i in range(3):
            dst.write(stretched[i], i + 1)
        dst.build_overviews([2, 4, 8, 16], Resampling.average)
        dst.update_tags(ns="rio_overview", resampling="average")

    log.info("Wrote true-color COG: %s (%d x %d)", output_path, min_w, min_h)


def compute_ndwi(
    item: Any,
    bbox: list[float],
    output_path: Path,
) -> np.ndarray:
    """Compute NDWI = (Green - NIR) / (Green + NIR) and write as float32 COG.

    Returns the NDWI array for difference computation.
    """
    green_href = item.assets[NDWI_GREEN].href
    nir_href = item.assets[NDWI_NIR].href

    log.info("  Reading green (B03): %s", green_href.split("/")[-1])
    green, transform, crs = read_band_clipped(green_href, bbox)
    log.info("  Reading NIR (B08): %s", nir_href.split("/")[-1])
    nir, nir_transform, _ = read_band_clipped(nir_href, bbox)

    # Align shapes
    min_h = min(green.shape[0], nir.shape[0])
    min_w = min(green.shape[1], nir.shape[1])
    green = green[:min_h, :min_w].astype(np.float32)
    nir = nir[:min_h, :min_w].astype(np.float32)

    # NDWI: positive values = water
    denominator = green + nir
    ndwi = np.where(denominator > 0, (green - nir) / denominator, 0.0).astype(np.float32)

    # Write COG
    output_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "width": min_w,
        "height": min_h,
        "count": 1,
        "crs": crs,
        "transform": transform,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "nodata": np.nan,
    }
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(ndwi, 1)
        dst.build_overviews([2, 4, 8, 16], Resampling.average)
        dst.update_tags(ns="rio_overview", resampling="average")

    log.info("Wrote NDWI COG: %s", output_path)
    return ndwi


def compute_ndwi_diff(
    before_ndwi: np.ndarray,
    after_ndwi: np.ndarray,
    transform: rasterio.transform.Affine,
    crs: CRS,
    output_path: Path,
) -> None:
    """Compute NDWI difference (after - before). Positive = new water (flooding)."""
    min_h = min(before_ndwi.shape[0], after_ndwi.shape[0])
    min_w = min(before_ndwi.shape[1], after_ndwi.shape[1])

    diff = (after_ndwi[:min_h, :min_w] - before_ndwi[:min_h, :min_w]).astype(np.float32)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "width": min_w,
        "height": min_h,
        "count": 1,
        "crs": crs,
        "transform": transform,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "nodata": np.nan,
    }
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(diff, 1)
        dst.build_overviews([2, 4, 8, 16], Resampling.average)
        dst.update_tags(ns="rio_overview", resampling="average")

    positive = (diff > 0).sum()
    total = diff.size
    log.info(
        "Wrote NDWI diff COG: %s — %d/%d pixels positive (%.1f%%)",
        output_path, positive, total, 100 * positive / total if total else 0,
    )


# ---------------------------------------------------------------------------
# STAC Item JSON output
# ---------------------------------------------------------------------------

def write_stac_item(item: Any, output_path: Path, local_assets: dict[str, str]) -> None:
    """Write a STAC 1.0.0-compliant Item JSON for a selected scene.

    Includes original STAC metadata plus references to local processed assets.
    """
    stac_item = {
        "type": "Feature",
        "stac_version": "1.0.0",
        "stac_extensions": [
            "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
            "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
        ],
        "id": item.id,
        "geometry": item.geometry,
        "bbox": list(item.bbox),
        "properties": {
            "datetime": item.datetime.isoformat() if item.datetime else None,
            "eo:cloud_cover": item.properties.get("eo:cloud_cover"),
            "platform": item.properties.get("platform", "sentinel-2"),
            "constellation": item.properties.get("constellation", "sentinel-2"),
            "instruments": item.properties.get("instruments", ["msi"]),
            "proj:epsg": item.properties.get("proj:epsg"),
            "sentinel:mgrs_tile": item.properties.get("grid:code", ""),
            "processing:software": {"cheias.pt/fetch_sentinel2_stac": "1.0"},
        },
        "links": [
            {
                "rel": "self",
                "href": str(output_path),
                "type": "application/json",
            },
            {
                "rel": "derived_from",
                "href": item.get_self_href() or f"https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/{item.id}",
                "type": "application/json",
                "title": f"Original STAC item: {item.id}",
            },
        ],
        "assets": {},
    }

    for asset_key, local_path in local_assets.items():
        stac_item["assets"][asset_key] = {
            "href": local_path,
            "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            "title": asset_key.replace("-", " ").title(),
            "roles": ["data"],
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(stac_item, f, indent=2)
    log.info("Wrote STAC Item: %s", output_path)


def write_search_results(
    before_items: list,
    after_items: list,
    selected_before: Any,
    selected_after: Any,
    output_path: Path,
) -> None:
    """Write full search results and selection rationale to JSON."""

    def item_summary(item: Any) -> dict:
        return {
            "id": item.id,
            "datetime": item.datetime.isoformat() if item.datetime else None,
            "cloud_cover": item.properties.get("eo:cloud_cover"),
            "bbox": list(item.bbox) if item.bbox else None,
            "platform": item.properties.get("platform"),
        }

    results = {
        "search_parameters": {
            "stac_url": STAC_URL,
            "collection": COLLECTION,
            "bbox": BBOX,
            "before_range": f"{BEFORE_START}/{BEFORE_END}",
            "after_range": f"{AFTER_START}/{AFTER_END}",
            "max_cloud_before": MAX_CLOUD_BEFORE,
            "max_cloud_after": MAX_CLOUD_AFTER,
        },
        "before_candidates": [item_summary(i) for i in before_items],
        "after_candidates": [item_summary(i) for i in after_items],
        "selected": {
            "before": item_summary(selected_before) if selected_before else None,
            "after": item_summary(selected_after) if selected_after else None,
            "rationale": "Selected scenes with lowest cloud cover in each date range.",
        },
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    log.info("Wrote search results: %s", output_path)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Sentinel-2 before/after flood imagery via Earth Search STAC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Default parameters
  %(prog)s --max-cloud-before 10        # Stricter cloud filter for before scene
  %(prog)s --output-dir data/sentinel-2 # Custom output directory

Products:
  - True-color composites (3-band uint8 COG with overviews)
  - NDWI per scene (float32 COG)
  - NDWI difference (after - before, positive = new water)
  - STAC Item JSON per scene (1.0.0 spec)
  - Search results JSON with selection rationale

Attribution:
  Contains modified Copernicus Sentinel data 2026, processed by ESA.
  Accessed via Element 84 Earth Search.
        """,
    )
    parser.add_argument(
        "--output-dir", type=Path, default=OUTPUT_DIR,
        help="Output directory (default: %(default)s)",
    )
    parser.add_argument(
        "--max-cloud-before", type=int, default=MAX_CLOUD_BEFORE,
        help="Max cloud cover %% for before scene (default: %(default)s)",
    )
    parser.add_argument(
        "--max-cloud-after", type=int, default=MAX_CLOUD_AFTER,
        help="Max cloud cover %% for after scene (default: %(default)s)",
    )
    parser.add_argument(
        "--before-start", default=BEFORE_START,
        help="Before period start date (default: %(default)s)",
    )
    parser.add_argument(
        "--before-end", default=BEFORE_END,
        help="Before period end date (default: %(default)s)",
    )
    parser.add_argument(
        "--after-start", default=AFTER_START,
        help="After period start date (default: %(default)s)",
    )
    parser.add_argument(
        "--after-end", default=AFTER_END,
        help="After period end date (default: %(default)s)",
    )
    args = parser.parse_args()

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Connect to STAC catalog ---
    log.info("Connecting to Earth Search STAC: %s", STAC_URL)
    catalog = Client.open(STAC_URL)

    # --- Step 2: Search for before scenes ---
    log.info("Searching for BEFORE scenes (%s to %s, cloud < %d%%)",
             args.before_start, args.before_end, args.max_cloud_before)
    before_items = search_scenes(
        catalog, args.before_start, args.before_end, args.max_cloud_before,
    )
    before = select_best_scene(before_items)
    if before is None:
        log.error("No suitable BEFORE scene found. Try increasing --max-cloud-before.")
        sys.exit(1)
    log.info("Selected BEFORE: %s (cloud=%.1f%%, date=%s)",
             before.id, before.properties["eo:cloud_cover"], before.datetime.date())

    # --- Step 3: Search for after scenes ---
    log.info("Searching for AFTER scenes (%s to %s, cloud < %d%%)",
             args.after_start, args.after_end, args.max_cloud_after)
    after_items = search_scenes(
        catalog, args.after_start, args.after_end, args.max_cloud_after,
    )
    after = select_best_scene(after_items)
    if after is None:
        log.error("No suitable AFTER scene found. Try increasing --max-cloud-after.")
        sys.exit(1)
    log.info("Selected AFTER: %s (cloud=%.1f%%, date=%s)",
             after.id, after.properties["eo:cloud_cover"], after.datetime.date())

    # --- Step 4: Write search results ---
    write_search_results(before_items, after_items, before, after, out / "search-results.json")

    # --- Step 5: Build true-color composites ---
    before_date = before.datetime.strftime("%Y%m%d")
    after_date = after.datetime.strftime("%Y%m%d")

    before_tc_path = out / f"salvaterra-before-{before_date}.tif"
    after_tc_path = out / f"salvaterra-after-{after_date}.tif"

    log.info("Building true-color composite: BEFORE (%s)", before.id)
    build_true_color(before, BBOX, before_tc_path)

    log.info("Building true-color composite: AFTER (%s)", after.id)
    build_true_color(after, BBOX, after_tc_path)

    # --- Step 6: Compute NDWI ---
    before_ndwi_path = out / f"salvaterra-ndwi-before-{before_date}.tif"
    after_ndwi_path = out / f"salvaterra-ndwi-after-{after_date}.tif"
    diff_path = out / "salvaterra-ndwi-diff.tif"

    log.info("Computing NDWI: BEFORE (%s)", before.id)
    before_ndwi = compute_ndwi(before, BBOX, before_ndwi_path)

    log.info("Computing NDWI: AFTER (%s)", after.id)
    after_ndwi = compute_ndwi(after, BBOX, after_ndwi_path)

    # Get transform from the before green band for the diff output
    green_href = before.assets[NDWI_GREEN].href
    _, diff_transform, diff_crs = read_band_clipped(green_href, BBOX)

    log.info("Computing NDWI difference (after - before)")
    compute_ndwi_diff(before_ndwi, after_ndwi, diff_transform, diff_crs, diff_path)

    # --- Step 7: Write STAC Items ---
    write_stac_item(before, out / "before-item.json", {
        "true-color": str(before_tc_path),
        "ndwi": str(before_ndwi_path),
    })
    write_stac_item(after, out / "after-item.json", {
        "true-color": str(after_tc_path),
        "ndwi": str(after_ndwi_path),
        "ndwi-diff": str(diff_path),
    })

    # --- Summary ---
    log.info("=" * 60)
    log.info("DONE — Sentinel-2 before/after products generated")
    log.info("  Before: %s (%s, cloud=%.1f%%)",
             before.id, before.datetime.date(), before.properties["eo:cloud_cover"])
    log.info("  After:  %s (%s, cloud=%.1f%%)",
             after.id, after.datetime.date(), after.properties["eo:cloud_cover"])
    log.info("  Output: %s", out.resolve())
    log.info("=" * 60)


if __name__ == "__main__":
    main()
