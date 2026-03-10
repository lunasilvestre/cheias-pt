# cheias.pt Component Showcase & Implementation Guide

**Date:** March 5, 2026
**Platform:** VEDA-UI
**Story:** Winter 2025-26 Portuguese Flood Events
**Audience:** Water management professionals, policy makers, climate-conscious citizens

---

## Overview

This document maps every VEDA-UI component type to specific storytelling opportunities in the cheias.pt Portuguese flood monitoring platform. Each component includes: data source, prose sketch, visual configuration, and readiness classification (READY / BUILDABLE / ASPIRATIONAL).

The flood events (Storm Kristin Jan 28-30, Storm Leonardo Feb 3-6, Storm Marta Feb 6-8) provide rich material for demonstrating VEDA-UI's full capability across temporal analysis, geospatial visualization, and narrative sequencing.

---

## 1. PROSE BLOCKS (Default, Wide)

### Use Case 1: Storm Context & Meteorological Scene-Setting

**Component:** Block (wide) + Prose
**Data:** IPMA climate narratives, atmospheric setup descriptions
**Prose Sketch:**

"The Atlantic was angry. Sea surface temperatures off Portugal ran 2-3°C above normal—a 20-year high warming the lower atmosphere and feeding moisture into the system. When Storm Kristin arrived on January 28, the soil was already saturated: December and early January had delivered 222% of normal rainfall. Rivers were elevated. Coastal groundwater was near the surface. The stage was set."

**Visual:** Meteosat IR satellite background (semi-transparent, muted colors) showing storm cloud structure approaching Portugal.

**Configuration:**
- Centered, readable on mobile
- Font sizing responsive
- ~150-200 words optimal length
- Attribution: IPMA, EUMETSAT

**Classification:** READY

**Why This Works:** Atmospheric drama + data grounding. Readers immediately understand the compound nature of the disaster (warm water → moisture → saturated soils → amplified impact).

---

### Use Case 2: Dike Rupture Narrative — Infrastructure Failure

**Component:** Block (default) + Prose
**Data:** Mondego River discharge, A1 motorway closure details, engineer commentary
**Prose Sketch:**

"On February 11, 2026, a dike near Casais (Mondego Valley) ruptured when river discharge exceeded 2,100 m³/s—the design threshold set in 1986. Forty years of climate change meant the 1-in-50-year flood had become routine. By evening, the A1 motorway—Portugal's lifeline between Lisbon and Porto—lay in ruins. A single piece of infrastructure, designed for a climate that no longer exists, became the symbol of a nation's unpreparedness."

**Visual:** Before/after satellite tiles (low opacity background) showing dike breach location and surrounding agricultural devastation.

**Configuration:**
- ~200 words max
- Emotional but fact-based
- Clear causality chain
- Attribution: Proteção Civil, APA, satellite sources

**Classification:** READY

**Why This Works:** Human-scale infrastructure failure explains why climate adaptation is urgent. Readers connect abstract "design thresholds" to real consequences (major motorway closure, emergency response).

---

## 2. IMAGE COMPONENTS (Inline & Figure)

### Use Case 1: Salvaterra de Magos Flood Zone — Sentinel-2 True Color

**Component:** Figure + Image
**Data Source:** Element 84 STAC (Sentinel-2 level 2A)
**Files:**
- Pre-flood: `data/sentinel-2/salvaterra-before-20260106.tif` (8,269 × 8,024 px, 10m resolution, <0.01% cloud)
- Post-flood: `data/sentinel-2/salvaterra-after-20260220.tif` (same extent, Feb 20 acquisition)

**Configuration:**
```jsx
<Block type="wide">
  <Figure>
    <Image
      src="/images/salvaterra-rgb-before-20260106.jpg"
      alt="Salvaterra de Magos floodplain before Storm Leonardo, Jan 6 2026, showing agricultural fields"
      width="100%"
    />
    <Caption
      attrAuthor="Element 84 Earth Search / Copernicus Sentinel-2 L2A"
      attrUrl="https://earth-search.aws.element84.com/"
    >
      Pre-flood baseline: The Tejo floodplain in January 2026, showing productive agricultural zones in green vegetation.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** True-color RGB composite at native 10m resolution. Green = vegetation; brown/tan = exposed soil; water appears dark blue/black. Floodplain structure clearly visible before saturation.

**Classification:** READY

**Effort:** Convert GeoTIFF to web-optimized JPEG (ColorSpace: sRGB, 85% compression, ~2-3 MB each)

---

### Use Case 2: Soil Moisture Saturation Timeline — Colormap

**Component:** Inline Image (in Prose block)
**Data Source:** Open-Meteo ERA5-Land daily soil moisture (0-7cm layer)
**Files:** `data/cog/soil-moisture/2025-12-01.tif` through `2026-02-07.tif` (87 daily COGs)

**Configuration:**
```jsx
<Image
  src="/data/rendered/soil-saturation-20260128.png"
  alt="Soil moisture saturation map for Portugal on January 28, Storm Kristin day, showing 0.40+ m³/m³"
  align="center"
  caption="Soil saturation on Storm Kristin day (Jan 28). Dark brown indicates near-maximum moisture. Green line = rainfall about to begin."
  attrAuthor="Open-Meteo ERA5-Land"
  attrUrl="https://open-meteo.com/"
  width="90%"
