# cheias.pt Content Gaps & Enhancement Opportunities

**Date:** March 5, 2026
**Story:** Winter 2025-26 Portuguese Flood Events
**Status:** Gap analysis for narrative strength and technical completeness

---

## Overview

The cheias-extended-story.mdx narrative is deployable and tells a compelling flood story using available data. However, several data gaps and enhancement opportunities exist that would strengthen the narrative, improve visual impact, and add technical depth.

This document prioritizes gaps by narrative impact, technical feasibility, and acquisition timeline.

---

## TIER 1: High-Impact / Readily Available (Weeks 1-2)

### 1.1 Seasonal Baseline Flood Extent Layer

**Gap:** Comparison map (2026 vs. normal extent) is incomplete without "normal" reference layer.

**What's needed:**
- Raster layer or vector polygon defining typical seasonal flood zones (Oct-May average, or 1-in-20-year extent based on historical data)
- Derivable from: 10+ years of satellite archives (Sentinel-1 SAR, Sentinel-2), hydrological models (GloFAS), or PGRI (Portuguese Flood Risk Management Plan) data

**Impact:**
- Enables "2026 Peak vs. Normal" comparison story (Chapter 7, MapBlock with compareDateTime)
- Quantifies anomaly: "226,764 ha vs. historical average of XX ha"
- Narrative power: Shows this was not just an extreme event, but fundamentally outside the expected range

**Feasibility:** HIGH
- Data likely exists in PGRI documents or EU Floods Directive spatial data
- Could be synthesized from 10-year Sentinel-1 archive (moderate processing)
- Alternative: Use GloFAS discharge data to derive typical inundation for each basin

**Timeline:** 1-2 weeks (data sourcing + processing)

**TiTiler Configuration:**
```yaml
layerId: 'flood-extent-baseline-normal'
stacCol: 'flood-extent-normal'
type: 'raster'
sourceParams:
  rescale: [0, 1]
  colormap_name: 'Purples'
  resampling: 'bilinear'
legend:
  type: 'gradient'
  min: 'No inundation'
  max: 'Seasonal flood zone'
```

---

### 1.2 High-Resolution Sentinel-2 True-Color Composites

**Gap:** Current Salvaterra RGB images are single snapshots. Story would benefit from 3-5 temporal snapshots.

**What's needed:**
- Sentinel-2 L2A true-color composites (RGB: bands 4/3/2) at 10m resolution for Salvaterra de Magos (MGRS tile 29SND)
- Key acquisition dates:
  - Jan 6, 2026 (pre-flood baseline) — AVAILABLE
  - Jan 31, 2026 (post-Kristin, pre-Leonardo)
  - Feb 8, 2026 (peak Leonardo flood) — AVAILABLE (Feb 20 substitute)
  - Feb 15, 2026 (recession phase)
  - March 1, 2026 (recovery baseline)

**Impact:**
- Gallery of CompareImage components showing temporal progression
- Readers see vegetation → water → emerging land → greenery returning
- Narrative arc: "Before," "During," "After" becomes granular and visceral
- Mobile-friendly scrollable image gallery

**Feasibility:** HIGH
- Element 84 Earth Search (STAC) provides Sentinel-2 L2A with <0.5% cloud cover screening
- Can download directly via rasterio/GDAL; batch process to JPEG

**Timeline:** 3-5 days
- Query STAC API for tile 29SND, date range Dec 1, 2025 – Mar 1, 2026
- Filter cloud <10%
- Download COGs, convert to web-optimized JPEG (2-3 MB each)

