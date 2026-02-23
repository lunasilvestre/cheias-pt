"""Dataset 6: Precondition Index — Computed from soil moisture + precipitation"""
import numpy as np
import pandas as pd
from pathlib import Path

# Load the soil moisture and precipitation data
sm = pd.read_parquet("data/temporal/moisture/soil_moisture.parquet")
precip = pd.read_parquet("data/temporal/precipitation/precipitation.parquet")

print(f"Soil moisture: {len(sm)} records", flush=True)
print(f"Precipitation: {len(precip)} records", flush=True)

# Merge on date + lat + lon
df = sm.merge(precip, on=["date", "lat", "lon"], how="inner")
print(f"Merged: {len(df)} records", flush=True)

# Porosity constant (sandy loam typical for Portuguese basins)
POROSITY = 0.42  # m³/m³
ROOT_DEPTH_MM = 1000  # 1m root zone in mm

# Compute remaining capacity
df["remaining_capacity_mm"] = (POROSITY - df["sm_rootzone"]) * ROOT_DEPTH_MM
df["remaining_capacity_mm"] = df["remaining_capacity_mm"].clip(lower=1.0)  # avoid div/0

# Component 1: Forward-looking — 3-day precip / remaining capacity
df["ratio_3d"] = df["precip_3d"] / df["remaining_capacity_mm"]

# Component 2: Antecedent wetness (normalized 14-day precip)
precip_14d_p90 = df["precip_14d"].quantile(0.90)
df["antecedent_score"] = (df["precip_14d"] / precip_14d_p90).clip(upper=1.0)

# Combined score
df["precondition_index"] = 0.6 * df["ratio_3d"] + 0.4 * df["antecedent_score"]

# Classification
def classify(score):
    if score < 0.3: return "green"
    elif score < 0.6: return "yellow"
    elif score < 0.9: return "orange"
    else: return "red"

df["risk_class"] = df["precondition_index"].apply(classify)

outpath = Path("data/temporal/precondition/precondition.parquet")
outpath.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(outpath)
print(f"Saved: {outpath}", flush=True)
print(f"\nRisk class distribution (all dates, all points):", flush=True)
print(df["risk_class"].value_counts(normalize=True).round(3), flush=True)
print(f"\nPeak precondition days (>50% of grid in orange/red):", flush=True)
daily_risk = df.groupby("date")["risk_class"].apply(
    lambda x: (x.isin(["orange", "red"])).mean()
).reset_index(name="frac_high_risk")
peak_days = daily_risk[daily_risk["frac_high_risk"] > 0.5].sort_values("frac_high_risk", ascending=False)
print(peak_days.head(10), flush=True)