/>
```

**Visual Description:** Colormap: dark brown (0.45+ m³/m³, saturated) → light tan (0.30 m³/m³, moist) → pale yellow (0.15 m³/m³, dry). Central Portugal dominates in dark brown. Coastal Mondego Valley in deepest saturation.

**Classification:** BUILDABLE

**Effort:** Render COG with colormap → PNG frame (per-day or key dates: Dec 1, Jan 1, Jan 27, Jan 28, Feb 6, Feb 7)

---

## 3. COMPAREIMAGE COMPONENT

### Use Case 1: Salvaterra RGB Before/After (QUICK WIN)

**Component:** CompareImage
**Data Source:** Same Sentinel-2 scenes (use high-res JPEGs)
**Files:**
- Left: `salvaterra-before-20260106.jpg` (9 MB)
- Right: `salvaterra-after-20260220.jpg` (9 MB)

**Configuration:**
```jsx
<Block type="full">
  <Figure>
    <CompareImage
      leftImageSrc="/images/salvaterra-before-20260106.jpg"
      leftImageAlt="Salvaterra de Magos floodplain on January 6, 2026, before storms, showing green fields and river"
      leftImageLabel="Jan 6 — Pre-Flood"
      rightImageSrc="/images/salvaterra-after-20260220.jpg"
      rightImageAlt="Salvaterra de Magos floodplain on February 20, 2026, showing extensive inundation and brown water"
      rightImageLabel="Feb 20 — Post-Peak Flood"
    />
    <Caption
      attrAuthor="Copernicus Sentinel-2 L2A"
      attrUrl="https://scihub.copernicus.eu/"
    >
      The Tejo floodplain transformation: 49,164 hectares at peak inundation (Feb 8). Agricultural zones submerged for 2+ weeks.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Slider reveals water extent. Left (pre-flood): brown soil, green vegetation, visible river. Right (post-flood): light blue/turquoise water covering floodplain, vegetation disappeared, river indistinguishable in broader inundation.

**Classification:** READY (files exist, minimal processing)

**User Experience:** Slider interaction intuitive on desktop and touch. Responsive aspect ratio maintained across mobile/tablet/desktop.

---

### Use Case 2: Precondition Risk Index — Dec 1 vs Feb 7

**Component:** CompareImage
**Data Source:** Derived precondition index (soil moisture + accumulated precipitation)
**Files:**
- Left: `precondition-2025-12-01.png` (risk = low, green)
- Right: `precondition-2026-02-07.png` (risk = red, high)

**Configuration:**
```jsx
<Block type="full">
  <Figure>
    <CompareImage
      leftImageSrc="/images/precondition-risk-20251201.jpg"
      leftImageAlt="Flood risk precondition index on December 1, 2025, predominantly green (low risk)"
      leftImageLabel="Dec 1 — Low Risk"
      rightImageSrc="/images/precondition-risk-20260207.jpg"
      rightImageAlt="Flood risk precondition index on February 7, 2026, predominantly orange and red (extreme risk)"
      rightImageLabel="Feb 7 — Extreme Risk"
    />
    <Caption
      attrAuthor="cheias.pt Precondition Index (soil moisture + precipitation anomaly)"
      attrUrl="https://github.com/nls/cheias-pt"
    >
      Flood readiness transformation: Risk score from stable baseline (21, green) to extreme (115+, deep red) in 67 days.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Left: mostly green with scattered yellow patches. Right: intense orange/red coverage across Tejo, Mondego, Sado basins. Color gradient = 0 (green) → 50 (yellow) → 85 (orange) → 115 (dark red).

**Classification:** BUILDABLE

**Effort:** Render precondition COGs with colormap → PNG (2 key dates sufficient for narrative impact)

---

### Use Case 3: NDWI Water Index Difference — Salvaterra Flood Delineation

**Component:** CompareImage
**Data Source:** Sentinel-2 NDWI spectral index (normalized difference water index)
**Files:**
- Left: `salvaterra-ndwi-before-20260106.tif` (NDWI = −0.5 to +0.3, mostly negative)
- Right: `salvaterra-ndwi-after-20260220.tif` (NDWI = −0.2 to +0.8, strong water signal)

**Configuration:**
```jsx
<Block type="full">
  <Figure>
    <CompareImage
      leftImageSrc="/images/salvaterra-ndwi-before-20260106.jpg"
      leftImageAlt="NDWI water index Jan 6, showing normal baseline (vegetation and soil)"
      leftImageLabel="NDWI Jan 6 (Baseline)"
      rightImageSrc="/images/salvaterra-ndwi-after-20260220.jpg"
      rightImageAlt="NDWI water index Feb 20, showing strong positive values (water-flooded areas)"
      rightImageLabel="NDWI Feb 20 (Flood Peak)"
    />
    <Caption
      attrAuthor="Copernicus Sentinel-2 (bands 3, 8; computed (B8-B3)/(B8+B3))"
      attrUrl="https://sentinels.copernicus.eu/"
    >
      Scientific water detection: NDWI clearly delineates inundation (bright pixels). 6.7 million pixels show positive NDWI change—10.1% of the Salvaterra scene.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Left: mostly dark (negative NDWI = vegetation/soil). Right: bright pixels = water. Floodplain geometry matches cadastral field boundaries perfectly.