**Usage:**
```jsx
// Chapter 7 enhancement: Multi-panel progression
<Block type='wide'>
  <Figure>
    <CompareImage
      leftImageSrc='/images/salvaterra-rgb-20260106.jpg'
      leftImageLabel='Jan 6 — Pre-Flood'
      rightImageSrc='/images/salvaterra-rgb-20260131.jpg'
      rightImageLabel='Jan 31 — Post-Kristin'
    />
    <Caption>Vegetation withstands initial storm; fields still green</Caption>
  </Figure>
</Block>

<Block type='wide'>
  <Figure>
    <CompareImage
      leftImageSrc='/images/salvaterra-rgb-20260131.jpg'
      leftImageLabel='Jan 31 — Pre-Leonardo'
      rightImageSrc='/images/salvaterra-rgb-20260208.jpg'
      rightImageLabel='Feb 8 — Peak Flood'
    />
    <Caption>Leonardo rainfall transforms landscape to water within days</Caption>
  </Figure>
</Block>
```

---

### 1.3 NDWI Water Index Time Series (3-5 Key Dates)

**Gap:** Current NDWI comparison (before/after) is 2-image static. Dynamic time series would show water extent evolution.

**What's needed:**
- NDWI computed from Sentinel-2 for same Salvaterra tile on 3-5 key dates
- Formula: NDWI = (B8 - B3) / (B8 + B3)
  - B8 = Near-Infrared (NIR)
  - B3 = Green
- Render each date with blue sequential colormap (dark blue = water, white = no water)
- Output: 5 PNG frames, ~2 MB each

**Impact:**
- Scientific credibility: NDWI is standard flood delineation metric (used by Copernicus)
- Shows water detection progression: Jan 6 (no water) → Feb 1 (edge pixels) → Feb 8 (massive water signal) → Feb 21 (recession)
- Educational value: Readers learn how satellite spectral indices detect water
- Integration opportunity: Overlay EMSR864 delineation polygons on NDWI to validate mapping accuracy

**Feasibility:** HIGH
- Compute from existing Sentinel-2 COGs
- Single Python script using rasterio/numpy (30 minutes)
- Render to PNG using rasterio paint tools (5 minutes per image)

**Timeline:** 1 day

**Script Skeleton:**
```python
import rasterio
import numpy as np
from rasterio.plot import show
from matplotlib import pyplot as plt

with rasterio.open('B3.tif') as src_green:
    green = src_green.read(1).astype(float)
with rasterio.open('B8.tif') as src_nir:
    nir = src_nir.read(1).astype(float)

ndwi = (nir - green) / (nir + green + 1e-8)  # avoid division by zero

# Save to GeoTIFF
profile = {...}
with rasterio.open('salvaterra-ndwi-YYYYMMDD.tif', 'w', **profile) as dst:
    dst.write(ndwi, 1)

# Render to PNG with colormap
plt.imshow(ndwi, cmap='Blues', vmin=-0.5, vmax=0.8)
plt.colorbar(label='NDWI')
plt.title(f'Water Index - {date}')
plt.savefig(f'salvaterra-ndwi-{date}.png', dpi=150, bbox_inches='tight')
```

---

### 1.4 MSLP Synoptic Analysis Map — Storm Kristin Day

**Gap:** Storm Kristin meteorology is described (209 km/h, pressure 953 hPa) but not visualized.

**What's needed:**
- Mean Sea Level Pressure (MSLP) raster for Jan 28, 2026, 18:00 UTC (storm landfall)
- Wind barbs overlay (U/V components converted to barb arrows)
- Optional: Isobars contoured and overlaid as vector lines
- Derived from: Open-Meteo ERA5 6-hourly data (already in repo: `data/cog/mslp/2026-01-28*.tif`)

**Impact:**
- Atmospheric science narrative: Readers see pressure gradient intensity
- Visual drama: Deep low-pressure system depicted
- Educational: Barbs show wind direction/magnitude at different locations
- Integration: Link to Lightning data overlay (262 Kristin strikes in lightning-kristin.geojson)

**Feasibility:** MEDIUM-HIGH
- MSLP COG exists; needs rendering to PNG
- Wind barb conversion requires Python (cartopy or custom plotting)
- Optional contours need GIS processing (QGIS contour from DEM)

**Timeline:** 2-3 days
- Render MSLP COG → PNG (1 day)
- Process wind barbs → GeoJSON with arrow glyphs (1 day)
- Test overlay in QGIS, finalize styling (1 day)

