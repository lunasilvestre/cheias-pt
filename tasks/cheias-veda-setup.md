# VEDA-UI Setup & Migration Guide for cheias.pt

**Document Date:** 2026-03-06
**Status:** Ready for implementation
**Target Outcome:** Transform the scrollytelling pipeline into a production VEDA instance serving cheias.pt data

---

## Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Clone & Configure veda-config-template](#1-clone--configure-veda-config-template)
3. [Environment Setup](#2-environment-setup)
4. [Dataset Registration](#3-dataset-registration)
5. [Migration Plan: What to Keep vs Discard](#4-migration-plan-what-to-keep-vs-discard)
6. [Obsidian Vault References](#5-obsidian-vault-references)
7. [Deployment Checklist](#6-deployment-checklist)

---

## Overview & Architecture

### Why VEDA-UI?

The current cheias-pt implementation (`/home/nls/Documents/dev/cheias-pt`) is a **custom scrollytelling engine** with:

- Hand-coded scroll detection (scrollama + GSAP)
- Manual layer orchestration (deck.gl, WeatherLayers GL)
- Custom temporal player and map transitions
- Hard-coded chapter state management

**VEDA-UI** replaces all of this with:

- **Component library:** Pre-built Map, ScrollytellingBlock, Chart, Table, CompareImage blocks
- **MDX-based content:** Write stories in Markdown; components auto-render
- **Built-in responsive design:** Mobile, tablet, desktop all handled
- **Standard STAC integration:** Temporal metadata, analysis metrics, layer legends
- **Zero scroll logic:** Declarative chapter transitions

### Technology Stack

| Component | Solution |
|-----------|----------|
| **Frontend Framework** | React (Vite build) |
| **Map Library** | MapLibre GL JS |
| **Tile Server** | TiTiler (on Sliplane, `https://titiler.cheias.pt/`) |
| **Data Format** | Cloud-Optimized GeoTIFF (COG) for rasters, GeoJSON/PMTiles for vectors |
| **Content Format** | MDX (Markdown + JSX) |
| **Deployment** | Vercel (cheias.pt domain) |
| **Data Hosting** | Cloudflare R2 (COG storage) + TiTiler proxy |

### What Stays vs What Goes

**KEEP:**
- All COG raster assets (`data/cog/` — 1.6 GB)
- All flood extent vectors (`data/flood-extent/` — 1.8 GB, including PMTiles)
- All satellite imagery (`data/sentinel-2/` — 179 MB)
- All temporal timeseries (`data/temporal/` — 149 MB as parquet + GeoTIFF)
- All colormaps (12 QML styles will be translated to VEDA colormap JSON)
- All basemap design decisions and QA docs
- All research & chapter outlines (`tasks/`, `research/`)
- All data generation scripts (`scripts/`)

**DISCARD:**
- Custom scroll engine (`src/scroll-engine.ts`)
- Manual GSAP animations (`src/animations.ts`)
- WeatherLayers GL integration (`src/weather-layers.ts`)
- deck.gl overlay logic
- Custom temporal player UI (`src/temporal-player.ts`)
- Custom layer orchestration (`src/layer-manager.ts`)
- All HTML/CSS in `src/` and `css/` (VEDA provides styling)

---

## 1. Clone & Configure veda-config-template

### Step 1.1: Clone the Template

```bash
cd /tmp
git clone https://github.com/developmentseed/veda-config-template.git
cd veda-config-template
npm install
```

### Step 1.2: Directory Structure Overview

After cloning, you'll have:

```
veda-config-template/
├── app/
│   ├── components/          # VEDA React components (don't edit)
│   ├── content/
│   │   ├── datasets/        # <-- YOUR DATASET CONFIGS (YAML frontmatter)
│   │   │   └── *.mdx
│   │   └── stories/         # <-- YOUR SCROLLYTELLING STORIES (MDX)
│   │       └── *.mdx
│   ├── data/                # Static data (GeoJSON, CSV for charts)
│   ├── styles/              # Global CSS (rarely modified)
│   └── index.tsx            # App entry point
├── public/
│   └── images/              # Cover images, icons
├── vite.config.ts           # Build config (update for cheias.pt)
├── .env.example             # Environment variables template
├── package.json             # Dependencies
└── README.md                # Official documentation
```

### Step 1.3: Update Key Config Files

#### A. Update `vite.config.ts`

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: false,
  },
  build: {
    target: 'es2022',
    outDir: 'dist',
  },
  define: {
    __APP_VERSION__: JSON.stringify('1.0.0'),
  },
});
```

#### B. Update `package.json`

Ensure these fields:

```json
{
  "name": "cheias-veda",
  "version": "1.0.0",
  "homepage": "https://cheias.pt",
  "license": "CC-BY-4.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "deploy": "vercel --prod"
  }
}
```

#### C. Create `.env.local`

```bash
VITE_STAC_API_ENDPOINT=https://stac.cheias.pt  # (or use default if public STAC available)
VITE_TITILER_URL=https://titiler.cheias.pt
VITE_MAPBOX_TOKEN=your_free_tier_token_here    # (see Section 2)
VITE_ANALYTICS_ID=optional_tracking_id
```

### Step 1.4: Install Dependencies

```bash
npm install
```

Expected time: 2–3 minutes.

Verify build:

```bash
npm run build
```

---

## 2. Environment Setup

### Step 2.1: Mapbox Token (Free Tier)

VEDA uses Mapbox GL for basemaps. Free tier includes:

- **50,000 map loads/month** (cheias.pt typical usage: 5,000–10,000/month)
- **25 tilesets** (we'll use 1–2)
- **Raster sources** (our COGs don't require Mapbox; only basemap tiles do)

#### To Get a Token:

1. Go to [mapbox.com/account/tokens](https://mapbox.com/account/tokens)
2. Sign up (free)
3. Create a default public token
4. Copy and add to `.env.local`: `VITE_MAPBOX_TOKEN=pk_...`

**Alternative (Stamen/CARTO):** VEDA also supports free basemaps via CARTO. Set:

```bash
VITE_BASEMAP_STYLE=carto-positron  # or carto-voyager, carto-dark-matter
```

### Step 2.2: TiTiler Configuration

TiTiler is already running on **Sliplane** at `https://titiler.cheias.pt/`.

#### To Verify Connectivity:

```bash
curl https://titiler.cheias.pt/cog/info?url=s3://your-bucket/path/to/cog.tif
```

Expected response: JSON with COG metadata (bounds, resolution, bands, etc.).

#### Usage in Dataset Config:

```yaml
tileApiEndpoint: 'https://titiler.cheias.pt'

layers:
  - id: soil-moisture-daily
    stacCol: soil-moisture  # Optional; TiTiler doesn't require STAC
    tileApiEndpoint: 'https://titiler.cheias.pt'
    sourceParams:
      rescale: [0.05, 0.50]
      colormap_name: 'viridis'
      resampling: 'bilinear'
```

**Key TiTiler Endpoints:**

| Endpoint | Purpose |
|----------|---------|
| `/cog/info?url=...` | Get metadata for a COG |
| `/cog/tiles/{z}/{x}/{y}.png?url=...&colormap_name=X` | Serve PNG tiles |
| `/cog/tiles/{z}/{x}/{y}.webp?url=...` | Serve WebP tiles (faster) |
| `/cog/tiles/{z}/{x}/{y}.json?url=...` | Serve GeoJSON tiles (vector) |
| `/cog/statistics?url=...` | Get min/max/mean for a COG |

### Step 2.3: Vercel Deployment Configuration

#### A. Create `vercel.json` in repo root:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "env": {
    "VITE_MAPBOX_TOKEN": "@mapbox-token",
    "VITE_TITILER_URL": "https://titiler.cheias.pt"
  }
}
```

#### B. Add Secrets to Vercel Dashboard:

1. Log into [vercel.com](https://vercel.com)
2. Select project `cheias-veda`
3. Go to **Settings → Environment Variables**
4. Add:
   - `VITE_MAPBOX_TOKEN`: `pk_...`
   - `VITE_TITILER_URL`: `https://titiler.cheias.pt`

