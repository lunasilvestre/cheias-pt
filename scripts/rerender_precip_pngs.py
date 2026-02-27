#!/usr/bin/env python3
"""Re-render precipitation PNGs with blues colormap, gaussian blur, and intensity-proportional alpha.

Scroll timeline spec (Ch.3):
  - Sequential blues: transparent → #b3d9e8 → #6baed6 → #3182bd → #08519c
  - Alpha proportional to intensity
  - Gaussian blur σ=3 for soft rain-band appearance

Usage:
  cd /home/nls/Documents/dev/cheias-pt
  source .venv/bin/activate
  python scripts/rerender_precip_pngs.py
"""

import sys
import time
from pathlib import Path

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from shapely.ops import unary_union
from scipy.ndimage import gaussian_filter, distance_transform_edt
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.colors as mcolors

# ─── Config ──────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
COG_PRECIP = ROOT / "data" / "cog" / "precipitation"
PNG_PRECIP = ROOT / "data" / "raster-frames" / "precipitation"

WEST, SOUTH, EAST, NORTH = -9.6, 36.9, -6.1, 42.2

TARGET_WIDTH = 700
TARGET_HEIGHT = 1060

# Mask erosion: shrink polygon by this many degrees to avoid edge interpolation artifacts
MASK_EROSION = 0.005  # ~500m inward

# Border feather: gaussian-blur the alpha edge by this many pixels
FEATHER_PX = 2

# Gaussian blur sigma for rain-band soft appearance (applied to data before colormapping)
BLUR_SIGMA = 3

# Fixed normalization max (mm/day). Captures extreme events without saturating typical days.
# Scan shows storm peaks ~80mm; use 80 as the reference ceiling.
PRECIP_MAX_MM = 80.0

# Blues colormap stops (from scroll-timeline-symbology.md)
BLUES_CMAP = mcolors.LinearSegmentedColormap.from_list('precip_blues', [
    (0.00, '#e8f4f8'),  # trace
    (0.25, '#b3d9e8'),  # light
    (0.50, '#6baed6'),  # moderate
    (0.75, '#3182bd'),  # heavy
    (1.00, '#08519c'),  # extreme
])
BLUES_CMAP.set_bad(alpha=0)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_portugal_mask():
    """Rasterize eroded Portugal polygon at final PNG resolution.
    Returns (H, W) boolean mask and a feathered (H, W) float alpha [0-1]."""
    gdf = gpd.read_file(ASSETS / "districts.geojson")
    polygon = unary_union(gdf.geometry)

    # Erode slightly to avoid interpolation edge artifacts
    eroded = polygon.buffer(-MASK_EROSION)

    transform = from_bounds(WEST, SOUTH, EAST, NORTH, TARGET_WIDTH, TARGET_HEIGHT)

    # Rasterize: 1 inside, 0 outside
    mask = rasterize(
        [(eroded, 1)],
        out_shape=(TARGET_HEIGHT, TARGET_WIDTH),
        transform=transform,
        fill=0,
        dtype='uint8',
        all_touched=True,
    ).astype(bool)

    # Feathered alpha: gaussian blur the binary mask for soft edges
    alpha = gaussian_filter(mask.astype(np.float64), sigma=FEATHER_PX)
    # Normalize so interior is 1.0
    alpha = np.clip(alpha / max(alpha.max(), 1e-10), 0, 1)

    return mask, alpha


def upscale_data(cog_path, target_h, target_w):
    """Read COG float data and upscale to target resolution using bicubic.
    Returns (H, W) float array with NaN for nodata."""
    with rasterio.open(cog_path) as ds:
        data = ds.read(1)

    # Replace nodata with NaN for interpolation
    nodata_mask = np.isnan(data)

    # For interpolation: fill nodata with nearest valid value to avoid edge NaN propagation
    if nodata_mask.any():
        _, nearest_idx = distance_transform_edt(nodata_mask, return_distances=True, return_indices=True)
        data_filled = data[tuple(nearest_idx)]
    else:
        data_filled = data

    # Bicubic upscale using PIL (high quality)
    img_f = Image.fromarray(data_filled.astype(np.float32), mode='F')
    img_up = img_f.resize((target_w, target_h), Image.BICUBIC)
    result = np.array(img_up)

    # Upscale the nodata mask with nearest-neighbor to preserve hard edges
    mask_img = Image.fromarray(nodata_mask.astype(np.uint8) * 255, mode='L')
    mask_up = mask_img.resize((target_w, target_h), Image.NEAREST)
    nodata_up = np.array(mask_up) > 128
    result[nodata_up] = np.nan

    return result


def scan_global_max():
    """Scan all precip COGs for global maximum to inform normalization."""
    gmax = 0.0
    cogs = sorted(COG_PRECIP.glob("*.tif"))
    for cog in cogs:
        with rasterio.open(cog) as ds:
            d = ds.read(1)
            valid = d[~np.isnan(d)]
            if len(valid):
                gmax = max(gmax, float(valid.max()))
    return gmax


