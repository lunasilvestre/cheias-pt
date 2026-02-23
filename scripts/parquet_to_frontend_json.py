#!/usr/bin/env python3
"""Convert temporal backbone Parquet files to frontend-consumable JSON.

Reads from data/temporal/ and writes to data/frontend/.
Idempotent — safe to re-run.
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
TEMPORAL = BASE / "data" / "temporal"
OUTPUT = BASE / "data" / "frontend"

# Field capacity for soil moisture normalisation (m³/m³)
FIELD_CAPACITY = 0.42

# Storm window for precipitation totals
STORM_START = "2026-01-25"
STORM_END = "2026-02-07"


def ensure_output_dir():
    OUTPUT.mkdir(parents=True, exist_ok=True)


# ---------- 1. Soil Moisture Frames ----------

def soil_moisture_frames():
    """Daily frames of normalised root-zone soil moisture."""
    df = pd.read_parquet(TEMPORAL / "moisture" / "soil_moisture.parquet")

    # Drop points that are always zero (ocean/border artefacts)
    always_zero = df.groupby(["lat", "lon"])["sm_rootzone"].max()
    valid = always_zero[always_zero > 0].index
    df = df.set_index(["lat", "lon"]).loc[valid].reset_index()

    df["value"] = (df["sm_rootzone"] / FIELD_CAPACITY).clip(upper=1.0).round(3)
    df["lat"] = df["lat"].round(2)
    df["lon"] = df["lon"].round(2)
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

    frames = []
    for date_str, group in df.groupby("date_str"):
        pts = group[["lat", "lon", "value"]].to_dict("records")
        frames.append({"date": date_str, "points": pts})

    frames.sort(key=lambda f: f["date"])
    return frames


# ---------- 2. Precipitation Storm Totals ----------

def precip_storm_totals():
    """Accumulated precipitation during the storm window."""
    df = pd.read_parquet(TEMPORAL / "precipitation" / "precipitation.parquet")
    mask = (df["date"] >= STORM_START) & (df["date"] <= STORM_END)
    storm = df[mask].groupby(["lat", "lon"])["precip_mm"].sum().reset_index()
    storm.rename(columns={"precip_mm": "total_mm"}, inplace=True)
    storm["total_mm"] = storm["total_mm"].round(1)
    storm["lat"] = storm["lat"].round(2)
    storm["lon"] = storm["lon"].round(2)
    # Drop zero-accumulation points
    storm = storm[storm["total_mm"] > 0]
    return {"points": storm[["lat", "lon", "total_mm"]].to_dict("records")}


# ---------- 3. Precipitation Daily Frames ----------

def precip_frames():
    """Daily precipitation frames."""
    df = pd.read_parquet(TEMPORAL / "precipitation" / "precipitation.parquet")
    df["value"] = df["precip_mm"].round(1)
    df["lat"] = df["lat"].round(2)
    df["lon"] = df["lon"].round(2)
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

    frames = []
    for date_str, group in df.groupby("date_str"):
        pts = group[["lat", "lon", "value"]].to_dict("records")
        frames.append({"date": date_str, "points": pts})

    frames.sort(key=lambda f: f["date"])
    return frames


# ---------- 4. Discharge Timeseries ----------

def discharge_timeseries():
    """Per-station discharge timeseries."""
    df = pd.read_parquet(TEMPORAL / "discharge" / "discharge.parquet")
    stations = []
    for name, group in df.groupby("name"):
        group = group.sort_values("date")
        first = group.iloc[0]
        ts = []
        for _, row in group.iterrows():
            entry = {"date": row["date"].strftime("%Y-%m-%d")}
            entry["discharge"] = round(float(row["discharge"]), 1)
            entry["discharge_ratio"] = round(float(row["discharge_ratio"]), 2)
            ts.append(entry)
        stations.append({
            "name": name,
            "basin": first["basin"],
            "lat": round(float(first["lat"]), 2),
            "lon": round(float(first["lon"]), 2),
            "timeseries": ts,
        })
    return {"stations": stations}


# ---------- 5. Precondition Daily Frames ----------

def precondition_frames():
    """Daily frames of precondition index + risk class."""
    df = pd.read_parquet(TEMPORAL / "precondition" / "precondition.parquet")

    # Filter out always-zero points (same ocean points as moisture)
    dfm = pd.read_parquet(TEMPORAL / "moisture" / "soil_moisture.parquet")
    always_zero = dfm.groupby(["lat", "lon"])["sm_rootzone"].max()
    valid = always_zero[always_zero > 0].index
    df = df.set_index(["lat", "lon"]).loc[valid].reset_index()

    df["index"] = df["precondition_index"].round(3)
    df["lat"] = df["lat"].round(2)
    df["lon"] = df["lon"].round(2)
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

    frames = []
    for date_str, group in df.groupby("date_str"):
        pts = group[["lat", "lon", "index", "risk_class"]].to_dict("records")
        frames.append({"date": date_str, "points": pts})

    frames.sort(key=lambda f: f["date"])
    return frames


# ---------- 6. Precondition Peak Snapshot ----------

def precondition_peak(frames):
    """Single snapshot at peak risk date (highest fraction of orange+red)."""
    best_date = None
    best_frac = -1

    for frame in frames:
        high = sum(1 for p in frame["points"] if p["index"] >= 0.6)
        frac = high / len(frame["points"]) if frame["points"] else 0
        if frac > best_frac:
            best_frac = frac
            best_date = frame["date"]

    peak = next(f for f in frames if f["date"] == best_date)
    return {"date": peak["date"], "points": peak["points"]}


# ---------- 7. IVT Peak Storm Snapshot ----------

def ivt_peak_storm():
    """Single IVT snapshot during Kristin's peak."""
    df = pd.read_parquet(TEMPORAL / "ivt" / "ivt.parquet")
    # Find date with highest mean IVT
    daily_mean = df.groupby("date")["moisture_flux"].mean()
    peak_date = daily_mean.idxmax()

    peak = df[df["date"] == peak_date].copy()
    peak["lat"] = peak["lat"].round(1)
    peak["lon"] = peak["lon"].round(1)
    peak["ivt"] = peak["moisture_flux"].round(1)

    # Filter out near-zero IVT to reduce size
    peak = peak[peak["ivt"] > 5.0]

    return {
        "date": peak_date.strftime("%Y-%m-%d"),
        "points": peak[["lat", "lon", "ivt"]].to_dict("records"),
    }