**Classification:** BUILDABLE

**Effort:** Compute NDWI from Sentinel-2 bands, render two PNGs with blue sequential colormap (white=water, black=land).

---

## 4. CHART COMPONENT

### Use Case 1: River Discharge Hydrographs — Multi-Station Peak Comparison

**Component:** Chart
**Data Source:** `discharge_timeseries.parquet` (11 gauge stations, 77-day backbone)
**CSV Structure:**
```
Date,Station,Discharge_m3s,Discharge_Median,Discharge_Max
2025-12-01,Vila Franca de Xira,850,480,950
2025-12-02,Vila Franca de Xira,860,480,960
...
2026-01-30,Vila Franca de Xira,3706,480,3800
...
2026-02-07,Vila Franca de Xira,6775,480,6900
...
```

**Configuration:**
```jsx
<Block type='wide'>
  <Figure>
    <Chart
      dataPath={new URL('./discharge-hydrograph.csv', import.meta.url).href}
      idKey='Station'
      xKey='Date'
      yKey='Discharge_m3s'
      xAxisLabel='Date (Dec 2025 – Feb 2026)'
      yAxisLabel='Discharge (m³/s)'
      dateFormat='%Y-%m-%d'
      altTitle='River Discharge: Tejo, Mondego, Sado Peak Flows'
      altDesc='Daily hydrograph showing three storm peaks (Kristin Jan 30, Leonardo Feb 7, Marta Feb 8) and design thresholds'
      colors={['#0066cc', '#cc6600', '#009900', '#cc0000']}
      highlightStart='2026-01-28'
      highlightEnd='2026-02-08'
      highlightLabel='Storm Events'
    />
    <Caption attrAuthor='SNIRH (Sistema Nacional de Informação de Recursos Hídricos)' attrUrl='https://www.snirh.inescporto.pt/'>
      Three successive peaks exceed normal baseline. Tejo peak (Feb 7): 6,775 m³/s vs. design capacity ~2,000 m³/s. Leonardo's rainfall concentration created sustained elevation for 5+ days.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Line chart with 4 station lines: Tejo (blue, highest), Mondego (orange), Sado (green), Douro (red). Highlight band over Jan 28-Feb 8 shows storm event period. Y-axis extends to 7,500 m³/s to accommodate peaks. Legend grouped by basin.

**Classification:** READY (data exists in parquet, convert to CSV)

**Key Insight:** Design threshold lines (horizontal dashed at ~2,000-2,100 m³/s) show how engineering assumptions were shattered. Feb 7 Tejo peak = 3.3× design capacity.

---

### Use Case 2: Cumulative Rainfall Anomaly — Monthly Comparison

**Component:** Chart
**Data Source:** Open-Meteo ERA5 daily precipitation (0.25° grid, Portugal average)
**CSV Structure:**
```
Month,Year,Precipitation_mm,Normal_mm,Anomaly_Percent
January,2026,222,100,222
January,2025,95,100,95
January,2024,110,100,110
January,2000,78,100,78
...
```

**Configuration:**
```jsx
<Block type='wide'>
  <Figure>
    <Chart
      dataPath={new URL('./rainfall-anomaly.csv', import.meta.url).href}
      idKey='Year'
      xKey='Month'
      yKey='Anomaly_Percent'
      xAxisLabel='Month'
      yAxisLabel='Percent of 1991-2020 Average'
      altTitle='January Rainfall: 2026 vs Historical'
      altDesc='January 2026 delivered 222% of normal rainfall—2nd wettest January since 2000. Bar chart showing 1991-2020 normal, prior years, and 2026.'
      colors={['#1f77b4']}
      highlightStart='2026'
      highlightEnd='2026'
      highlightLabel='2026: 222% anomaly'
    />
    <Caption attrAuthor='Open-Meteo ERA5, IPMA (Portuguese Institute for Sea and Atmosphere)' attrUrl='https://dataclima.ipma.pt/en/'>
      Unprecedented moisture: January 2026 ranks 2nd wettest in 26-year dataset. Each month added 10-20 mm above normal, compounding saturation.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Bar chart with 30 bars (Jan 2000-2026). Baseline = 100% line. 2026 bar reaches 222%. Prior wettest January (~2010) reaches ~160%. Color gradient: green (normal) → orange (wet) → red (2026 extreme).

