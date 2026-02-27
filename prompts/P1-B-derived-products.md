# P1.B — Derived Analytical Products (Agent Team Prompt)

## Mission

Transform raw COGs into scientific products that demonstrate analytical depth. Each task
reads from existing data and writes to its own output directory — fully parallelizable.

**Read first:** `CLAUDE.md`, `prompts/sprint-backlog.md` (tasks P1.B1-B5),
`prompts/scroll-timeline-symbology.md` §2-3 (what the products are for).

## Setup

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

## Prompt

```
We need to compute derived analytical products for cheias.pt from the raw COGs.
Five independent compute tasks, each reading existing data and writing to its own
output directory.

Read CLAUDE.md first. Use the project .venv for all Python work.
Use Sonnet for the teammates, keep the lead on default.

Spawn 5 teammates:

- One to extract automated storm track LineStrings from MSLP minima (P1.B1).
  Create scripts/extract_storm_tracks.py.
  For each hourly timestep in data/cog/mslp/, find the grid cell with minimum
  MSLP within the Atlantic+Iberia domain (60W-5E, 30N-60N). Track the minimum
  across timesteps — when pressure < 990 hPa, it's a named storm. Group into
  continuous tracks (gap > 12 hours = new storm). Smooth with Savitzky-Golay
  filter (scipy.signal.savgol_filter, window=11, polyorder=3) to remove jitter.
  Output: data/qgis/storm-tracks-auto.geojson — FeatureCollection with 3
  LineString features (Kristin, Leonardo, Marta). Each vertex has properties:
  datetime, min_pressure_hpa. Feature properties: name, min_pressure_hpa (overall),
  start_datetime, end_datetime, duration_hours.
  There may be an existing hand-drawn data/qgis/storm-tracks.geojson — compare
  if it exists. Write method notes to data/qgis/storm-tracks-auto.md.
  Verify: 3 features, Kristin min ~960 hPa, Leonardo min ~975 hPa.

- One to extract flood depth COGs from CEMS raw data (P1.B2).
  Create scripts/extract_flood_depth.py.
  Read the CEMS monitoring TIFs — search in data/flood-extent/ for files matching
  *floodDepth*.tif or *flood_depth*.tif (explore the directory structure first,
  file paths in the sprint backlog may not be exact). There should be 2-3 monitoring
  products for Salvaterra (EMSR864 AOI03).
  Clip each to Salvaterra bbox: [-8.85, 38.85, -8.55, 39.15].
  Convert to Cloud-Optimized GeoTIFF: LZW compression, tiled, with overviews.
  Write manifest.json with per-file stats (min/max depth, nodata %, CRS, bbox)
  and CEMS attribution text.
  Output: data/flood-depth/ (new directory).
  Verify: COGs are valid, max depth ~7-10m range.

- One to compute running 7-day precipitation accumulation (P1.B4).
  Create scripts/compute_precip_accumulation.py.
  Read daily precip COGs from data/cog/precipitation/ (78 files, Dec 1 - Feb 15).
  For each day from day 7 onward, sum the preceding 7 days (trailing window).
  Output 71 COGs to data/cog/precipitation-7day/YYYY-MM-DD.tif.
  Also compute a single total-period accumulation COG: sum of ALL 78 daily files.
  Output to data/cog/precipitation-total.tif.
  All outputs as Cloud-Optimized GeoTIFF (LZW, tiled, overviews).
  Verify: 71 files in precipitation-7day/, the 7-day sum for Feb 7 should show
  high values over western Iberia (~150+ mm).

- One to re-render precipitation PNGs with blues colormap (P1.B5).
  The scroll timeline specifies blues with gaussian blur and intensity-proportional
  alpha for Ch.3 precipitation overlay. Current PNGs may use a different colormap.
  Create or modify scripts/rerender_precip_pngs.py.
  Read the 78 daily precip COGs from data/cog/precipitation/.
  Apply: scipy.ndimage.gaussian_filter(data, sigma=3) BEFORE colormapping.
  Colormap: sequential blues — #e8f4f8 (trace) → #b3d9e8 (light) → #6baed6
  (moderate) → #3182bd (heavy) → #08519c (extreme). Use matplotlib
  LinearSegmentedColormap.from_list or manual lookup table.
  Alpha proportional to intensity: alpha = np.clip(80 + 175 * normalized, 0, 255)
  where normalized is 0-1 scaled precipitation.
  Output: data/raster-frames/precipitation/*.png (overwrite existing).
  Preserve the same spatial extent and resolution as existing PNGs.
  Verify: open a frame — blue channel should dominate over red channel.

- One to draw frontal boundary GeoJSONs (P1.B3).
  Create scripts/analyze_frontal_positions.py — a diagnostic that loads MSLP +
  wind COGs at 4 key timesteps and computes pressure gradient magnitude to help
  place fronts. Print the gradient analysis and suggested front positions.
  Then create data/qgis/frontal-boundaries.geojson with 4 LineString features:

  | front_type | storm    | datetime        | description                    |
  |------------|----------|-----------------|--------------------------------|
  | cold       | Kristin  | 2026-01-28T00Z  | Trailing cold front            |
  | cold       | Kristin  | 2026-01-28T12Z  | Cold front passed              |
  | warm       | Leonardo | 2026-02-05T12Z  | Warm front ahead of low        |
  | cold       | Marta    | 2026-02-10T06Z  | Trailing cold front            |

  Properties per feature: front_type, storm, datetime, label (Portuguese),
  label_en (English).
  The frontal positions should be meteorologically reasonable — cold fronts trail
  SW from the low center, warm fronts extend E/NE. Use the MSLP gradient analysis
  to place them, not guesswork.
  Verify: 4 features, all LineStrings, all within Atlantic/Iberia domain.

Each teammate owns its own output:
  - Storm tracks agent: data/qgis/storm-tracks-auto.* + scripts/extract_storm_tracks.py
  - Flood depth agent: data/flood-depth/ + scripts/extract_flood_depth.py
  - Precip accumulation agent: data/cog/precipitation-7day/ + data/cog/precipitation-total.tif + scripts/compute_precip_accumulation.py
  - Precip PNG agent: data/raster-frames/precipitation/ + scripts/rerender_precip_pngs.py
  - Frontal boundaries agent: data/qgis/frontal-boundaries.* + scripts/analyze_frontal_positions.py

No file conflicts. Share progress with the lead as each task completes.
The lead should produce a summary: outputs per task, verification results,
any issues found.
```