#### C. Domain Setup (Cloudflare → Vercel)

1. In Cloudflare DNS for `cheias.pt`:
   - Add CNAME record: `cheias.pt` → `cname.vercel.com`
   - OR: Go to Vercel → Settings → Domains → Add `cheias.pt`
2. Vercel auto-provisions SSL; takes 2–5 minutes

### Step 2.4: Environment Variables Summary

**Development (.env.local):**

```bash
VITE_MAPBOX_TOKEN=pk_your_public_token_here
VITE_TITILER_URL=https://titiler.cheias.pt
VITE_STAC_API_ENDPOINT=https://stac.example.com  # optional; falls back to public STAC
```

**Production (Vercel Secrets):**

Same as above, set via Vercel dashboard.

---

## 3. Dataset Registration

### Step 3.1: Understanding VEDA Dataset Format

Datasets in VEDA are **MDX files** with:

1. **YAML frontmatter:** Metadata (id, name, description, layers, taxonomy)
2. **MDX body:** Overview content (markdown + React components)

**File location:** `app/content/datasets/`

### Step 3.2: Dataset YAML Schema

```yaml
---
# REQUIRED
id: soil-moisture            # Unique slug (lowercase, dashes)
name: 'Soil Moisture'        # Display name
description: 'Daily soil water content from ERA5-Land reanalysis'

# Dataset card cover image
media:
  src: /images/datasets/soil-moisture-cover.jpg
  alt: 'Soil moisture visualization'
  author:
    name: 'Open-Meteo'
    url: 'https://open-meteo.com'

# Taxonomy (for filtering on homepage)
taxonomy:
  - name: 'Topics'
    values:
      - 'Hydrology'
      - 'Precipitation'
  - name: 'Temporal Resolution'
    values:
      - 'Daily'

# Featured on homepage?
featured: true

# Disable "Explore Data" section?
disableExplore: false

# Layers that belong to this dataset
layers:
  - id: soil-moisture-daily
    name: 'Soil Moisture (0–7cm layer)'
    description: 'Daily volumetric water content'
    type: raster

    # STAC Collection reference (optional)
    stacCol: soil-moisture-daily
    stacApiEndpoint: 'https://stac.cheias.pt/api/v1'

    # TiTiler configuration
    tileApiEndpoint: 'https://titiler.cheias.pt'

    # Temporal extent
    initialDatetime: '2025-12-01'

    # Map projection
    projection:
      id: 'mercator'

    # Map bounds
    bounds: [-9.6, 36.9, -6.1, 42.2]  # [minLon, minLat, maxLon, maxLat]
    zoomExtent: [4, 14]
    basemapId: 'dark'

    # TiTiler rendering parameters
    sourceParams:
      rescale: [0.05, 0.50]            # min/max values for colormap scaling
      colormap_name: 'viridis'          # rio-tiler colormap
      resampling: 'bilinear'            # Interpolation method
      bidx: 1                            # Band index (1-indexed)
      minzoom: 0
      maxzoom: 20

    # Visual legend
    legend:
      type: 'gradient'
      unit:
        label: 'Water Content (m³/m³)'
      min: 'Dry'
      max: 'Saturated'
      stops:
        - '#f5e6d3'  # Light brown (dry)
        - '#a6611a'  # Medium brown
        - '#7fb3d5'  # Light blue
        - '#1b4965'  # Dark blue (wet)
        - '#0a2840'  # Very dark blue (saturated)

    # Optional: comparison layer
    compare:
      datasetId: 'soil-moisture'
      layerId: 'soil-moisture-anomaly'
      mapLabel: |
        ::js ({ dateFns, datetime, compareDatetime }) => {
          return `${dateFns.format(datetime, 'dd MMM')} vs baseline`;
        }

    # Statistical analysis configuration
    analysis:
      metrics: ['min', 'max', 'mean', 'std']
      exclude: false
      sourceParams:
        resampling: 'bilinear'

    # Metadata display
    info:
      source: 'Open-Meteo / ERA5-Land'
      spatialExtent: 'Portugal'
      temporalResolution: 'Daily'
      unit: 'm³/m³'

# Additional metadata
usage:
  - url: 'https://notebooks.example.com/soil-moisture'
    label: 'Analysis notebook'
    title: 'Soil moisture time series analysis'

# Rich text block (markdown + links)
infoDescription: |
  ::markdown
    - **Source:** Open-Meteo ERA5-Land reanalysis
    - **Temporal Extent:** December 1, 2025 – February 15, 2026
    - **Spatial Resolution:** 0.25° (~28 km)
    - **Update Frequency:** Daily
    - **Licensing:** CC-BY-4.0
---

# MDX BODY (below frontmatter)
# Write markdown and JSX components here

<Block>
  <Prose>
    ## About This Dataset

    Soil moisture is a critical precursor to flooding. When soils are already saturated
    and rain is forecasted, flood risk skyrockets.

    This dataset shows volumetric water content (0–7 cm layer) from ERA5-Land,
    a global reanalysis with excellent accuracy over land.
  </Prose>
</Block>
```

