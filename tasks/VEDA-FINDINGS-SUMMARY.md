# VEDA-UI Component Investigation - Summary & Key Findings

**Investigation Date:** March 5, 2026
**Source Repositories:** eoviz-esip2025, veda-config-template, NASA-IMPACT/veda-ui
**Deliverable:** `/home/nls/Documents/dev/cheias-pt/tasks/veda-component-map.md` (1216 lines, 31KB)

---

## Executive Summary

VEDA-UI is a highly modular React component library designed for geospatial storytelling and environmental data exploration. It excels at:

1. **Responsive layout blocks** with flexible composition (8 predefined types)
2. **Time-series data visualization** via maps with temporal comparison sliders
3. **Interactive scrollytelling** with synchronized map animations
4. **Multi-format data display** (CSV, JSON, Excel tables with sorting)
5. **Raster and vector layer support** via TiTiler tile endpoint

For the **cheias.pt Portuguese flood monitoring platform**, VEDA-UI provides production-ready components for flood narratives, real-time data visualization, and temporal analysis stories.

---

## Components Inventory

### Layout (Block) Components - 8 Types

All blocks are responsive across mobile/tablet/desktop:

| Block Type | Use Case | Desktop Layout | Mobile Layout |
|-----------|----------|---|---|
| **Default Prose** | Text-heavy narrative | Single column, centered | Full width |
| **Wide Prose** | Wider text | Wider column | Full width |
| **Wide Figure** | Prominent media | Wide media container | Full width |
| **Full Figure** | Hero/banner | Full viewport width | Full viewport |
| **Prose + Figure** | Text + side media | 2 columns (text L, image R) | Single column (text on top) |
| **Figure + Prose** | Image + text | 2 columns (image L, text R) | Single column (image on top) |
| **Prose + Full Figure** | Text + hero image | 2 columns | Single column |
| **Full Figure + Prose** | Hero image + text | 2 columns | Single column |

### Content Components

#### Media Display
- **Image** - Inline images with alignment, captions, attribution
- **Caption** - Rich HTML captions for figures
- **CompareImage** - Side-by-side slider comparison (static images only)

#### Data Visualization
- **Chart** - Line charts for time-series data (CSV/JSON)
- **Table** - Sortable tables with virtual scrolling (CSV/JSON/Excel)

#### Interactive Maps
- **Map** - Full-featured geospatial data display with temporal controls
  - Layer selection from datasets
  - Time slider for temporal data
  - Comparison mode (side-by-side dates)
  - Zoom/pan, basemap toggle
  - Statistics on click

#### Embedding
- **Embed** - iframe wrapper for external dashboards/notebooks
- **Link** - Relative routing component

#### Narratives
- **ScrollytellingBlock** - Map with scrollable story chapters
- **Chapter** - Individual narrative sections with map state

---

## Critical Capabilities for Flood Monitoring

### 1. Temporal Comparison (Excellent)

Maps support date-based comparison with automatic slider:

```jsx
<Map
  layerId='flood-extent'
  dateTime='2022-01-15'          // Before flood
  compareDateTime='2022-01-20'   // After flood
  compareLabel='Jan 15 vs Jan 20'
/>
```

**Perfect for:** Pre/post-flood satellite comparisons

### 2. Scrollytelling (Excellent)

Synchronized map animations during story scroll:

```jsx
<ScrollytellingBlock>
  <Chapter center={[10, 39]} zoom={6} layerId='rainfall-jan'>
    ## Storm Approaches
    Heavy rainfall begins accumulating in the north...
  </Chapter>
  <Chapter center={[10, 39]} zoom={8} layerId='flood-extent'>
    ## Rivers Overflow
    Water levels exceed danger thresholds...
  </Chapter>
</ScrollytellingBlock>
```

**Perfect for:** Event-by-event flood narrative (warning → impact → recovery)

### 3. Time-Series Charts (Good)

Line charts for rainfall, discharge, water levels:

```jsx
<Chart
  dataPath='/data/discharge-timeseries.csv'
  idKey='Station'
  xKey='Date'
  yKey='Discharge m³/s'
  dateFormat='%Y-%m-%d'
  highlightStart='2022-01-15'
  highlightEnd='2022-01-20'
  highlightLabel='Flood Event'
/>
```

**Perfect for:** River discharge, rainfall accumulation, water level alerts

