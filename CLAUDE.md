# cheias.pt — The Winter That Broke the Rivers

## Environment
Always use the project virtual environment at `.venv/`. Activate with `source .venv/bin/activate` before any pip install or python3 command. NEVER use --break-system-packages.

## What This Is

A **geo-narrative** about Portugal's January–February 2026 flood crisis — what happened,
why it happened, and what it means. Told through maps, satellite imagery, and
hydro-meteorological data.

Portfolio piece targeting Development Seed (Lisbon + DC). Public service artifact for
Portuguese citizens, journalists, and local officials.

**The crisis:** Storm cluster (Kristin → Leonardo → Marta) killed 11+, displaced thousands,
collapsed the A1 motorway, burst the Mondego levee, triggered €2.5B aid package across 69
municipalities. Tejo at highest since 1997. Sado at levels unseen since 1989. CEMS rapid
mapping activated (EMSR861, EMSR864).

## Key References

| What | Where |
|------|-------|
| **Design document (source of truth)** | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/12-design-document.md` |
| Motion analysis (6 visual effects) | `data/video-analysis/MOTION-ANALYSIS.md` |
| Library catalogue | `deckgl-dynamic-mapping-examples.md` |
| Planetary Computer NWP pipeline | `prompts/refactor-nwp-planetary-computer.md` |
| Vizzuality methodology (quality bar) | `~/.vaults/root/2nd-Brain/Projects/vizzuality-methodology/` (8 files: design philosophy, visual system, scrollytelling, architecture, trust, anti-patterns, portfolio) |
| Flood dynamics & data sources | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/07-flood-dynamics-prediction.md` |
| Data source tier list | `~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/06-synthesis.md` |
| Previous CLAUDE.md (detailed specs) | `CLAUDE-v4-scrollytelling.md` |

## Current Prototype

`deckgl-prototype.html` — a single-file MapLibre + deck.gl v9 prototype used as a
development spike. It demonstrates COG-from-R2 rendering, temporal animation, and
layer composition. It is NOT the final architecture — the creative direction phase
will determine the right stack and structure.

## Geographic Assets (validated, ready)

| Asset | Features | Key Properties |
|-------|----------|----------------|
| `assets/districts.geojson` | 18 districts | `district`, `ipma_code` |
| `assets/basins.geojson` | 11 basins | `river`, `name_pt`, `type` |

## Data — See `data/` directory

All raw data has been acquired and validated. Formats include COG, GeoJSON, PMTiles,
Parquet, NetCDF, and frontend JSON. Walk `data/` for the full inventory.
See `CLAUDE-v4-scrollytelling.md` for the detailed data pipeline documentation.
