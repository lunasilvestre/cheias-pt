"""Dataset 4: River Discharge from Open-Meteo Flood API (GloFAS proxy)"""
import numpy as np
import pandas as pd
import requests
import time
from pathlib import Path

river_points = [
    {"name": "Tejo - Santarém", "lat": 39.24, "lon": -8.68, "basin": "Tejo"},
    {"name": "Tejo - Vila Franca de Xira", "lat": 38.95, "lon": -8.99, "basin": "Tejo"},
    {"name": "Sado - Alcácer do Sal", "lat": 38.37, "lon": -8.51, "basin": "Sado"},
    {"name": "Mondego - Coimbra", "lat": 40.21, "lon": -8.43, "basin": "Mondego"},
    {"name": "Douro - Porto", "lat": 41.14, "lon": -8.61, "basin": "Douro"},
    {"name": "Douro - Peso da Régua", "lat": 41.16, "lon": -7.79, "basin": "Douro"},
    {"name": "Guadiana - Mértola", "lat": 37.64, "lon": -7.66, "basin": "Guadiana"},
    {"name": "Minho - Valença", "lat": 42.03, "lon": -8.64, "basin": "Minho"},
    {"name": "Vouga - Aveiro", "lat": 40.64, "lon": -8.65, "basin": "Vouga"},
    {"name": "Lis - Leiria", "lat": 39.74, "lon": -8.81, "basin": "Lis"},
    {"name": "Zêzere - Tomar", "lat": 39.60, "lon": -8.41, "basin": "Zêzere"},
]

all_records = []

for point in river_points:
    url = "https://flood-api.open-meteo.com/v1/flood"
    params = {
        "latitude": point["lat"],
        "longitude": point["lon"],
        "start_date": "2025-12-01",
        "end_date": "2026-02-15",
        "daily": "river_discharge,river_discharge_median,river_discharge_max,river_discharge_min",
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        daily = data["daily"]
        for j, date in enumerate(daily["time"]):
            all_records.append({
                "date": date,
                "name": point["name"],
                "basin": point["basin"],
                "lat": point["lat"],
                "lon": point["lon"],
                "discharge": daily["river_discharge"][j],
                "discharge_median": daily["river_discharge_median"][j],
                "discharge_max": daily["river_discharge_max"][j],
                "discharge_min": daily["river_discharge_min"][j],
            })
        print(f"  {point['name']}: OK")
    except Exception as e:
        print(f"  {point['name']}: FAILED ({e})")

    time.sleep(0.5)

df = pd.DataFrame(all_records)
df["date"] = pd.to_datetime(df["date"])

# Compute discharge ratio (current / median)
df["discharge_ratio"] = df["discharge"] / df["discharge_median"].replace(0, np.nan)

outpath = Path("data/temporal/discharge/discharge.parquet")
outpath.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(outpath)
print(f"\nSaved: {outpath}")
print(f"Peak discharge ratios:")
for name, grp in df.groupby("name"):
    peak = grp.loc[grp["discharge_ratio"].idxmax()]
    print(f"  {name}: {peak['discharge_ratio']:.1f}x median on {peak['date'].strftime('%Y-%m-%d')}")
