# PROMPT: Acquire Wildfire Scars (2024+2025) and IPMA Historical Warnings

## Context

You are working on `cheias-pt`, a scrollytelling platform about the January–February 2026 flood crisis in Portugal. The narrative argues that summer wildfires stripped vegetation from hillsides, making them vulnerable to landslides and accelerated runoff during winter storms. We need burned area polygons to show this fire-flood connection visually.

We also need historical IPMA weather warnings for the crisis period (Jan 25 – Feb 14, 2026) to show the escalation from yellow → orange → red across Portuguese districts.

**Working directory:** `~/Documents/dev/cheias-pt/`
**Output directory:** `data/qgis/` (GeoJSON vectors)
**Existing assets:** `assets/districts.geojson` (18 districts with `ipma_code` property)

---

## Task 1: Wildfire Burned Areas (Summer 2024 + 2025)

### Goal
Download burned area polygons for Portugal from **both** 2024 and 2025 fire seasons. Output as GeoJSON clipped to Portugal, with year and area attributes.

### Data Sources (try in order)

#### Option A: EFFIS WFS (preferred — authoritative, pan-European)
EFFIS provides burned area polygons via WFS. The endpoint is:

```
https://maps.effis.emergency.copernicus.eu/effis?
  SERVICE=WFS&
  REQUEST=GetFeature&
  VERSION=2.0.0&
  TYPENAMES=ecmwf:modis.ba.poly&
  OUTPUTFORMAT=application/json&
  CQL_FILTER=COUNTRY='PT' AND FIREDATE >= '2024-01-01' AND FIREDATE <= '2025-12-31'&
  SRSNAME=EPSG:4326
```

**Important:** The exact layer name may differ. Probe the WFS capabilities first:
```bash
curl -s "https://maps.effis.emergency.copernicus.eu/effis?SERVICE=WFS&REQUEST=GetCapabilities&VERSION=2.0.0" | head -200
```

Look for layer names containing `burnt`, `burned`, `ba`, or `fire`. Common EFFIS WFS layers:
- `ecmwf:modis.ba.poly` (MODIS burned area polygons)
- `EFFIS:BurntAreasAll` (all burned areas for current season — may only have 2025)

If the WFS has a TIME parameter instead of CQL_FILTER, try:
```
&TIME=2024-01-01/2025-12-31
```

If the WFS blocks large requests, paginate with `&COUNT=5000&STARTINDEX=0`.

**Portugal September 2024 fires were massive (>100,000 ha)** — expect large polygons especially in Aveiro, Viseu, Coimbra, and Leiria districts.

#### Option B: ICNF Open Data (Portuguese national authority)
ICNF publishes annual burned area shapefiles on dados.gov.pt:
- Portal: https://dados.gov.pt/en/datasets/areas-ardidas-desde-1975/
- Direct GIS portal: https://geocatalogo.icnf.pt/catalogo_tema5.html
- ArcGIS REST: https://sig.icnf.pt/portal/home/

Try fetching the resource URLs from dados.gov.pt first:
```bash
curl -s "https://dados.gov.pt/api/1/datasets/areas-ardidas-desde-1975/" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for r in d.get('resources', []):
    print(f\"{r.get('title','?'):60s} {r.get('format','?'):10s} {r.get('url','')[:100]}\")
"
```

Download shapefiles for 2024 and 2025 (if available). Convert to GeoJSON with ogr2ogr.

**Note:** ICNF 2025 data may not be published yet — it sometimes lags by months. If only 2024 is available, that's fine. The September 2024 fires are the most narratively important ones anyway.

#### Option C: FIRMS/MODIS active fire + burned area (NASA)
If EFFIS and ICNF both fail, use NASA FIRMS:
```
https://firms.modaps.eosdis.nasa.gov/api/country/csv/MAP_KEY/MODIS_NRT/PRT/10/2024-06-01
```
This gives active fire points, not polygons. Less useful but can be converted to a heatmap.

### Processing Requirements