### Step 3.3: STAC Entry Format (Optional)

If you want full STAC integration (temporal metadata, automatic date picking):

```json
{
  "type": "Feature",
  "stac_version": "1.0.0",
  "stac_extensions": ["rendering"],
  "id": "soil-moisture-daily-20260301",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[-9.6, 36.9], [-6.1, 36.9], [-6.1, 42.2], [-9.6, 42.2], [-9.6, 36.9]]]
  },
  "bbox": [-9.6, 36.9, -6.1, 42.2],
  "properties": {
    "datetime": "2026-03-01T00:00:00Z",
    "start_datetime": "2025-12-01T00:00:00Z",
    "end_datetime": "2026-03-01T00:00:00Z"
  },
  "links": [
    {
      "rel": "item",
      "href": "https://titiler.cheias.pt/cog/info?url=https://pub-xxx.r2.dev/cog/soil-moisture/2026-03-01.tif"
    }
  ],
  "assets": {
    "cog": {
      "href": "https://pub-xxx.r2.dev/cog/soil-moisture/2026-03-01.tif",
      "type": "image/tiff; application=geotiff",
      "roles": ["data"],
      "rendering": {
        "rescale": [[0.05, 0.50]],
        "colormap_name": "viridis"
      }
    }
  }
}
```

**Note:** STAC is optional. TiTiler works with direct COG URLs.

