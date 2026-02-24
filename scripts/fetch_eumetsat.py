#!/usr/bin/env python3
"""
Fetch MSG (Meteosat Second Generation) SEVIRI imagery from EUMETSAT Data Store.

Downloads Level 1.5 native files, generates Natural Colour RGB composites and
IR 10.8μm channel imagery, resamples to EPSG:4326, and exports as COGs.

Target: Storm Kristin approach and landfall over Portugal (Jan 27-28, 2026).

Requires:
  - eumdac (EUMETSAT Data Access Client)
  - satpy (satellite data processing)
  - rioxarray (COG export)
  - python-dotenv (credential loading)

Credentials: EUMETSAT_CONSUMER_KEY and EUMETSAT_CONSUMER_SECRET in .env

Attribution: "Contains modified EUMETSAT Meteosat data 2026"

Usage:
  python scripts/fetch_eumetsat.py                    # All hourly timestamps
  python scripts/fetch_eumetsat.py --test              # Single test timestamp
  python scripts/fetch_eumetsat.py --interval 3        # Every 3 hours
  python scripts/fetch_eumetsat.py --start 2026-01-27T06 --end 2026-01-28T18
"""

import argparse
import os
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings('ignore')

from dotenv import load_dotenv

# --- Configuration -----------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / '.env'

VIS_OUTPUT_DIR = PROJECT_ROOT / 'data' / 'cog' / 'satellite-vis'
IR_OUTPUT_DIR = PROJECT_ROOT / 'data' / 'cog' / 'satellite-ir'
TMP_DIR = Path('/tmp/eumetsat_download')

# Euro-Atlantic domain: covers storm approach from Atlantic to Iberia
# 30N-60N, 40W-10E at ~3km resolution
AREA_EXTENT = (-40.0, 30.0, 10.0, 60.0)
AREA_RESOLUTION = 0.03  # degrees (~3km)

# Default time window: Storm Kristin Jan 27-28, 2026
DEFAULT_START = datetime(2026, 1, 27, 0, 0)
DEFAULT_END = datetime(2026, 1, 28, 23, 59)
DEFAULT_INTERVAL_HOURS = 1

COLLECTION_ID = 'EO:EUM:DAT:MSG:HRSEVIRI'


def get_credentials():
    """Load EUMETSAT credentials from .env file."""
    load_dotenv(ENV_FILE)
    key = os.environ.get('EUMETSAT_CONSUMER_KEY')
    secret = os.environ.get('EUMETSAT_CONSUMER_SECRET')
    if not key or not secret:
        print("ERROR: EUMETSAT_CONSUMER_KEY and EUMETSAT_CONSUMER_SECRET must be set in .env")
        sys.exit(1)
    return key, secret


def setup_datastore(key, secret):
    """Initialize EUMETSAT Data Store with OAuth2 credentials."""
    import eumdac
    credentials = eumdac.AccessToken((key, secret))
    datastore = eumdac.DataStore(credentials)
    return datastore


def find_product(collection, target_time):
    """Find the MSG product closest to the target time."""
    dt_start = target_time - timedelta(minutes=8)
    dt_end = target_time + timedelta(minutes=8)
    products = list(collection.search(dtstart=dt_start, dtend=dt_end))
    if not products:
        return None
    # Return the one closest to target
    products.sort(key=lambda p: abs(p.sensing_start.replace(tzinfo=None) - target_time))
    return products[0]


def download_native(product, download_dir):
    """Download .nat file from product, return filepath."""
    download_dir.mkdir(parents=True, exist_ok=True)
    for entry in product.entries:
        if str(entry).endswith('.nat'):
            filepath = download_dir / str(entry)
            if filepath.exists():
                print(f"    Already downloaded: {filepath.name}")
                return filepath
            with product.open(entry=entry) as fsrc:
                content = fsrc.read()
                with open(filepath, 'wb') as fdst:
                    fdst.write(content)
            size_mb = len(content) / 1024 / 1024
            print(f"    Downloaded: {filepath.name} ({size_mb:.0f} MB)")
            return filepath
    return None


def process_to_cog(nat_filepath, timestamp_str, vis_dir, ir_dir):
    """Process native file to Natural Colour and IR COGs."""
    from satpy import Scene
    from pyresample import create_area_def
    import rioxarray

    vis_path = vis_dir / f'{timestamp_str}.tif'
    ir_path = ir_dir / f'{timestamp_str}.tif'

    # Skip if both outputs exist
    if vis_path.exists() and ir_path.exists():
        print(f"    Both COGs exist, skipping processing")
        return True

    # Load scene
    scn = Scene(filenames=[str(nat_filepath)], reader='seviri_l1b_native')

    # Define target area
    area_def = create_area_def(
        'euro_atlantic',
        {'proj': 'longlat', 'datum': 'WGS84'},
        area_extent=AREA_EXTENT,
        resolution=AREA_RESOLUTION,
        units='degrees',
        description='Euro-Atlantic domain for storm tracking'
    )

    # Process Natural Colour RGB
    if not vis_path.exists():
        scn.load(['natural_color'])
        resampled = scn.resample(area_def, resampler='nearest')

        # Save intermediate GeoTIFF
        tmp_vis = str(nat_filepath) + '_vis.tif'
        resampled.save_dataset('natural_color', tmp_vis, writer='geotiff')

        # Convert to COG
        ds = rioxarray.open_rasterio(tmp_vis)
        vis_dir.mkdir(parents=True, exist_ok=True)
        ds.rio.to_raster(str(vis_path), driver='COG', compress='LZW')
        ds.close()
        os.remove(tmp_vis)
        size_mb = vis_path.stat().st_size / 1024 / 1024
        print(f"    Natural Colour COG: {vis_path.name} ({size_mb:.1f} MB)")

        # Unload to free memory
        scn.unload()
        del resampled

    # Process IR 10.8μm
    if not ir_path.exists():
        scn.load(['IR_108'])
        resampled = scn.resample(area_def, resampler='nearest')

        tmp_ir = str(nat_filepath) + '_ir.tif'
        resampled.save_dataset('IR_108', tmp_ir, writer='geotiff')

        ds = rioxarray.open_rasterio(tmp_ir)
        ir_dir.mkdir(parents=True, exist_ok=True)
        ds.rio.to_raster(str(ir_path), driver='COG', compress='LZW')
        ds.close()
        os.remove(tmp_ir)
        size_mb = ir_path.stat().st_size / 1024 / 1024
        print(f"    IR 10.8μm COG: {ir_path.name} ({size_mb:.1f} MB)")

        scn.unload()
        del resampled

    return True