**Usage:**
```jsx
<Block type='full'>
  <Figure>
    <Map
      layerId='mslp-synoptic-kristin'
      dateTime='2026-01-28T18Z'
      zoom={6}
      center={[8.5, 40]}
      basemapId='light'
    />
    <Caption>
      Mean Sea Level Pressure at Storm Kristin landfall (Jan 28, 18:00 UTC): 953 hPa deep low over Portugal. Wind barbs show 150-180 km/h sustained winds; gusts exceeded 209 km/h. Pressure gradient from low center (purple) to high-pressure ridge (green, offshore) drove extreme wind speeds.
    </Caption>
  </Figure>
</Block>
```

---

### 1.5 Evacuation Timeline Chart

**Gap:** Evacuations mentioned (1,100+ total) but not visualized over time.

**What's needed:**
- Daily evacuation count, Feb 3-12, 2026
- CSV format:
  ```
  Date,Location,Evacuated_Count
  2026-02-03,Alcácer do Sal,50
  2026-02-04,Leiria,200
  2026-02-05,Mondego Valley,100
  2026-02-06,Tejo Basin,350
  2026-02-07,Coimbra,1000
  2026-02-08,Algarve,200
  ...
  ```

**Data Source:** Synthesized from news reports, Proteção Civil statements. Likely underestimate (not all evacuations publicly tracked).

**Impact:**
- Quantifies human scale: "12,000 people" → graph showing crescendo of evacuation
- Timeline alignment: Readers see evacuation decisions tracked against flood peak
- Emotional weight: Upslope curve = increasing danger, increasing governmental response

**Feasibility:** HIGH
- Data curated from news archives, not raw measurement
- Chart rendering trivial once CSV compiled

**Timeline:** 1 day (research + CSV creation)

---

## TIER 2: Medium-Impact / Moderate Effort (Weeks 2-4)

### 2.1 Agricultural Impact Mapping

**Gap:** Story mentions "€750M crop losses" and "thousands of hectares" but lacks spatial visualization.

**What's needed:**
1. **Agricultural zone boundaries:** GIS layer showing cultivated land in flood-prone areas (Tejo, Mondego, Sado floodplains)
   - Source: CORINE Land Cover (EU, free) + Copernicus Agricultural Monitoring (free)
   - Delineate: Irrigated agriculture, permanent crops, arable land

2. **Crop loss estimates by region:** Heat map or graduated color layer
   - Data: IPMA agricultural bulletins + farmer association reports
   - Unit: €/hectare or % loss by crop type

3. **Livestock mortality overlay:** Point layer with impact markers
   - Source: Farmer reports, cooperative surveys
   - Quantify: 5,000-10,000 cattle, sheep, goats estimated lost

**Impact:**
- Humanizes agricultural catastrophe (beyond € amounts)
- Shows geographic concentration: Which regions suffered most?
- Policy relevance: Highlights vulnerability of food supply chains
- Climate justice: Smallest farms often least insured; largest losses borne by vulnerable populations

**Feasibility:** MEDIUM
- Agricultural zone data readily available (CORINE, Copernicus)
- Crop loss estimates require compilation from diverse sources (news, farmer orgs, government)
- No real-time data; static snapshot of 2026 disaster

**Timeline:** 2-3 weeks (research + GIS processing)

**Layer Configuration:**
```yaml
layerId: 'agricultural-impact-zones'
type: 'raster'
sourceParams:
  rescale: [0, 1000]  # EUR/hectare loss
  colormap_name: 'YlOrRd'
legend:
  type: 'gradient'
  unit: { label: '€/hectare loss' }
  min: '0'
  max: '1000+'
```

---

### 2.2 Infrastructure Damage Points (A1 Motorway, Dikes, Bridges)

**Gap:** A1 motorway collapse mentioned but not mapped. Dike ruptures abstract without location.