def render_precip_blues(data, mask, alpha_feather):
    """Render precipitation float array → RGBA PIL Image with blues colormap.

    Steps:
    1. Clip negative values (precip is non-negative)
    2. Apply gaussian blur for soft rain-band appearance
    3. Normalize to [0, 1] using fixed PRECIP_MAX_MM ceiling
    4. Apply blues colormap
    5. Compute intensity-proportional alpha
    6. Apply Portugal mask + feathering
    """
    # 1. Clip negatives
    data = np.where(np.isnan(data), 0.0, np.clip(data, 0, None))

    # 2. Gaussian blur for soft rain-band appearance (σ=3)
    data_blurred = gaussian_filter(data, sigma=BLUR_SIGMA)

    # 3. Normalize to [0, 1]
    normalized = np.clip(data_blurred / PRECIP_MAX_MM, 0, 1)

    # 4. Apply blues colormap → (H, W, 4) float [0, 1]
    colored = BLUES_CMAP(normalized)

    # 5. Intensity-proportional alpha: alpha = clip(80 + 175 * normalized, 0, 255) / 255
    #    For zero/trace (normalized < ~0.004 = 0.3mm/80mm), set alpha to 0 (transparent)
    intensity_alpha = np.clip(80 + 175 * normalized, 0, 255) / 255.0
    # Zero/trace threshold: less than 0.3mm is transparent
    trace_threshold = 0.3 / PRECIP_MAX_MM
    intensity_alpha[normalized < trace_threshold] = 0.0

    # Combine: intensity alpha × feathered border alpha
    colored[..., 3] = intensity_alpha * alpha_feather

    # Hard zero outside Portugal mask
    colored[~mask] = [0, 0, 0, 0]

    rgba = (colored * 255).astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA')


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    print("Re-rendering precipitation PNGs — blues colormap")
    print(f"Target resolution: {TARGET_WIDTH}×{TARGET_HEIGHT}")
    print(f"Blur sigma: {BLUR_SIGMA}, mask erosion: {MASK_EROSION}°, feather: {FEATHER_PX}px")
    print("=" * 60)

    # Build Portugal mask (reused for all frames)
    print("Building Portugal mask at target resolution...")
    mask, alpha_feather = get_portugal_mask()
    print(f"  Mask pixels: {mask.sum()} / {mask.size} ({100*mask.sum()/mask.size:.1f}%)")

    # Determine normalization ceiling
    print(f"Using fixed normalization ceiling: {PRECIP_MAX_MM} mm/day")
    print("  (scanning global max for info only...)")
    observed_max = scan_global_max()
    print(f"  Observed global max: {observed_max:.1f} mm/day")
    if observed_max > PRECIP_MAX_MM * 1.2:
        print(f"  WARNING: Observed max exceeds ceiling by >20% — consider raising PRECIP_MAX_MM")

    # Gather COGs (skip .aux.xml)
    cogs = sorted(p for p in COG_PRECIP.iterdir() if p.suffix == '.tif')
    print(f"\nRendering {len(cogs)} precipitation PNGs...")
    PNG_PRECIP.mkdir(parents=True, exist_ok=True)

    for i, cog in enumerate(cogs):
        if i == 0 or (i + 1) % 10 == 0 or i == len(cogs) - 1:
            print(f"  [{i+1}/{len(cogs)}] {cog.stem}")

        data = upscale_data(cog, TARGET_HEIGHT, TARGET_WIDTH)
        img = render_precip_blues(data, mask, alpha_feather)
        img.save(PNG_PRECIP / f"{cog.stem}.png", optimize=True, compress_level=9)

    # Summary
    elapsed = time.time() - t0
    pngs = list(PNG_PRECIP.glob("*.png"))
    sizes = [f.stat().st_size for f in pngs]
    total_mb = sum(sizes) / 1e6

    print(f"\n{'=' * 60}")
    print(f"Done: {len(pngs)} PNGs in {elapsed:.0f}s")
    print(f"  Size range: {min(sizes)/1024:.0f} – {max(sizes)/1024:.0f} KB")
    print(f"  Total: {total_mb:.1f} MB")

    # QA: verify blue > red in a storm-peak frame
    test_date = "2026-01-28"
    test_path = PNG_PRECIP / f"{test_date}.png"
    if test_path.exists():
        img_arr = np.array(Image.open(test_path))
        alpha_ch = img_arr[:, :, 3]
        # Only check pixels with meaningful alpha
        visible = alpha_ch > 10
        if visible.any():
            r_mean = img_arr[:, :, 0][visible].mean()
            b_mean = img_arr[:, :, 2][visible].mean()
            print(f"\nQA ({test_date} — visible pixels only):")
            print(f"  R mean: {r_mean:.0f}, B mean: {b_mean:.0f}")
            if b_mean > r_mean:
                print("  PASS: Blue > Red (blues colormap confirmed)")
            else:
                print("  FAIL: Red >= Blue — check colormap")
        else:
            print(f"\nQA: {test_date} has no visible pixels (all alpha=0) — dry day or check data")
    else:
        print(f"\nQA: {test_date}.png not found — skipping color check")

    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
