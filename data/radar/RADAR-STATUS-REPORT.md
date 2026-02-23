# Radar Data Investigation — Status Report

**Date:** 2026-02-22
**Investigator:** Agent 7 (Radar Data)
**Target dates:** January 27–28, 2026 (Storm Leonardo peak over Portugal)
**Target domain:** Portugal mainland (36.9°N–42.2°N, 9.6°W–6.1°W)

## Executive Summary

**Actual ground-based radar data for Jan 27–28 is NOT freely available for retrospective access.**

European radar data is institutionally locked behind EUMETNET/OPERA membership (national met service level). IPMA's radar portal serves only the last ~24 hours with randomized URLs. The best available alternatives are satellite-derived precipitation (GPM IMERG, requires free NASA registration) and model-based hourly precipitation (Open-Meteo, available now with zero auth).

## Sources Investigated

### 1. OPERA / EUMETNET Radar Composites — BLOCKED

- **What:** European radar composite at 2km resolution, produced by EUMETNET OPERA programme
- **Distribution:** OPERA OIFS Data Hub (Rasdaman-based)
- **Access:** National Met Service membership ONLY — not available to public, researchers, or even EUMETSAT data store customers
- **EUMETSAT Data Store:** Does NOT carry OPERA products (confirmed: searched all 175 collections, zero radar matches)
- **Known collection IDs (EO:EUM:DAT:OPERA:*):** All return 404 on EUMETSAT Data Store
- **Status:** DEAD END. Would require institutional partnership with IPMA.

### 2. RainViewer API — DEAD END

- **What:** Commercial radar aggregation service with global coverage
- **API status:** Working (returns real-time data)
- **Historical data:** NO. Only the last ~2 hours of radar frames are available.
- **Archive:** Does not exist in their public API
- **Status:** DEAD END for retrospective analysis. Jan 27–28 is 25+ days ago, far beyond their 2-hour window.

### 3. IPMA Radar (Direct) — PARTIALLY AVAILABLE

- **What:** Portuguese Met Service ground radar network (3 stations: Coruche, Arouca, Loulé)
- **Product:** Precipitation intensity composite (mm/h), mainland coverage
- **Resolution:** ~1km (excellent for narrative purposes)
- **Current access:** YES — 144 frames available (~24h at 10-min intervals)
- **URL pattern:** `https://www.ipma.pt/resources.www/data/observacao/radar/imagens/{YYYYMMDD}/{random-20-char-token}/{filename}.jpg`
- **Critical limitation:** Each image URL contains a random 20-character alphabetic token. Historical tokens cannot be guessed or predicted.
- **Historical access:** BLOCKED. Date directories for past dates return HTTP 403 (data exists but is access-restricted). No public archive API.
- **Wayback Machine:** Rate-limited during investigation (HTTP 429). Would need to check if archive.org captured the page around Jan 27–28.
- **Sample image verified:** Downloaded and confirmed valid JPEG (67 KB), shows excellent radar composite with terrain background.
- **Status:** AVAILABLE FOR FUTURE EVENTS ONLY. Script `fetch_radar.py --source ipma-current` can scrape current images. Set up as cron job to build archive.

### 4. AEMET (Spanish Met Service) — DEAD END

- **What:** Spanish radar network, covers western Iberia
- **API:** AEMET Open Data API exists, returns HTTP 200 for radar endpoints
- **Content:** Empty response body on radar endpoints — requires API key (free registration)
- **Historical data:** NO. AEMET radar API provides current/real-time images only.
- **Status:** DEAD END for Jan 27–28 retrospective. No historical radar archive via API.

### 5. GPM IMERG (NASA) — BEST OPTION (requires free registration)

- **What:** Global Precipitation Measurement mission, multi-satellite merged precipitation
- **Product:** IMERG Late Run V07B (half-hourly, 0.1° = ~11km resolution)
- **Data confirmed:** 96 files per day (48 half-hourly HDF5 + 48 XML) for Jan 27 AND Jan 28
- **File pattern:** `3B-HHR-L.MS.MRG.3IMERG.20260127-S{HHMMSS}-E{HHMMSS}.{MMMM}.V07B.HDF5`
- **Variables:** `precipitation` (mm/hr), `precipitationQualityIndex`, `MWprecipitation`, `IRprecipitation`
- **Grid:** 3600×1800 global (0.1° resolution)
- **OPeNDAP:** Available for spatial subsetting (Portugal domain: lat[1269:1322], lon[1704:1739])
- **Authentication:** REQUIRED. NASA Earthdata login (free registration at urs.earthdata.nasa.gov).
- **Metadata access:** Free (DAS/DDS accessible without auth)
- **Data download:** Requires auth (returns 401 without credentials)
- **Status:** ACTIONABLE. Register for NASA Earthdata (free, ~5 min), then `fetch_radar.py --source gpm-imerg --start 2026-01-27 --end 2026-01-28` will download Portugal subsets.

