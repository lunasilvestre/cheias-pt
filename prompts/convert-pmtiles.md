# Task: Convert CEMS Flood Extent GeoJSON → PMTiles for Web Delivery

## Context

We have processed CEMS flood extent polygons in `data/flood-extent/`:
- `emsr861.geojson` — 506 polygons, 2.3 MB (Storm Kristin, Coimbra)
- `emsr864.geojson` — 4,546 polygons, 44.7 MB (Storm Leonardo/Marta, Tejo+Sado)
- `combined.geojson` — 5,052 polygons, 47 MB (both activations)

These are too large for direct GeoJSON loading in MapLibre. We need PMTiles for efficient web delivery.

## Environment

Use the project virtual environment: `source .venv/bin/activate`

## Steps

### 1. Install tippecanoe

```bash
# Check if tippecanoe is already installed
which tippecanoe || {
  sudo apt-get update && sudo apt-get install -y tippecanoe
}
```

If not available via apt, build from source:
```bash
git clone https://github.com/felt/tippecanoe.git /tmp/tippecanoe
cd /tmp/tippecanoe && make -j && sudo make install
```

### 2. Convert to PMTiles

Generate three PMTiles files matching the GeoJSON outputs:

```bash
cd data/flood-extent

# Combined — primary file for the scrollytelling map
tippecanoe -o combined.pmtiles \
  -Z4 -z14 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  -l flood_extent \
  --force \
  combined.geojson

# Per-activation files (useful for chapter-specific loading)
tippecanoe -o emsr861.pmtiles \
  -Z4 -z14 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  -l flood_extent \
  --force \
  emsr861.geojson

tippecanoe -o emsr864.pmtiles \
  -Z4 -z14 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  -l flood_extent \
  --force \
  emsr864.geojson
```

### 3. Also generate a temporal PMTiles for Salvaterra de Magos animation

This is the scrollytelling anchor — 3 snapshots showing flood growth over 2 days.

```bash
# First, extract the 3 temporal snapshots using Python
source ../../.venv/bin/activate
python3 << 'PYEOF'
import geopandas as gpd
import json

gdf = gpd.read_file("emsr864.geojson")
salvaterra = gdf[gdf["locality"] == "Salvaterra de Magos"].copy()

# Verify we have 3 temporal snapshots
print(f"Salvaterra features: {len(salvaterra)}")
print(f"Product types: {salvaterra['product_type'].unique()}")
print(f"Dates: {salvaterra['source_date'].unique()}")

# Save per-snapshot for temporal animation
for date in sorted(salvaterra["source_date"].unique()):
    subset = salvaterra[salvaterra["source_date"] == date]
    fname = f"salvaterra_{date}.geojson"
    subset.to_file(fname, driver="GeoJSON")
    print(f"  {fname}: {len(subset)} features, {subset['area_ha'].sum():.0f} ha")

# Also save combined Salvaterra
salvaterra.to_file("salvaterra_temporal.geojson", driver="GeoJSON")
print(f"\nsalvaterra_temporal.geojson: {len(salvaterra)} total features")
PYEOF

# Convert Salvaterra temporal to PMTiles
tippecanoe -o salvaterra_temporal.pmtiles \
  -Z6 -z14 \
  --no-feature-limit --no-tile-size-limit \
  -l flood_extent \
  --force \
  salvaterra_temporal.geojson
```

### 4. Also convert to GeoParquet (for Python/notebook use)

```bash
source ../../.venv/bin/activate
pip install pyarrow 2>/dev/null

python3 << 'PYEOF'
import geopandas as gpd

for name in ["emsr861", "emsr864", "combined"]:
    gdf = gpd.read_file(f"{name}.geojson")
    gdf.to_parquet(f"{name}.parquet")
    print(f"{name}.parquet: {len(gdf)} features")
PYEOF
```

### 5. Verify PMTiles are valid

```bash
# Check file sizes
ls -lh *.pmtiles

# If pmtiles CLI is available, inspect metadata
which pmtiles && {
  pmtiles show combined.pmtiles
  pmtiles show salvaterra_temporal.pmtiles
}
```

### 6. Update README

Append the new output files to `data/flood-extent/README.md` under a new section:

```markdown
## Web-Optimized Formats

### PMTiles (for MapLibre)

| File | Source | Size | Zoom Range |
|------|--------|------|------------|
| `combined.pmtiles` | All flood polygons | TBD | z4-z14 |
| `emsr861.pmtiles` | Storm Kristin only | TBD | z4-z14 |
| `emsr864.pmtiles` | Storm Leonardo/Marta only | TBD | z4-z14 |
| `salvaterra_temporal.pmtiles` | Salvaterra 3-snapshot animation | TBD | z6-z14 |

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

### GeoParquet (for Python notebooks)

| File | Features | Size |
|------|----------|------|
| `combined.parquet` | 5,052 | TBD |
| `emsr861.parquet` | 506 | TBD |
| `emsr864.parquet` | 4,546 | TBD |
```

Fill in the actual file sizes after generation. Also update the main output table at the top of README.md to include these new formats.

### 7. Update .gitignore

Add to the project `.gitignore` if not already present — the GeoJSON and Parquet files are too large for git:

```
data/flood-extent/*.geojson
data/flood-extent/*.parquet
data/flood-extent/EMSR*/
```

PMTiles should also be gitignored (regenerable from source), but note this in the README so someone cloning knows to run the processing pipeline.