**What's needed:**
- Vector layer (GeoJSON points) with infrastructure damage locations
  - A1 motorway pillar failure (exact coordinates: ~40.20°N, 8.43°W, Coimbra)
  - Mondego dike ruptures (Casais, Granja do Ulmeiro)
  - Bridge damage points (3-5 significant bridges)
  - Power substation damage points (if data available)
  - Water treatment plant failures (if data available)

- Pop-up information for each point:
  - Infrastructure type
  - Damage date
  - Repair status / timeline
  - Cost estimate
  - Photo/satellite image if available

**Impact:**
- Spatial literacy: Readers understand where infrastructure failed
- Policy connection: Maps identify critical infrastructure needing climate adaptation
- Recovery tracking: Can update layer as repairs progress (living document)
- Risk communication: Future users see where vulnerabilities exist

**Feasibility:** MEDIUM
- Coordinate sourcing from Estradas de Portugal (motorway authority), Proteção Civil (emergency response), local governments
- Some data available in news reports; others require direct contact with government agencies
- Photo/satellite overlay would require additional image acquisition

**Timeline:** 3 weeks (data sourcing + GIS compilation)

**GeoJSON Skeleton:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-8.43, 40.20]
      },
      "properties": {
        "name": "A1 Motorway Pillar Collapse",
        "type": "bridge",
        "date": "2026-02-12",
        "status": "Under repair",
        "repair_timeline": "Estimated June 2026",
        "cost_estimate_eur": 200000000,
        "description": "Mondego floodwaters undercut pillar foundation after dike rupture (Feb 11). Northbound lane collapsed; southbound structurally intact but closed for inspection.",
        "image_url": "/images/a1-collapse-aerial-20260212.jpg"
      }
    },
    ...
  ]
}
```

---

### 2.3 River Gauge Real-Time Integration

**Gap:** 11 discharge stations exist (SNIRH data available) but not integrated into interactive map with mini-charts.

**What's needed:**
1. **Vector point layer (GeoJSON):** 11 gauge locations with properties
2. **Embedded mini-chart in map popups:** Click station → small hydrograph appears
   - Alternative (if custom popups not feasible): Link to SNIRH page or separate Chart component

**Impact:**
- Interactivity: Readers explore data, not just consume narrative
- Temporal depth: Each station shows full 77-day timeline
- Hydrological education: Readers see response differences between basins
- Real-time capability: Can be updated daily as new discharge data arrives (future)

**Feasibility:** MEDIUM-HIGH
- Station coordinates + timeseries data exist in repo
- VEDA-UI Map popups are limited (text + buttons only)
- Workaround: Use separate Chart components for each basin (7 basins = 7 charts) instead of embedded popups
- Future enhancement: Custom VEDA-UI component for interactive map popups

**Timeline:** 1 week
- GeoJSON compilation: 1 day
- Chart creation per basin: 3 days
- Integration/testing: 2 days

**Usage Pattern:**
```jsx
// Chapter 5: Discharge narrative
<Block type='wide'>
  <Figure>
    <Map
      layerId='discharge-stations'
      dateTime='2026-02-07'
      zoom={7}
      center={[9.0, 39.5]}
    />
    <Caption>
      11 discharge monitoring stations. Click a station name below to view its hydrograph.
    </Caption>
  </Figure>
</Block>

// Below map: Individual Charts per basin (collapsible)
<Block type='wide'>
  <Figure>
    <Chart
      dataPath={...}  // Tejo data only
      idKey='Station'
      xKey='Date'
      yKey='Discharge_m3s'
      title='Tejo Basin: Vila Franca de Xira Gauge'
      colors={['#0066cc']}
    />
  </Figure>