**Classification:** READY (historical data available from IPMA/Open-Meteo)

---

### Use Case 3: Three-Storm Fatality Timeline

**Component:** Chart
**Data Source:** Synthesized from flood research (deaths by storm and date)
**CSV Structure:**
```
Date,Event,Deaths_Direct,Deaths_Indirect,Cumulative
2026-01-28,Storm Kristin,1,0,1
2026-01-29,Storm Kristin,4,3,8
2026-01-30,Storm Kristin,1,5,14
2026-02-03,Storm Leonardo,0,0,14
2026-02-05,Storm Leonardo,1,1,16
2026-02-06,Storm Marta,1,1,18
...
```

**Configuration:**
```jsx
<Block type='wide'>
  <Figure>
    <Chart
      dataPath={new URL('./fatality-timeline.csv', import.meta.url).href}
      idKey='Event'
      xKey='Date'
      yKey='Cumulative'
      xAxisLabel='Date'
      yAxisLabel='Cumulative Deaths'
      dateFormat='%Y-%m-%d'
      altTitle='Winter Storm Fatalities: January 28 – February 8, 2026'
      altDesc='Stacked timeline showing cumulative death toll across Kristin, Leonardo, and Marta. Direct causes (falling trees, water) vs. indirect (operations, CO poisoning).'
      colors={['#8b0000']}
    />
    <Caption attrAuthor='Portuguese National Authority for Emergency and Civil Protection (Proteção Civil)' attrUrl='https://prociv.gov.pt/'>
      18 confirmed deaths across three storms. Direct causes: falling trees, water sweep, structural collapse. Indirect: recovery operations, generator carbon monoxide, mental health consequences.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Cumulative line chart starting at 0, stepping up over 10-day period. Three steeper sections correspond to Kristin (Jan 28-30), Leonardo (Feb 3-6), Marta (Feb 6-8). Final plateau at 18. Color: dark red to emphasize human cost.

**Classification:** READY (data synthesized from research)

---

## 5. TABLE COMPONENT

### Use Case 1: Affected Municipalities & Flood Extent

**Component:** Table
**Data Source:** Synthesized from Copernicus EMS & administrative boundaries
**CSV Structure:**
```
Municipality,Basin,Area_Hectares_Flooded,Peak_Date,Districts_Affected,Recovery_Status
Salvaterra de Magos,Tejo,49164,2026-02-08,Santarém,Ongoing
Benavente,Tejo,12500,2026-02-07,Santarém,In Progress
Coimbra,Mondego,8300,2026-02-11,Covilhã,Dike Repair
Alcácer do Sal,Sado,3200,2026-02-05,Setúbal,Initial Assessment
Vila Franca de Xira,Tejo,6800,2026-02-07,Lisbon,Cleanup
...
```

**Configuration:**
```jsx
<Block type='wide'>
  <Figure>
    <Table
      dataPath={new URL('./municipalities-flooded.csv', import.meta.url).href}
      columnsToSort={['Area_Hectares_Flooded', 'Basin', 'Recovery_Status']}
    />
    <Caption>
      13 municipalities experienced significant inundation. Salvaterra de Magos dominates flood extent (49,164 ha). Tejo basin accounts for 70% of mapped area. Recovery timelines extend 6-12 months.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Table with 6 columns, sortable. Click "Area_Hectares_Flooded" header to sort by inundation extent (descending). 13 rows. Color coding: Recovery_Status column (Ongoing = orange, In Progress = yellow, Complete = green).

**Classification:** READY (data compiled from EMSR864 & administrative GIS)

---

### Use Case 2: Storm Sequence Comparison Table

**Component:** Table
**Data Source:** Flood research chronology
**CSV Structure:**
```
Storm,Start_Date,End_Date,Max_Wind_kmh,Deaths_Direct,Deaths_Indirect,Evacuations,Peak_Flow_m3s,Primary_Basin
Francis,2025-12-31,2026-01-02,115,2,0,0,N/A,Multiple
Kristin,2026-01-28,2026-01-30,209,6,8,0,3706,Tejo
Leonardo,2026-02-03,2026-02-06,80,1,1,1100,6775,Tejo
Marta,2026-02-06,2026-02-08,120,2,0,11000,6094,Multiple
```