### Step 3.4: Example Dataset Configs for cheias.pt Data

#### Example 1: Flood Extent (Vector)

**File:** `app/content/datasets/flood-extent.mdx`

```yaml
---
id: flood-extent
name: 'Flood Extent (CEMS Rapid Mapping)'
description: 'Observed flood polygons from Copernicus Emergency Management Service (EMSR861 & EMSR864)'

media:
  src: /images/datasets/flood-extent-cover.jpg
  alt: 'Flooded areas in red'
  author:
    name: 'Copernicus EMS'
    url: 'https://rapid-mapping.emergency.copernicus.eu/'

taxonomy:
  - name: 'Topics'
    values:
      - 'Flood Risk'
      - 'Emergency Response'
  - name: 'Source'
    values:
      - 'Satellite'

featured: true
disableExplore: false

layers:
  - id: flood-extent-combined
    name: 'Combined EMSR861 & EMSR864'
    description: '15,253 mapped flood polygons (7,723 ha + 219,041 ha)'
    type: vector

    sourceParams:
      opacity: 0.55

    legend:
      type: categorical
      stops:
        - color: '#2471a3'
          label: 'Flooded Area'

    info:
      source: 'Copernicus Emergency Management Service'
      spatialExtent: '13 Portuguese AOIs'
      temporalResolution: 'Activation dates: Jan 28, Feb 3–10, 2026'
      unit: 'Binary (flooded/not flooded)'

infoDescription: |
  ::markdown
    - **Activation 1 (EMSR861):** Storm Kristin, Coimbra region
    - **Activation 2 (EMSR864):** Storms Leonardo & Marta, nationwide
    - **Data Format:** PMTiles (web-optimized) + GeoJSON (full detail)
---

<Block>
  <Prose>
    ## Rapid Flood Mapping

    Within hours of major flooding, Copernicus EMS deploys satellite imagery analysts
    to map the extent of affected areas. These maps guide emergency response.
  </Prose>
</Block>
```

#### Example 2: Precipitation (Raster COG)

**File:** `app/content/datasets/precipitation.mdx`

```yaml
---
id: precipitation
name: 'Precipitation'
description: 'Daily accumulated rainfall from ERA5 reanalysis'

media:
  src: /images/datasets/precipitation-cover.jpg
  alt: 'Rain clouds'
  author:
    name: 'ECMWF'
    url: 'https://www.ecmwf.int/'

taxonomy:
  - name: 'Topics'
    values:
      - 'Meteorology'
      - 'Hydrology'

featured: true

layers:
  - id: precipitation-daily
    name: 'Daily Precipitation'
    type: raster
    initialDatetime: newest

    tileApiEndpoint: 'https://titiler.cheias.pt'

    bounds: [-9.6, 36.9, -6.1, 42.2]
    zoomExtent: [4, 14]
    basemapId: 'dark'

    sourceParams:
      rescale: [0, 80]
      colormap_name: 'blues'
      resampling: 'bilinear'

    legend:
      type: gradient
      unit:
        label: 'Precipitation (mm/day)'
      min: 'None'
      max: 'Extreme'
      stops:
        - '#f7fbff'  # Very light blue
        - '#deebf7'
        - '#9ecae1'  # Medium blue
        - '#3182bd'  # Dark blue
        - '#08306b'  # Very dark blue

    analysis:
      metrics: ['min', 'max', 'mean', 'std']

    info:
      source: 'ECMWF / ERA5'
      spatialExtent: 'Global (zoomed to Portugal)'
      temporalResolution: 'Daily'
      unit: 'mm/day'

infoDescription: |
  ::markdown
    - **Coverage:** Dec 1, 2025 – Feb 15, 2026
    - **Resolution:** 0.25° (~28 km)
    - **Data Quality:** Reanalysis (hindcast + observations)
---

<Block type="wide">
  <Figure>
    <Map
      layerId="precipitation-daily"
      dateTime="2026-02-07"
      zoom={6}
      center={[-8.2, 39.5]}
    />
    <Caption>
      Peak rainfall during Storm Leonardo, February 7, 2026.
      The Tejo and Mondego basins received 60–80 mm, saturating soils.
    </Caption>
  </Figure>
</Block>
```

#### Example 3: Sentinel-2 Before/After

**File:** `app/content/datasets/sentinel-2-salvaterra.mdx`