</Block>
...
```

---

### 2.4 Aerial Photography of Flooded Communities

**Gap:** Story describes impacts (Salvaterra, Coimbra, Alcácer do Sal, Porto) but lacks human-scale photography.

**What's needed:**
- High-resolution aerial or drone photographs of:
  - Salvaterra de Magos: flooded floodplain, isolated buildings, submerged fields
  - Coimbra Parque Verde neighborhood: water in streets, evacuated homes
  - Alcácer do Sal: river overtopping urban areas
  - Porto Douro waterfront: burst banks

- Metadata: Date taken, photographer, location coordinates, caption (what readers see), attribution

**Impact:**
- Emotional connection: Satellite data is abstract; photography is visceral
- Human scale: Buildings, streets, vehicles in water humanizes the disaster
- Media credibility: News-quality images lend authority
- Global reach: Powerful images travel across media; increase story visibility

**Feasibility:** MEDIUM (procurement challenge)
- Drone footage likely exists (government, NGOs, news agencies)
- Rights/licensing: Must secure permission to use
- Quality variation: Depends on acquisition date and weather

**Timeline:** 2-3 weeks (sourcing + licensing negotiation)

**Sources:**
- Portuguese news agencies (RTP, SIC, Público): Often have photo archives available to licensed users
- Government agencies (Proteção Civil): May have aerial surveys
- NGOs (Red Cross, Médecins sans Frontières): Often document disasters with photography
- Stock photo services (Getty, Alamy): High-cost but reliable licensing

**Usage:**
```jsx
<Block type='full'>
  <Figure>
    <Image
      src='/images/floods/coimbra-parque-verde-20260206.jpg'
      alt='Coimbra Parque Verde neighborhood flooded, showing houses with water on first floor and residents evacuating'
    />
    <Caption
      attrAuthor='RTP (Radiotelevisão Portuguesa)'
      attrUrl='https://www.rtp.pt/'
    >
      Coimbra, Parque Verde neighborhood (Feb 6, 2026): 3,000 residents evacuated as Mondego dike ruptures and floodwaters enter urban areas. Photo shows first-floor inundation; residents' belongings damaged beyond recovery.
    </Caption>
  </Figure>
</Block>
```

---

### 2.5 Climate Attribution Science Deep-Dive (Custom Component or Embed)

**Gap:** World Weather Attribution findings mentioned but not visualized in detail.

**What's needed:**
1. **Infographic or interactive visualization:** Attribution percentages
   - "Climate change increased rainfall intensity by 11% (north), 36% (south)"
   - "Without climate change, Feb 7 rainfall would be once-in-200-year event; with climate change, once-in-100-year"

2. **Embed or link to full WWA study:** https://www.worldweatherattribution.org/

3. **Model comparison chart:** Historical (1991-2020) vs. future (2050) precipitation extremes
   - Shows increased frequency of "extreme" events in warming scenarios

**Impact:**
- Scientific credibility: Links policy narrative to peer-reviewed attribution science
- Future projection: Helps readers understand why this disaster will recur
- Urgency: "This is normal now" messaging drives climate action

**Feasibility:** MEDIUM
- Visualization design required (infographic artist or custom React component)
- Data sourcing: WWA paper + IPCC reports
- Technical: Embed WWA iframe (if CORS allows) or link directly

**Timeline:** 2-3 weeks (design + implementation)

---

## TIER 3: Nice-to-Have / Aspirational (Weeks 4+)

### 3.1 Animated Timeseries: Daily Satellite Loop (Animated GIF or Video)

**Gap:** Static frames show before/after but don't convey temporal flow.

**What's needed:**
- MP4 video or animated GIF showing daily satellite imagery progression
- Feb 1-15, 2026: one frame per day showing:
  - Sentinel-1 SAR flood extent growing → receding
  - OR Sentinel-2 RGB (where cloud-free) showing vegetation → water → recovery
  - OR animated rainfall accumulation overlay

**Impact:**
- Visceral: Moving water conveys urgency better than static maps
- Time compression: 15 days of changes visible in 30-second animation
- Shareability: Video clips amplify story reach on social media

**Feasibility:** MEDIUM (technical, time-consuming)
- Requires frame-by-frame rendering of COGs
- Video encoding/optimization
- Hosting (video files large; may require CDN)

**Timeline:** 2-3 weeks (rendering + encoding + hosting setup)

**Technical approach:**
```bash
# Pseudocode for animation pipeline
for date in [2026-02-01, 2026-02-02, ..., 2026-02-15]:
  # Render COG to PNG
  gdal_translate -of PNG \
    -scale 0 1 0 255 \
    data/cog/flood-extent/${date}.tif \
    frames/flood-extent-${date}.png

