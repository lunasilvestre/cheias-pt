"""Dataset 5: IVT Proxy — Atmospheric River Visualization
Uses surface-level moisture flux as IVT proxy since Open-Meteo doesn't expose
pressure-level specific humidity. Coarser grid (1°) to keep API calls manageable.

Computes: moisture_flux ≈ precip + (humidity × wind × directional_weight)
Where directional_weight favors SW→NE flow (typical atmospheric river trajectory).
"""
import numpy as np
import pandas as pd
import requests
import time
from pathlib import Path
from itertools import product

# 1° grid across North Atlantic → Iberia (coarser than prompt's 0.5°)
ivt_lats = np.arange(25, 55, 1.0)  # 30 points
ivt_lons = np.arange(-45, 5, 1.0)  # 50 points
ivt_grid = list(product(ivt_lats, ivt_lons))
print(f"IVT proxy grid: {len(ivt_lats)} x {len(ivt_lons)} = {len(ivt_grid)} points", flush=True)
print(f"Estimated time: ~{len(ivt_grid) * 0.25 / 60:.0f} minutes", flush=True)

all_records = []
failed = 0

for i, (lat, lon) in enumerate(ivt_grid):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": float(lat),
        "longitude": float(lon),
        "start_date": "2025-12-01",
        "end_date": "2026-02-15",
        "hourly": "relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation",
        "timezone": "UTC",
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        hourly = data["hourly"]

        # Build hourly dataframe
        hdf = pd.DataFrame({
            "time": pd.to_datetime(hourly["time"]),
            "rh": hourly["relative_humidity_2m"],
            "ws": hourly["wind_speed_10m"],
            "wd": hourly["wind_direction_10m"],
            "precip": hourly["precipitation"],
        })
        hdf["date"] = hdf["time"].dt.date

        # Compute moisture flux proxy per hour:
        # moisture_flux = (RH/100) * wind_speed * directional_weight
        # directional_weight = max(0, cos(wind_dir - 225°)) [favors SW→NE flow]
        # 225° = coming FROM southwest
        hdf["rh_frac"] = hdf["rh"].fillna(50) / 100.0
        hdf["ws_clean"] = hdf["ws"].fillna(0)
        wd_rad = np.deg2rad(hdf["wd"].fillna(0) - 225)
        hdf["dir_weight"] = np.clip(np.cos(wd_rad), 0, 1)
        hdf["moisture_flux"] = hdf["rh_frac"] * hdf["ws_clean"] * hdf["dir_weight"]

        # Aggregate to daily
        daily = hdf.groupby("date").agg({
            "moisture_flux": "mean",
            "rh": "mean",
            "ws": "mean",
            "precip": "sum",
        }).reset_index()

        for _, row in daily.iterrows():
            all_records.append({
                "date": row["date"],
                "lat": float(lat),
                "lon": float(lon),
                "moisture_flux": row["moisture_flux"],
                "rh_mean": row["rh"],
                "wind_mean": row["ws"],
                "precip_sum": row["precip"],
            })

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(ivt_grid)} ({(i+1)/len(ivt_grid)*100:.0f}%) — {failed} failures", flush=True)
    except Exception as e:
        failed += 1
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(ivt_grid)} ({(i+1)/len(ivt_grid)*100:.0f}%) — {failed} failures", flush=True)

    time.sleep(0.2)

df = pd.DataFrame(all_records)
df["date"] = pd.to_datetime(df["date"])

outpath = Path("data/temporal/ivt/ivt.parquet")
outpath.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(outpath)
print(f"\nSaved: {outpath} ({len(df)} records, {df['date'].nunique()} days, {len(ivt_grid)} grid points)", flush=True)
print(f"Moisture flux range: {df['moisture_flux'].min():.1f} - {df['moisture_flux'].max():.1f}", flush=True)
print(f"Failed points: {failed}/{len(ivt_grid)}", flush=True)