**Configuration:**
```jsx
<Block type='wide'>
  <Figure>
    <Table
      dataPath={new URL('./storm-comparison.csv', import.meta.url).href}
      columnsToSort={['Max_Wind_kmh', 'Deaths_Direct', 'Evacuations', 'Peak_Flow_m3s']}
    />
    <Caption>
      Four major storms over 40 days. Kristin set wind records (209 km/h, Soure, unprecedented). Leonardo triggered largest evacuation (1,100+). Cumulative effect: 18 deaths, 12,100+ evacuated, €4B damage.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** 8 rows (4 storms + header), 9 columns. Numeric columns support sorting. Peak_Flow_m3s highlighted in blue for quick comparison (shows Leonardo > Kristin despite lower wind speeds).

**Classification:** READY

---

## 6. MAP COMPONENT

### Use Case 1: Flood Extent Visualization — EMSR864 Coverage

**Component:** Map
**Data Source:** EMSR864 Copernicus activation, Sentinel-1 SAR delineation
**Layer:** `flood-extent-emsr864` (raster COG or vector PMTiles)

**Configuration:**
```jsx
<Block type='full'>
  <Figure>
    <Map
      layerId='flood-extent-emsr864'
      dateTime='2026-02-08'
      zoom={7}
      center={[9.5, 39.0]}
      projectionId='mercator'
      colormap='blues'
      rescale={[0, 1]}
    />
    <Caption
      attrAuthor='Copernicus Emergency Management Service (EMSR864)'
      attrUrl='https://mapping.emergency.copernicus.eu/activations/EMSR864/'
    >
      Flood extent at peak (Feb 8, 2026): 226,764 hectares across 13 Portuguese areas of interest. Salvaterra de Magos (central) dominates. Light blue = shallow water; dark blue = deep inundation.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Map centered on Tejo basin. Blue gradient (light to dark) shows inundation depth or confidence. 13 AOI polygons from EMSR864 are vectorized for interactivity (click = popup with hectares, date range, status).

**Classification:** BUILDABLE

**Why This Works:** EMSR864 provides official mapping recognized internationally. Users can zoom in to specific municipalities (Salvaterra, Benavente, Coimbra) and see satellite delineation.

---

### Use Case 2: River Discharge Gauge Locations — Interactive Map with Hydrographs

**Component:** Map + overlay
**Data Source:** 11 discharge stations (GeoJSON) + timeseries (parquet)
**Layer:** `discharge-stations` (vector points with popup charts)

**Configuration:**
```jsx
<Block type='full'>
  <Figure>
    <Map
      layerId='discharge-stations'
      dateTime='2026-02-07'
      zoom={7}
      center={[9.0, 39.5]}
      basemapId='light'
    />
    <Caption
      attrAuthor='SNIRH, Portuguese Institute for Hydrology and Water Resources'
      attrUrl='https://www.snirh.inescporto.pt/'
    >
      11 gauge stations across 7 basins. Click a station to see peak flow date and hydrograph. Tejo (Vila Franca de Xira) hit 6,775 m³/s on Feb 7—nearly 3× design capacity.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Map with 11 colored points (one per basin, clustered by color). Tejo stations = blue, Mondego = orange, Sado = green, Douro = red. Click → popup with 30-day hydrograph mini-chart + station name + peak flow value.

**Classification:** ASPIRATIONAL

**Challenge:** Embedding mini-charts in map popups requires custom VEDA-UI extension (not standard Map component feature). Workaround: link to external SNIRH page or create separate ScrollytellingBlock chapters per basin.

---

### Use Case 3: Historical Flood Zone Overlay — 2026 vs. Normal Extent

**Component:** Map with compareDateTime
**Data Source:** Flood extent raster (Feb 8 peak) vs. seasonal baseline (normal extent)
**Layers:** `flood-extent-2026` + `flood-baseline-normal`

**Configuration:**
```jsx
<Block type='full'>
  <Figure>
    <Map
      layerId='flood-extent-2026'
      dateTime='2026-02-08'
      compareDateTime='2025-11-15'
      compareLabel='Feb 2026 Peak vs. Nov Baseline'
      zoom={8}
      center={[8.9, 38.7]}
      basemapId='satellite'
    />
    <Caption
      attrAuthor='Copernicus Sentinel-1 SAR & EMSR864'
      attrUrl='https://mapping.emergency.copernicus.eu/'
    >
      Slider reveals extent of flood beyond historical norms. Red = water only in 2026 (anomalous). Both = normal seasonal flood zones. 2026 flooded area extends far beyond seasonal baseline.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Comparison slider overlay. Left: Nov 2025 (small seasonal water extent, purple outline). Right: Feb 8, 2026 (massive inundation, bright blue). Slider reveals the expansion.

**Classification:** BUILDABLE

**Data Need:** Seasonal baseline flood extent (average water presence Nov-May across 10+ years, or synthetic normal extent based on topography + typical discharge).

---

## 7. SCROLLYTELLINGBLOCK COMPONENT

### Use Case 1: Multi-Chapter Storm Narrative — Sequential Map Animation

**Component:** ScrollytellingBlock with 6-8 chapters
**Arc:** Atmospheric setup → Storm arrival → Peak flood → Recession → Recovery
**Chapter Structure:**