```yaml
---
id: sentinel-2-salvaterra
name: 'Sentinel-2 Before/After (Salvaterra de Magos)'
description: 'True-color satellite imagery showing landscape change'

media:
  src: /images/datasets/sentinel-2-cover.jpg
  alt: 'Satellite image'
  author:
    name: 'ESA / Copernicus'
    url: 'https://scihub.copernicus.eu/'

featured: true

layers:
  - id: sentinel-2-before
    name: 'Before (Jan 6, 2026)'
    type: raster

    sourceParams:
      rescale: [0, 3000]
      colormap_name: none

    info:
      source: 'Copernicus Sentinel-2'
      unit: 'Digital Numbers (0–3000)'

  - id: sentinel-2-after
    name: 'After (Feb 20, 2026)'
    type: raster

infoDescription: |
  ::markdown
    - **Satellite:** Sentinel-2B (before), Sentinel-2C (after)
    - **Resolution:** 10 m/pixel (RGB) + 20 m/pixel (shortwave IR)
    - **Cloud Cover:** <1%
---

<Block type="full">
  <Figure>
    <CompareImage
      leftImageSrc="https://pub-xxx.r2.dev/sentinel-2/salvaterra-before-20260106.tif"
      leftImageAlt="Normal river conditions"
      leftImageLabel="Before: Jan 6, 2026"
      rightImageSrc="https://pub-xxx.r2.dev/sentinel-2/salvaterra-after-20260220.tif"
      rightImageAlt="Flooded floodplain"
      rightImageLabel="After: Feb 20, 2026"
    />
    <Caption
      attrAuthor="ESA / Copernicus"
      attrUrl="https://scihub.copernicus.eu/"
    >
      The Salvaterra de Magos floodplain flooded from 31,164 ha (Feb 6) to 49,164 ha (Feb 8),
      visible as water (dark blue) covering agricultural land (light tan/green).
    </Caption>
  </Figure>
</Block>
```

### Step 3.5: Colormaps Translation

Your existing QML colormaps must be converted to VEDA JSON format.

**From QGIS QML → TiTiler Colormap JSON:**

**QGIS QML Example:**

```xml
<rasterrenderer type="singlebandpseudocolor">
  <colorramp name="cpt-city-set1" type="PresetColorRamp">
    <color rgb="255,0,0" label="0"/>
    <color rgb="255,255,0" label="50"/>
    <color rgb="0,255,0" label="100"/>
  </colorramp>
  <item value="0" color="#ff0000" label="Low"/>
  <item value="50" color="#ffff00" label="Medium"/>
  <item value="100" color="#00ff00" label="High"/>
</rasterrenderer>
```

**TiTiler Colormap JSON (for sourceParams):**

```json
{
  "name": "precipitation-blues",
  "type": "sequential",
  "stops": [
    { "value": 0, "color": "#f7fbff" },
    { "value": 20, "color": "#deebf7" },
    { "value": 40, "color": "#9ecae1" },
    { "value": 60, "color": "#3182bd" },
    { "value": 80, "color": "#08306b" }
  ],
  "domain": [0, 80],
  "units": "mm/day",
  "colorblind_safe": true
}
```

**Script to Extract Colormaps from QML:**

```bash
# Use QGIS Python API or:
# 1. Open QGIS
# 2. Right-click layer → Export as JSON
# 3. Convert stops to rio-tiler format
```

For cheias.pt, translate all 12 colormaps from `data/colormaps/` to TiTiler JSON.

---

## 4. Migration Plan: What to Keep vs Discard

### 4.1: Data Assets to KEEP (Migrate to VEDA)

All data assets are location-agnostic and integrate directly with VEDA:

| Directory | Status | Action |
|-----------|--------|--------|
| `data/flood-extent/` | 1.8 GB | Keep; use PMTiles for vector tiles + GeoJSON for analysis |
| `data/cog/` | 1.6 GB | Keep; host on R2, reference via TiTiler |
| `data/sentinel-2/` | 179 MB | Keep; serve as static GeoTIFF or tile via TiTiler |
| `data/temporal/` | 149 MB | Keep; reference in Chart components for timeseries |
| `data/colormaps/` | 6.7 MB | Keep; translate to VEDA colormap JSON |
| `data/basemap/` | 3.8 MB | Keep; design docs; import MapLibre style into VEDA |
| `data/assets/` | 91 KB | Keep; use in feature layers (basins, districts) |
| `data/qgis/` | 35 MB | Keep; reference in story content |
| `data/consequences/` | 60 KB | Keep; use for event markers in maps |

**Action:** Copy entire `data/` directory to `veda-config-template/public/data/`

```bash
cp -r /home/nls/Documents/dev/cheias-pt/data/* veda-config-template/public/data/
```

### 4.2: Code & Scripts to KEEP