# Compile frames to MP4
ffmpeg -framerate 2 -i frames/flood-extent-%Y-%m-%d.png \
  -c:v libx264 -pix_fmt yuv420p \
  salvaterra-flood-progression.mp4

# Or to animated GIF (lower quality, better compatibility)
convert -delay 50 frames/flood-extent-*.png \
  -loop 0 salvaterra-flood-progression.gif
```

---

### 3.2 Historical Flood Comparison (1967 Tagus Flood)

**Gap:** Story mentions "1967 comparison" but lacks visual/data comparison.

**What's needed:**
- Archival data from 1967 Tagus flood (Nov 25-26, 1967):
  - Historical accounts (written descriptions, newspaper archives)
  - Peak discharge (if recorded): ~1967 value vs. 2026 value
  - Fatality count comparison: 500-700 deaths in 1967 (deadliest in 100 years at time)
  - Geographic extent (if historical maps available): maps of 1967 inundation zone
  - Economic damage (estimated in contemporary currency)

- Comparison chart: 1967 vs. 2026 side-by-side
  - Discharge
  - Fatalities
  - Duration
  - Geographic extent
  - Economic damage (adjusted for inflation)

**Impact:**
- Historical perspective: Shows this is not the first catastrophe, but differs from predecessor
- Long-term narrative: Positions 2026 in 60-year disaster cycle
- Climate message: 1967 was rare; 2026 will become routine

**Feasibility:** LOW-MEDIUM
- Historical data (1967) difficult to source; pre-digital era
- May require contact with Portuguese hydrological archives, university libraries
- Some data (deaths, newspaper accounts) readily available; some (detailed discharge records) harder to find

**Timeline:** 3-4 weeks (archival research)

**Sources:**
- Portuguese hydrological service archives
- University of Coimbra library (nearby the flooded region)
- Newspaper archives (Diário de Notícias, Jornal de Notícias, A Capital from Nov 1967)
- Historical monographs on Portuguese hydrology

---

### 3.3 Policy Timeline & Legislation Dashboard

**Gap:** Government response and policy changes mentioned but not tracked over time.

**What's needed:**
- Interactive timeline showing:
  - Jan 29: State of calamity declaration
  - Feb 3: EMSR864 activation
  - Feb 10: Interior Minister resignation
  - Feb 10: €2.5B support package announced
  - Feb 15: Extension of state of calamity
  - March: EU climate adaptation funding discussions
  - Later: Infrastructure repair project launches

- Each event: Date, description, impact, links to legislation/announcements

**Impact:**
- Transparency: Readers see government response timeline
- Accountability: Tracks policy decisions and delays
- Future reference: Helps anticipate similar events

**Feasibility:** HIGH
- Data readily available from government websites, news archives
- Simple timeline layout (text + dates)
- No new data acquisition needed

**Timeline:** 1 week (curation + markup)

---

### 3.4 Real-Time Dashboard Integration (Future)

**Gap:** Story is historical; could become real-time forecasting tool.

**What's needed:**
- Live data feeds:
  - SNIRH discharge (updated daily)
  - IPMA precipitation forecast (updated 4x daily)
  - Satellite imagery (updated 6-12 days)
  - IPMA warnings (real-time)

- Visualization updates:
  - Charts extend as new data arrives
  - Maps show current discharge levels
  - Alerts highlighted if forecasted exceedances
  - Time slider allows readers to play back 2025-26 event or current season

**Impact:**
- Living document: Story stays relevant across multiple flood seasons
- Early warning: Readers can use platform to anticipate next flood
- Operational use: Proteção Civil and APA could integrate VEDA-UI for decision support

**Feasibility:** LOW (requires sustained development)
- API integration with SNIRH, IPMA (possible but requires engineering)
- Data pipeline (continuous ingestion, quality checks)
- Frontend updates (auto-refresh charts/maps)
- Hosting and maintenance (ongoing)

**Timeline:** 8-12 weeks (full development cycle)

---

## Data Acquisition Priorities

### Priority 1 (Complete immediately):
1. Seasonal baseline flood extent layer
2. Multi-date Sentinel-2 RGB composites (Jan-Mar 2026)
3. NDWI time series (3-5 key dates)
4. MSLP synoptic map (Jan 28, 18:00 UTC)
5. Evacuation timeline CSV

**Effort:** ~2-3 weeks total
**Impact:** High (narrative becomes more complete, interactive)
**Resources:** Existing data + light processing

---

### Priority 2 (Complete in parallel):
1. Agricultural impact mapping
2. Infrastructure damage point layer
3. River gauge integration (workaround: separate Charts)
4. Aerial photography sourcing

**Effort:** ~3-4 weeks
**Impact:** Medium-high (human scale, spatial coverage)
**Resources:** Data sourcing + GIS, photography licensing negotiation

---

### Priority 3 (Aspirational):
1. Animated satellite loop
2. 1967 flood comparison
3. Policy timeline dashboard
4. Real-time integration

**Effort:** 4-8+ weeks
**Impact:** Variable (3.1 high, 3.2 medium, 3.3 medium, 3.4 very high for long-term)
**Resources:** Video production, archival research, API engineering

---

## Custom Component Extensions

The story would benefit from VEDA-UI extensions not currently available:

### 1. FlagCard Component

**Current limitation:** No built-in component for key event milestones.
**Workaround:** Use wide Prose blocks with styled borders and icons (CSS).
**Enhancement:** Custom React component showing:
- Icon (event type: storm, evacuation, policy)
- Date
- Title + description
- Status badge (completed, ongoing, pending)
- Link to source/documentation

---

### 2. Interactive Map Popups with Charts

**Current limitation:** Map component popups are text-only.
**Workaround:** Separate charts below map, indexed by station name.
**Enhancement:** Click gauges on map → mini-chart appears in popup, showing 30-day hydrograph for that station.
**Technical:** Requires custom deckgl layer or Mapbox popup with embedded Vega-Lite.

---

### 3. Timeline Widget

**Current limitation:** No dedicated timeline component for storm sequence.
**Workaround:** Use Table component with dates, or prose narrative with embedded dates.
**Enhancement:** Interactive timeline showing:
- Event dots on axis (date)
- Vertical hover details
- Highlighted periods (storm events, peak flood, recovery)
- Data overlay (discharge, rainfall, wind speed on timeline)

---

### 4. Animated Map Time-Slider

**Current limitation:** ScrollytellingBlock updates layer instantly; no smooth transition.
**Enhancement:** Map shows daily progression of flood extent with play/pause/slider controls. Readers can manually step through time or auto-play animation.
**Technical:** Requires custom MapGL layer rendering with temporal indexing.

---

## Summary Table: Content Gaps

| Gap | Impact | Feasibility | Timeline | Priority | Status |
|-----|--------|-------------|----------|----------|--------|
| Seasonal baseline flood extent | High | HIGH | 1-2 wks | 1 | BUILDABLE |
| Multi-date Sentinel-2 RGB | High | HIGH | 3-5 days | 1 | BUILDABLE |
| NDWI time series | Medium | HIGH | 1 day | 1 | BUILDABLE |
| MSLP synoptic + wind barbs | Medium | MEDIUM | 2-3 days | 1 | BUILDABLE |
| Evacuation timeline chart | Medium | HIGH | 1 day | 1 | BUILDABLE |
| Agricultural impact mapping | Medium | MEDIUM | 2-3 wks | 2 | BUILDABLE |
| Infrastructure damage layer | Medium | MEDIUM | 3 wks | 2 | BUILDABLE |
| River gauge integration | Medium | MEDIUM | 1 wk | 2 | BUILDABLE |
| Aerial photography | High | MEDIUM | 2-3 wks | 2 | BUILDABLE |
| Climate attribution viz | Medium | MEDIUM | 2-3 wks | 2 | BUILDABLE |
| Animated timeseries | High | MEDIUM | 2-3 wks | 3 | ASPIRATIONAL |
| 1967 flood comparison | Medium | LOW | 3-4 wks | 3 | ASPIRATIONAL |
| Policy timeline dashboard | Medium | HIGH | 1 wk | 3 | BUILDABLE |
| Real-time integration | Very High | LOW | 8-12 wks | 3 | ASPIRATIONAL |

---

## Implementation Roadmap

### **Phase 1: Narrative Completeness (Weeks 1-3)**
Focus on gaps that enhance existing chapters without major new development.

**Deliverables:**
- Seasonal baseline layer (enables Chapter 7 comparison)
- Multi-date Sentinel-2 gallery (strengthens visual narrative)
- NDWI time series (adds scientific depth)
- Synoptic map (illustrates Storm Kristin meteorology)
- Evacuation chart (quantifies human impact)

**Story impact:** 60% → 85% completeness

---

### **Phase 2: Human-Scale Enhancement (Weeks 4-6)**
Add spatial and photographic elements that ground story in real communities.

**Deliverables:**
- Agricultural impact mapping
- Infrastructure damage layer
- Aerial photography integration
- River gauge interactive map (workaround)
- Policy timeline dashboard

**Story impact:** 85% → 95% completeness

---

### **Phase 3: Long-Term Value (Weeks 7+)**
Develop features that enable future disaster documentation and real-time monitoring.

**Deliverables:**
- Animated satellite loop (proof of concept)
- 1967 flood comparison (historical context)
- Real-time integration architecture (future phases)
- Custom VEDA-UI extensions (if major investment justified)

**Story impact:** 95% → 100%+ (extensibility)

---

## Estimated Total Development Effort

**Current state (MVP):** ~2 weeks (story written, core maps/charts functional)

**Phase 1:** +3 weeks = 5 weeks total
**Phase 2:** +4 weeks = 9 weeks total
**Phase 3:** +6-10 weeks = 15-19 weeks total

**Full deployment timeline:** 3-5 months (with parallel work streams)

---

## Content Quality Assurance Checklist

Before publishing, verify:

- [ ] All VEDA-UI components render correctly on mobile, tablet, desktop
- [ ] Attribution complete for all data sources (Copernicus, IPMA, SNIRH, Open-Meteo, etc.)
- [ ] Chart/table data validated against source documents
- [ ] Map layers load without errors; legends display correctly
- [ ] Imagery optimized for web (max 5 MB per JPEG, 2 MB per PNG)
- [ ] Colorblindness: All colormaps tested (Deuteranopia especially for flood extent)
- [ ] Accessibility: Alt-text on all images, chart descriptions, captions
- [ ] Factual accuracy: Numbers/dates verified against sources
- [ ] External links tested (Copernicus EMS, IPMA, SNIRH, WWA)
- [ ] Mobile performance: Page load <3 seconds on 4G, no layout shifts
- [ ] Metadata complete: Front matter YAML valid, geographic bounds correct

---

## Long-Term Vision

The completed cheias-extended-story with all gap-fillings becomes:

1. **Educational resource:** School curricula on climate extremes, flood hydrology, climate attribution
2. **Policy tool:** Evidence base for EU Floods Directive implementation in Portugal
3. **Operational platform:** Integration with Proteção Civil and APA for real-time flood monitoring
4. **Replicable template:** Other nations (Spain, Italy, Greece) could adapt for their flood events
5. **Living document:** Updated annually as new events occur; becomes multi-event platform

This is the dream for cheias.pt: not a one-off story, but a **foundational platform for Portugal's climate adaptation narrative**, renewed and extended with each seasonal cycle.

---

**Document prepared:** March 5, 2026
**Gap analysis version:** 1.0
**Next review:** After Phase 1 completion (Week 3)