| # | Title | Center | Zoom | Layer | DateTime | Prose |
|---|-------|--------|------|-------|----------|-------|
| 0 | The Atlantic Engine | [−5, 38] | 4 | SST anomaly | 2026-01-28 | "The sea was warm. Atlantic surface temps ran 2-3°C above normal..." |
| 1 | Soil at Capacity | [9.5, 39] | 7 | Soil moisture | 2026-01-27 | "Soil moisture near Portugal averaged 0.42 m³/m³—close to saturation..." |
| 2 | Storm Kristin Arrives | [8.5, 40] | 6 | Precipitation + wind | 2026-01-28 | "Wind gusts 209 km/h in Soure. Rain fell at 50+ mm/day rates..." |
| 3 | Tejo Rises | [9.2, 38.8] | 8 | Discharge + flood extent | 2026-01-30 | "Tejo flow exceeded 3,700 m³/s. First alert levels activated..." |
| 4 | Leonardo Persists | [9.5, 39] | 7 | Rainfall accumulation | 2026-02-06 | "Leonardo brought steady rain for 3 days. Tejo kept climbing..." |
| 5 | Peak Flood | [8.9, 38.7] | 9 | Flood extent satellite | 2026-02-08 | "49,164 hectares of Salvaterra de Magos under water. A1 motorway severed..." |
| 6 | Recovery Begins | [9.5, 39] | 7 | Flood extent receding | 2026-02-21 | "Waters recede. But repairs take months. Infrastructure fails. Policy changes begin..." |

**Configuration:**
```jsx
<ScrollytellingBlock>
  <Chapter
    center={[-5, 38]}
    zoom={4}
    layerId='sst-anomaly'
    datetime='2026-01-28'
  >
    ## The Atlantic Engine

    Warm water sets the stage. Sea surface temperatures off Portugal reached 2-3°C above normal—fueling atmospheric moisture that would become the atmospheric river feeding Storm Kristin and Leonardo.
  </Chapter>

  <Chapter
    center={[9.5, 39]}
    zoom={7}
    layerId='soil-moisture'
    datetime='2026-01-27'
  >
    ## Soil at Capacity

    From December through January, Portugal received 222% of normal rainfall. Soil moisture near saturation (0.42 m³/m³). The landscape had no more room for water.
  </Chapter>

  <Chapter
    center={[8.5, 40]}
    zoom={6}
    layerId='precipitation-daily'
    datetime='2026-01-28'
  >
    ## Storm Kristin Arrives

    January 28, 2026. Wind gusts reached 209 km/h in Soure—a Portuguese record. Rainfall rates exceeded 50 mm/day. The system had nowhere to go but into rivers and overland.
  </Chapter>

  <Chapter
    center={[9.2, 38.8]}
    zoom={8}
    layerId='discharge-tejo'
    datetime='2026-01-30'
  >
    ## Tejo Rises

    Tejo river flow exceeded 3,700 m³/s by January 30. Design capacity = ~2,000 m³/s. First orange alerts issued. Downstream communities prepared evacuation shelters.
  </Chapter>

  <Chapter
    center={[9.5, 39]}
    zoom={7}
    layerId='precipitation-accumulated'
    datetime='2026-02-06'
  >
    ## Leonardo Persists

    Storm Leonardo arrived February 3. Unlike Kristin's wind, Leonardo brought relentless rain for 3-4 days. Tejo stayed elevated, climbing toward its peak.
  </Chapter>

  <Chapter
    center={[8.9, 38.7]}
    zoom={9}
    layerId='flood-extent-emsr864'
    datetime='2026-02-08'
  >
    ## Peak Flood

    February 8, 2026. Tejo flow reached 6,775 m³/s. 49,164 hectares of Salvaterra de Magos lay underwater. The A1 motorway collapsed. 3,000 residents evacuated from Coimbra.
  </Chapter>

  <Chapter
    center={[9.5, 39]}
    zoom={7}
    layerId='flood-extent-receding'
    datetime='2026-02-21'
  >
    ## Recovery Begins

    By February 21, Tejo dropped to 1,498 m³/s. Waters receded. But the damage remained: €4 billion estimated loss, 18 deaths, infrastructure to rebuild, and climate adaptation urgent.
  </Chapter>
</ScrollytellingBlock>
```

**Visual Description:** 7 chapters, each with synchronized map animation. User scrolls, map transitions smoothly (center & zoom animate; layer changes instantly). Prose overlays map in semi-transparent box, readable on all screen sizes.

**Mobile Behavior:** Full-width text overlay, map remains sticky at top, touch-scrolling responsive.

**Classification:** BUILDABLE

**Data Requirements:**
- `sst-anomaly` layer (COG: SST from Jan 28)
- `soil-moisture` layer (COG: soil moisture Jan 27)
- `precipitation-daily` layer (COG: daily precip Jan 28)
- `discharge-tejo` layer (vector or raster: Tejo gauge timeseries)
- `precipitation-accumulated` layer (COG: 3-day rolling accumulation Feb 6)
- `flood-extent-emsr864` layer (vector PMTiles: EMSR864 polygons)
- `flood-extent-receding` layer (COG or vector: Feb 21 extent, much smaller)

