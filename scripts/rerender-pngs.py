#!/usr/bin/env python3
"""Re-render PNGs from existing COGs with proper resolution and masking.

Fixes two Sprint 04 defects:
1. Color quantization (// 4 * 4) creating visible banding
2. LANCZOS upscale smearing alpha channel into 8.8% fringe pixels

Approach: read COG float data → upscale data only (bicubic) → rasterize mask at
final resolution → apply colormap → clean alpha. No color quantization.

Usage:
  cd /home/nls/Documents/dev/cheias-pt
  source .venv/bin/activate
  python scripts/rerender-pngs.py
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
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.colors as mcolors

# ─── Config ──────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
COG_SM = ROOT / "data" / "cog" / "soil-moisture"
COG_PRECIP = ROOT / "data" / "cog" / "precipitation"
PNG_SM = ROOT / "data" / "raster-frames" / "soil-moisture"
PNG_PRECIP = ROOT / "data" / "raster-frames" / "precipitation"
FIGURES = ROOT / "notebooks" / "figures"

WEST, SOUTH, EAST, NORTH = -9.6, 36.9, -6.1, 42.2

# Final PNG resolution — interpolate directly at this size, no upscale
# ~0.005° per pixel → clean at zoom 7-9
TARGET_WIDTH = 700
TARGET_HEIGHT = 1060

# Mask erosion: shrink polygon by this many degrees to avoid edge interpolation artifacts
MASK_EROSION = 0.005  # ~500m inward

# Border feather: gaussian-blur the alpha edge by this many pixels
FEATHER_PX = 2

# ─── Colormaps (same as Sprint 04) ──────────────────────────────────────────

SM_CMAP = mcolors.LinearSegmentedColormap.from_list('soil_moisture', [
    (0.0,  '#8B6914'),
    (0.25, '#B8860B'),
    (0.45, '#7A9A6E'),
    (0.6,  '#4A90A4'),
    (0.8,  '#2E86AB'),
    (1.0,  '#1B4965'),
])
SM_CMAP.set_bad(alpha=0)

PRECIP_BOUNDS = [0, 1, 5, 15, 30, 50, 80, 150]
PRECIP_COLORS = [
    '#000000',
    '#FFF9C4',
    '#FFD54F',
    '#FF8F00',
    '#E53935',
    '#B71C1C',
    '#4A0000',
]
PRECIP_CMAP = mcolors.ListedColormap(PRECIP_COLORS)
PRECIP_CMAP.set_over(PRECIP_COLORS[-1])
PRECIP_CMAP.set_bad(alpha=0)
PRECIP_NORM = mcolors.BoundaryNorm(PRECIP_BOUNDS, PRECIP_CMAP.N)


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
    from scipy.ndimage import gaussian_filter
    alpha = gaussian_filter(mask.astype(np.float64), sigma=FEATHER_PX)
    # Normalize so interior is 1.0
    alpha = np.clip(alpha / max(alpha.max(), 1e-10), 0, 1)

    return mask, alpha


def upscale_data(cog_path, target_h, target_w):
    """Read COG float data and upscale to target resolution using bicubic.
    Returns (H, W) float array with NaN for nodata."""
    with rasterio.open(cog_path) as ds:
        data = ds.read(1)  # (265, 175) float32

    # Replace nodata with NaN for interpolation
    nodata_mask = np.isnan(data)

    # For interpolation: fill nodata with nearest valid value to avoid edge NaN propagation
    if nodata_mask.any():
        from scipy.ndimage import distance_transform_edt
        _, nearest_idx = distance_transform_edt(nodata_mask, return_distances=True, return_indices=True)
        data_filled = data[tuple(nearest_idx)]
    else:
        data_filled = data

    # Bicubic upscale using PIL (high quality, handles float via intermediate)
    img_f = Image.fromarray(data_filled.astype(np.float32), mode='F')
    img_up = img_f.resize((target_w, target_h), Image.BICUBIC)
    result = np.array(img_up)

    # Upscale the nodata mask with nearest-neighbor to preserve hard edges
    mask_img = Image.fromarray(nodata_mask.astype(np.uint8) * 255, mode='L')
    mask_up = mask_img.resize((target_w, target_h), Image.NEAREST)
    nodata_up = np.array(mask_up) > 128
    result[nodata_up] = np.nan

    return result


def get_global_sm_range():
    """Scan all soil moisture COGs for global min/max."""
    vmin, vmax = float('inf'), float('-inf')
    for cog in sorted(COG_SM.glob("*.tif")):
        with rasterio.open(cog) as ds:
            d = ds.read(1)
            valid = d[~np.isnan(d)]
            if len(valid):
                vmin = min(vmin, float(valid.min()))
                vmax = max(vmax, float(valid.max()))
    return vmin, vmax


def render_sm(data, mask, alpha_feather, vmin, vmax):
    """Render soil moisture float array → RGBA PIL Image."""
    # Normalize to [0, 1]
    norm = np.clip((data - max(vmin, 0)) / (max(vmax, 0.01) - max(vmin, 0)), 0, 1)

    # Apply colormap
    colored = SM_CMAP(norm)  # (H, W, 4)

    # Alpha: feathered mask × 0.85 (slightly translucent for basemap labels)
    colored[..., 3] = alpha_feather * 0.85

    # Hard zero outside mask
    colored[~mask] = [0, 0, 0, 0]

    rgba = (colored * 255).astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA')


def render_precip(data, mask, alpha_feather):
    """Render precipitation float array → RGBA PIL Image."""
    # Apply classified colormap
    colored = PRECIP_CMAP(PRECIP_NORM(data))  # (H, W, 4)

    # Alpha varies with intensity
    value_alpha = np.zeros_like(data)
    value_alpha[(data >= 1) & (data < 5)] = 0.4
    value_alpha[(data >= 5) & (data < 30)] = 0.8
    value_alpha[data >= 30] = 0.9

    # Combine: value-based alpha × feathered border
    colored[..., 3] = value_alpha * alpha_feather

    # Hard zero outside mask
    colored[~mask] = [0, 0, 0, 0]

    rgba = (colored * 255).astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA')


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    print("Re-rendering PNGs from existing COGs")
    print(f"Target resolution: {TARGET_WIDTH}×{TARGET_HEIGHT} (~0.005°/px)")
    print(f"Mask erosion: {MASK_EROSION}°, feather: {FEATHER_PX}px")
    print("=" * 60)

    # Build mask once (same for all frames)
    print("Building Portugal mask at target resolution...")
    mask, alpha_feather = get_portugal_mask()
    print(f"  Mask pixels: {mask.sum()} / {mask.size} ({100*mask.sum()/mask.size:.1f}%)")

    # Global soil moisture range
    print("Scanning soil moisture value range...")
    sm_min, sm_max = get_global_sm_range()
    print(f"  Range: {sm_min:.4f} → {sm_max:.4f}")

    # Render soil moisture
    sm_cogs = sorted(COG_SM.glob("*.tif"))
    print(f"\nRendering {len(sm_cogs)} soil moisture PNGs...")
    PNG_SM.mkdir(parents=True, exist_ok=True)

    for i, cog in enumerate(sm_cogs):
        if i == 0 or (i + 1) % 10 == 0 or i == len(sm_cogs) - 1:
            print(f"  [{i+1}/{len(sm_cogs)}] {cog.stem}")

        data = upscale_data(cog, TARGET_HEIGHT, TARGET_WIDTH)
        img = render_sm(data, mask, alpha_feather, sm_min, sm_max)
        img.save(PNG_SM / f"{cog.stem}.png", optimize=True, compress_level=9)

    # Render precipitation
    precip_cogs = sorted(COG_PRECIP.glob("*.tif"))
    print(f"\nRendering {len(precip_cogs)} precipitation PNGs...")
    PNG_PRECIP.mkdir(parents=True, exist_ok=True)

    for i, cog in enumerate(precip_cogs):
        if i == 0 or (i + 1) % 10 == 0 or i == len(precip_cogs) - 1:
            print(f"  [{i+1}/{len(precip_cogs)}] {cog.stem}")

        data = upscale_data(cog, TARGET_HEIGHT, TARGET_WIDTH)
        img = render_precip(data, mask, alpha_feather)
        img.save(PNG_PRECIP / f"{cog.stem}.png", optimize=True, compress_level=9)

    # Summary
    elapsed = time.time() - t0
    all_pngs = list(PNG_SM.glob("*.png")) + list(PNG_PRECIP.glob("*.png"))
    sizes = [f.stat().st_size for f in all_pngs]
    total_mb = sum(sizes) / 1e6

    print(f"\n{'=' * 60}")
    print(f"✓ Re-rendered {len(all_pngs)} PNGs in {elapsed:.0f}s")
    print(f"  Size range: {min(sizes)/1024:.0f} – {max(sizes)/1024:.0f} KB")
    print(f"  Total: {total_mb:.1f} MB")

    # Quick QA: check alpha distribution of one frame
    test_img = np.array(Image.open(PNG_SM / "2026-01-28.png"))
    test_alpha = test_img[:,:,3]
    fringe = ((test_alpha > 0) & (test_alpha < 200)).sum()
    solid = (test_alpha >= 200).sum()
    print(f"  Border fringe: {fringe} px ({100*fringe/(fringe+solid+1):.1f}% of data) — target < 2%")

    # Check color depth
    r = test_img[:,:,0][test_alpha > 10]
    print(f"  Red channel unique values: {len(np.unique(r))} — target > 100")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
