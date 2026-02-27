# Sentinel-2 Before/After Flood Imagery

Before/after satellite imagery of the Salvaterra de Magos floodplain (lower Tejo valley)
for the January-February 2026 Portugal flood crisis.

## Source

- **Catalog:** [Earth Search v1](https://earth-search.aws.element84.com/v1) by Element 84
- **Collection:** `sentinel-2-l2a` (Sentinel-2 L2A, atmospherically corrected by ESA)
- **Resolution:** 10 m (B02 Blue, B03 Green, B04 Red, B08 NIR)
- **Access:** S3 unsigned (public via `AWS_NO_SIGN_REQUEST=YES`)

## Search Parameters

| Parameter | Before | After |
|-----------|--------|-------|
| Bbox | `[-9.16, 38.65, -8.05, 39.48]` | same |
| Date range | 2026-01-01 to 2026-01-26 | 2026-02-06 to 2026-02-20 |
| Max cloud cover | 15% | 30% |
| Max items | 10 | 10 |
| Selection | Lowest cloud cover | Lowest cloud cover |

## Selected Scenes

| Scene | Before | After |
|-------|--------|-------|
| **ID** | `S2B_29SND_20260106_0_L2A` | `S2C_29SND_20260220_0_L2A` |
| **Date** | 2026-01-06 | 2026-02-20 |
| **Cloud cover** | 0.01% | 0.02% |
| **MGRS tile** | 29SND | 29SND |
| **Platform** | Sentinel-2B | Sentinel-2C |

**Rationale:** Both scenes are from the same MGRS tile (29SND) with near-zero cloud cover,
ensuring a clean comparison. The before scene (Jan 6) shows pre-storm baseline conditions.
The after scene (Feb 20) captures residual flooding 14 days after peak discharge (Feb 5-7),
when the Tejo valley was still partially inundated.

## Products

| File | Description | Format |
|------|-------------|--------|
| `salvaterra-before-20260106.tif` | True-color composite (B04/B03/B02) | 3-band uint8 COG |
| `salvaterra-after-20260220.tif` | True-color composite (B04/B03/B02) | 3-band uint8 COG |
| `salvaterra-ndwi-before-20260106.tif` | NDWI before | float32 COG |
| `salvaterra-ndwi-after-20260220.tif` | NDWI after | float32 COG |
| `salvaterra-ndwi-diff.tif` | NDWI difference (after - before) | float32 COG |
| `before-item.json` | STAC Item 1.0.0 for before scene | JSON |
| `after-item.json` | STAC Item 1.0.0 for after scene | JSON |
| `search-results.json` | Full search results with rationale | JSON |

## NDWI Methodology

**Normalized Difference Water Index (NDWI)** detects surface water using spectral
reflectance differences between green and near-infrared bands:

```
NDWI = (B03_green - B08_nir) / (B03_green + B08_nir)
```

- **Positive NDWI:** Water surfaces (green reflects more than NIR)
- **Negative NDWI:** Vegetation and soil (NIR reflects more than green)

The **NDWI difference** (after - before) isolates flood-induced water extent changes:
- **Positive pixels** = areas that became more water-like (flooding)
- **Negative pixels** = areas that became less water-like (drying or vegetation change)

### Results

- **6,691,187 pixels** with positive NDWI difference (10.1% of scene)
- **Max NDWI diff:** 1.531 (strong flooding signal)
- **Mean NDWI diff:** 0.012 (slight overall increase in water)

## True-Color Processing

- Bands: B04 (Red), B03 (Green), B02 (Blue) at 10 m native resolution
- Clipped to bbox, reprojected to EPSG:32629 (UTM 29N)
- Percentile stretch: 2nd-98th percentile mapped to 0-255 uint8
- Written as Cloud-Optimized GeoTIFF with 4 overview levels (2x, 4x, 8x, 16x)

## Reproduction

```bash
source .venv/bin/activate
python scripts/fetch_sentinel2_stac.py
```

Requires: `pystac-client`, `rasterio`, `numpy`

## Attribution

Contains modified Copernicus Sentinel data 2026, processed by ESA.
Accessed via [Element 84 Earth Search](https://earth-search.aws.element84.com/v1).

Script: `scripts/fetch_sentinel2_stac.py`
Generated: 2026-02-26
