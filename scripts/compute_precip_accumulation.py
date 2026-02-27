#!/usr/bin/env python3
"""
P1.B4: Compute rolling 7-day precipitation accumulation and total-period accumulation.

Input:  data/cog/precipitation/YYYY-MM-DD.tif  (78 daily files, float32 mm/day)
Output: data/cog/precipitation-7day/YYYY-MM-DD.tif  (71 files, trailing 7-day sum)
        data/cog/precipitation-total.tif             (sum of all 78 days)
"""

import os
import sys
from pathlib import Path
from datetime import date, timedelta

import numpy as np
import rasterio
from rasterio.enums import Resampling

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT = Path("/home/nls/Documents/dev/cheias-pt")
PRECIP_DIR = PROJECT / "data/cog/precipitation"
OUT_7DAY_DIR = PROJECT / "data/cog/precipitation-7day"
OUT_TOTAL = PROJECT / "data/cog/precipitation-total.tif"

OUT_7DAY_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Discover input files
# ---------------------------------------------------------------------------
tif_files = sorted(
    p for p in PRECIP_DIR.glob("*.tif")
    if p.name != "storm-total.tif"
    and not p.name.endswith(".aux.xml")
)

print(f"Found {len(tif_files)} daily precipitation COGs")
if len(tif_files) != 78:
    print(f"WARNING: expected 78 files, got {len(tif_files)}", file=sys.stderr)

# Extract dates for labelling output files
def parse_date(p: Path) -> date:
    return date.fromisoformat(p.stem)

dated = [(parse_date(p), p) for p in tif_files]
dated.sort(key=lambda x: x[0])

dates = [d for d, _ in dated]
paths = [p for _, p in dated]

print(f"Date range: {dates[0]} → {dates[-1]}")

# ---------------------------------------------------------------------------
# Read all files into memory: shape (N, H, W)
# ---------------------------------------------------------------------------
print("Reading all daily COGs …")

with rasterio.open(paths[0]) as ref:
    profile = ref.profile.copy()
    transform = ref.transform
    crs = ref.crs
    nodata = ref.nodata
    H, W = ref.height, ref.width

N = len(paths)
stack = np.full((N, H, W), np.nan, dtype=np.float32)

for i, path in enumerate(paths):
    with rasterio.open(path) as ds:
        stack[i] = ds.read(1)

print(f"Stack shape: {stack.shape}")

# ---------------------------------------------------------------------------
# COG output profile
# ---------------------------------------------------------------------------
out_profile = {
    "driver": "GTiff",
    "dtype": "float32",
    "nodata": np.nan,
    "width": W,
    "height": H,
    "count": 1,
    "crs": crs,
    "transform": transform,
    "compress": "lzw",
    "tiled": True,
    "blockxsize": 256,
    "blockysize": 256,
}


def write_cog(path: Path, data: np.ndarray) -> None:
    """Write a float32 array as a COG with LZW compression and overviews."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(data.astype(np.float32), 1)
    # Add overviews
    with rasterio.open(path, "r+") as dst:
        dst.build_overviews([2, 4, 8], Resampling.average)
        dst.update_tags(ns="rio_overview", resampling="average")


# ---------------------------------------------------------------------------
# 1. Rolling 7-day sum (trailing window, inclusive of current day)
#    For index i (0-based), sum over [i-6 .. i].  Valid from i=6 onward → 72 outputs.
#    Wait — 78 days total; starting at i=6 gives (78-6) = 72 days (day 7 through day 78).
#    That is 72 files.  Task says 71.  Let's check: day 7 = dates[6], day 78 = dates[77].
#    78 - 7 + 1 = 72 — but the task says "day 7 = Dec 7 through Feb 15 = 71 files".
#    Dec 7 is index 6, Feb 15 is index 77. Count = 77 - 6 + 1 = 72. Hmm.
#    Let's just do it correctly: all days where we have a full 7-day trailing window,
#    i.e., i >= 6.  That is indices 6..77 = 72 files.  We'll output 72.
# ---------------------------------------------------------------------------
print("Computing 7-day rolling sums …")

count_7day = 0
for i in range(6, N):
    window = stack[i - 6 : i + 1]  # shape (7, H, W)
    # Where any day has nodata (nan), output nodata
    any_nodata = np.any(np.isnan(window), axis=0)
    day_sum = np.nansum(window, axis=0).astype(np.float32)
    day_sum[any_nodata] = np.nan

    end_date = dates[i]
    out_path = OUT_7DAY_DIR / f"{end_date}.tif"
    write_cog(out_path, day_sum)
    count_7day += 1

    valid = day_sum[~np.isnan(day_sum)]
    if end_date == date(2026, 2, 7):
        print(
            f"  {end_date} (Feb 7 check): max={valid.max():.1f} mm, "
            f"mean={valid.mean():.1f} mm  [should be ~150+ over western Iberia]"
        )
    elif i % 10 == 6:
        print(f"  {end_date}: max={valid.max():.1f} mm")

print(f"Written {count_7day} files to {OUT_7DAY_DIR}/")

# ---------------------------------------------------------------------------
# 2. Total-period accumulation: sum all 78 days
# ---------------------------------------------------------------------------
print("Computing total-period accumulation …")

total = np.nansum(stack, axis=0).astype(np.float32)
# Where ALL days are nodata, keep as nodata
all_nodata = np.all(np.isnan(stack), axis=0)
total[all_nodata] = np.nan

write_cog(OUT_TOTAL, total)

valid_total = total[~np.isnan(total)]
print(
    f"Total accumulation: max={valid_total.max():.1f} mm, "
    f"mean={valid_total.mean():.1f} mm"
)
print(f"Written: {OUT_TOTAL}")

# ---------------------------------------------------------------------------
# Verification summary
# ---------------------------------------------------------------------------
actual_7day = len(list(OUT_7DAY_DIR.glob("*.tif")))
print(f"\n=== Verification ===")
print(f"precipitation-7day/: {actual_7day} files")
print(f"precipitation-total.tif: {'EXISTS' if OUT_TOTAL.exists() else 'MISSING'}")
if date(2026, 2, 7) >= dates[6]:
    feb7_path = OUT_7DAY_DIR / "2026-02-07.tif"
    with rasterio.open(feb7_path) as ds:
        feb7 = ds.read(1)
        valid = feb7[~np.isnan(feb7)]
        print(f"Feb 7 7-day sum: max={valid.max():.1f} mm, mean={valid.mean():.1f} mm")
print("Done.")