### 4. Data Tables (Good)

Sortable tables for flood alerts, affected areas:

```jsx
<Table
  dataPath='/alerts/daily-flood-alerts.xlsx'
  columnsToSort={['Date', 'River', 'AlertLevel']}
  excelOption={{ sheetNumber: 0 }}
/>
```

**Perfect for:** Daily alert bulletins, affected municipalities list

### 5. Comparison Images (Good)

Before/after flood imagery:

```jsx
<CompareImage
  leftImageSrc='/sat/jan-10-clear.jpg'
  leftImageLabel='Jan 10 - Pre-Flood'
  rightImageSrc='/sat/jan-20-flooded.jpg'
  rightImageLabel='Jan 20 - Peak Flood'
/>
```

**Good for:** Static satellite comparisons (but Map comparison is more flexible)

---

## Dataset & Layer Configuration

VEDA stores datasets as **MDX files with YAML frontmatter**:

```
/content/datasets/
  ├── rainfall.mdx
  ├── water-levels.mdx
  ├── flood-extent.mdx
  └── discharge.mdx
```

### Layer Configuration Format

```yaml
layers:
  - id: flood-extent-2022
    stacCol: flood-extent-2022
    name: 'Flood Extent Jan 2022'
    type: raster                     # raster, vector, wms, wmts
    projection:
      id: 'mercator'                 # or polarNorth for Portugal focus
    bounds: [-10, 36, 4, 42]         # Portugal bounding box
    zoomExtent: [2, 18]
    basemapId: 'satellite'           # dark, light, satellite, topo

    sourceParams:
      rescale: [0, 100]              # Data min/max for color scaling
      colormap_name: 'blues'         # rio-tiler colormaps
      resampling: 'bilinear'

    legend:
      type: gradient
      unit: { label: 'Inundation (%)' }
      min: 'No Water'
      max: 'Full Inundation'
      stops:
        - '#ffffff'
        - '#e0f2ff'
        - '#0066cc'
        - '#0033aa'

    analysis:
      metrics: [min, max, mean]
      exclude: false

    compare:
      datasetId: flood-extent
      layerId: flood-extent-2021     # Compare to 2021
      mapLabel: '2022 vs 2021 Flood Extent'
```

### STAC Integration

Layers reference **STAC Collections** for data discovery:

```yaml
stacCol: flood-extent-2022                    # Collection ID
stacApiEndpoint: 'https://stac.example.com'  # STAC server
tileApiEndpoint: 'https://titiler.example.com' # Tile server
```

TiTiler automatically generates tiles from Cloud Optimized GeoTIFFs (COGs).

---

## Mobile & Responsive Design

### All Components are Fully Responsive

| Component | Mobile | Tablet | Desktop |
|-----------|--------|--------|---------|
| Blocks | Full width, single column | Full width | Flexible layout |
| Maps | Full width, interactive | Full width | Full width |
| Charts | Full width, auto height | Full width | Full width |
| Tables | Horizontal scroll | Horizontal scroll | Horizontal scroll |
| Scrollytelling | Full width overlay text | Full width overlay | Full width overlay |

### Key Features

- **No horizontal scroll** for main content
- **Touch-friendly** controls on mobile
- **Sticky headers** in tables while scrolling
- **Responsive font sizes** (0.8rem baseline for charts on mobile)
- **Overlay optimization** for scrollytelling on narrow screens

---

## Known Limitations & Workarounds

### 1. CompareImage Limitations

**Issue:** Cannot compare different datasets or apply dynamic colormaps.

**Workaround:** Use `Map` with `compareDateTime` instead:

```jsx
// Better for dataset comparison
<Map
  layerId='flood-extent'
  dateTime='2022-01-15'
  compareDateTime='2022-01-20'
/>

// vs static image comparison
<CompareImage
  leftImageSrc='/static/before.jpg'
  rightImageSrc='/static/after.jpg'
/>
```

### 2. Chart Data Requirements

**Issue:** Charts require consistent column structure with no gaps.

**Solution:** Pre-process data to ensure continuous date ranges in CSV/JSON.

### 3. Embed CORS Restrictions

**Issue:** Some external services block iframe embedding.

**Workarounds:**
- Host a wrapper page on your domain
- Use `<Link>` for external links instead
- Check IPMA/SNIRH documentation for official embed options