def generate_timestamps(start, end, interval_hours):
    """Generate list of target timestamps."""
    timestamps = []
    current = start
    while current <= end:
        timestamps.append(current)
        current += timedelta(hours=interval_hours)
    return timestamps


def main():
    parser = argparse.ArgumentParser(description='Fetch EUMETSAT MSG SEVIRI imagery')
    parser.add_argument('--test', action='store_true',
                        help='Process single test timestamp (Jan 27 12:00 UTC)')
    parser.add_argument('--interval', type=int, default=DEFAULT_INTERVAL_HOURS,
                        help=f'Hours between timestamps (default: {DEFAULT_INTERVAL_HOURS})')
    parser.add_argument('--start', type=str, default=None,
                        help='Start datetime (YYYY-MM-DDTHH)')
    parser.add_argument('--end', type=str, default=None,
                        help='End datetime (YYYY-MM-DDTHH)')
    parser.add_argument('--keep-native', action='store_true',
                        help='Keep raw .nat files after processing')
    args = parser.parse_args()

    # Parse time range
    if args.test:
        start = datetime(2026, 1, 27, 12, 0)
        end = start
        interval = 1
        print("=== TEST MODE: Single timestamp (2026-01-27T12:00Z) ===\n")
    else:
        start = datetime.fromisoformat(args.start) if args.start else DEFAULT_START
        end = datetime.fromisoformat(args.end) if args.end else DEFAULT_END
        interval = args.interval

    timestamps = generate_timestamps(start, end, interval)
    print(f"EUMETSAT MSG SEVIRI Acquisition")
    print(f"Collection: {COLLECTION_ID}")
    print(f"Time range: {start.isoformat()} → {end.isoformat()}")
    print(f"Interval: {interval}h → {len(timestamps)} timestamps")
    print(f"Domain: {AREA_EXTENT[0]}W-{AREA_EXTENT[2]}E, {AREA_EXTENT[1]}N-{AREA_EXTENT[3]}N")
    print(f"Output VIS: {VIS_OUTPUT_DIR}")
    print(f"Output IR:  {IR_OUTPUT_DIR}")
    print()

    # Setup
    key, secret = get_credentials()
    datastore = setup_datastore(key, secret)
    collection = datastore.get_collection(COLLECTION_ID)
    print(f"Connected to: {collection.title}\n")

    VIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    # Process each timestamp
    success = 0
    failed = 0
    skipped = 0

    for i, ts in enumerate(timestamps):
        ts_str = ts.strftime('%Y-%m-%dT%H-%M')
        vis_exists = (VIS_OUTPUT_DIR / f'{ts_str}.tif').exists()
        ir_exists = (IR_OUTPUT_DIR / f'{ts_str}.tif').exists()

        if vis_exists and ir_exists:
            print(f"[{i+1}/{len(timestamps)}] {ts_str} — already processed, skipping")
            skipped += 1
            continue

        print(f"[{i+1}/{len(timestamps)}] {ts_str}")

        # Find product
        product = find_product(collection, ts)
        if not product:
            print(f"    WARNING: No product found near {ts_str}")
            failed += 1
            continue

        print(f"    Product: {product}")

        # Download
        try:
            nat_path = download_native(product, TMP_DIR)
            if not nat_path:
                print(f"    ERROR: No .nat file in product")
                failed += 1
                continue
        except Exception as e:
            print(f"    ERROR downloading: {e}")
            failed += 1
            continue

        # Process to COG
        try:
            process_to_cog(nat_path, ts_str, VIS_OUTPUT_DIR, IR_OUTPUT_DIR)
            success += 1
        except Exception as e:
            print(f"    ERROR processing: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            continue
        finally:
            # Clean up raw file to save disk
            if not args.keep_native and nat_path and nat_path.exists():
                nat_path.unlink()
                print(f"    Cleaned up raw file")

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Processed: {success}")
    print(f"  Skipped (existing): {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Total: {success + skipped + failed}/{len(timestamps)}")

    vis_files = list(VIS_OUTPUT_DIR.glob('*.tif'))
    ir_files = list(IR_OUTPUT_DIR.glob('*.tif'))
    vis_size = sum(f.stat().st_size for f in vis_files) / 1024 / 1024
    ir_size = sum(f.stat().st_size for f in ir_files) / 1024 / 1024

    print(f"\n  Natural Colour COGs: {len(vis_files)} files ({vis_size:.0f} MB)")
    print(f"  IR 10.8μm COGs:     {len(ir_files)} files ({ir_size:.0f} MB)")
    print(f"  Total disk:          {vis_size + ir_size:.0f} MB")
    print(f"\nAttribution: Contains modified EUMETSAT Meteosat data 2026")


if __name__ == '__main__':
    main()
