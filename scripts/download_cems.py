"""
download_cems.py
================
Downloads and processes all Portuguese CEMS flood extent data.

Queries the CEMS Rapid Mapping API for EMSR861 and EMSR864,
identifies Portuguese AOIs with downloadable products,
downloads ZIPs, extracts observedEventA shapefiles,
converts to enriched GeoJSON, and rebuilds merged files.

Run: source .venv/bin/activate && python scripts/download_cems.py
"""

import json
import os
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent / "data" / "flood-extent"
API_BASE = "https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/"
DL_BASE = "https://rapidmapping.emergency.copernicus.eu/backend"

ACTIVATIONS = {
    "EMSR861": "Kristin",
    "EMSR864": "Leonardo/Marta",
}

# Portuguese AOI names (lowercase) — from API inspection
PORTUGAL_AOIS = {
    "EMSR861": {5: "Coimbra", 6: "Castelo Branco"},
    "EMSR864": {
        1: "Ermidas Sado",
        2: "Rio de Moinhos",
        3: "Salvaterra de Magos",
        4: "Leiria",
        5: "Coimbra",
        6: "Aveiro",
        7: "Porto",
        8: "Marco de Canaveses",
        9: "Peso de Regua",
        10: "Santo Tirso",
        11: "Barcelos",
        12: "Ponte de Lima",
        13: "Chaves",
        14: "Tomar",
        15: "Mertola",
        16: "Silves",
        17: "Mira River",
        18: "Minho river",
    },
}

