"""Validation: Sanity check all temporal datasets"""
import pandas as pd
import xarray as xr
from pathlib import Path

datasets = {
    "Soil moisture": "data/temporal/moisture/soil_moisture.parquet",
    "Precipitation": "data/temporal/precipitation/precipitation.parquet",
    "Discharge": "data/temporal/discharge/discharge.parquet",
    "Precondition": "data/temporal/precondition/precondition.parquet",
}

# Optional
if Path("data/temporal/ivt/ivt.parquet").exists():
    datasets["IVT proxy"] = "data/temporal/ivt/ivt.parquet"

for name, path in datasets.items():
    df = pd.read_parquet(path)
    print(f"\n{name}: {len(df)} records")
    print(f"  Dates: {df['date'].min()} → {df['date'].max()} ({df['date'].nunique()} days)")
    if 'lat' in df.columns:
        print(f"  Grid points: {df.groupby(['lat','lon']).ngroups}")
    if 'basin' in df.columns:
        print(f"  Basins: {df['basin'].unique().tolist()}")

# Check SST
sst_nc = Path("data/temporal/sst/sst_anomaly.nc")
if sst_nc.exists():
    sst = xr.open_dataset(sst_nc)
    print(f"\nSST anomaly: {dict(sst.dims)}")
    print(f"  Time: {str(sst.time.values[0])[:10]} → {str(sst.time.values[-1])[:10]} ({len(sst.time)} days)")
    sst_tifs = list(Path("data/temporal/sst/daily").glob("sst_anom_*.tif"))
    print(f"  COG files: {len(sst_tifs)}")
    sst.close()

# Key validation: precondition index during storms
pc = pd.read_parquet("data/temporal/precondition/precondition.parquet")
print("\n--- VALIDATION: Precondition index should peak during storms ---")
storm_dates = {
    "Kristin": ("2026-01-27", "2026-01-30"),
    "Leonardo": ("2026-02-03", "2026-02-07"),
    "Marta": ("2026-02-08", "2026-02-10"),
}
for storm, (start, end) in storm_dates.items():
    mask = (pc["date"] >= start) & (pc["date"] <= end)
    frac_red = (pc.loc[mask, "risk_class"].isin(["orange", "red"])).mean()
    print(f"  {storm}: {frac_red:.0%} of grid in orange/red")

# Discharge validation
print("\n--- VALIDATION: Discharge should show storm response ---")
dis = pd.read_parquet("data/temporal/discharge/discharge.parquet")
for storm, (start, end) in storm_dates.items():
    mask = (dis["date"] >= start) & (dis["date"] <= end)
    storm_dis = dis.loc[mask]
    if len(storm_dis) > 0:
        peak = storm_dis.loc[storm_dis["discharge"].idxmax()]
        print(f"  {storm}: Peak {peak['discharge']:.0f} m³/s at {peak['name']} on {peak['date'].strftime('%Y-%m-%d')}")

# File sizes
print("\n--- FILE SIZES ---")
temporal_dir = Path("data/temporal")
for p in sorted(temporal_dir.rglob("*")):
    if p.is_file() and not p.name.startswith(".") and p.suffix in (".parquet", ".nc", ".tif"):
        size_mb = p.stat().st_size / 1024 / 1024
        if size_mb > 0.1:
            print(f"  {p.relative_to(temporal_dir)}: {size_mb:.1f} MB")
        elif p.suffix != ".tif":  # Skip individual COGs
            print(f"  {p.relative_to(temporal_dir)}: {p.stat().st_size / 1024:.0f} KB")
