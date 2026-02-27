#!/usr/bin/env python3
"""
analyze_frontal_positions.py

Diagnostic script for identifying frontal boundary positions from MSLP and wind COGs.
Reads ERA5 MSLP, wind-u, wind-v at 4 key timesteps, computes pressure gradient
magnitude and wind direction shift to locate frontal zones.

Outputs analysis to stdout and saves derived metrics to data/qgis/ for GeoJSON construction.

Key timesteps:
  1. 2026-01-28T00 — Kristin trailing cold front
  2. 2026-01-28T12 — Kristin cold front passed
  3. 2026-02-05T12 — Leonardo warm front ahead of low
  4. 2026-02-10T06 — Marta trailing cold front
"""

import sys
import numpy as np
import rasterio
from rasterio.transform import xy
from pathlib import Path

PROJECT = Path("/home/nls/Documents/dev/cheias-pt")
MSLP_DIR = PROJECT / "data/cog/mslp"
WIND_U_DIR = PROJECT / "data/cog/wind-u"
WIND_V_DIR = PROJECT / "data/cog/wind-v"

TIMESTEPS = [
    {
        "datetime": "2026-01-28T00",
        "storm": "Kristin",
        "front_type": "cold",
        "label": "Frente fria (Kristin)",
    },
    {
        "datetime": "2026-01-28T12",
        "storm": "Kristin",
        "front_type": "cold",
        "label": "Frente fria (Kristin) — passagem",
    },
    {
        "datetime": "2026-02-05T12",
        "storm": "Leonardo",
        "front_type": "warm",
        "label": "Frente quente (Leonardo)",
    },
    {
        "datetime": "2026-02-10T06",
        "storm": "Marta",
        "front_type": "cold",
        "label": "Frente fria (Marta)",
    },
]


def read_cog(filepath):
    """Read a COG and return (data_array, transform, crs, lons, lats)."""
    with rasterio.open(filepath) as src:
        data = src.read(1).astype(np.float32)
        transform = src.transform
        crs = src.crs
        height, width = data.shape
        rows, cols = np.mgrid[0:height, 0:width]
        lons_flat, lats_flat = rasterio.transform.xy(transform, rows.ravel(), cols.ravel())
        lons = np.array(lons_flat).reshape(height, width)
        lats = np.array(lats_flat).reshape(height, width)
        return data, transform, crs, lons, lats


def compute_gradient_magnitude(mslp, lons, lats):
    """
    Compute pressure gradient magnitude in hPa/degree, accounting for
    approximate grid spacing (gradient in lat/lon space).
    """
    # Gradient in pixel space — convert to approximate physical gradient
    dy, dx = np.gradient(mslp)
    # Approximate lat/lon spacing in degrees
    dlat = np.abs(np.gradient(lats, axis=0))
    dlon = np.abs(np.gradient(lons, axis=1))
    dlat = np.where(dlat < 1e-6, 1e-6, dlat)
    dlon = np.where(dlon < 1e-6, 1e-6, dlon)
    grad_lat = dy / dlat  # hPa/degree lat
    grad_lon = dx / dlon  # hPa/degree lon
    grad_mag = np.sqrt(grad_lat**2 + grad_lon**2)
    return grad_mag, grad_lat, grad_lon


def compute_wind_direction(u, v):
    """Meteorological wind direction: direction FROM which wind blows, 0=N, 90=E."""
    wdir = (270 - np.degrees(np.arctan2(v, u))) % 360
    return wdir


def find_low_center(mslp, lons, lats, domain=None):
    """Find the minimum MSLP position within an optional lat/lon domain."""
    if domain:
        lon_min, lon_max, lat_min, lat_max = domain
        mask = (lons >= lon_min) & (lons <= lon_max) & (lats >= lat_min) & (lats <= lat_max)
        mslp_masked = np.where(mask, mslp, np.nan)
    else:
        mslp_masked = mslp.copy()
    # Replace masked nans with large value for argmin
    min_val = np.nanmin(mslp_masked)
    idx = np.unravel_index(np.nanargmin(mslp_masked), mslp_masked.shape)
    low_lon = lons[idx]
    low_lat = lats[idx]
    return low_lon, low_lat, min_val, idx


