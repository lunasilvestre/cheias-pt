# CEMS Flood Extent Data — Portugal Floods 2026

## Summary

Two Copernicus EMS Rapid Mapping activations cover the Portugal 2026 flood crisis:

| Activation | Event | Date | Total AOIs | PT AOIs with data | Countries |
|------------|-------|------|------------|-------------------|-----------|
| **EMSR861** | Storm Kristin | 2026-01-28 | 27 | 1 (Coimbra) | Portugal, Spain |
| **EMSR864** | Storm Leonardo | 2026-02-03 | 18 | 13 | Portugal, Spain |

Both activations are **still active** (not closed) as of 2026-02-16.

## Output Files

| File | Activation | Polygons | Total Area (ha) | Size |
|------|-----------|----------|-----------------|------|
| `emsr861.geojson` | EMSR861 | 506 | 7,723 | 2.3 MB |
| `emsr864.geojson` | EMSR864 | 14,747 | 219,041 | 120 MB |
| `combined.geojson` | Both | 15,253 | 226,764 | 122 MB |

All GeoJSON files are EPSG:4326 (WGS84) and contain these properties per feature:
- `activation` — EMSR861 or EMSR864
- `aoi` — Area of Interest identifier (e.g. AOI03)
- `locality` — Place name (e.g. Salvaterra de Magos)
- `source_date` — Satellite image acquisition date
- `sensor` — Satellite/sensor used
- `product_type` — Delineation, Monitoring 1, Monitoring 2, etc.
- `storm` — Storm name (Kristin or Leonardo/Marta)
- `area_ha` — Polygon area in hectares (ETRS89-LAEA equal-area projection)
- `event_type`, `obj_desc`, `det_method`, `notation` — CEMS classification fields

## Per-AOI Breakdown

### EMSR861 — Storm Kristin (1 Portuguese AOI)

| AOI | Location | Product | Polygons | Area (ha) |
|-----|----------|---------|----------|-----------|
| AOI05 | Coimbra | Delineation | 506 | 7,723 |

AOI06 (Castelo Branco) was requested but returned no data due to remote sensing limitations.

### EMSR864 — Storm Leonardo/Marta (13 Portuguese AOIs)

| AOI | Location | Product | Polygons | Area (ha) |
|-----|----------|---------|----------|-----------|
| AOI01 | Ermidas Sado | Delineation | 73 | 2,112 |
| AOI01 | Ermidas Sado | Monitoring 1 | 158 | 1,326 |
| AOI01 | Ermidas Sado | Monitoring 2 | 474 | 972 |
| AOI02 | Rio de Moinhos | Delineation | 239 | 3,089 |
| AOI02 | Rio de Moinhos | Monitoring 1 | 277 | 3,754 |
| AOI02 | Rio de Moinhos | Monitoring 2 | 310 | 4,781 |
| AOI02 | Rio de Moinhos | Monitoring 3 | 189 | 4,652 |
| AOI03 | Salvaterra de Magos | Delineation | 2,389 | 31,164 |
| AOI03 | Salvaterra de Magos | Monitoring 1 | 1,112 | 42,673 |
| AOI03 | Salvaterra de Magos | Monitoring 2 | 733 | 49,164 |
| AOI04 | Leiria | Delineation | 83 | 1,089 |
| AOI04 | Leiria | Monitoring 1 | 65 | 683 |
| AOI04 | Leiria | Monitoring 2 | 115 | 757 |
| AOI05 | Coimbra | Delineation | 521 | 10,766 |
| AOI05 | Coimbra | Monitoring 1 | 441 | 9,324 |
| AOI05 | Coimbra | Monitoring 2 | 467 | 9,969 |
| AOI05 | Coimbra | Monitoring 3 | 123 | 8,782 |
| AOI05 | Coimbra | Monitoring 4 | 385 | 11,813 |
| AOI06 | Aveiro | Delineation | 1,785 | 9,395 |
| AOI06 | Aveiro | Monitoring 1 | 503 | 7,091 |
| AOI06 | Aveiro | Monitoring 2 | 818 | 2,746 |
| AOI11 | Barcelos | Delineation | 87 | 116 |
| AOI11 | Barcelos | Monitoring 1 | 102 | 150 |
| AOI12 | Ponte de Lima | Delineation | 605 | 219 |
| AOI12 | Ponte de Lima | Monitoring 1 | 107 | 76 |
| AOI12 | Ponte de Lima | Monitoring 2 | 554 | 226 |
| AOI13 | Chaves | Delineation | 517 | 110 |
| AOI13 | Chaves | Monitoring 1 | 52 | 23 |
| AOI13 | Chaves | Monitoring 2 | 172 | 31 |
| AOI14 | Tomar | Monitoring 1 | 80 | 58 |
| AOI15 | Mertola | Delineation | 181 | 212 |
| AOI15 | Mertola | Monitoring 1 | 245 | 159 |
| AOI17 | Mira River | Delineation | 374 | 690 |
| AOI17 | Mira River | Monitoring 1 | 261 | 415 |
| AOI17 | Mira River | Monitoring 2 | 120 | 414 |
| AOI18 | Minho river | Delineation | 30 | 41 |

**Portuguese AOIs with no data** (remote sensing limitations): Porto (AOI07), Marco de Canaveses (AOI08), Peso de Regua (AOI09), Santo Tirso (AOI10), Silves (AOI16), Tomar (AOI14 delineation only).

