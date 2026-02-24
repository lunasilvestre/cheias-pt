# Sprint 04 — Cloud-Optimized Raster Pipeline

## What This Is

cheias.pt scrollytelling needs smooth, weather-map-quality surfaces for soil moisture (Ch3) and precipitation (Ch4). The current approach sends ~256 GeoJSON points to MapLibre's heatmap layer, producing a visible grid pattern. We're replacing this with a proper raster pipeline:

**Open-Meteo API → COGs (canonical) → pre-rendered PNGs (scrollytelling) → manifest JSON**

The COGs also serve as the data source for a titiler instance (deployed separately) that will power the interactive explore chapter (Ch11) with dynamic tile rendering and a date slider.

## What To Build

A single pipeline script: `scripts/generate-cog-frames.py`

Two variables, 77 days each (2025-12-01 → 2026-02-15), two output formats:

| Output | Format | Purpose | Location |
|--------|--------|---------|----------|
| COGs | GeoTIFF, float32, deflate, EPSG:4326 | Canonical data, titiler source | `data/cog/{variable}/{date}.tif` |
| PNGs | RGBA, transparent background | Scrollytelling image overlays | `data/raster-frames/{variable}/{date}.png` |
| Manifest | JSON | Frontend frame index | `data/frontend/raster-manifest.json` |

## Phase 0: Resolution Test

Before fetching 1500+ points, **verify Open-Meteo actually provides 0.1° resolution**.

Test: fetch `soil_moisture_0_to_7cm` for 2026-01-15 at four adjacent 0.1° grid points around Lisbon (e.g., lat 38.7/38.8, lon -9.2/-9.1). If all four return distinct values, Open-Meteo is serving true 0.1° data. If pairs are identical, it's interpolating from a coarser grid — in that case, fall back to 0.25° fetch with heavier interpolation.

Print results and the resolution decision before proceeding.

## Phase 1: Data Fetching

### Grid Generation

```
Bounding box: lat 36.9→42.2, lon -9.6→-6.1
Spacing: 0.1° (if resolution test passes) or 0.25° (fallback)
```

1. Generate regular grid over bounding box
2. Load clipping polygon: dissolve `assets/districts.geojson` into a single continental Portugal polygon
3. Filter: keep only grid points inside the polygon (+ 0.15° buffer to avoid edge artifacts after interpolation)
4. Print: "Grid: {N} points at {spacing}° inside Portugal"

### Fetching

**Soil moisture:**
- API: `https://archive-api.open-meteo.com/v1/archive`
- Params: `hourly=soil_moisture_0_to_7cm`, `start_date=2025-12-01`, `end_date=2026-02-15`
- Aggregate hourly → daily mean
- Each API call returns the full 77-day timeseries for one point

**Precipitation:**
- Same API, params: `daily=precipitation_sum`
- Already daily, no aggregation needed

**Strategy:**
- Cache each point's raw JSON response to `data/cache/soil-moisture-01/{lat}_{lon}.json` and `data/cache/precipitation-01/{lat}_{lon}.json`
- Before each fetch, check if cache file exists — skip if so (resume-safe)
- Rate limit: `time.sleep(0.25)` between requests
- Progress: print every 100 points ("Fetched 300/1487 soil moisture points...")
- Both variables can be fetched in the same API call (combine params) — do this to halve the number of requests

**IMPORTANT:** If the cache directories already contain files, count them and report: "Found {N} cached points, fetching {M} remaining"

## Phase 2: COG Generation

For each variable, for each day:

1. Extract that day's values from all cached point responses → (lat, lon, value) arrays
2. Create fine target grid at 0.02° spacing over the bounding box
3. Interpolate using `scipy.interpolate.griddata(method='cubic')`, fallback to `'linear'` if cubic produces NaN artifacts
4. Mask: set pixels outside the Portugal polygon to NaN
5. Write as COG using rasterio:
   - dtype: float32
   - CRS: EPSG:4326
   - nodata: NaN
   - transform: computed from the fine grid bounds and resolution
   - compress: deflate
   - tiled: True (256×256 internal tiles — this is what makes it a COG)
   - Overview levels: [2, 4] (small files, just two levels is fine)

Output: `data/cog/soil-moisture/2025-12-01.tif`, etc.

### Data Notes

- **Soil moisture** raw values for `soil_moisture_0_to_7cm` should range roughly 0.05 → 0.50 m³/m³. Store raw values in the COG — color mapping happens at render time.
- **Precipitation** values in mm/day, range 0 → ~100+. Store raw values.

## Phase 3: PNG Rendering

For each COG, render a color-mapped transparent PNG for the scrollytelling:

### Soil Moisture Color Ramp

Narrative: brown (dry, December) → deep teal (saturated, late January)

Normalize across ALL frames: find global min/max of soil moisture values, then map to 0→1.

```python
from matplotlib.colors import LinearSegmentedColormap

sm_cmap = LinearSegmentedColormap.from_list('soil_moisture', [
    (0.0, '#8B6914'),   # dry brown/amber
    (0.25, '#B8860B'),  # dark goldenrod  
    (0.45, '#7A9A6E'),  # olive transition
    (0.6, '#4A90A4'),   # steel blue
    (0.8, '#2E86AB'),   # ocean blue
    (1.0, '#1B4965'),   # deep teal
])
```

