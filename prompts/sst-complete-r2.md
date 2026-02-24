
# PROMPT: Complete SST Anomaly Collection + R2 Mirror

## Context

cheias.pt is a flood scrollytelling platform. Chapter 2 ("The Atlantic Engine") needs
Sea Surface Temperature anomaly rasters showing the persistently warm Atlantic that
fueled moisture loading before the January-February 2026 Portugal floods.

## Current State

- **62 daily SST anomaly TIFs** exist in `data/temporal/sst/daily/sst_anom_YYYYMMDD.tif`
- Date range: 2025-12-01 to 2026-01-31 (missing Feb 1-15)
- Source: NOAA OISST v2.1 via `scripts/fetch_sst.py`
- **CRITICAL BUG:** TIFs contain raw integer encoding (hundredths of °C). Values range -696 to 905 instead of -6.96 to 9.05 °C. The NetCDF source (`data/temporal/sst/sst_anomaly.nc`) confirms valid range is -8.68 to +9.35 °C.
- Extent: North Atlantic box (-60°W to 5°E, 20°N to 60°N), 0.25° resolution (260×160 pixels)
- EPSG:4326, Float32, NoData=-999
- **No SST COGs on R2 yet** — only soil-moisture, precipitation, precondition, and 1 IVT COG exist

## Infrastructure

- **R2 bucket:** `cheias-cog` via rclone remote `r2:`
  - Path pattern: `r2:cheias-cog/cog/sst/{date}.tif`
  - Public URL: `https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/sst/{date}.tif`
- **Titiler:** `https://titiler.cheias.pt`
  - Tile URL: `https://titiler.cheias.pt/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png?url=https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/sst/2026-01-31.tif&colormap_name=rdbu_r&rescale=-5,5`
- **rclone** is configured and working (`rclone lsd r2:cheias-cog/cog/` works)
- **Project root:** `/home/nls/Documents/dev/cheias-pt`
- **Python venv:** `.venv/bin/python3` has xarray, rioxarray, rasterio, numpy, requests

## Tasks

### Task 1: Fix existing 62 TIFs (rescale ÷100)

For each TIF in `data/temporal/sst/daily/`:
1. Read with rasterio
2. Divide all non-NoData values by 100.0
3. Write back as Cloud-Optimized GeoTIFF (COG) with proper metadata
4. Preserve NoData=-999 (but note: -999/100 = -9.99, so mask BEFORE dividing)

**Algorithm:**
```python
data = src.read(1)
mask = data == -999  # or check against nodata
data = np.where(mask, -999.0, data / 100.0)
# Write as COG with Float32
```

Verify after fix: values should range roughly -9 to +10 °C.

### Task 2: Fetch missing Feb 1-15 SST

Use the same NOAA OISST source as `scripts/fetch_sst.py`:
- URL pattern: `https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/{YYYYMM}/oisst-avhrr-v02r01.{YYYYMMDD}.nc`
- Download for dates: 2026-02-01 through 2026-02-15
- Extract `anom` variable, clip to bbox (-60, 20, 5, 60)
- **Apply ÷100 correction immediately** (NOAA stores as hundredths)
- Save as COG to `data/temporal/sst/daily/sst_anom_YYYYMMDD.tif`

**IMPORTANT:** Check if NOAA OISST data for February 2026 is available yet. If the latest available date is before Feb 15, fetch whatever is available and report the actual end date.

### Task 3: Convert all to properly named COGs

Create final COGs in `data/cog/sst/` with naming convention matching other variables:
- Input: `data/temporal/sst/daily/sst_anom_YYYYMMDD.tif` (now corrected)
- Output: `data/cog/sst/YYYY-MM-DD.tif` (e.g., `2025-12-01.tif`)
- Format: Cloud-Optimized GeoTIFF, Float32, LZW compression, tiled 256×256
- EPSG:4326

```python
# COG creation profile
profile.update(
    driver='GTiff',
    dtype='float32',
    compress='lzw',
    tiled=True,
    blockxsize=256,
    blockysize=256,
)
# Add COG overviews
with rasterio.open(path, 'r+') as ds:
    ds.build_overviews([2, 4, 8], Resampling.average)
    ds.update_tags(ns='rio_overview', resampling='average')
```

### Task 4: Upload all COGs to R2

```bash
rclone sync data/cog/sst/ r2:cheias-cog/cog/sst/ --progress
```

### Task 5: Verify via titiler

Test at least 3 dates:
```bash
curl -s "https://titiler.cheias.pt/cog/info?url=https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/sst/2025-12-01.tif" | python3 -m json.tool | head -20
curl -s "https://titiler.cheias.pt/cog/info?url=https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/sst/2026-01-31.tif" | python3 -m json.tool | head -20
curl -s "https://titiler.cheias.pt/cog/info?url=https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/sst/2026-02-10.tif" | python3 -m json.tool | head -20
```

Values in `statistics` should show min/max in the range of roughly -10 to +10.

## Expected Outputs

- `data/cog/sst/` — 77 COGs (or up to 77, depending on NOAA Feb availability)
- Named: `YYYY-MM-DD.tif` (e.g., `2025-12-01.tif` through `2026-02-15.tif`)
- All on R2 at `cog/sst/` path
- All verifiable via titiler with `colormap_name=rdbu_r&rescale=-5,5`
- Print summary: total files, date range, value range stats

## Do NOT

- Select narrative keyframes (we'll do that in QGIS)
- Create PNGs or frontend JSON
- Modify the NetCDF source file
- Touch any other COG directories (soil-moisture, precipitation, precondition, ivt)