1. **Clip to Portugal** — use a bounding box `[-9.6, 36.9, -6.1, 42.2]` or intersect with Portugal border
2. **Separate by year** — add a `fire_year` property (2024 or 2025) if not already present
3. **Calculate area** — add `area_ha` property (hectares) per polygon
4. **Filter** — keep only fires ≥ 30 ha (skip small agricultural burns)
5. **Simplify** — if file > 5MB, simplify geometries with `ogr2ogr -simplify 0.001`

### Output

```
data/qgis/wildfires-2024.geojson    # All burned areas in Portugal, 2024 season
data/qgis/wildfires-2025.geojson    # All burned areas in Portugal, 2025 season  
data/qgis/wildfires-combined.geojson # Both years merged, with fire_year property
```

Each feature should have at minimum:
- `fire_year`: 2024 or 2025
- `area_ha`: burned area in hectares
- `fire_date` or `firedate`: date of fire (if available from source)
- `geometry`: Polygon/MultiPolygon in EPSG:4326

### Verification

```bash
ogrinfo -so -al data/qgis/wildfires-2024.geojson
ogrinfo -so -al data/qgis/wildfires-2025.geojson
echo "2024 total hectares:"
python3 -c "
import json
with open('data/qgis/wildfires-2024.geojson') as f:
    d = json.load(f)
total = sum(f['properties'].get('area_ha', 0) for f in d['features'])
print(f'  {len(d[\"features\"])} fires, {total:,.0f} ha')
"
```

Expected: 2024 should show ~150,000+ ha total (September 2024 fires alone were >100,000 ha). Major clusters around Aveiro, Viseu, Coimbra districts — which overlap significantly with the Feb 2026 flood zones, proving the fire-flood thesis.

---

## Task 2: IPMA Historical Weather Warnings

### Goal
Reconstruct the IPMA weather warnings issued during the flood crisis (January 25 – February 14, 2026) as a GeoJSON timeline that can be joined to `assets/districts.geojson`.

### The Problem
IPMA's API (`https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json`) only serves **current** warnings. There is no official archive endpoint. Historical warnings must be reconstructed.

### Data Sources (try in order)

#### Option A: Wayback Machine snapshots of IPMA warnings API
The Wayback Machine (web.archive.org) may have cached the IPMA warnings JSON during the crisis period.

```bash
# Check what snapshots exist for the warnings endpoint
curl -s "https://web.archive.org/web/timemap/json/https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json" | python3 -c "
import sys, json
snapshots = json.load(sys.stdin)
# Filter to Jan-Feb 2026
for s in snapshots:
    ts = s[1] if isinstance(s, list) else s.get('timestamp','')
    if ts.startswith('2026'):
        print(ts)
" 2>/dev/null | head -50
```

For each snapshot that falls within Jan 25 – Feb 14, 2026:
```bash
curl -s "https://web.archive.org/web/20260206120000*/https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json"
```

The IPMA warnings JSON format is:
```json
{
  "owner": "IPMA",
  "data": [
    {
      "text": "Precipitação forte",
      "awarenessTypeName": "Precipitação",
      "startTime": "2026-02-06T00:00:00",
      "endTime": "2026-02-06T23:59:00", 
      "idAreaAviso": "AVR",
      "awarenessLevelID": "orange"
    }
  ]
}
```

The `idAreaAviso` maps to districts. The mapping is in `assets/districts.geojson` as the `ipma_code` property.

#### Option B: Wayback Machine snapshots of IPMA website
If the API JSON wasn't cached, try the warnings page itself:
```bash
curl -s "https://web.archive.org/web/20260206/https://www.ipma.pt/pt/otempo/prev.localidade/index.jsp"
```

Or the warnings-specific page. Parse HTML for warning data.

#### Option C: Manual reconstruction from news + IPMA social media
If Wayback Machine has no snapshots, reconstruct from:

1. **IPMA Twitter/X posts** — IPMA posts warnings on social media. Search:
   - `site:twitter.com ipma aviso meteorologico fevereiro 2026`
   - `site:x.com ipma aviso vermelho janeiro 2026`

2. **News articles** — Portuguese media always reports IPMA warnings. Key events:
   - Jan 29: Storm Kristin — red warnings for precipitation in Coimbra, Leiria, Aveiro, Lisboa
   - Feb 5-6: Storm Leonardo — red warnings for precipitation and coastal agitation
   - Feb 10-11: Storm Marta — orange/red warnings again
   
