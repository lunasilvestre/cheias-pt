# Meteosat IR 10.8um COG Fetch Status

## Pipeline
Script: `scripts/fetch_eumetsat.py`
Source: EUMETSAT Data Store — `EO:EUM:DAT:MSG:HRSEVIRI` (MSG3 SEVIRI Level 1.5)
Processing: satpy (native -> resample -> COG), pyresample to EPSG:4326
Domain: 40W-10E, 30N-60N (~3km resolution)
Output: `data/cog/satellite-ir/` (IR 10.8um) + `data/cog/satellite-vis/` (Natural Colour RGB)
Attribution: "Contains modified EUMETSAT Meteosat data 2026"

## Storm Periods

### Kristin (Jan 27-28)
- **Status:** COMPLETE
- **Period:** 2026-01-27T00 to 2026-01-28T23, hourly
- **Files:** 48 IR COGs, 48 VIS COGs
- **Fetched:** 2026-02-22

### Leonardo (Feb 4-8)
- **Status:** COMPLETE
- **Period:** 2026-02-04T00 to 2026-02-08T00, hourly
- **Files:** 97 IR COGs, 97 VIS COGs (96 processed + 1 pre-existing test)
- **Failures:** 0
- **Fetched:** 2026-02-26

### Marta (Feb 9-12)
- **Status:** COMPLETE
- **Period:** 2026-02-09T00 to 2026-02-12T00, hourly
- **Files:** 73 IR COGs, 73 VIS COGs
- **Failures:** 0
- **Fetched:** 2026-02-26/27

## Totals
- **IR COGs:** 218 files (437 MB)
- **VIS COGs:** 218 files (621 MB)
- **Combined:** 436 files, 1,058 MB (~1 GB)

## Per-Timestamp Stats (typical)
- Download: ~259 MB .nat file per timestamp
- IR COG: ~2.0 MB
- VIS COG: ~0.1-6.5 MB (smaller at night, larger during day)
- Processing time: ~30-40 seconds per timestamp (sustained)

## Resumability
The script is idempotent -- it skips timestamps where both VIS and IR COGs already exist.
To resume an interrupted fetch, re-run the same command.

## If Credentials Expire
1. Go to https://eoportal.eumetsat.int/ and regenerate API keys
2. Update `EUMETSAT_CONSUMER_KEY` and `EUMETSAT_CONSUMER_SECRET` in `.env`
3. Re-run the same commands
