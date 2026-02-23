"""Datasets 2+3 Combined: Soil Moisture + Precipitation from Open-Meteo Archive API
Uses the optimization from the prompt: single API call per grid point for both variables.
"""
import numpy as np
import pandas as pd
import requests
import time
from pathlib import Path
from itertools import product

# Portugal bounding box with 0.25° spacing
lats = np.arange(36.75, 42.50, 0.25)  # ~23 points
lons = np.arange(-9.75, -6.00, 0.25)  # ~15 points
grid_points = list(product(lats, lons))
print(f"Grid: {len(lats)} x {len(lons)} = {len(grid_points)} points")

sm_records = []
precip_records = []

for i, (lat, lon) in enumerate(grid_points):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": float(lat),
        "longitude": float(lon),
        "start_date": "2025-12-01",
        "end_date": "2026-02-15",
        "daily": "soil_moisture_0_to_7cm_mean,soil_moisture_7_to_28cm_mean,soil_moisture_28_to_100cm_mean,precipitation_sum,rain_sum",
        "timezone": "UTC"
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        daily = data["daily"]
        for j, date in enumerate(daily["time"]):
            sm_records.append({
                "date": date,
                "lat": float(lat),
                "lon": float(lon),
                "sm_0_7": daily["soil_moisture_0_to_7cm_mean"][j],
                "sm_7_28": daily["soil_moisture_7_to_28cm_mean"][j],
                "sm_28_100": daily["soil_moisture_28_to_100cm_mean"][j],
            })
            precip_records.append({
                "date": date,
                "lat": float(lat),
                "lon": float(lon),
                "precip_mm": daily["precipitation_sum"][j],
                "rain_mm": daily["rain_sum"][j],
            })

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(grid_points)} points fetched")
    except Exception as e:
        print(f"  Point ({lat}, {lon}) failed: {e}")

    time.sleep(0.3)

# Process soil moisture
print("\nProcessing soil moisture...")
sm_df = pd.DataFrame(sm_records)
sm_df["date"] = pd.to_datetime(sm_df["date"])
sm_df["sm_rootzone"] = (
    sm_df["sm_0_7"] * 0.07 +
    sm_df["sm_7_28"] * 0.21 +
    sm_df["sm_28_100"] * 0.72
) / (0.07 + 0.21 + 0.72)

sm_path = Path("data/temporal/moisture/soil_moisture.parquet")
sm_path.parent.mkdir(parents=True, exist_ok=True)
sm_df.to_parquet(sm_path)
print(f"Saved: {sm_path} ({len(sm_df)} records, {sm_df['date'].nunique()} days, {len(grid_points)} points)")
print(f"Root-zone moisture range: {sm_df['sm_rootzone'].min():.3f} - {sm_df['sm_rootzone'].max():.3f} m³/m³")

# Process precipitation with rolling accumulations
print("\nProcessing precipitation...")
precip_df = pd.DataFrame(precip_records)
precip_df["date"] = pd.to_datetime(precip_df["date"])

for point, grp in precip_df.groupby(["lat", "lon"]):
    idx = grp.index
    precip_df.loc[idx, "precip_3d"] = grp["precip_mm"].rolling(3, min_periods=1).sum()
    precip_df.loc[idx, "precip_7d"] = grp["precip_mm"].rolling(7, min_periods=1).sum()
    precip_df.loc[idx, "precip_14d"] = grp["precip_mm"].rolling(14, min_periods=1).sum()
    precip_df.loc[idx, "precip_30d"] = grp["precip_mm"].rolling(30, min_periods=1).sum()

precip_path = Path("data/temporal/precipitation/precipitation.parquet")
precip_path.parent.mkdir(parents=True, exist_ok=True)
precip_df.to_parquet(precip_path)
print(f"Saved: {precip_path} ({len(precip_df)} records)")
print(f"Max daily precip: {precip_df['precip_mm'].max():.1f} mm")
print(f"Max 7-day accumulation: {precip_df['precip_7d'].max():.1f} mm")
