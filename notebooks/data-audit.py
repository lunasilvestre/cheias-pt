#!/usr/bin/env python3
"""Data Audit: every layer we have, properly aligned, one notebook.

NO presentation code. Just: what data do we have, what does it look like,
does it align to Portugal's actual geography?

Layers:
  1. Portugal boundaries (districts.geojson)
  2. Soil moisture COGs (77 days)
  3. Precipitation COGs (77 days)
  4. Flood extent PMTiles / shapefiles (EMSR861 + EMSR864)
  5. GloFAS discharge (if any processed data exists)
  6. Basins (if any)
  7. Consequence markers / news events (if any)

Output: notebooks/data-audit.py (run as script or convert to notebook)
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap

warnings.filterwarnings('ignore')

ROOT = Path("/home/nls/Documents/dev/cheias-pt")
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
FIGURES = ROOT / "notebooks" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

WEST, SOUTH, EAST, NORTH = -9.6, 36.9, -6.1, 42.2

# ─── Color ramps (same as pipeline) ─────────────────────────────────────────

SM_CMAP = LinearSegmentedColormap.from_list('soil_moisture', [
    (0.0,  '#8B6914'),
    (0.25, '#B8860B'),
    (0.45, '#7A9A6E'),
    (0.6,  '#4A90A4'),
    (0.8,  '#2E86AB'),
    (1.0,  '#1B4965'),
])

PRECIP_BOUNDS = [0, 1, 5, 15, 30, 50, 80, 150]
PRECIP_COLORS = ['#f0f0f0', '#FFF9C4', '#FFD54F', '#FF8F00', '#E53935', '#B71C1C', '#4A0000']
PRECIP_CMAP = ListedColormap(PRECIP_COLORS)
PRECIP_CMAP.set_over(PRECIP_COLORS[-1])
PRECIP_NORM = BoundaryNorm(PRECIP_BOUNDS, PRECIP_CMAP.N)

# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("DATA AUDIT — cheias.pt")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. PORTUGAL BOUNDARIES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n1. PORTUGAL BOUNDARIES")
print("-" * 40)

districts = gpd.read_file(ASSETS / "districts.geojson")
print(f"   File: assets/districts.geojson")
print(f"   CRS: {districts.crs}")
print(f"   Features: {len(districts)}")
print(f"   Bounds: {districts.total_bounds}")
print(f"   Columns: {list(districts.columns)}")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. SOIL MOISTURE COGs
# ═══════════════════════════════════════════════════════════════════════════════
print("\n2. SOIL MOISTURE COGs")
print("-" * 40)

sm_cogs = sorted((DATA / "cog" / "soil-moisture").glob("*.tif"))
print(f"   Count: {len(sm_cogs)}")
print(f"   Date range: {sm_cogs[0].stem} → {sm_cogs[-1].stem}")

with rasterio.open(sm_cogs[0]) as ds:
    print(f"   CRS: {ds.crs}")
    print(f"   Size: {ds.width}×{ds.height}")
    print(f"   Pixel size: {ds.res[0]:.4f}° = {ds.res[0]*111:.1f}km")
    print(f"   Bounds: {ds.bounds}")
    print(f"   Transform: {ds.transform}")
    sm_profile = ds.profile.copy()
    sm_transform = ds.transform
    sm_bounds = ds.bounds

# Read a peak frame
with rasterio.open(DATA / "cog" / "soil-moisture" / "2026-01-28.tif") as ds:
    sm_data = ds.read(1)
    sm_valid = sm_data[~np.isnan(sm_data)]
    print(f"   Jan 28 stats: min={sm_valid.min():.4f}, max={sm_valid.max():.4f}, "
          f"mean={sm_valid.mean():.4f}, std={sm_valid.std():.4f}")
    print(f"   Negative values: {(sm_valid < 0).sum()}")
    print(f"   Valid pixels: {len(sm_valid)} / {sm_data.size}")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. PRECIPITATION COGs
# ═══════════════════════════════════════════════════════════════════════════════
print("\n3. PRECIPITATION COGs")
print("-" * 40)

pr_cogs = sorted((DATA / "cog" / "precipitation").glob("*.tif"))
print(f"   Count: {len(pr_cogs)}")

with rasterio.open(pr_cogs[0]) as ds:
    print(f"   CRS: {ds.crs}")
    print(f"   Size: {ds.width}×{ds.height}")
    print(f"   Pixel size: {ds.res[0]:.4f}°")

# Storm peak
with rasterio.open(DATA / "cog" / "precipitation" / "2026-01-29.tif") as ds:
    pr_data = ds.read(1)
    pr_valid = pr_data[~np.isnan(pr_data)]
    print(f"   Jan 29 (Kristin): min={pr_valid.min():.1f}, max={pr_valid.max():.1f}, "
          f"mean={pr_valid.mean():.1f}mm")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. FLOOD EXTENT DATA
# ═══════════════════════════════════════════════════════════════════════════════
print("\n4. FLOOD EXTENT DATA")
print("-" * 40)

# PMTiles
pmtiles = sorted((DATA / "flood-extent").glob("*.pmtiles"))
for p in pmtiles:
    print(f"   PMTiles: {p.name} ({p.stat().st_size/1e6:.1f} MB)")

# Shapefiles — read all flood extent polygons
flood_gdfs = []
shp_dirs = sorted((DATA / "flood-extent").glob("EMSR*"))
print(f"   CEMS directories: {len(shp_dirs)}")

for d in shp_dirs:
    shps = list(d.glob("*floodDepth*.shp"))
    jsons = list(d.glob("*floodDepth*.json"))
    src = shps[0] if shps else (jsons[0] if jsons else None)
    if src:
        try:
            gdf = gpd.read_file(src)
            gdf['source_dir'] = d.name
            flood_gdfs.append(gdf)
        except Exception as e:
            print(f"   ⚠ Failed to read {d.name}: {e}")

if flood_gdfs:
    all_floods = gpd.GeoDataFrame(pd.concat(flood_gdfs, ignore_index=True))
    print(f"   Total flood polygons: {len(all_floods)}")
    print(f"   CRS: {all_floods.crs}")
    print(f"   Bounds: {all_floods.total_bounds}")
    print(f"   Columns: {[c for c in all_floods.columns if c != 'geometry'][:10]}")
    
    # EMSR breakdown
    emsr_ids = set()
    for name in all_floods['source_dir'].unique():
        emsr_id = name.split('_')[0]
        emsr_ids.add(emsr_id)
    for eid in sorted(emsr_ids):
        subset = all_floods[all_floods['source_dir'].str.startswith(eid)]
        print(f"   {eid}: {len(subset)} polygons")
else:
    all_floods = None
    print("   ⚠ No flood polygons loaded")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. OTHER DATA
# ═══════════════════════════════════════════════════════════════════════════════
print("\n5. OTHER DATA FILES")
print("-" * 40)

# Check for basins, discharge, consequence markers
for pattern in ["basins*", "glofas*", "discharge*", "consequence*", "markers*", "news*"]:
    found = list(DATA.rglob(pattern))
    found += list(ASSETS.rglob(pattern))
    if found:
        for f in found[:5]:
            print(f"   {f.relative_to(ROOT)} ({f.stat().st_size/1e6:.1f} MB)")

# Frontend JSON data
frontend_dir = DATA / "frontend"
if frontend_dir.exists():
    for f in sorted(frontend_dir.glob("*.json")):
        print(f"   {f.relative_to(ROOT)} ({f.stat().st_size/1e6:.1f} MB)")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1: All layers on one map — EPSG:4326 (native CRS, no distortion)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("GENERATING ALIGNMENT FIGURES")

fig, axes = plt.subplots(1, 3, figsize=(24, 12))

# --- Panel 1: Soil moisture + districts ---
ax = axes[0]
ax.set_title("Soil Moisture (Jan 28) + District Boundaries", fontsize=11, fontweight='bold')

with rasterio.open(DATA / "cog" / "soil-moisture" / "2026-01-28.tif") as ds:
    data = ds.read(1)
    extent = [ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top]

masked = np.ma.masked_invalid(data)
im = ax.imshow(masked, extent=extent, origin='upper', cmap=SM_CMAP,
               vmin=0, vmax=0.55, interpolation='nearest', zorder=1)
districts.boundary.plot(ax=ax, color='white', linewidth=0.8, zorder=2)
ax.set_xlim(WEST - 0.2, EAST + 0.5)
ax.set_ylim(SOUTH - 0.2, NORTH + 0.2)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3, linewidth=0.5)
plt.colorbar(im, ax=ax, label='m³/m³', shrink=0.7)

# --- Panel 2: Precipitation (Kristin) + districts ---
ax = axes[1]
ax.set_title("Precipitation Jan 29 (Kristin) + Districts", fontsize=11, fontweight='bold')

with rasterio.open(DATA / "cog" / "precipitation" / "2026-01-29.tif") as ds:
    data = ds.read(1)
    extent = [ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top]

masked = np.ma.masked_where(np.isnan(data) | (data < 1), data)
im = ax.imshow(masked, extent=extent, origin='upper', cmap=PRECIP_CMAP, norm=PRECIP_NORM,
               interpolation='nearest', zorder=1)
districts.boundary.plot(ax=ax, color='white', linewidth=0.8, zorder=2)
ax.set_xlim(WEST - 0.2, EAST + 0.5)
ax.set_ylim(SOUTH - 0.2, NORTH + 0.2)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3, linewidth=0.5)
plt.colorbar(im, ax=ax, label='mm/day', shrink=0.7)

# --- Panel 3: Flood extents + districts ---
ax = axes[2]
ax.set_title("CEMS Flood Extents + Districts", fontsize=11, fontweight='bold')

districts.boundary.plot(ax=ax, color='#666666', linewidth=0.8, zorder=1)
if all_floods is not None and len(all_floods) > 0:
    # Ensure same CRS
    if all_floods.crs != districts.crs:
        all_floods = all_floods.to_crs(districts.crs)
    all_floods.plot(ax=ax, color='#e74c3c', alpha=0.6, edgecolor='#b71c1c',
                    linewidth=0.3, zorder=2)
ax.set_xlim(WEST - 0.2, EAST + 0.5)
ax.set_ylim(SOUTH - 0.2, NORTH + 0.2)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3, linewidth=0.5)

plt.suptitle("DATA AUDIT — All Layers in EPSG:4326 (Native CRS, No Reprojection)",
             fontsize=14, fontweight='bold', y=0.98)
plt.tight_layout()
out = FIGURES / "data-audit-alignment.png"
fig.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"✓ Saved: {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2: Zoom to flood areas — verify spatial accuracy
# ═══════════════════════════════════════════════════════════════════════════════

if all_floods is not None and len(all_floods) > 0:
    # Find distinct flood clusters
    fb = all_floods.total_bounds  # [minx, miny, maxx, maxy]
    
    # Key flood zones from EMSR864 (Tejo/Sorraia) and EMSR861
    zoom_areas = []
    
    for eid in sorted(emsr_ids):
        subset = all_floods[all_floods['source_dir'].str.startswith(eid)]
        if len(subset) > 0:
            b = subset.total_bounds
            cx, cy = (b[0]+b[2])/2, (b[1]+b[3])/2
            span = max(b[2]-b[0], b[3]-b[1])
            pad = max(span * 0.5, 0.1)
            zoom_areas.append({
                'name': eid,
                'bounds': [b[0]-pad, b[1]-pad, b[2]+pad, b[3]+pad],
                'n_polys': len(subset),
                'subset': subset,
            })
    
    n_zooms = min(len(zoom_areas), 4)
    if n_zooms > 0:
        fig, axes = plt.subplots(1, n_zooms, figsize=(7*n_zooms, 8))
        if n_zooms == 1:
            axes = [axes]
        
        for ax, za in zip(axes, zoom_areas[:n_zooms]):
            b = za['bounds']
            ax.set_title(f"{za['name']} ({za['n_polys']} polygons)", fontsize=11, fontweight='bold')
            
            districts.boundary.plot(ax=ax, color='#666666', linewidth=1, zorder=1)
            za['subset'].plot(ax=ax, color='#e74c3c', alpha=0.7, edgecolor='#b71c1c',
                             linewidth=0.5, zorder=2)
            
            # Overlay soil moisture for context
            with rasterio.open(DATA / "cog" / "soil-moisture" / "2026-01-28.tif") as ds:
                data = ds.read(1)
                extent = [ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top]
            masked = np.ma.masked_invalid(data)
            ax.imshow(masked, extent=extent, origin='upper', cmap=SM_CMAP,
                      vmin=0, vmax=0.55, alpha=0.3, interpolation='nearest', zorder=0)
            
            ax.set_xlim(b[0], b[2])
            ax.set_ylim(b[1], b[3])
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3, linewidth=0.5)
        
        plt.suptitle("FLOOD EXTENT ZOOM — CEMS polygons over soil moisture",
                     fontsize=14, fontweight='bold', y=0.98)
        plt.tight_layout()
        out = FIGURES / "data-audit-flood-zoom.png"
        fig.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"✓ Saved: {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 3: Pixel grid visibility test — how granular is 0.1° really?
# ═══════════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# Left: full Portugal with pixel grid visible
ax = axes[0]
ax.set_title("Full Portugal — pixel grid at 0.02° (interpolated from 0.1°)", fontsize=10, fontweight='bold')

with rasterio.open(DATA / "cog" / "soil-moisture" / "2026-01-28.tif") as ds:
    data = ds.read(1)
    extent = [ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top]

masked = np.ma.masked_invalid(data)
ax.imshow(masked, extent=extent, origin='upper', cmap=SM_CMAP,
          vmin=0, vmax=0.55, interpolation='nearest', zorder=1)
districts.boundary.plot(ax=ax, color='white', linewidth=0.8, zorder=2)
ax.set_xlim(WEST, EAST)
ax.set_ylim(SOUTH, NORTH)
ax.set_aspect('equal')

# Right: zoom to Lisbon area to see actual pixel size
ax = axes[1]
ax.set_title("Zoom: Lisbon/Santarém — each pixel = 0.02° = 2.2km", fontsize=10, fontweight='bold')

ax.imshow(masked, extent=extent, origin='upper', cmap=SM_CMAP,
          vmin=0, vmax=0.55, interpolation='nearest', zorder=1)
districts.boundary.plot(ax=ax, color='white', linewidth=1, zorder=2)
ax.set_xlim(-9.5, -8.5)
ax.set_ylim(38.5, 39.5)
ax.set_aspect('equal')
ax.grid(True, alpha=0.5, linewidth=0.5)

plt.suptitle("RESOLUTION AUDIT — interpolation='nearest' to show true pixel edges",
             fontsize=13, fontweight='bold')
plt.tight_layout()
out = FIGURES / "data-audit-resolution.png"
fig.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print(f"✓ Saved: {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 4: Source data points vs interpolated grid
# ═══════════════════════════════════════════════════════════════════════════════

# Show where the actual Open-Meteo sample points are
cache_dir = DATA / "cache" / "soil-moisture-01"
cache_files = sorted(cache_dir.glob("*.json"))

src_lats, src_lons = [], []
for f in cache_files:
    d = json.load(open(f))
    src_lats.append(d['lat'])
    src_lons.append(d['lon'])

fig, ax = plt.subplots(figsize=(10, 12))
ax.set_title(f"Source Grid: {len(cache_files)} Open-Meteo points at 0.1° spacing\n"
             f"vs COG pixels at 0.02° (5× interpolated)", fontsize=11, fontweight='bold')

# Show COG pixel grid as faint background
with rasterio.open(DATA / "cog" / "soil-moisture" / "2026-01-28.tif") as ds:
    data = ds.read(1)
    extent = [ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top]
masked = np.ma.masked_invalid(data)
ax.imshow(masked, extent=extent, origin='upper', cmap=SM_CMAP,
          vmin=0, vmax=0.55, alpha=0.4, interpolation='nearest', zorder=0)

# District boundaries
districts.boundary.plot(ax=ax, color='#333333', linewidth=1, zorder=2)

# Source points
ax.scatter(src_lons, src_lats, c='red', s=8, zorder=3, label=f'Open-Meteo points ({len(cache_files)})')
ax.legend(fontsize=10)
ax.set_xlim(WEST - 0.2, EAST + 0.5)
ax.set_ylim(SOUTH - 0.2, NORTH + 0.2)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3, linewidth=0.5)

plt.tight_layout()
out = FIGURES / "data-audit-source-points.png"
fig.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"✓ Saved: {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 5: Extreme values / interpolation artifacts
# ═══════════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# Left: soil moisture with extreme pixels highlighted
ax = axes[0]
ax.set_title("Soil Moisture Jan 28 — extreme pixels (< P2 or > P98)", fontsize=10, fontweight='bold')

with rasterio.open(DATA / "cog" / "soil-moisture" / "2026-01-28.tif") as ds:
    data = ds.read(1)
    extent = [ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top]

valid_mask = ~np.isnan(data)
valid_vals = data[valid_mask]
p2, p98 = np.percentile(valid_vals, [2, 98])

masked = np.ma.masked_invalid(data)
ax.imshow(masked, extent=extent, origin='upper', cmap=SM_CMAP,
          vmin=0, vmax=0.55, interpolation='nearest', zorder=1)

# Highlight extreme pixels
extreme_mask = valid_mask & ((data < p2) | (data > p98))
extreme_overlay = np.zeros((*data.shape, 4))
extreme_overlay[extreme_mask] = [1, 0, 1, 0.8]  # magenta
ax.imshow(extreme_overlay, extent=extent, origin='upper', zorder=2)

districts.boundary.plot(ax=ax, color='white', linewidth=0.5, zorder=3)
ax.set_xlim(WEST, EAST)
ax.set_ylim(SOUTH, NORTH)
ax.set_aspect('equal')
ax.text(0.02, 0.02, f'P2={p2:.4f}, P98={p98:.4f}\nNegatives: {(valid_vals<0).sum()}',
        transform=ax.transAxes, fontsize=9, color='magenta',
        bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))

# Right: histogram
ax = axes[1]
ax.set_title("Value Distribution — Soil Moisture Jan 28", fontsize=10, fontweight='bold')
ax.hist(valid_vals, bins=100, color='steelblue', alpha=0.7, edgecolor='none')
ax.axvline(p2, color='magenta', linestyle='--', label=f'P2={p2:.4f}')
ax.axvline(p98, color='magenta', linestyle='--', label=f'P98={p98:.4f}')
ax.axvline(0, color='red', linestyle='-', linewidth=2, label='Zero (physical min)')
ax.set_xlabel('Soil moisture (m³/m³)')
ax.set_ylabel('Pixel count')
ax.legend()

plt.tight_layout()
out = FIGURES / "data-audit-extremes.png"
fig.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"✓ Saved: {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SUMMARY OF ISSUES")
print("=" * 70)
print("""
1. PROJECTION OFFSET: COGs are EPSG:4326 (equirectangular). MapLibre is
   EPSG:3857 (Web Mercator). PNG image sources get ~7.3km shift at center
   of Portugal. PNGs MUST be reprojected to 3857 before serving.

2. RESOLUTION: Source data is 0.1° (11km) from Open-Meteo. COGs interpolate
   to 0.02° (2.2km) via cubic but this is synthetic resolution — the actual
   spatial information content is 11km. At zoom 7-8, pixels are visible.

3. INTERPOLATION ARTIFACTS: Cubic interpolation creates negative soil moisture
   values and extreme outlier pixels near coastline/nodata boundaries.
   Need percentile clamping + gaussian smoothing.

4. FLOOD EXTENTS: CEMS shapefiles exist and load correctly. Need to verify
   PMTiles contain the same data and render in MapLibre.

5. BORDER MISMATCH: COG mask uses districts.geojson polygon, which has its
   own coastline generalization. Any reprojection will need the mask
   re-rasterized in the target CRS.
""")

print("Figures saved to notebooks/figures/data-audit-*.png")