def find_gradient_ridge(grad_mag, lons, lats, domain):
    """Find the top-N gradient pixels within a domain — the frontal zone."""
    lon_min, lon_max, lat_min, lat_max = domain
    mask = (lons >= lon_min) & (lons <= lon_max) & (lats >= lat_min) & (lats <= lat_max)
    grad_in_domain = np.where(mask, grad_mag, 0.0)
    # Get top 200 strongest gradient points
    flat_indices = np.argsort(grad_in_domain.ravel())[-200:]
    rows, cols = np.unravel_index(flat_indices, grad_mag.shape)
    pts = [(lons[r, c], lats[r, c], grad_mag[r, c]) for r, c in zip(rows, cols)]
    return pts


def analyze_timestep(ts):
    """Full analysis for one timestep."""
    dt = ts["datetime"]
    print(f"\n{'='*60}")
    print(f"Timestep: {dt}  |  Storm: {ts['storm']}  |  Front: {ts['front_type'].upper()}")
    print(f"{'='*60}")

    mslp_file = MSLP_DIR / f"{dt}.tif"
    u_file = WIND_U_DIR / f"{dt}.tif"
    v_file = WIND_V_DIR / f"{dt}.tif"

    for f in [mslp_file, u_file, v_file]:
        if not f.exists():
            print(f"  ERROR: Missing file {f}")
            return None

    mslp, transform, crs, lons, lats = read_cog(mslp_file)
    u, _, _, _, _ = read_cog(u_file)
    v, _, _, _, _ = read_cog(v_file)

    print(f"  Grid size: {mslp.shape[0]}x{mslp.shape[1]}")
    print(f"  Lon range: {lons.min():.2f} to {lons.max():.2f}")
    print(f"  Lat range: {lats.min():.2f} to {lats.max():.2f}")
    print(f"  MSLP range: {mslp.min():.1f} to {mslp.max():.1f} hPa")

    # Pressure gradient
    grad_mag, grad_lat, grad_lon = compute_gradient_magnitude(mslp, lons, lats)
    print(f"  Gradient magnitude max: {grad_mag.max():.3f} hPa/deg")

    # Wind direction
    wdir = compute_wind_direction(u, v)
    wind_speed = np.sqrt(u**2 + v**2)
    print(f"  Wind speed max: {wind_speed.max():.1f} m/s")

    # --- Find the low center in Atlantic/Iberia region ---
    # Storm lows are typically W of Iberia in the Atlantic
    low_lon, low_lat, low_mslp, low_idx = find_low_center(
        mslp, lons, lats, domain=(-40, 0, 35, 65)
    )
    print(f"  Low center: lon={low_lon:.2f}, lat={low_lat:.2f}, MSLP={low_mslp:.1f} hPa")

    # --- Find strongest gradient zone (frontal zone) ---
    # Cold fronts: search SW of the low center
    # Warm fronts: search E/NE of the low center
    if ts["front_type"] == "cold":
        # Cold front trails SW from low
        front_domain = (
            low_lon - 20,  # W
            low_lon + 5,   # E (close to low)
            low_lat - 25,  # S (cold air pushes south)
            low_lat + 5,   # N
        )
    else:
        # Warm front extends E/NE from low
        front_domain = (
            low_lon - 5,   # W (close to low)
            low_lon + 25,  # E
            low_lat - 5,   # S
            low_lat + 20,  # N
        )

    # Clamp to data bounds
    front_domain = (
        max(front_domain[0], lons.min()),
        min(front_domain[1], lons.max()),
        max(front_domain[2], lats.min()),
        min(front_domain[3], lats.max()),
    )

    print(f"  Front search domain (lon): {front_domain[0]:.1f} to {front_domain[1]:.1f}")
    print(f"  Front search domain (lat): {front_domain[2]:.1f} to {front_domain[3]:.1f}")

    top_pts = find_gradient_ridge(grad_mag, lons, lats, front_domain)

    if not top_pts:
        print("  WARNING: No gradient points found in domain")
        return None

    # Sort by gradient magnitude desc
    top_pts.sort(key=lambda x: x[2], reverse=True)
    print(f"  Top gradient points (lon, lat, grad):")
    for lon, lat, g in top_pts[:5]:
        print(f"    lon={lon:.2f}, lat={lat:.2f}, grad={g:.4f} hPa/deg")

    # --- Wind shift analysis at frontal zone ---
    # Sample wind direction in the top-gradient zone
    top10 = top_pts[:10]
    if top10:
        print(f"  Wind direction at top gradient points:")
        for lon, lat, g in top10[:5]:
            # Find nearest grid cell
            dist = np.sqrt((lons - lon)**2 + (lats - lat)**2)
            row, col = np.unravel_index(np.argmin(dist), dist.shape)
            wd = wdir[row, col]
            ws = wind_speed[row, col]
            print(f"    lon={lon:.2f}, lat={lat:.2f}, wdir={wd:.0f}°, wspd={ws:.1f} m/s")

    return {
        "datetime": dt,
        "storm": ts["storm"],
        "front_type": ts["front_type"],
        "low_lon": float(low_lon),
        "low_lat": float(low_lat),
        "low_mslp": float(low_mslp),
        "top_gradient_pts": [(float(lon), float(lat), float(g)) for lon, lat, g in top_pts[:50]],
        "lons": lons,
        "lats": lats,
        "mslp": mslp,
        "grad_mag": grad_mag,
        "wdir": wdir,
        "wind_speed": wind_speed,
    }