# Already downloaded — skip these
ALREADY_HAVE = {
    ("EMSR861", 5, "DEL_PRODUCT", 1),
    ("EMSR864", 1, "DEL_PRODUCT", 1),
    ("EMSR864", 2, "DEL_PRODUCT", 1),
    ("EMSR864", 3, "DEL_PRODUCT", 1),
    ("EMSR864", 3, "DEL_MONIT01", 2),
    ("EMSR864", 3, "DEL_MONIT02", 1),
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def product_code(mon_number: int) -> str:
    """Convert monitoring number to product code."""
    if mon_number == 0:
        return "DEL_PRODUCT"
    return f"DEL_MONIT{mon_number:02d}"


def product_type_label(mon_number: int) -> str:
    """Human-readable product type."""
    if mon_number == 0:
        return "Delineation"
    return f"Monitoring {mon_number}"


def download_url(activation: str, aoi_num: int, prod_code: str, version: int) -> str:
    """Construct CEMS download URL."""
    aoi_str = f"AOI{aoi_num:02d}"
    filename = f"{activation}_{aoi_str}_{prod_code}_v{version}.zip"
    return f"{DL_BASE}/{activation}/{aoi_str}/{prod_code}/{filename}"


def fetch_activation(code: str) -> dict:
    """Fetch activation details from CEMS API."""
    url = f"{API_BASE}?code={code}"
    print(f"  Fetching {url}")
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    if isinstance(data, list):
        return data[0] if data else {}
    if isinstance(data, dict) and "results" in data:
        return data["results"][0] if data["results"] else {}
    return data


def download_file(url: str, dest: Path) -> bool:
    """Download a file with progress indication."""
    if dest.exists():
        print(f"    Already exists: {dest.name}")
        return True
    print(f"    Downloading: {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            data = resp.read()
            dest.write_bytes(data)
            size_mb = len(data) / (1024 * 1024)
            print(f"    Saved: {dest.name} ({size_mb:.1f} MB)")
            return True
    except Exception as e:
        print(f"    FAILED: {e}")
        return False


def extract_zip(zip_path: Path) -> Path:
    """Extract ZIP to directory, return extraction path."""
    extract_dir = zip_path.with_suffix("")
    if extract_dir.exists():
        print(f"    Already extracted: {extract_dir.name}")
        return extract_dir
    print(f"    Extracting: {zip_path.name}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    return extract_dir


def find_observed_event_shp(extract_dir: Path) -> Path | None:
    """Find the observedEventA shapefile in extracted product."""
    for shp in extract_dir.rglob("*observedEventA*.shp"):
        return shp
    # Some products use different naming
    for shp in extract_dir.rglob("*observed_event*.shp"):
        return shp
    return None


def find_image_footprint_shp(extract_dir: Path) -> Path | None:
    """Find the imageFootprintA shapefile for sensor metadata."""
    for shp in extract_dir.rglob("*imageFootprintA*.shp"):
        return shp
    return None


def process_product(
    activation: str,
    aoi_num: int,
    aoi_name: str,
    mon_number: int,
    version: int,
    storm: str,
) -> gpd.GeoDataFrame | None:
    """Process a single CEMS product: download, extract, convert to GeoDataFrame."""
    prod_code = product_code(mon_number)
    aoi_str = f"AOI{aoi_num:02d}"
    zip_name = f"{activation}_{aoi_str}_{prod_code}_v{version}.zip"
    zip_path = BASE_DIR / zip_name

    # Download
    url = download_url(activation, aoi_num, prod_code, version)
    if not download_file(url, zip_path):
        return None

    # Extract
    extract_dir = extract_zip(zip_path)

    # Find observedEventA shapefile
    shp_path = find_observed_event_shp(extract_dir)
    if shp_path is None:
        print(f"    WARNING: No observedEventA shapefile found in {extract_dir.name}")
        return None

    # Read shapefile
    gdf = gpd.read_file(shp_path)
    if gdf.empty:
        print(f"    WARNING: Empty observedEventA in {extract_dir.name}")
        return None

    # Ensure WGS84
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # Try to get sensor info from imageFootprintA
    sensor = ""
    source_date = ""
    fp_shp = find_image_footprint_shp(extract_dir)
    if fp_shp is not None:
        try:
            fp = gpd.read_file(fp_shp)
            if not fp.empty:
                # Get sensor from first feature
                for col in ["sensor", "source", "satellite", "sensorName"]:
                    if col in fp.columns:
                        sensor = str(fp[col].iloc[0])
                        break
                for col in ["acq_date", "source_dat", "sourceDate", "date"]:
                    if col in fp.columns:
                        source_date = str(fp[col].iloc[0])
                        break
        except Exception:
            pass

    # Enrich with metadata
    gdf["activation"] = activation
    gdf["aoi"] = aoi_str
    gdf["locality"] = aoi_name
    gdf["source_date"] = source_date
    gdf["sensor"] = sensor
    gdf["product_type"] = product_type_label(mon_number)
    gdf["storm"] = storm

    # Calculate area in hectares (ETRS89-LAEA Europe, equal-area)
    gdf_proj = gdf.to_crs(epsg=3035)
    gdf["area_ha"] = gdf_proj.geometry.area / 10000

    # Keep useful original columns
    keep_cols = [
        "geometry", "activation", "aoi", "locality", "source_date",
        "sensor", "product_type", "storm", "area_ha",
    ]
    # Preserve CEMS classification columns if present
    for col in ["event_type", "obj_desc", "det_method", "notation",
                "eventType", "objDesc", "detMethod"]:
        if col in gdf.columns:
            keep_cols.append(col)

    gdf = gdf[[c for c in keep_cols if c in gdf.columns]]

    # Standardize column names
    rename = {
        "eventType": "event_type",
        "objDesc": "obj_desc",
        "detMethod": "det_method",
    }
    gdf = gdf.rename(columns={k: v for k, v in rename.items() if k in gdf.columns})

    n_features = len(gdf)
    total_ha = gdf["area_ha"].sum()
    print(f"    Processed: {n_features} features, {total_ha:,.0f} ha")
    return gdf


# ── Main pipeline ─────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("CEMS Flood Extent Download & Processing")
    print("=" * 60)

    os.makedirs(BASE_DIR, exist_ok=True)

    # Collect all GeoDataFrames per activation
    all_gdfs = {"EMSR861": [], "EMSR864": []}

    for activation, storm in ACTIVATIONS.items():
        print(f"\n{'─' * 60}")
        print(f"Activation: {activation} ({storm})")
        print(f"{'─' * 60}")

        # Fetch activation details
        act_data = fetch_activation(activation)
        if not act_data:
            print(f"  ERROR: Could not fetch activation data")
            continue

        aois = act_data.get("aois", [])
        pt_aois = PORTUGAL_AOIS.get(activation, {})

        for aoi in aois:
            aoi_num = aoi.get("number", 0)
            aoi_name = aoi.get("name", "unnamed")

            # Skip non-Portugal AOIs
            if aoi_num not in pt_aois:
                continue

            print(f"\n  AOI{aoi_num:02d}: {aoi_name}")

            products = aoi.get("products", [])
            for prod in products:
                prod_type = prod.get("type", "")
                mon_number = prod.get("monitoringNumber", 0)

                # Only process DEL (delineation) products, not FEP or GRA
                if prod_type not in ("DEL",):
                    continue

                # Check if product has data
                version_info = prod.get("version", {})
                if isinstance(version_info, dict):
                    status = version_info.get("statusCode", "")
                    version_num = version_info.get("number", 1)
                else:
                    status = ""
                    version_num = 1

                has_download = prod.get("downloadPath", False)

                if status != "F" or not has_download:
                    prod_code = product_code(mon_number)
                    reason = version_info.get("reason", "") if isinstance(version_info, dict) else ""
                    print(f"    Skipping {prod_code}: status={status}, reason={reason}")
                    continue

                prod_code = product_code(mon_number)

                # Check if already downloaded
                key = (activation, aoi_num, prod_code, version_num)
                if key in ALREADY_HAVE:
                    print(f"    {prod_code} v{version_num}: already have, re-processing...")

                # Process the product
                gdf = process_product(
                    activation, aoi_num, aoi_name,
                    mon_number, version_num, storm,
                )
                if gdf is not None and not gdf.empty:
                    all_gdfs[activation].append(gdf)

    # ── Merge and save ────────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("Merging and saving GeoJSON files...")
    print(f"{'=' * 60}")

    combined_parts = []

    for activation in ACTIVATIONS:
        gdfs = all_gdfs[activation]
        if not gdfs:
            print(f"\n  {activation}: No data to merge")
            continue

        merged = pd.concat(gdfs, ignore_index=True)
        merged = gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:4326")

        out_path = BASE_DIR / f"{activation.lower()}.geojson"
        merged.to_file(out_path, driver="GeoJSON")

        n = len(merged)
        total_ha = merged["area_ha"].sum()
        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"\n  {activation}: {n} features, {total_ha:,.0f} ha, {size_mb:.1f} MB")
        print(f"    Saved: {out_path.name}")

        # Per-AOI summary
        for (aoi, pt), group in merged.groupby(["aoi", "product_type"]):
            print(f"    {aoi} {pt}: {len(group)} features, {group['area_ha'].sum():,.0f} ha")

        combined_parts.append(merged)

    # Combined
    if combined_parts:
        combined = pd.concat(combined_parts, ignore_index=True)
        combined = gpd.GeoDataFrame(combined, geometry="geometry", crs="EPSG:4326")
        out_path = BASE_DIR / "combined.geojson"
        combined.to_file(out_path, driver="GeoJSON")
        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"\n  Combined: {len(combined)} features, {combined['area_ha'].sum():,.0f} ha, {size_mb:.1f} MB")

    print(f"\n{'=' * 60}")
    print("Done! Run tippecanoe to rebuild PMTiles.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