### 4. Layer Styling Limitations

**Vector layers:** No custom style control (uses default vector styling)
**Solution:** Convert to raster (COG) format for full control

### 5. No Multi-Image Comparison

**Issue:** CompareImage limited to 2 images (no slider for 3+ images)
**Solution:** Use multiple CompareImage components side-by-side

---

## Recommended Architecture for cheias.pt

### Data Flow

```
Raw Satellite Data (GeoTIFF)
    ↓
Cloud Optimized GeoTIFF (COG)
    ↓
STAC Metadata + TiTiler Endpoint
    ↓
Dataset MDX Config → Map Component
```

### Story Structure

**Suggested story template:**

1. **Introduction Block** - Context about recent floods
2. **ScrollytellingBlock** - 4-6 chapters showing event progression
   - Chapter 1: Rainfall accumulation (rainfall map)
   - Chapter 2: River rise (discharge chart overlay)
   - Chapter 3: Peak flood (satellite map)
   - Chapter 4: Recovery phase (timelapses)
3. **Map Block** - Full temporal comparison for detailed exploration
4. **Table Block** - Daily alert bulletin
5. **Chart Block** - Discharge vs rainfall correlation

### Dataset Organization

```
Flood Events/
├── 2024-January-Flood/
│   ├── rainfall.mdx          (daily rainfall data)
│   ├── discharge.mdx         (river discharge levels)
│   ├── water-levels.mdx      (gauge readings)
│   ├── flood-extent.mdx      (satellite mapping)
│   └── damage-assessment.mdx (impact assessment)

Real-Time Monitoring/
├── current-discharge.mdx
├── current-rainfall.mdx
└── flood-risk-alerts.mdx
```

---

## Color Schemes & Legends

### Recommended for Flood Data

```yaml
# Flood Extent / Inundation
legend:
  type: gradient
  stops:
    - '#ffffff'  # No water
    - '#c6dbef'  # Shallow water
    - '#6baed6'  # Medium water
    - '#2171b5'  # Deep water
    - '#08519c'  # Very deep water

# Rainfall / Precipitation
legend:
  type: gradient
  stops:
    - '#ffffcc'  # No rain
    - '#ffeda0'  # Light
    - '#fed976'  # Moderate
    - '#fd8d3c'  # Heavy
    - '#e31a1c'  # Extreme

# Risk / Alert Levels
legend:
  type: categorical
  stops:
    - color: '#00ff00'
      label: Low Risk
    - color: '#ffff00'
      label: Moderate Risk
    - color: '#ff9900'
      label: High Risk
    - color: '#ff0000'
      label: Extreme Risk
```

---

## Next Steps for Implementation

### Phase 1: Setup
1. Create STAC collections for flood datasets
2. Configure TiTiler for Cloud Optimized GeoTIFFs
3. Create dataset MDX files with layer configs

### Phase 2: Content
1. Develop 2-3 story templates (event narrative, monitoring guide, recovery)
2. Build real-time monitoring dashboard with Map + Chart combo
3. Create daily alert bulletin view

### Phase 3: Enhancement
1. Add custom JavaScript functions for dynamic legends
2. Integrate IPMA/SNIRH data (via Embed if available)
3. Set up automated story generation from new flood events

---

## References & Resources

- **Full Component Documentation:** `/home/nls/Documents/dev/cheias-pt/tasks/veda-component-map.md`
- **VEDA Documentation:** https://github.com/NASA-IMPACT/veda-ui/docs/
- **Layer Configuration Spec:** https://github.com/NASA-IMPACT/veda-ui/docs/content/frontmatter/layer.md
- **TiTiler Documentation:** https://developmentseed.org/titiler/
- **STAC Specification:** https://stacspec.org/
- **Rio-Tiler Colormaps:** https://cogeotiff.github.io/rio-tiler/colormap/

---

## Document Metadata

- **Total Component Reference Lines:** 1216
- **Components Documented:** 15+
- **Real Examples Included:** 10+
- **Configuration Samples:** 30+
- **Responsive Design Coverage:** Complete
- **Mobile Breakpoints Covered:** Yes
- **Limitations & Workarounds:** Documented

This investigation covers VEDA-UI's complete component library as implemented in production deployments. All information is derived from official documentation, source code inspection, and real-world example analysis from the eoviz-esip2025 and veda-config-template repositories.