## Expected Duration

All compute-bound on local data — no network queues:

| Task | Work | ~Time |
|------|------|-------|
| B1 Storm tracks | Read ~1100 MSLP COGs, track minima | 15-25 min |
| B2 Flood depth | Read 2-3 TIFs, clip, convert | 5-10 min |
| B3 Frontal boundaries | Read 4 timesteps, gradient analysis | 10-15 min |
| B4 Precip accumulation | Read 78 COGs, rolling sum | 10-15 min |
| B5 Precip PNG re-render | Read 78 COGs, blur + colormap | 10-15 min |

Wall-clock: ~25 min parallel. These are lightweight Sonnet tasks.

## Definition of Done

- [ ] `data/qgis/storm-tracks-auto.geojson` — 3 LineStrings, Kristin min ~960 hPa
- [ ] `data/flood-depth/*.tif` — valid COGs with manifest.json
- [ ] `data/qgis/frontal-boundaries.geojson` — 4 LineStrings
- [ ] `data/cog/precipitation-7day/*.tif` — 71 files
- [ ] `data/cog/precipitation-total.tif` — single full-period accumulation
- [ ] `data/raster-frames/precipitation/*.png` — blue-dominant, blurred
- [ ] All scripts clean portfolio code
- [ ] Commits on v2/phase-1 branch