def compute_frontal_line(result, n_points=7):
    """
    From the gradient analysis, construct a smooth frontal line.

    Strategy:
    1. Take the top gradient points within the frontal search domain
    2. Sort them by latitude to get a N→S or S→N ordering
    3. Bin by latitude bands and take the median longitude in each band
    4. Return 5-8 representative vertices
    """
    pts = result["top_gradient_pts"]
    front_type = result["front_type"]

    if not pts:
        return []

    # Use top 50 points already extracted
    lons_pts = np.array([p[0] for p in pts])
    lats_pts = np.array([p[1] for p in pts])

    # Determine lat range
    lat_min = lats_pts.min()
    lat_max = lats_pts.max()

    if lat_max - lat_min < 1.0:
        # Degenerate — just return the centroid
        return [(float(np.median(lons_pts)), float(np.median(lats_pts)))]

    # Bin into n_points latitude bands
    lat_bins = np.linspace(lat_min, lat_max, n_points + 1)
    vertices = []
    for i in range(n_points):
        bin_lo = lat_bins[i]
        bin_hi = lat_bins[i + 1]
        in_bin = (lats_pts >= bin_lo) & (lats_pts < bin_hi)
        if in_bin.sum() == 0:
            continue
        lon_med = float(np.median(lons_pts[in_bin]))
        lat_med = float((bin_lo + bin_hi) / 2)
        vertices.append((lon_med, lat_med))

    # For cold fronts: sort S→N (lat ascending), warm fronts: N→S
    if front_type == "cold":
        vertices.sort(key=lambda v: v[1])  # S to N
    else:
        vertices.sort(key=lambda v: v[1], reverse=True)  # N to S

    return vertices


def main():
    print("Frontal Position Analysis — cheias.pt")
    print(f"MSLP dir: {MSLP_DIR}")
    print(f"Wind dirs: {WIND_U_DIR}, {WIND_V_DIR}")

    results = []
    for ts in TIMESTEPS:
        result = analyze_timestep(ts)
        if result:
            results.append(result)

    print("\n\n" + "="*60)
    print("SUMMARY: Frontal Line Vertices")
    print("="*60)

    for r in results:
        vertices = compute_frontal_line(r)
        print(f"\n{r['datetime']} | {r['storm']} | {r['front_type'].upper()}")
        print(f"  Low center: ({r['low_lon']:.2f}, {r['low_lat']:.2f}) at {r['low_mslp']:.1f} hPa")
        print(f"  Frontal line vertices ({len(vertices)} pts):")
        for lon, lat in vertices:
            print(f"    [{lon:.3f}, {lat:.3f}]")

    return results


if __name__ == "__main__":
    main()