3. **Proteção Civil situation reports** — ANEPC reports always reference IPMA warning levels

Create a manual JSON with the best available information:

```json
[
  {
    "date": "2026-01-29",
    "storm": "Kristin", 
    "districts_red": ["AVR", "CBR", "LRA", "LSB"],
    "districts_orange": ["VIS", "STR", "PTG", "FAR", "BJA", "EVR", "STB"],
    "districts_yellow": ["BRG", "VCT", "PRT", "VRL", "GRD", "CTB", "BGC"],
    "warning_type": "precipitation",
    "source": "reconstructed from news reports"
  }
]
```

#### Option D: Open-Meteo weather codes as proxy
If all else fails, we can approximate warning levels from actual weather severity. Fetch daily weather data from Open-Meteo for each district capital and classify:
- precipitation_sum > 40mm/day → "orange equivalent" 
- precipitation_sum > 80mm/day → "red equivalent"

This is a fallback — clearly label as "approximated from observed data, not official IPMA warnings."

### Processing Requirements

1. **Output as timeline GeoJSON** — each feature is a district polygon for one day with warning properties
2. **Join to districts.geojson** — use the `ipma_code` property to match warnings to district polygons
3. **Cover full period** — January 25 through February 14, 2026 (21 days)
4. **Warning levels** — green (no warning), yellow, orange, red
5. **Warning types** — precipitation, wind, coastal agitation, snow (where applicable)

### Output Files

```
data/qgis/ipma-warnings-timeline.geojson   # District polygons × days, with warning level
data/frontend/ipma-warnings.json            # Compact JSON for frontend animation
```

**ipma-warnings-timeline.geojson** — each feature is a district-day:
```json
{
  "type": "Feature",
  "properties": {
    "district": "Coimbra",
    "ipma_code": "CBR",
    "date": "2026-02-06",
    "storm": "Leonardo",
    "warning_level": "red",
    "warning_type": "precipitation",
    "source": "wayback_machine|news_reconstruction|open_meteo_proxy",
    "confidence": "high|medium|low"
  },
  "geometry": { ... district polygon ... }
}
```

**ipma-warnings.json** — compact for web frontend:
```json
{
  "dates": ["2026-01-25", ..., "2026-02-14"],
  "districts": {
    "AVR": ["green", "green", "yellow", "orange", "red", ...],
    "CBR": ["green", "yellow", "orange", "red", "red", ...],
    ...
  },
  "storms": {
    "Kristin": { "start": "2026-01-28", "end": "2026-01-31" },
    "Leonardo": { "start": "2026-02-05", "end": "2026-02-08" },
    "Marta": { "start": "2026-02-10", "end": "2026-02-12" }
  },
  "source": "wayback_machine|news_reconstruction|open_meteo_proxy"
}
```

### Verification

```bash
python3 -c "
import json
with open('data/qgis/ipma-warnings-timeline.geojson') as f:
    d = json.load(f)
from collections import Counter
levels = Counter(f['properties']['warning_level'] for f in d['features'])
dates = sorted(set(f['properties']['date'] for f in d['features']))
print(f'Features: {len(d[\"features\"])}')
print(f'Date range: {dates[0]} → {dates[-1]} ({len(dates)} days)')
print(f'Warning levels: {dict(levels)}')
print(f'Sources: {Counter(f[\"properties\"][\"source\"] for f in d[\"features\"])}')
# Expect: ~18 districts × 21 days = ~378 features
# Expect: several red warnings during Kristin (Jan 29-30), Leonardo (Feb 5-7), Marta (Feb 10-11)
"
```

---

## Execution Order

1. **Task 1 first** — wildfire data is more straightforward (download + clip)
2. **Task 2 second** — IPMA warnings require multi-source investigation

## Dependencies

```bash
pip install geopandas shapely requests --user
# ogr2ogr should already be available (GDAL)
```

## Git

Commit after each task:
```bash
cd ~/Documents/dev/cheias-pt
git add data/qgis/wildfires-*.geojson data/qgis/ipma-warnings-timeline.geojson data/frontend/ipma-warnings.json
git commit -m "feat: add wildfire scars 2024+2025 and IPMA historical warnings"
```