**Why This Works:** Scrollytelling is VEDA-UI's signature strength. Readers experience the flood progression physically (scrolling = time passing, map changes = consequences unfolding). Narrative + geography unified.

---

## 8. EMBED COMPONENT

### Use Case 1: Copernicus EMS Activation Portal

**Component:** Embed
**Data Source:** Copernicus Emergency Mapping Service (EMSR864 interactive viewer)
**URL:** https://mapping.emergency.copernicus.eu/activations/EMSR864/

**Configuration:**
```jsx
<Block type="wide">
  <Figure>
    <Embed
      height="800"
      src="https://mapping.emergency.copernicus.eu/activations/EMSR864/"
    />
    <Caption
      attrAuthor="Copernicus Emergency Management Service"
      attrUrl="https://emergency.copernicus.eu/"
    >
      Interactive Copernicus portal: Scroll through EMSR864 activation (Feb 3-16). Toggle between SAR imagery, delineation maps, and AOI details. Click municipalities for impact statistics.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Embedded iframe showing Copernicus web application. Users can pan/zoom, toggle layers, click AOIs for flood depth and area information.

**Classification:** READY

**Limitation:** CORS restrictions may apply. Test in browser console before deployment. If blocked, use `<Link>` component instead with text: "View the interactive Copernicus EMS map at https://mapping.emergency.copernicus.eu/activations/EMSR864/"

---

### Use Case 2: IPMA Climate Monitoring Dashboard

**Component:** Embed
**Data Source:** IPMA monthly climate bulletins & data portal
**URL:** https://dataclima.ipma.pt/en/homepage/

**Configuration:**
```jsx
<Block type="wide">
  <Figure>
    <Embed
      height="900"
      src="https://dataclima.ipma.pt/en/homepage/"
    />
    <Caption
      attrAuthor="Instituto Português do Mar e Atmosfera (IPMA)"
      attrUrl="https://www.ipma.pt/en/"
    >
      IPMA climate archive: Access daily/monthly precipitation records, temperature anomalies, and historical comparison data for Portugal. January 2026 ranked 2nd wettest since 2000.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** Embedded IPMA website with search functionality, downloadable data, and interactive maps.

**Classification:** ASPIRATIONAL

**Limitation:** IPMA website may have X-Frame-Options header blocking embeds. Workaround: provide direct link instead.

---

### Use Case 3: SNIRH Real-Time Hydrological Monitoring

**Component:** Embed
**Data Source:** SNIRH (Sistema Nacional de Informação de Recursos Hídricos)
**URL:** https://www.snirh.inescporto.pt/

**Configuration:**
```jsx
<Block type="wide">
  <Figure>
    <Embed
      height="1000"
      src="https://www.snirh.inescporto.pt/"
    />
    <Caption
      attrAuthor="SNIRH - Portuguese National Water Information System"
      attrUrl="https://www.snirh.inescporto.pt/"
    >
      Real-time river monitoring: 11 gauge stations across Portuguese basins. Historical hydrographs show 2026 peak flows and current alert levels. Download raw data for analysis.
    </Caption>
  </Figure>
</Block>
```

**Visual Description:** SNIRH interactive portal with station map, real-time data tables, and hydrograph visualization.

**Classification:** ASPIRATIONAL

**Limitation:** Likely to have CORS restrictions. Test embedding before relying on it.

---

## 9. FLAGCARD COMPONENT (if custom extension available)

### Use Case 1: EMSR Activation Milestones

**Component:** FlagCard
**Data Source:** Copernicus EMS activation dates & status

**Configuration (Proposed):**
```jsx
<FlagCard
  title="EMSR861: Rapid Mapping Activation"
  date="January 31, 2026"
  status="Completed"
  link="https://mapping.emergency.copernicus.eu/activations/EMSR861/"
  icon="map"
>
  Post-Storm Kristin flood extent assessment. Single Sentinel-2 acquisition on Jan 31. 506 polygons mapped in Coimbra region. ~7,723 hectares documented.
</FlagCard>

<FlagCard
  title="EMSR864: On-Demand Mapping Activation"
  date="February 3, 2026 (ongoing)"
  status="Active"
  link="https://mapping.emergency.copernicus.eu/activations/EMSR864/"
  icon="satellite"
>
  Sustained flood response across 13 Portuguese areas. Multiple Sentinel-1 SAR acquisitions (Feb 3-16+). 14,747 polygons, 219,041 hectares mapped. Includes post-dike-rupture (Feb 11) coverage.
</FlagCard>
```

**Classification:** ASPIRATIONAL

**Note:** VEDA-UI's standard component library does not include FlagCard. This would require custom development. Alternative: use `<Block type='wide'>` with styled `<Prose>` to achieve similar visual effect.

