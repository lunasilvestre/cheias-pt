#!/usr/bin/env python3
"""Sprint 04: Cloud-Optimized Raster Pipeline for cheias.pt

Open-Meteo API → COGs (canonical) → pre-rendered PNGs (scrollytelling) → manifest JSON

Two variables, 77 days each (2025-12-01 → 2026-02-15):
  - Soil moisture (hourly → daily mean)
  - Precipitation (daily sum)
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import geopandas as gpd
import requests
from shapely.ops import unary_union
from shapely.geometry import Point
import scipy.interpolate
import rasterio
from rasterio.transform import from_bounds
from rasterio.enums import Resampling
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PIL import Image

# ─── Configuration ───────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
CACHE = DATA / "cache"
COG_SM = DATA / "cog" / "soil-moisture"
COG_PRECIP = DATA / "cog" / "precipitation"
PNG_SM = DATA / "raster-frames" / "soil-moisture"
PNG_PRECIP = DATA / "raster-frames" / "precipitation"
FRONTEND = DATA / "frontend"
FIGURES = ROOT / "notebooks" / "figures"

WEST, SOUTH, EAST, NORTH = -9.6, 36.9, -6.1, 42.2
BBOX = (WEST, SOUTH, EAST, NORTH)
START_DATE = "2025-12-01"
END_DATE = "2026-02-15"
PIXEL_SIZE = 0.02   # degrees — interpolation grid spacing
PNG_SCALE = 4       # upscale factor → ~700×1060 PNGs

API_URL = "https://archive-api.open-meteo.com/v1/archive"

# ─── Colormaps ───────────────────────────────────────────────────────────────

SM_CMAP = mcolors.LinearSegmentedColormap.from_list('soil_moisture', [
    (0.0,  '#8B6914'),  # dry brown/amber
    (0.25, '#B8860B'),  # dark goldenrod
    (0.45, '#7A9A6E'),  # olive transition
    (0.6,  '#4A90A4'),  # steel blue
    (0.8,  '#2E86AB'),  # ocean blue
    (1.0,  '#1B4965'),  # deep teal
])
SM_CMAP.set_bad(alpha=0)

PRECIP_BOUNDS = [0, 1, 5, 15, 30, 50, 80, 150]
PRECIP_COLORS = [
    '#000000',  # 0-1: placeholder (transparent via alpha)
    '#FFF9C4',  # 1-5: pale yellow
    '#FFD54F',  # 5-15: amber
    '#FF8F00',  # 15-30: dark orange
    '#E53935',  # 30-50: red
    '#B71C1C',  # 50-80: dark red
    '#4A0000',  # 80+: near black red
]
PRECIP_CMAP = mcolors.ListedColormap(PRECIP_COLORS)
PRECIP_CMAP.set_over(PRECIP_COLORS[-1])
PRECIP_CMAP.set_bad(alpha=0)
PRECIP_NORM = mcolors.BoundaryNorm(PRECIP_BOUNDS, PRECIP_CMAP.N)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_portugal_polygon():
    """Dissolve districts.geojson into a single continental Portugal polygon."""
    gdf = gpd.read_file(ASSETS / "districts.geojson")
    return unary_union(gdf.geometry)


def make_mask(polygon, grid_lon, grid_lat):
    """Boolean mask: True where grid point is inside the polygon."""
    try:
        import shapely as shp
        points = shp.points(grid_lon.ravel(), grid_lat.ravel())
        inside = shp.contains(polygon, points)
        return inside.reshape(grid_lon.shape)
    except (ImportError, AttributeError):
        from shapely.prepared import prep
        prepared = prep(polygon)
        mask = np.zeros(grid_lon.shape, dtype=bool)
        for i in range(grid_lon.shape[0]):
            for j in range(grid_lon.shape[1]):
                mask[i, j] = prepared.contains(Point(grid_lon[i, j], grid_lat[i, j]))
        return mask


def date_range(start, end):
    """List of date strings from start to end inclusive."""
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end, "%Y-%m-%d")
    return [(s + timedelta(days=d)).strftime("%Y-%m-%d")
            for d in range((e - s).days + 1)]


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 0: Resolution Test
# ═══════════════════════════════════════════════════════════════════════════════

def phase0_resolution_test():
    print("=" * 60)
    print("PHASE 0: Resolution Test")
    print("=" * 60)

    test_points = [(38.7, -9.2), (38.7, -9.1), (38.8, -9.2), (38.8, -9.1)]
    values = []

    for lat, lon in test_points:
        resp = requests.get(API_URL, params={
            "latitude": lat, "longitude": lon,
            "hourly": "soil_moisture_0_to_7cm",
            "start_date": "2026-01-15", "end_date": "2026-01-15",
            "timezone": "UTC"
        }, timeout=30)
        resp.raise_for_status()
        hourly = resp.json()["hourly"]["soil_moisture_0_to_7cm"]
        daily_mean = float(np.nanmean([v for v in hourly if v is not None]))
        values.append(daily_mean)
        print(f"  ({lat}, {lon}): {daily_mean:.6f}")
        time.sleep(0.25)

    unique = len(set(f"{v:.6f}" for v in values))
    if unique >= 3:
        print(f"✓ Resolution: {unique}/4 distinct values → using 0.1° spacing")
        return 0.1
    else:
        print(f"⚠ Resolution: only {unique}/4 distinct → falling back to 0.25°")
        return 0.25


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: Data Fetching
# ═══════════════════════════════════════════════════════════════════════════════

def generate_grid(spacing, polygon):
    """Grid points inside Portugal polygon + 0.15° buffer."""
    buffer_poly = polygon.buffer(0.15)

    lats = np.arange(SOUTH, NORTH + spacing / 2, spacing)
    lons = np.arange(WEST, EAST + spacing / 2, spacing)
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    mask = make_mask(buffer_poly, lon_grid, lat_grid)
    coords = list(zip(lat_grid.ravel(), lon_grid.ravel()))
    grid_points = [
        (round(float(lat), 2), round(float(lon), 2))
        for (lat, lon), inside in zip(coords, mask.ravel()) if inside
    ]
    print(f"Grid: {len(grid_points)} points at {spacing}° inside Portugal")
    return grid_points


def phase1_fetch(grid_points):
    print("\n" + "=" * 60)
    print("PHASE 1: Data Fetching")
    print("=" * 60)

    sm_cache = CACHE / "soil-moisture-01"
    precip_cache = CACHE / "precipitation-01"
    sm_cache.mkdir(parents=True, exist_ok=True)
    precip_cache.mkdir(parents=True, exist_ok=True)

    # Count existing cache
    existing_sm = len(list(sm_cache.glob("*.json")))
    existing_precip = len(list(precip_cache.glob("*.json")))

    to_fetch = []
    for lat, lon in grid_points:
        sm_file = sm_cache / f"{lat}_{lon}.json"
        precip_file = precip_cache / f"{lat}_{lon}.json"
        if not sm_file.exists() or not precip_file.exists():
            to_fetch.append((lat, lon))

    if existing_sm > 0 or existing_precip > 0:
        print(f"Found {existing_sm} cached SM, {existing_precip} cached precip")
        print(f"Fetching {len(to_fetch)} remaining...")

    if not to_fetch:
        print("✓ All points already cached!")
        return

    print(f"Fetching {len(to_fetch)} points from Open-Meteo...")
    errors = 0

    for i, (lat, lon) in enumerate(to_fetch):
        if i == 0 or (i + 1) % 100 == 0:
            print(f"  Fetched {i + 1}/{len(to_fetch)} points...")

        try:
            resp = requests.get(API_URL, params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "soil_moisture_0_to_7cm",
                "daily": "precipitation_sum",
                "start_date": START_DATE,
                "end_date": END_DATE,
                "timezone": "UTC"
            }, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  ⚠ Error at ({lat}, {lon}): {e}")
            errors += 1
            time.sleep(1)
            continue

        # Soil moisture: hourly → daily mean
        hourly_times = data["hourly"]["time"]
        hourly_sm = data["hourly"]["soil_moisture_0_to_7cm"]

        sm_by_date = {}
        for t, v in zip(hourly_times, hourly_sm):
            date = t[:10]
            if date not in sm_by_date:
                sm_by_date[date] = []
            if v is not None:
                sm_by_date[date].append(v)

        sm_dates = sorted(sm_by_date.keys())
        sm_values = [
            float(np.mean(sm_by_date[d])) if sm_by_date[d] else None
            for d in sm_dates
        ]

        sm_result = {"lat": lat, "lon": lon, "dates": sm_dates, "values": sm_values}

        # Precipitation (already daily)
        precip_result = {
            "lat": lat, "lon": lon,
            "dates": data["daily"]["time"],
            "values": data["daily"]["precipitation_sum"]
        }

        sm_file = sm_cache / f"{lat}_{lon}.json"
        precip_file = precip_cache / f"{lat}_{lon}.json"
        with open(sm_file, 'w') as f:
            json.dump(sm_result, f)
        with open(precip_file, 'w') as f:
            json.dump(precip_result, f)

        time.sleep(0.25)

    print(f"✓ Fetching complete ({errors} errors)")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: COG Generation
# ═══════════════════════════════════════════════════════════════════════════════

def load_variable_data(variable, grid_points):
    """Load cached data → dict: date → list of (lat, lon, value)."""
    cache_name = "soil-moisture-01" if variable == "soil-moisture" else "precipitation-01"
    cache_dir = CACHE / cache_name
    all_data = {}
    loaded = 0

    for lat, lon in grid_points:
        cache_file = cache_dir / f"{lat}_{lon}.json"
        if not cache_file.exists():
            continue

        with open(cache_file) as f:
            data = json.load(f)

        for date, value in zip(data["dates"], data["values"]):
            if value is None:
                continue
            all_data.setdefault(date, []).append(
                (data["lat"], data["lon"], float(value))
            )
        loaded += 1

    print(f"  Loaded {loaded} files for {variable}, {len(all_data)} dates")
    return all_data


def phase2_generate_cogs(variable, grid_points, polygon):
    """Generate COGs for one variable. Returns (dates, global_min, global_max)."""
    output_dir = COG_SM if variable == "soil-moisture" else COG_PRECIP
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  Generating COGs for {variable}...")
    all_data = load_variable_data(variable, grid_points)

    # Build interpolation target grid at pixel centers
    ncols = int(round((EAST - WEST) / PIXEL_SIZE))
    nrows = int(round((NORTH - SOUTH) / PIXEL_SIZE))
    fine_lons = np.linspace(WEST + PIXEL_SIZE / 2, EAST - PIXEL_SIZE / 2, ncols)
    fine_lats = np.linspace(SOUTH + PIXEL_SIZE / 2, NORTH - PIXEL_SIZE / 2, nrows)
    grid_lon, grid_lat = np.meshgrid(fine_lons, fine_lats)

    mask = make_mask(polygon, grid_lon, grid_lat)
    transform = from_bounds(WEST, SOUTH, EAST, NORTH, ncols, nrows)

    dates = sorted(all_data.keys())
    global_min = float('inf')
    global_max = float('-inf')

    profile = {
        'driver': 'GTiff',
        'height': nrows,
        'width': ncols,
        'count': 1,
        'dtype': 'float32',
        'crs': 'EPSG:4326',
        'transform': transform,
        'nodata': float('nan'),
        'compress': 'deflate',
        'tiled': True,
        'blockxsize': 256,
        'blockysize': 256,
    }

    for i, date in enumerate(dates):
        if i == 0 or (i + 1) % 10 == 0:
            print(f"    COG {i + 1}/{len(dates)}: {date}")

        points = all_data[date]
        src_lats = np.array([p[0] for p in points])
        src_lons = np.array([p[1] for p in points])
        src_vals = np.array([p[2] for p in points])

        global_min = min(global_min, float(np.nanmin(src_vals)))
        global_max = max(global_max, float(np.nanmax(src_vals)))

        # Cubic interpolation with linear fallback
        try:
            grid_z = scipy.interpolate.griddata(
                (src_lons, src_lats), src_vals,
                (grid_lon, grid_lat), method='cubic'
            )
            nan_in_mask = np.isnan(grid_z[mask]).sum()
            if nan_in_mask > 0.3 * mask.sum():
                raise ValueError("Too many NaN from cubic")
        except Exception:
            grid_z = scipy.interpolate.griddata(
                (src_lons, src_lats), src_vals,
                (grid_lon, grid_lat), method='linear'
            )

        # Clamp negatives for precipitation
        if variable == "precipitation":
            grid_z = np.where(np.isnan(grid_z), grid_z, np.maximum(grid_z, 0))

        # Mask outside Portugal
        grid_z[~mask] = np.nan

        # Flip to north-up for rasterio
        grid_z_flip = np.flipud(grid_z)

        output_path = output_dir / f"{date}.tif"
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(grid_z_flip.astype(np.float32), 1)

        # Add overviews
        with rasterio.open(output_path, 'r+') as dst:
            dst.build_overviews([2, 4], Resampling.average)
            dst.update_tags(ns='rio_overview', resampling='average')

    print(f"  ✓ {len(dates)} COGs → {output_dir}")
    print(f"  Value range: {global_min:.4f} → {global_max:.4f}")
    return dates, global_min, global_max


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: PNG Rendering
# ═══════════════════════════════════════════════════════════════════════════════

def render_sm_png(cog_path, output_path, vmin, vmax):
    """Render soil moisture COG → transparent RGBA PNG."""
    with rasterio.open(cog_path) as ds:
        data = ds.read(1)

    nodata = np.isnan(data)

    # Clamp to physical range (cubic interpolation can produce slight negatives)
    data = np.where(nodata, data, np.maximum(data, 0))

    # Normalize to [0, 1]
    norm = np.clip((data - max(vmin, 0)) / (vmax - max(vmin, 0)), 0, 1)
    colored = SM_CMAP(norm)  # (H, W, 4) float [0,1]

    # Alpha: 0.80 for data, 0 for nodata
    colored[..., 3] = 0.80
    colored[nodata] = [0, 0, 0, 0]

    rgba = (colored * 255).astype(np.uint8)
    img = Image.fromarray(rgba, 'RGBA')
    img = img.resize((img.width * PNG_SCALE, img.height * PNG_SCALE), Image.LANCZOS)

    # Quantize RGB after upscale for better PNG compression
    arr = np.array(img)
    arr[..., :3] = (arr[..., :3] // 4) * 4
    img = Image.fromarray(arr, 'RGBA')

    img.save(output_path, optimize=True, compress_level=9)


def render_precip_png(cog_path, output_path):
    """Render precipitation COG → transparent RGBA PNG."""
    with rasterio.open(cog_path) as ds:
        data = ds.read(1)

    nodata = np.isnan(data)

    # Color from BoundaryNorm
    colored = PRECIP_CMAP(PRECIP_NORM(data))  # (H, W, 4) float

    # Alpha by value
    alpha = np.zeros_like(data)
    alpha[(data >= 1) & (data < 5)] = 0.4
    alpha[(data >= 5) & (data < 30)] = 0.8
    alpha[data >= 30] = 0.9
    colored[..., 3] = alpha
    colored[nodata] = [0, 0, 0, 0]

    rgba = (colored * 255).astype(np.uint8)
    img = Image.fromarray(rgba, 'RGBA')
    img = img.resize((img.width * PNG_SCALE, img.height * PNG_SCALE), Image.LANCZOS)

    # Quantize RGB after upscale for better PNG compression
    arr = np.array(img)
    arr[..., :3] = (arr[..., :3] // 4) * 4
    img = Image.fromarray(arr, 'RGBA')

    img.save(output_path, optimize=True, compress_level=9)


def phase3_render_pngs(sm_min, sm_max):
    print("\n" + "=" * 60)
    print("PHASE 3: PNG Rendering")
    print("=" * 60)

    # Soil moisture
    PNG_SM.mkdir(parents=True, exist_ok=True)
    sm_cogs = sorted(COG_SM.glob("*.tif"))
    print(f"Rendering {len(sm_cogs)} soil moisture PNGs...")
    for i, cog in enumerate(sm_cogs):
        if i == 0 or (i + 1) % 10 == 0:
            print(f"  PNG {i + 1}/{len(sm_cogs)}: {cog.stem}")
        render_sm_png(cog, PNG_SM / f"{cog.stem}.png", sm_min, sm_max)

    # Precipitation
    PNG_PRECIP.mkdir(parents=True, exist_ok=True)
    precip_cogs = sorted(COG_PRECIP.glob("*.tif"))
    print(f"Rendering {len(precip_cogs)} precipitation PNGs...")
    for i, cog in enumerate(precip_cogs):
        if i == 0 or (i + 1) % 10 == 0:
            print(f"  PNG {i + 1}/{len(precip_cogs)}: {cog.stem}")
        render_precip_png(cog, PNG_PRECIP / f"{cog.stem}.png")

    print("✓ All PNGs rendered")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: Manifest
# ═══════════════════════════════════════════════════════════════════════════════

def phase4_manifest():
    print("\n" + "=" * 60)
    print("PHASE 4: Manifest")
    print("=" * 60)

    FRONTEND.mkdir(parents=True, exist_ok=True)

    sm_frames = sorted(PNG_SM.glob("*.png"))
    precip_frames = sorted(PNG_PRECIP.glob("*.png"))

    manifest = {
        "soil_moisture": {
            "bounds": [WEST, SOUTH, EAST, NORTH],
            "frames": [
                {"date": f.stem, "url": f"raster-frames/soil-moisture/{f.name}"}
                for f in sm_frames
            ]
        },
        "precipitation": {
            "bounds": [WEST, SOUTH, EAST, NORTH],
            "frames": [
                {"date": f.stem, "url": f"raster-frames/precipitation/{f.name}"}
                for f in precip_frames
            ]
        },
        "cog": {
            "soil_moisture_dir": "cog/soil-moisture/",
            "precipitation_dir": "cog/precipitation/",
            "crs": "EPSG:4326",
            "note": "COGs for titiler dynamic rendering"
        }
    }

    path = FRONTEND / "raster-manifest.json"
    with open(path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"✓ Manifest: {path}")
    print(f"  SM frames: {len(sm_frames)}, Precip frames: {len(precip_frames)}")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: Visual QA
# ═══════════════════════════════════════════════════════════════════════════════

def phase5_qa():
    print("\n" + "=" * 60)
    print("PHASE 5: Visual QA")
    print("=" * 60)

    FIGURES.mkdir(parents=True, exist_ok=True)
    gdf = gpd.read_file(ASSETS / "districts.geojson")

    # ── 1. Soil moisture filmstrip ──
    sm_dates = [
        "2025-12-01", "2025-12-15", "2026-01-01", "2026-01-15",
        "2026-01-28", "2026-02-01", "2026-02-07", "2026-02-15"
    ]
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    fig.suptitle("Soil Moisture Progression (Dec 2025 → Feb 2026)",
                 fontsize=16, fontweight='bold')

    for ax, date in zip(axes.ravel(), sm_dates):
        png_path = PNG_SM / f"{date}.png"
        gdf.boundary.plot(ax=ax, color='#999999', linewidth=0.5)
        if png_path.exists():
            img = Image.open(png_path)
            ax.imshow(np.array(img), extent=[WEST, EAST, SOUTH, NORTH], zorder=2)
        ax.set_title(date, fontsize=11)
        ax.set_xlim(WEST, EAST)
        ax.set_ylim(SOUTH, NORTH)
        ax.set_aspect('equal')
        ax.axis('off')

    plt.tight_layout()
    out = FIGURES / "soil-moisture-filmstrip.png"
    fig.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ {out}")

    # ── 2. Precipitation filmstrip ──
    precip_dates = [
        "2026-01-28", "2026-01-29", "2026-01-30", "2026-02-05",
        "2026-02-06", "2026-02-07", "2026-02-10", "2026-02-11"
    ]
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    fig.suptitle("Precipitation Storm Pulses (Jan–Feb 2026)",
                 fontsize=16, fontweight='bold')

    for ax, date in zip(axes.ravel(), precip_dates):
        png_path = PNG_PRECIP / f"{date}.png"
        gdf.boundary.plot(ax=ax, color='#999999', linewidth=0.5)
        if png_path.exists():
            img = Image.open(png_path)
            ax.imshow(np.array(img), extent=[WEST, EAST, SOUTH, NORTH], zorder=2)
        ax.set_title(date, fontsize=11)
        ax.set_xlim(WEST, EAST)
        ax.set_ylim(SOUTH, NORTH)
        ax.set_aspect('equal')
        ax.axis('off')

    plt.tight_layout()
    out = FIGURES / "precipitation-filmstrip.png"
    fig.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ {out}")

    # ── 3. Summary statistics ──
    print("\n  ─── Summary Statistics ───")

    sm_cogs = sorted(COG_SM.glob("*.tif"))
    precip_cogs = sorted(COG_PRECIP.glob("*.tif"))
    sm_pngs = sorted(PNG_SM.glob("*.png"))
    precip_pngs = sorted(PNG_PRECIP.glob("*.png"))

    cog_total = sum(f.stat().st_size for f in sm_cogs + precip_cogs)
    png_total = sum(f.stat().st_size for f in sm_pngs + precip_pngs)
    total = cog_total + png_total

    print(f"  COGs: {len(sm_cogs)} SM + {len(precip_cogs)} precip"
          f" = {len(sm_cogs) + len(precip_cogs)}, {cog_total / 1e6:.1f} MB")
    print(f"  PNGs: {len(sm_pngs)} SM + {len(precip_pngs)} precip"
          f" = {len(sm_pngs) + len(precip_pngs)}, {png_total / 1e6:.1f} MB")
    print(f"  Total raster output: {total / 1e6:.1f} MB")

    # Value ranges from COGs
    sm_min, sm_max = float('inf'), float('-inf')
    for cog in sm_cogs:
        with rasterio.open(cog) as ds:
            d = ds.read(1)
            valid = d[~np.isnan(d)]
            if len(valid):
                sm_min = min(sm_min, float(valid.min()))
                sm_max = max(sm_max, float(valid.max()))
    print(f"  Soil moisture range: {sm_min:.4f} → {sm_max:.4f} m³/m³")

    pr_min, pr_max = float('inf'), float('-inf')
    for cog in precip_cogs:
        with rasterio.open(cog) as ds:
            d = ds.read(1)
            valid = d[~np.isnan(d)]
            if len(valid):
                pr_min = min(pr_min, float(valid.min()))
                pr_max = max(pr_max, float(valid.max()))
    print(f"  Precipitation range: {pr_min:.1f} → {pr_max:.1f} mm/day")

    # PNG sizes
    all_pngs = sm_pngs + precip_pngs
    if all_pngs:
        sizes = [f.stat().st_size for f in all_pngs]
        print(f"  PNG size range: {min(sizes)/1024:.0f} KB → {max(sizes)/1024:.0f} KB")
        over = sum(1 for s in sizes if s > 300 * 1024)
        if over:
            print(f"  ⚠ {over} PNGs exceed 300 KB")
        else:
            print(f"  ✓ All PNGs under 300 KB")

    if total > 50 * 1e6:
        print(f"  ⚠ Total raster output exceeds 50 MB budget")
    else:
        print(f"  ✓ Total raster output within 50 MB budget")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()
    print("Sprint 04: Cloud-Optimized Raster Pipeline")
    print("=" * 60)

    portugal_poly = get_portugal_polygon()

    # Phase 0
    spacing = phase0_resolution_test()

    # Phase 1
    grid_points = generate_grid(spacing, portugal_poly)
    phase1_fetch(grid_points)

    # Phase 2
    print("\n" + "=" * 60)
    print("PHASE 2: COG Generation")
    print("=" * 60)
    sm_dates, sm_min, sm_max = phase2_generate_cogs(
        "soil-moisture", grid_points, portugal_poly
    )
    precip_dates, pr_min, pr_max = phase2_generate_cogs(
        "precipitation", grid_points, portugal_poly
    )

    # Phase 3
    phase3_render_pngs(sm_min, sm_max)

    # Phase 4
    phase4_manifest()

    # Phase 5
    phase5_qa()

    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"✓ Sprint 04 complete! ({elapsed / 60:.1f} min)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