### Key Findings

**Salvaterra de Magos (Tejo basin)** dominates the dataset:
- Flood area grew from **31,164 ha** (Feb 6) → **42,673 ha** (Feb 7) → **49,164 ha** (Feb 8)
- Three temporal snapshots enable scrollytelling animation of progressive inundation
- The 58% growth over 2 days captures the Tejo floodplain reaching peak extent

**Coimbra (Mondego basin)** now has coverage from both activations:
- EMSR861: 7,723 ha (Storm Kristin, Feb 2)
- EMSR864: 10,766 ha delineation growing to 11,813 ha (Storm Leonardo, Feb 6–15)

**Aveiro (Vouga/Ria de Aveiro)** — 9,395 ha flooded, extensive lagoon flooding.

**New geographic coverage** extends from Minho (north) to Mertola (Guadiana, south), covering the full extent of the crisis across Portugal.

## Source URLs

### EMSR861 (Storm Kristin)
- Activation page: https://rapidmapping.emergency.copernicus.eu/EMSR861
- AOI05 Coimbra: https://rapidmapping.emergency.copernicus.eu/backend/EMSR861/AOI05/DEL_PRODUCT/EMSR861_AOI05_DEL_PRODUCT_v1.zip

### EMSR864 (Storm Leonardo/Marta)
- Activation page: https://rapidmapping.emergency.copernicus.eu/EMSR864
- All Portuguese AOIs downloaded via `scripts/download_cems.py` (queries API, filters Portugal, downloads + processes automatically)

### Story Maps
- EMSR861: https://storymaps.arcgis.com/stories/c90e86447624492ba61047133e200d70
- EMSR864: https://storymaps.arcgis.com/stories/575ccd1b705543d3a6368952de7e34b8

## Web-Optimized Formats

### PMTiles (for MapLibre)

| File | Source | Size | Zoom Range |
|------|--------|------|------------|
| `combined.pmtiles` | All flood polygons | 17 MB | z4-z14 |
| `emsr861.pmtiles` | Storm Kristin only | 458 KB | z4-z14 |
| `emsr864.pmtiles` | Storm Leonardo/Marta only | 17 MB | z4-z14 |
| `salvaterra_temporal.pmtiles` | Salvaterra 3-snapshot animation | 6.4 MB | z6-z14 |

Generated with tippecanoe using `--drop-densest-as-needed --extend-zooms-if-still-dropping`. Salvaterra temporal uses `--no-feature-limit --no-tile-size-limit` to preserve all polygons for animation accuracy.

Usage in MapLibre:
```js
import { PMTiles, Protocol } from 'pmtiles';
let protocol = new Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);
map.addSource('flood-extent', {
  type: 'vector',
  url: 'pmtiles://data/flood-extent/combined.pmtiles'
});
```

### Salvaterra Temporal Snapshots

Per-date GeoJSON files for the Salvaterra de Magos flood animation:

| File | Date | Features | Area (ha) | Product |
|------|------|----------|-----------|---------|
| `salvaterra_2026-02-06.geojson` | Feb 6 | 2,389 | 31,164 | Delineation |
| `salvaterra_2026-02-07.geojson` | Feb 7 | 1,112 | 42,673 | Monitoring 1 |
| `salvaterra_2026-02-08.geojson` | Feb 8 | 733 | 49,164 | Monitoring 2 |
| `salvaterra_temporal.geojson` | All 3 | 4,234 | — | Combined |

## Processing

Automated via `scripts/download_cems.py`:
1. Queries CEMS Rapid Mapping API for both activations
2. Identifies Portuguese AOIs by name matching
3. Downloads all available DEL products (delineation + monitoring) — ZIPs cached
4. Extracts `observedEventA` shapefiles from each product using geopandas
5. Enriches each feature with metadata: activation, AOI, locality, source_date, sensor, product_type, storm
6. Calculates area in hectares using ETRS89-LAEA equal-area projection (EPSG:3035)
7. Merges per activation → `emsr861.geojson`, `emsr864.geojson`
8. Combines both activations → `combined.geojson`
9. PMTiles built separately with tippecanoe

Re-run with: `source .venv/bin/activate && python scripts/download_cems.py`

### Layers in Source Products (not extracted)

Each CEMS product ZIP contains multiple thematic layers:
- `observedEventA` — **flood extent polygons from satellite observation** (extracted)
- `modelledEventA` — hydrological model outputs (not used)
- `floodDepthA` — estimated water depths (not used)
- `imageFootprintA` — sensor coverage area (not used)
- `areaOfInterestA` — analysis boundary (not used)
- `maximumFloodExtentA` — combined max extent across monitoring passes (monitoring products only, not used)

## Satellites Used

| Satellite | Resolution | AOIs |
|-----------|-----------|------|
| Sentinel-1 | HR+ (10m) | Multiple monitoring passes across all AOIs |
| COSMO-SkyMed 2G | HR+/VHR2 | Ermidas Sado, Coimbra |
| ICEYE | HR+ | Salvaterra de Magos initial |
| RADARSAT-2 | HR+ | Rio de Moinhos |

## Attribution

All data: Copernicus Emergency Management Service (CEMS), European Union.
License: Free and open for all uses with attribution.
Citation: "Copernicus Emergency Management Service (CEMS), EMSR861/EMSR864, European Union"