# ---------- Main ----------

def write_json(name, data):
    path = OUTPUT / name
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    size_kb = path.stat().st_size / 1024
    return size_kb


def main():
    ensure_output_dir()
    results = []

    print("Converting Parquet → frontend JSON...")
    print()

    # 1. Soil moisture
    print("  [1/7] Soil moisture frames...")
    data = soil_moisture_frames()
    kb = write_json("soil-moisture-frames.json", data)
    results.append(("soil-moisture-frames.json", len(data), f"{len(data[0]['points'])} pts/frame", kb))

    # 2. Precip storm totals
    print("  [2/7] Precipitation storm totals...")
    data = precip_storm_totals()
    kb = write_json("precip-storm-totals.json", data)
    results.append(("precip-storm-totals.json", 1, f"{len(data['points'])} points", kb))

    # 3. Precip daily frames
    print("  [3/7] Precipitation daily frames...")
    data = precip_frames()
    kb = write_json("precip-frames.json", data)
    results.append(("precip-frames.json", len(data), f"{len(data[0]['points'])} pts/frame", kb))

    # 4. Discharge timeseries
    print("  [4/7] Discharge timeseries...")
    data = discharge_timeseries()
    kb = write_json("discharge-timeseries.json", data)
    results.append(("discharge-timeseries.json", len(data['stations']), "stations", kb))

    # 5. Precondition frames
    print("  [5/7] Precondition frames...")
    data = precondition_frames()
    kb = write_json("precondition-frames.json", data)
    results.append(("precondition-frames.json", len(data), f"{len(data[0]['points'])} pts/frame", kb))

    # 6. Precondition peak
    print("  [6/7] Precondition peak snapshot...")
    peak = precondition_peak(data)
    kb = write_json("precondition-peak.json", peak)
    results.append(("precondition-peak.json", 1, f"peak={peak['date']}", kb))

    # 7. IVT peak storm
    print("  [7/7] IVT peak storm snapshot...")
    data = ivt_peak_storm()
    kb = write_json("ivt-peak-storm.json", data)
    results.append(("ivt-peak-storm.json", 1, f"peak={data['date']}, {len(data['points'])} pts", kb))

    # Summary
    print()
    print(f"{'File':<32} {'Items':>6}  {'Detail':<24} {'Size':>8}")
    print("-" * 76)
    total_kb = 0
    for name, items, detail, kb in results:
        print(f"{name:<32} {items:>6}  {detail:<24} {kb:>7.1f} KB")
        total_kb += kb
    print("-" * 76)
    print(f"{'TOTAL':<32} {'':>6}  {'':>24} {total_kb:>7.1f} KB")
    print(f"\nAll files written to {OUTPUT}/")

    if total_kb > 5120:
        print(f"\n⚠ WARNING: Total size {total_kb:.0f} KB exceeds 5 MB target!")
        sys.exit(1)


if __name__ == "__main__":
    main()