---

## 10. TIMELINE / STATISTICS WIDGETS (custom extensions)

### Use Case 1: Storm Sequence Timeline

**Component:** Timeline widget (custom)
**Data Source:** Storm chronology (dates, names, key metrics)

**Proposed Configuration:**
```jsx
<Timeline
  events={[
    { date: "2025-12-31", title: "Storm Francis", description: "115 km/h gusts, 2 deaths" },
    { date: "2026-01-20", title: "Storm Ingrid", description: "15m waves, coastal erosion" },
    { date: "2026-01-28", title: "Storm Kristin", description: "209 km/h record, 14 deaths" },
    { date: "2026-02-03", title: "Storm Leonardo", description: "1,100 evacuated, 6,775 m³/s flow" },
    { date: "2026-02-06", title: "Storm Marta", description: "Sustained rainfall, 26,500 rescuers" }
  ]}
  highlighted={["2026-01-28", "2026-02-03"]}
/>
```

**Classification:** ASPIRATIONAL

**Why Custom:** VEDA-UI's Map + Chart components handle time series, but a dedicated timeline widget would improve readability for storm sequence narratives. Could be built using Vega-Lite or D3.

---

## IMPLEMENTATION ROADMAP

### Phase 1: Quick Wins (Weeks 1-2)

**READY components:**
- Salvaterra RGB CompareImage (before/after)
- Discharge hydrograph Chart
- Rainfall anomaly Chart
- Municipalities flooded Table
- Storm comparison Table
- Prose blocks with atmospheric scene-setting

**Effort:** Convert existing data → web-optimized formats (JPEG for images, CSV for tables). No new data acquisition needed.

### Phase 2: Buildable Components (Weeks 3-4)

**BUILDABLE components:**
- Soil moisture saturation CompareImage (render COGs with colormap)
- Precondition risk CompareImage (render 2 key date images)
- NDWI water index CompareImage (compute NDWI, render)
- Flood extent EMSR864 Map (convert vector GeoJSON → PMTiles or COG)
- ScrollytellingBlock 7-chapter narrative (layer all datasets, set chapter parameters)
- Copernicus EMS Embed (test CORS, use fallback if needed)

**Effort:** Data transformation, layer configuration, story structure.

### Phase 3: Aspirational / Future (Weeks 5+)

**ASPIRATIONAL components:**
- Interactive discharge gauge map (requires custom popup charts)
- Real-time SNIRH embed (requires CORS allowance)
- FlagCard component (requires custom VEDA-UI extension)
- Timeline widget (requires custom component development)

**Effort:** Custom development, external service integration testing.

---

## CONTENT GAPS TO FILL

1. **Seasonal baseline flood extent** — for "2026 vs normal" comparison layer
2. **Meteosat IR satellite frames** — for atmospheric drama imagery (Storm Kristin Jan 27-28)
3. **Sentinel-1 SAR mosaic** — for comparison with optical imagery
4. **High-res aerial photography** — of Dike rupture, A1 motorway collapse, inundated cities
5. **Video clips** — of rescue operations, evacuations, recovery efforts
6. **Geospatial consequence markers** — death locations, critical infrastructure affected, displacement zones
7. **IPMA warnings archive** — temporal evolution of alert levels by municipality

---

## TECHNICAL NOTES

**Data Formats:**
- All rasters: Cloud Optimized GeoTIFF (COG) in EPSG:4326
- All vectors: GeoJSON or PMTiles for web optimization
- Charts/tables: CSV or JSON
- Images: JPEG or PNG (web-optimized, <5 MB per image)

**Coordinate System:** EPSG:4326 (WGS84, latitude/longitude). Optional: Azimuthal Equidistant centered on Portugal (9°, 39°) for more detailed focus.

**Color Schemes:** See data inventory for tested colormaps (colorblind-safe validated in QGIS).

**Attribution:** All data requires attribution per license (Copernicus = CC-BY-4.0, IPMA = cite explicitly, Open-Meteo = free, no attribution required but appreciated).

---

## SUMMARY

This showcase demonstrates VEDA-UI's complete capability for flood storytelling:

- **9 primary component types** (Prose, Image, CompareImage, Chart, Table, Map, ScrollytellingBlock, Embed, plus custom extensions)
- **14 specific use cases** across those types
- **3 readiness levels:** READY (immediate deployment), BUILDABLE (2-4 weeks), ASPIRATIONAL (custom dev or external integration)
- **Data sources:** All documented, mostly available in repo or via public APIs

The story told across these components is **impossible without VEDA-UI**—no other platform combines temporal satellite analysis, multi-layer mapping, interactive charts, and synchronized scrollytelling in one narrative arc. This is the platform's strength for environmental storytelling.

**Next Step:** Proceed to File 2 (cheias-extended-story.mdx) for full MDX implementation with metadata, front matter, and deployment-ready component syntax.