Alpha: 0.80 for all data pixels. Transparent (alpha=0) outside Portugal.

### Precipitation Color Ramp

Narrative: invisible on dry days, yellow→red pulses on storm days

```python
from matplotlib.colors import BoundaryNorm

precip_bounds = [0, 1, 5, 15, 30, 50, 80, 150]
precip_colors = [
    '#00000000',  # 0-1: transparent (no rain)
    '#FFF9C4',    # 1-5: pale yellow
    '#FFD54F',    # 5-15: amber  
    '#FF8F00',    # 15-30: dark orange
    '#E53935',    # 30-50: red
    '#B71C1C',    # 50-80: dark red
    '#4A0000',    # 80+: near black red
]
```

Alpha: scale with value. Below 1 mm → fully transparent. 1-5 mm → alpha 0.4. Above 5 mm → alpha 0.8. Above 30 mm → alpha 0.9.

### PNG Specs

- RGBA, Pillow or matplotlib output
- Resolution: match the COG grid (should be ~800-1200 pixels wide, depending on interpolation grid)
- Transparent background (alpha=0) for ocean, Spain, and sub-threshold precipitation
- NO axes, borders, labels, or whitespace — pure data image with exact geographic bounds

## Phase 4: Manifest

Generate `data/frontend/raster-manifest.json`:

```json
{
  "soil_moisture": {
    "bounds": [-9.6, 36.9, -6.1, 42.2],
    "frames": [
      {"date": "2025-12-01", "url": "raster-frames/soil-moisture/2025-12-01.png"},
      {"date": "2025-12-02", "url": "raster-frames/soil-moisture/2025-12-02.png"}
    ]
  },
  "precipitation": {
    "bounds": [-9.6, 36.9, -6.1, 42.2],
    "frames": [
      {"date": "2025-12-01", "url": "raster-frames/precipitation/2025-12-01.png"},
      {"date": "2025-12-02", "url": "raster-frames/precipitation/2025-12-02.png"}
    ]
  },
  "cog": {
    "soil_moisture_dir": "cog/soil-moisture/",
    "precipitation_dir": "cog/precipitation/",
    "crs": "EPSG:4326",
    "note": "COGs for titiler dynamic rendering"
  }
}
```

The `bounds` array uses MapLibre's image source convention: `[west, south, east, north]`.

## Phase 5: Visual QA

Generate validation figures saved to `notebooks/figures/`:

### 1. `soil-moisture-filmstrip.png`

8 subplots in 2×4 grid, showing these dates:
- Dec 1, Dec 15, Jan 1, Jan 15, Jan 28, Feb 1, Feb 7, Feb 15

Each subplot: the rendered PNG composited over a light gray Portugal outline. Title = date. Should show clear brown→teal progression.

### 2. `precipitation-filmstrip.png`

8 subplots showing storm days:
- Jan 28, Jan 29 (Kristin), Jan 30, Feb 5 (Leonardo), Feb 6, Feb 7, Feb 10 (Marta), Feb 11

Should show three distinct red/orange pulses, with quieter days nearly transparent.

### 3. Summary statistics

Print to stdout:
- Total COG files generated, total size
- Total PNG files generated, total size  
- Soil moisture value range (global min/max)
- Precipitation value range (global min/max)
- Largest/smallest PNG file sizes

## Execution Environment

```bash
cd /home/nls/Documents/dev/cheias-pt
source .venv/bin/activate
python scripts/generate-cog-frames.py
```

### Available in venv:
scipy, rasterio, rioxarray, matplotlib, pillow, shapely, geopandas, numpy, pandas, xarray, requests

### If anything is missing:
```bash
pip install <package> --break-system-packages  # won't be needed, venv has everything
```

## Timing Budget

- Resolution test: 10 seconds
- Fetching (~750 combined API calls with rate limiting): ~4 minutes
- COG generation (154 files): ~3 minutes  
- PNG rendering (154 files): ~2 minutes
- QA figures: 30 seconds
- **Total: ~10 minutes**

## Success Criteria

1. `data/cog/soil-moisture/` contains 77 COGs, each valid GeoTIFF with internal tiling + overviews
2. `data/cog/precipitation/` contains 77 COGs, same quality
3. `data/raster-frames/soil-moisture/` contains 77 PNGs with NO visible grid pattern
4. `data/raster-frames/precipitation/` contains 77 PNGs with transparent dry days
5. PNGs have clean Portugal boundary — no bleed into Atlantic or Spain
6. `soil-moisture-filmstrip.png` shows clear brown→teal temporal progression
7. `precipitation-filmstrip.png` shows three distinct storm pulses on correct dates
8. `raster-manifest.json` is valid and complete
9. Each PNG < 300KB, total raster output < 50MB
10. COGs are valid cloud-optimized GeoTIFFs (tiled, overviews, deflate compression)

## What NOT To Do

- Do NOT modify any frontend code (layer-manager.js, chapter-wiring.js, etc.)
- Do NOT deploy anything to the server
- Do NOT delete existing data in `data/frontend/` (the old JSON files are still used by the current frontend)
- Do NOT use notebook format — this is `scripts/`, not `notebooks/`
- Do NOT fetch data that's already cached