| File | Purpose | Migrate To |
|------|---------|------------|
| `scripts/fetch_soil_precip.py` | ERA5-Land updates | Keep in repo; run daily via cron/GH Actions |
| `scripts/fetch_sst.py` | SST data updates | Keep; monthly update job |
| `scripts/fetch_discharge.py` | GloFAS updates | Keep; daily |
| `scripts/compute_precondition.py` | Index calculation | Keep; daily |
| `scripts/download_cems.py` | EMSR activation mapping | Keep; event-triggered |
| `scripts/validate_temporal.py` | QA checks | Keep; pre-deploy |

**Action:** Keep `scripts/` directory; maintain in parallel with VEDA repo.

**Note:** These scripts generate COGs that TiTiler will serve. VEDA doesn't run them; they're your data pipeline.

### 4.3: Documentation to KEEP

| File | Purpose |
|------|---------|
| `tasks/data-inventory.md` | Reference for dataset descriptions |
| `tasks/veda-component-map.md` | Component usage (you're reading it!) |
| `tasks/data-summary.txt` | Quick reference |
| `research/` | Historical notes; preserve for audit trail |
| `README.md` | Update with VEDA architecture |

### 4.4: Code to DISCARD

**Delete from repo before migration:**

| File | Reason |
|------|--------|
| `src/scroll-engine.ts` | VEDA has native ScrollytellingBlock |
| `src/animations.ts` | VEDA handles transitions |
| `src/temporal-player.ts` | VEDA DateTimePicker built-in |
| `src/layer-manager.ts` | VEDA layer management automatic |
| `src/weather-layers.ts` | WeatherLayers GL not needed |
| `src/exploration-mode.ts` | VEDA Explore Data panel replaces this |
| `src/map-controller.js` | MapLibre GL managed by VEDA |
| `css/` | VEDA provides all styling |
| `src/*.js` (scroll-observer, chapter-wiring, map-setup) | Custom wiring not needed |

**Action:** Archive to `ARCHIVE-CUSTOM-ENGINE.tar.gz` before deletion.

```bash
tar -czf ARCHIVE-CUSTOM-ENGINE.tar.gz src/ css/
rm -rf src/ css/
```

### 4.5: Environment & Config to UPDATE

**Delete:**

- `vite.config.ts` (VEDA template will override)
- `.env` (use Vercel secrets instead)
- `tsconfig.json` (VEDA template includes)

**Preserve:**

- `.gitignore` (ensure `/dist`, `/node_modules` are ignored)
- `.git/` (maintain commit history)

### 4.6: Migration Checklist

- [ ] Archive custom code: `tar -czf ARCHIVE-CUSTOM-ENGINE.tar.gz src/ css/`
- [ ] Copy data assets: `cp -r data/* veda-template/public/data/`
- [ ] Copy scripts: `cp -r scripts/ veda-template/scripts/`
- [ ] Convert QML colormaps to JSON (see Section 3.5)
- [ ] Create dataset MDX files (see Section 3.4)
- [ ] Create story MDX files (next section)
- [ ] Update README.md with VEDA architecture
- [ ] Test build: `npm run build`
- [ ] Deploy to Vercel

---

## 5. Obsidian Vault References

When authoring content, consult these Second Brain documents:

### 5.1: Methodology & Principles

| Vault Link | Topic | Use For |
|-----------|-------|---------|
| `cheias.pt/Content Strategy` | Overall narrative arc | Structure of chapters |
| `Vizzuality Methods/Storytelling` | Narrative techniques | How to structure ScrollytellingBlock |
| `Vizzuality Methods/Data Visualization` | Visual encoding | Colormap selection, legend design |
| `cheias.pt/Creative Direction` | Visual identity | Typography, spacing, imagery |

### 5.2: Project-Specific Docs

| Vault Link | Topic | Use For |
|-----------|-------|---------|
| `cheias.pt/Chapter Outlines` | Ch0–Ch7 structure | What goes in each story section |
| `cheias.pt/Flood Event Timeline` | Kristin, Leonardo, Marta chronology | Temporal framing |
| `cheias.pt/Key Findings` | Research synthesis | Copy for Prose blocks |
| `cheias.pt/Visual References` | Design inspiration | Color palette, typography |

### 5.3: Implementation References

| Vault Link | Topic | Use For |
|-----------|-------|---------|
| `veda-config-template/README` | Official VEDA docs | Syntax reference |
| `eoviz-esip2025/Examples` | Real VEDA stories | Code snippets to adapt |
| `VEDA Component Map (this doc)` | Component API | Props, nesting rules |

### 5.4: Quick Reference: Story Outline from Vault

Your vault likely contains a **cheias.pt/Creative Brief** with chapters like:

```
Ch0: Title/Ghost Pulse
Ch1: Satellite Reveal (Sentinel-2 before/after)
Ch2: Atlantic Engine (SST + IVT atmospheric river)
Ch3: Soil Saturation (Precondition index timeline)
Ch4: Three Storms (Precipitation animation + IPMA)
Ch5: River Response (Discharge charts + hydrograph)
Ch6: Human Cost (Consequence markers + casualties)
Ch7: Lessons Learned (Burn scars + future prep)
```

Each chapter becomes a `<ScrollytellingBlock>` in your MDX story file.

---

## 6. Deployment Checklist

### Phase 1: Pre-Deployment Verification (Local)

- [ ] **Clone & setup:**
  ```bash
  git clone https://github.com/developmentseed/veda-config-template.git
  cd veda-config-template
  npm install
  ```

- [ ] **Create datasets** in `app/content/datasets/`:
  - [ ] `flood-extent.mdx`
  - [ ] `precipitation.mdx`
  - [ ] `soil-moisture.mdx`
  - [ ] `sentinel-2-salvaterra.mdx`
  - [ ] `discharge.mdx` (river gauge data)
  - [ ] (Add 2–3 more from data-inventory.md)

- [ ] **Create stories** in `app/content/stories/`:
  - [ ] `flood-story-2026.mdx` (main scrollytelling)
  - [ ] (Optional: narrative variants)

- [ ] **Add data assets:**
  ```bash
  cp -r /home/nls/Documents/dev/cheias-pt/data/* app/public/data/
  ```

- [ ] **Update environment:**
  ```bash
  cp .env.example .env.local
  # Edit with Mapbox token and TiTiler URL
  ```

- [ ] **Build & test locally:**
  ```bash
  npm run build
  npm run preview
  # Visit http://localhost:3000
  # Test:
  #   - Map loads at center of Portugal
  #   - ScrollytellingBlock chapters transition smoothly
  #   - Colormaps render correctly
  #   - Responsive on mobile
  ```

- [ ] **Performance checks:**
  - [ ] Largest COG loads < 5 MB/tile (check TiTiler compression)
  - [ ] Chart renders with 500+ points without lag
  - [ ] PMTiles vector tiles load fast (should be < 100 KB per zoom)
  - [ ] Lighthouse score > 80

### Phase 2: Vercel Configuration

- [ ] **Connect GitHub repo:**
  1. Log into [vercel.com](https://vercel.com)
  2. Click "Add New" → "Project"
  3. Import GitHub repo: `your-org/cheias-veda`

- [ ] **Configure build:**
  1. Settings → General
  2. Build Command: `npm run build`
  3. Output Directory: `dist`
  4. Framework Preset: `Vite`

- [ ] **Add environment variables:**
  1. Settings → Environment Variables
  2. Add each:
     - `VITE_MAPBOX_TOKEN` (secret)
     - `VITE_TITILER_URL` = `https://titiler.cheias.pt`
     - `VITE_STAC_API_ENDPOINT` (if using STAC)

- [ ] **Test deploy:**
  ```bash
  vercel deploy  # Creates preview URL
  # Test preview build (same as production)
  ```

### Phase 3: Domain Configuration

- [ ] **Cloudflare DNS:**
  1. Log into Cloudflare
  2. Go to cheias.pt DNS
  3. Add/update CNAME:
     - Name: `cheias`
     - Content: `cname.vercel.com`
     - Proxy: "DNS only"
  4. (Or let Vercel handle via dashboard)

- [ ] **Vercel domain setup:**
  1. Vercel Dashboard → Project Settings → Domains
  2. Add `cheias.pt`
  3. Verify DNS (Vercel auto-detects CNAME)
  4. Wait 2–5 min for SSL provisioning

- [ ] **Test production URL:**
  ```bash
  curl https://cheias.pt
  # Should return HTML (not 404)
  ```

### Phase 4: Content & Data Verification

- [ ] **Test all datasets load:**
  - [ ] Flood extent vectors visible
  - [ ] Precipitation raster colormaps render
  - [ ] Soil moisture heatmap displays
  - [ ] Sentinel-2 CompareImage loads

- [ ] **Verify temporal controls:**
  - [ ] Date slider works
  - [ ] Comparison slider functions
  - [ ] Time animations smooth (60 fps)

- [ ] **Test interactivity:**
  - [ ] Click to select basin/district
  - [ ] Info panel shows stats
  - [ ] Charts responsive to selection

- [ ] **Mobile testing:**
  - [ ] Use Chrome DevTools (Ctrl+Shift+M)
  - [ ] Test on iPhone/Android (real device if possible)
  - [ ] Verify touch interactions (map pan/zoom)
  - [ ] Check text readability

- [ ] **Accessibility audit:**
  - [ ] WAVE extension (Chrome): No critical errors
  - [ ] Keyboard navigation (Tab through map, buttons)
  - [ ] Color contrast > 4.5:1 (use WCAG contrast checker)

### Phase 5: Performance & Analytics

- [ ] **Lighthouse audit:**
  ```bash
  npm run build
  # Open in Chrome DevTools → Lighthouse
  # Target: Performance > 80, Accessibility > 85, Best Practices > 90
  ```

- [ ] **Bundle size check:**
  ```bash
  npm run build
  # Check dist/ size; should be < 2 MB gzipped
  ```

- [ ] **CDN & caching:**
  - [ ] Vercel auto-caches static assets
  - [ ] TiTiler tiles cache via HTTP headers
  - [ ] Cloudflare cache TTL = 1 hour (default, sufficient)

- [ ] **Analytics setup (optional):**
  - [ ] Add Google Analytics or Plausible
  - [ ] Track: pageviews, dataset clicks, story scrolls

### Phase 6: Monitoring & Maintenance

- [ ] **Set up alerting:**
  - [ ] Vercel dashboard: Enable deployment notifications
  - [ ] TiTiler health: `curl https://titiler.cheias.pt/healthz`

- [ ] **Establish data update schedule:**
  - [ ] Daily: `scripts/fetch_soil_precip.py` (COGs → R2)
  - [ ] Daily: `scripts/fetch_discharge.py`
  - [ ] Weekly: `scripts/fetch_sst.py` (NOAA 2-week lag)
  - [ ] Event-driven: `scripts/download_cems.py` (after major floods)

- [ ] **Backup strategy:**
  - [ ] COGs archived on R2 with versioning
  - [ ] Git repo backed up (GitHub default)
  - [ ] Weekly export of timeseries parquets

- [ ] **Maintenance log:**
  - [ ] Document any custom tweaks to VEDA template
  - [ ] Keep changelog of data updates
  - [ ] Note any colormap adjustments post-launch

### Phase 7: Launch & Post-Launch

- [ ] **Pre-launch communication:**
  - [ ] Announce on social media
  - [ ] Email stakeholders (IPMA, DPC, media)
  - [ ] Brief press (highlight real-time aspect)

- [ ] **Monitor first 48 hours:**
  - [ ] Watch Vercel analytics for load spikes
  - [ ] Check error logs (Vercel → Monitoring)
  - [ ] Verify TiTiler response times

- [ ] **Collect feedback:**
  - [ ] Issue form on site
  - [ ] Twitter/email for community input
  - [ ] Weekly review of engagement metrics

- [ ] **Schedule content updates:**
  - [ ] Every Friday: update datasets with latest data
  - [ ] Monthly: feature story on recent event
  - [ ] Quarterly: design/UX review

---

## Appendix: Quick Commands

### Development Workflow

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type-check TypeScript
npm run typecheck
```

### Data Sync to TiTiler

```bash
# Verify TiTiler connection
curl 'https://titiler.cheias.pt/cog/info?url=s3://your-bucket/path/soil-moisture/2026-03-01.tif'

# Generate tiles for a date
curl 'https://titiler.cheias.pt/cog/tiles/WebMercatorQuad/8/128/87.png?url=s3://your-bucket/cog/soil-moisture/2026-03-01.tif&colormap_name=viridis'
```

### Debugging

```bash
# Check build errors
npm run build 2>&1 | head -50

# Clear build cache
rm -rf dist node_modules/.vite

# Verify COG files
gdalinfo s3://your-bucket/cog/soil-moisture/2026-03-01.tif
```

### Deployment

```bash
# Deploy to Vercel (after git push)
vercel --prod

# Verify production
curl -I https://cheias.pt
```

---

## Summary

You now have a **complete roadmap** to migrate cheias-pt to VEDA-UI:

1. **Clone veda-config-template** and configure TiTiler + Mapbox tokens
2. **Translate datasets** from your data inventory into VEDA YAML format
3. **Author stories** in MDX using ScrollytellingBlock components
4. **Keep all data assets** and data generation scripts; VEDA consumes them via TiTiler
5. **Deploy to Vercel** with `cheias.pt` domain
6. **Maintain data pipeline** separately (scripts continue to run daily)

**Expected timeline:** 2–3 weeks from clone to production.

**Key advantages over custom engine:**
- ✅ Mobile-responsive out of the box
- ✅ Declarative, maintainable stories (MDX)
- ✅ Community support (100+ VEDA instances)
- ✅ Built-in accessibility
- ✅ Zero custom scroll logic = less bugs
- ✅ Easy to add new datasets/stories later

**Questions?** Consult the official docs:
- [VEDA Documentation](https://nasa-impact.github.io/veda-documentation/)
- [eoviz-esip2025 Example](https://github.com/NASA-IMPACT/eoviz-esip2025)
- This component map: `/home/nls/Documents/dev/cheias-pt/tasks/veda-component-map.md`

---

**Document maintained by:** Claude (Anthropic)
**Last updated:** 2026-03-06
**Status:** Ready for implementation
