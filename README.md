# cheias.pt — O Inverno Que Partiu os Rios

A scroll-driven geo-narrative about Portugal's Winter 2025–26 flood crisis.

**Live:** [cheias.pt](https://cheias.pt) (production version uses the [VEDA-UI build](https://github.com/lunasilvestre/cheias-pt-veda-ui))

This repo contains the **custom implementation** — Vite + vanilla TypeScript + MapLibre v5 + deck.gl v9 + GSAP + WeatherLayers GL. It was the original build, later complemented by a VEDA Dashboard version to demonstrate compatibility with NASA IMPACT's production framework.

## What it covers

Between December 2025 and February 2026, Portugal was hit by storms Kristin, Leonardo, and Marta in rapid succession. 11+ people died, 12,000 were evacuated, the A1 motorway collapsed, and 226,764 hectares were mapped as flooded by Copernicus Emergency Management Service.

This project tells that story through satellite data, hydrological models, and climate attribution — as a scrollytelling narrative with animated maps.

## Stack

| Layer | Technology |
|-------|-----------|
| Build | Vite 6 + TypeScript |
| Mapping | MapLibre GL JS v5 (globe + terrain) |
| Overlays | deck.gl v9, WeatherLayers GL |
| Animation | GSAP + ScrollTrigger, Scrollama |
| Raster tiles | Cloud-Optimized GeoTIFFs on Cloudflare R2, served via TiTiler |
| Vector tiles | PMTiles (flood extent from CEMS EMSR861/EMSR864) |
| Charts | Observable Plot |

## Data pipeline

```
ERA5 / NOAA OISST / GloFAS / CEMS
        ↓
  Python notebooks (analysis + validation)
        ↓
  COGs → Cloudflare R2 (data.cheias.pt)
  GeoJSON → PostGIS → tipg vector tiles
  GeoJSON → PMTiles (tippecanoe)
        ↓
  TiTiler / tipg → MapLibre rendering
```

## Structure

- `src/` — TypeScript source (scroll engine, chapter wiring, layer manager, temporal player, map setup)
- `data/` — Processed datasets, colormaps, flood extent archives, design documents
- `notebooks/` — Python analysis scripts with publication-quality figures
- `prompts/` — Implementation prompts documenting architecture decisions and build phases
- `tasks/` — Story text and content mapping
- `css/` — Styles

## Data sources

- **Satellite:** Copernicus Sentinel-1 SAR (EMSR861, EMSR864), Sentinel-2 L2A
- **Meteorological:** ERA5 reanalysis (ECMWF via Open-Meteo), NOAA OISST v2.1
- **Hydrological:** GloFAS river discharge, SNIRH (Portuguese national network)
- **Climate attribution:** World Weather Attribution study (2026)

## Related

- [cheias-pt-veda-ui](https://github.com/lunasilvestre/cheias-pt-veda-ui) — Production VEDA Dashboard version (deployed at cheias.pt)

## License

MIT
