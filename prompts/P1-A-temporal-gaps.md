# P1.A — Fill Temporal Gaps (Agent Team Prompt)

## Mission

Fill the temporal density gaps in cheias.pt data. Four independent fetch tasks that can
run simultaneously — each agent owns its own output directory, no file conflicts.

**Read first:** `CLAUDE.md`, `prompts/sprint-backlog.md` (tasks P1.A1-A4),
`prompts/scroll-timeline-symbology.md` §2 Ch.4 and §3 (data gaps).

## Setup

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

## Prompt

```
We need to fill temporal data gaps for cheias.pt. Four independent fetch jobs,
each hitting a different API with its own output directory — perfect for parallel work.

Read CLAUDE.md first. Use the project .venv for all Python work.

Spawn 4 teammates:

- One to extend ERA5 hourly synoptic data for storms Leonardo and Marta.
  The existing script is scripts/fetch_era5_synoptic.py — it produced hourly
  data for Kristin (Jan 26-30) but only 6-hourly for the rest.
  Modify it to support multiple storm periods:
    Leonardo: Feb 4-8 2026 (hourly)
    Marta: Feb 9-12 2026 (hourly)
  Add --storms-only flag to skip already-fetched dates.
  Add skip logic for existing COGs.
  Variables: mean_sea_level_pressure, 10m u/v wind, wind gust.
  Output: data/cog/mslp/, data/cog/wind-u/, data/cog/wind-v/, data/cog/wind-gust/
  Naming: YYYY-MM-DDTHH.tif (matches existing convention).
  Verify: ls data/cog/mslp/2026-02-06T*.tif | wc -l should be 24.
  CDS API can queue for 10-30 min — start the request early, then wait.
  If CDS is extremely slow, commit the script changes and document the
  run command in data/cog/FETCH-STATUS.md.

- One to fetch hourly ERA5 precipitation for all 3 storm windows.
  Create scripts/fetch_era5_precip_hourly.py (separate from synoptic script
  to avoid conflicts). Fetch total_precipitation for:
    Kristin: Jan 26-30
    Leonardo: Feb 4-8
    Marta: Feb 9-12
  ERA5 total_precipitation is accumulated — compute hourly rate as difference
  between consecutive accumulations (or use mean_total_precipitation_rate
  which is already a rate in m/s, multiply by 3600*1000 for mm/hr).
  Output: data/cog/precipitation-hourly/YYYY-MM-DDTHH.tif (NEW directory).
  Keep existing daily data/cog/precipitation/ untouched.
  Domain: 36N-60N, 60W-5E (same as synoptic script).
  Verify: ls data/cog/precipitation-hourly/2026-01-28T*.tif | wc -l → 24.

- One to fetch extended Meteosat IR satellite imagery for Leonardo and Marta.
  The existing script is scripts/fetch_eumetsat.py with --start/--end flags.
  Credentials are in .env (EUMETSAT_CONSUMER_KEY, EUMETSAT_CONSUMER_SECRET).
  First check if credentials work:
    python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('EUMETSAT_CONSUMER_KEY')[:8])"
  If valid, run:
    python scripts/fetch_eumetsat.py --start 2026-02-04T00 --end 2026-02-08T00 --interval 1
    python scripts/fetch_eumetsat.py --start 2026-02-09T00 --end 2026-02-12T00 --interval 1
  Output: data/cog/satellite-ir/ (existing directory, new date range files).
  If credentials expired, write data/cog/satellite-ir/FETCH-STATUS.md documenting
  the error and that manual credential renewal is needed at eumetsat.int.
  Verify: ls data/cog/satellite-ir/2026-02-06T*.tif | wc -l → ~24 (or FETCH-STATUS.md).

- One to fetch Sentinel-2 before/after scenes via Earth Search STAC.
  Create scripts/fetch_sentinel2_stac.py — this is a NEW script and a STAC
  portfolio showcase. The code itself is a work sample, so make it clean.
  Search Earth Search (https://earth-search.aws.element84.com/v1):
    Collection: sentinel-2-l2a
    Bbox: [-9.16, 38.65, -8.05, 39.48] (Salvaterra de Magos floodplain)
    Before: Jan 2026, cloud < 15%
    After: Feb 6-20 2026, cloud < 30%
  Use pystac-client for search, rasterio with AWS_NO_SIGN_REQUEST=YES for COG access.
  Read B04/B03/B02 for true-color composite (uint8, percentile stretch).
  Read B03/B08 to compute NDWI = (Green-NIR)/(Green+NIR) for both dates,
  then compute difference (positive = new water).
  Write STAC Item JSON (1.0.0 spec) per scene for portfolio.
  Output directory: data/sentinel-2/ (create it).
  Files: salvaterra-before-YYYYMMDD.tif, salvaterra-after-YYYYMMDD.tif,
         salvaterra-ndwi-diff.tif, search-results.json, README.md.
  Install pystac-client if missing: pip install pystac-client (in .venv).
  Verify: NDWI diff has positive pixels where flooding occurred.

Each teammate owns their output directory — no file conflicts:
  - ERA5 synoptic agent: data/cog/mslp/, wind-u/, wind-v/, wind-gust/
  - ERA5 precip agent: data/cog/precipitation-hourly/ (new dir)
  - Meteosat agent: data/cog/satellite-ir/
  - Sentinel-2 agent: data/sentinel-2/ (new dir)

Only one shared file gets modified: scripts/fetch_era5_synoptic.py (by the
ERA5 synoptic agent only). The precip agent creates a NEW script.

Share progress with the lead as each fetch completes — CDS API waits are long,
so report when requests are queued vs when data arrives. If any fetch fails,
document the failure clearly so we can retry later.

The lead should produce a summary report: what was fetched, what failed,
file counts per directory, and any issues for follow-up.
```

## Expected Duration

- ERA5 synoptic (A1): 30 min coding + 20-60 min CDS queue + 10 min processing
- ERA5 precip (A2): 30 min coding + 20-60 min CDS queue + 10 min processing
- Meteosat (A3): 5 min credential check + 30-90 min download (or 5 min if creds expired)
- Sentinel-2 (A4): 60-90 min (script from scratch, direct S3 access — no queue)

With 4 parallel agents, wall-clock time is ~90 min (bounded by slowest CDS request).
Sequential would be ~4 hours. Worth the parallel cost.

## Definition of Done

- [ ] `ls data/cog/mslp/2026-02-06T*.tif | wc -l` → 24
- [ ] `ls data/cog/mslp/2026-02-10T*.tif | wc -l` → 24
- [ ] `ls data/cog/precipitation-hourly/*.tif | wc -l` → ~336
- [ ] Satellite: new COGs in `data/cog/satellite-ir/2026-02-0*` OR `FETCH-STATUS.md`
- [ ] `data/sentinel-2/salvaterra-before-*.tif` exists (3-band true-color COG)
- [ ] `data/sentinel-2/salvaterra-ndwi-diff.tif` exists (positive pixels = new water)
- [ ] All scripts clean enough to serve as portfolio code samples
- [ ] Lead produces summary report with file counts and any failures