### 6. Open-Meteo Hourly Precipitation — AVAILABLE NOW

- **What:** ECMWF IFS025 model precipitation, served by Open-Meteo API
- **Resolution:** 0.25° (~25km) — coarser than radar but adequate for narrative
- **Temporal:** Hourly (shows storm progression)
- **Authentication:** NONE required
- **Archive:** Full coverage of our study period (Dec 2025 – Feb 2026)
- **Verified:** Jan 27–28 data confirmed: 67.1mm total at central Portugal test point, peak 5.3 mm/h
- **Limitation:** This is MODEL data (NWP), not observations. Shows predicted precipitation, not measured.
- **Status:** AVAILABLE NOW. `fetch_radar.py --source open-meteo --start 2026-01-25 --end 2026-02-10`

### 7. Other Sources Checked

| Source | Status | Notes |
|--------|--------|-------|
| **DWD (Germany)** | Out of range | Only European Met Service with open radar archive, but Portugal is ~2000km away |
| **KNMI (Netherlands)** | Out of range | Open radar for NL/Benelux only |
| **H-SAF (EUMETSAT SAF)** | Unreachable | Server timeouts on both HTTPS and FTP — may be down or geo-restricted |
| **CMORPH (NOAA)** | No 2026 data | Archive only goes to 2022–2023, no recent data |
| **PERSIANN (UC Irvine)** | Web portal only | Interactive visualization, not bulk download API for recent data |
| **ERA5** | Available via CDS | 0.25° hourly, but requires CDS credentials and has ~5 day delay. Redundant with Open-Meteo. |
| **Copernicus CDS** | Not radar | E-OBS provides daily gridded station data at 0.1°, not sub-daily |

## Recommendation: Practical Path Forward

### Immediate (no new credentials needed)
1. **Open-Meteo hourly grid** — Run `fetch_radar.py --source open-meteo --start 2026-01-25 --end 2026-02-10` for storm progression animation. Not "true" radar but shows hourly storm movement at 0.5° grid.

### Short-term (free registration)
2. **GPM IMERG** — Register at NASA Earthdata (free, 5 min), then download half-hourly precipitation at 0.1°. Best available retrospective "radar-like" data. Satellite-derived, not ground radar, but high quality and covers our exact dates.

### Future event preparedness
3. **IPMA scraper cron** — Set up `fetch_radar.py --source ipma-current` as a cron job. Captures actual Portuguese radar composites at 10-min intervals. Building an archive for the NEXT storm event.

### Institutional (future phase)
4. **Contact IPMA** — Request historical radar archive access for the Jan–Feb 2026 storm period. As a Portuguese public service project, there may be willingness to share.
5. **OPERA membership** — Requires institutional affiliation. Not viable for independent project.

## For the Scrollytelling Narrative

The project already has excellent daily precipitation data from Open-Meteo (Sprint 01 validated). What radar would add is **sub-daily storm progression** — showing the approaching wall of rain in near-real-time resolution.

**Recommended approach for v0:**
- Use the existing daily precipitation animation (already wired in Sprint 02)
- If GPM IMERG credentials are obtained: add half-hourly precipitation animation for the storm peak chapters (Ch4: Three Storms)
- The Open-Meteo hourly grid can serve as a bridge — same API already in use, just needs hourly instead of daily aggregation

**Visual impact assessment:**
- Ground radar (1km, 10-min): Would be stunning but is locked
- GPM IMERG (11km, 30-min): Very good for narrative — shows storm bands approaching from Atlantic
- Open-Meteo hourly (25km, 1h): Adequate for narrative — shows broad storm progression
- Existing daily grid (25km, daily): Already in use — misses intra-day storm dynamics

## Files Created

- `scripts/fetch_radar.py` — Multi-source fetch script with IPMA scraper, Open-Meteo grid, and GPM IMERG downloader
- `data/radar/test_ipma_radar.jpg` — Sample IPMA radar image (current, confirmed valid)
- `data/radar/RADAR-STATUS-REPORT.md` — This report
