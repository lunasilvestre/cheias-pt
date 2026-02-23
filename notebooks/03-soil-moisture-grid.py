#!/usr/bin/env python3
"""
03 - Soil Moisture Grid Validation
===================================
Validates the soil saturation hypothesis for Portugal's Jan-Feb 2026 flood crisis.
Fetches ERA5-Land soil moisture from Open-Meteo, computes normalized saturation index,
and outputs pre-processed JSON for the scrollytelling frontend.
"""

# %% [markdown]
# # Soil Moisture Saturation Validation
#
# **Thesis:** Weeks of persistent rain (Dec 2025 - Jan 2026) progressively saturated
# Portuguese soils, creating preconditions for catastrophic flooding when storms
# Kristin, Leonardo, and Marta hit in rapid succession.
#
# **Data source:** Open-Meteo Historical Weather API (ERA5-Land reanalysis)
# - `soil_moisture_0_to_7cm` (m3/m3) — hourly, aggregated to daily mean
# - `soil_moisture_7_to_28cm` (m3/m3) — hourly, aggregated to daily mean
#
# **Note:** Soil moisture is only available as hourly in the archive API, not daily.
# We fetch hourly and compute daily means.

# %%
import json
import time
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import requests
from shapely.geometry import Point, Polygon

warnings.filterwarnings("ignore", category=FutureWarning)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data" / "soil-moisture"
FIGURES_DIR = PROJECT_ROOT / "notebooks" / "figures"

DATA_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# %% [markdown]
# ## 1. Generate Grid Points

# %%
# Portugal mainland bounding box
BBOX = {"lat_min": 36.9, "lat_max": 42.2, "lon_min": -9.6, "lon_max": -6.1}
SPACING = 0.4  # degrees (~40 km) — coarser grid to keep ~80 points, reduce API load

lats = np.arange(BBOX["lat_min"], BBOX["lat_max"] + SPACING / 2, SPACING)
lons = np.arange(BBOX["lon_min"], BBOX["lon_max"] + SPACING / 2, SPACING)

# Create grid
grid_points = []
idx = 0
for lat in lats:
    for lon in lons:
        grid_points.append({"id": idx, "lat": round(float(lat), 4), "lon": round(float(lon), 4)})
        idx += 1

print(f"Raw grid: {len(grid_points)} points ({len(lats)} lat x {len(lons)} lon)")

# Simplified Portugal mainland outline (rough, for filtering)
portugal_rough = Polygon([
    (-9.5, 36.95), (-7.4, 36.95), (-7.0, 37.0), (-7.0, 38.0),
    (-7.2, 38.5), (-6.9, 38.7), (-6.9, 39.3), (-7.0, 39.5),
    (-6.8, 39.8), (-6.1, 41.0), (-6.1, 42.2), (-8.2, 42.2),
    (-8.9, 41.8), (-8.8, 41.2), (-8.8, 40.5), (-8.9, 40.2),
    (-9.0, 39.5), (-9.5, 38.8), (-9.5, 38.5), (-9.2, 38.0),
    (-8.9, 37.1), (-8.8, 37.0), (-9.5, 36.95),
])

filtered_points = []
idx = 0
for pt in grid_points:
    if portugal_rough.contains(Point(pt["lon"], pt["lat"])):
        pt_new = {"id": idx, "lat": pt["lat"], "lon": pt["lon"]}
        filtered_points.append(pt_new)
        idx += 1

grid_points = filtered_points
print(f"After Portugal filter: {len(grid_points)} points")

# %% [markdown]
# ## 2. Fetch Soil Moisture from Open-Meteo (hourly, then aggregate to daily)

# %%
API_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2025-12-01"
END_DATE = "2026-02-10"

BATCH_SIZE = 5  # Smaller batches for hourly data (more data per point)
DELAY_BETWEEN_BATCHES = 1.5  # seconds, be respectful


def fetch_batch(points_batch):
    """Fetch hourly soil moisture for a batch of points."""
    lats_str = ",".join(str(p["lat"]) for p in points_batch)
    lons_str = ",".join(str(p["lon"]) for p in points_batch)

    params = {
        "latitude": lats_str,
        "longitude": lons_str,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": "soil_moisture_0_to_7cm,soil_moisture_7_to_28cm",
    }

    resp = requests.get(API_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def hourly_to_daily(hourly_times, hourly_values):
    """Aggregate hourly values to daily means."""
    df = pd.DataFrame({"time": pd.to_datetime(hourly_times), "value": hourly_values})
    df["date"] = df["time"].dt.date
    daily = df.groupby("date")["value"].mean()
    return daily.index.tolist(), daily.values.tolist()


# Split into batches
batches = [grid_points[i : i + BATCH_SIZE] for i in range(0, len(grid_points), BATCH_SIZE)]
print(f"Fetching {len(grid_points)} points in {len(batches)} batches (batch size={BATCH_SIZE})...")
print(f"Using HOURLY endpoint, will aggregate to daily means.")

all_results = []
failed_points = []

for batch_idx, batch in enumerate(batches):
    try:
        result = fetch_batch(batch)
        # Open-Meteo returns a list if multiple locations, single dict if one
        if isinstance(result, list):
            all_results.extend(zip(batch, result))
        else:
            all_results.append((batch[0], result))
        print(f"  Batch {batch_idx + 1}/{len(batches)} OK ({len(batch)} points)")
    except Exception as e:
        print(f"  Batch {batch_idx + 1}/{len(batches)} FAILED: {e}")
        for pt in batch:
            failed_points.append(pt["id"])

    if batch_idx < len(batches) - 1:
        time.sleep(DELAY_BETWEEN_BATCHES)

print(f"\nFetched: {len(all_results)} points, Failed: {len(failed_points)} points")

# %% [markdown]
# ## 3. Process: Aggregate to Daily and Compute Saturation Index

# %%
dates = None
points_data = []
valid_count = 0
ocean_count = 0

for pt, result in all_results:
    hourly = result.get("hourly", {})
    sm_0_7_hourly = hourly.get("soil_moisture_0_to_7cm")
    sm_7_28_hourly = hourly.get("soil_moisture_7_to_28cm")
    time_arr = hourly.get("time")

    if sm_0_7_hourly is None or sm_7_28_hourly is None or time_arr is None:
        ocean_count += 1
        continue

    # Check for all-null data (ocean points)
    if all(v is None for v in sm_0_7_hourly) or all(v is None for v in sm_7_28_hourly):
        ocean_count += 1
        continue

    # Aggregate hourly to daily means
    dates_0_7, daily_0_7 = hourly_to_daily(time_arr, sm_0_7_hourly)
    dates_7_28, daily_7_28 = hourly_to_daily(time_arr, sm_7_28_hourly)

    # Convert to date strings
    date_strings = [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in dates_0_7]

    if dates is None:
        dates = date_strings

    sm_0_7_arr = np.array(daily_0_7, dtype=float)
    sm_7_28_arr = np.array(daily_7_28, dtype=float)

    # Check for mostly NaN
    if np.isnan(sm_0_7_arr).sum() > len(sm_0_7_arr) * 0.2:
        ocean_count += 1
        continue
    if np.isnan(sm_7_28_arr).sum() > len(sm_7_28_arr) * 0.2:
        ocean_count += 1
        continue

    # Interpolate isolated gaps
    if np.isnan(sm_0_7_arr).any():
        sm_0_7_arr = pd.Series(sm_0_7_arr).interpolate(limit=3).values
    if np.isnan(sm_7_28_arr).any():
        sm_7_28_arr = pd.Series(sm_7_28_arr).interpolate(limit=3).values

    # Weighted average: shallow=0.25, deep=0.75
    combined = 0.25 * sm_0_7_arr + 0.75 * sm_7_28_arr

    # Normalize to 0-1 range within the period
    min_val = np.nanmin(combined)
    max_val = np.nanmax(combined)
    if max_val - min_val > 0.001:
        saturation_idx = (combined - min_val) / (max_val - min_val)
    else:
        saturation_idx = np.zeros_like(combined)

    points_data.append({
        "id": pt["id"],
        "lat": pt["lat"],
        "lon": pt["lon"],
        "soil_moisture_0_7cm": [round(float(v), 4) if not np.isnan(v) else None for v in sm_0_7_arr],
        "soil_moisture_7_28cm": [round(float(v), 4) if not np.isnan(v) else None for v in sm_7_28_arr],
        "saturation_index": [round(float(v), 4) for v in saturation_idx],
        "combined_raw": combined.tolist(),  # Keep for analysis, strip before export
    })
    valid_count += 1

print(f"Valid land points: {valid_count}")
print(f"Filtered ocean/invalid: {ocean_count}")
if dates:
    print(f"Date range: {dates[0]} to {dates[-1]} ({len(dates)} days)")
else:
    print("ERROR: No valid data returned!")
    import sys
    sys.exit(1)

# %% [markdown]
# ## 4. Visualize at Key Dates

# %%
KEY_DATES = {
    "2025-12-01": "Dec 1 -- Baseline",
    "2026-01-15": "Jan 15 -- Mid-buildup",
    "2026-01-28": "Jan 28 -- Pre-Kristin",
    "2026-02-05": "Feb 5 -- Between Leonardo & Marta",
}

# Load basins for outline overlay
basins_gdf = gpd.read_file(ASSETS_DIR / "basins.geojson")

fig, axes = plt.subplots(1, 4, figsize=(20, 12), dpi=100)

for ax_idx, (date_str, label) in enumerate(KEY_DATES.items()):
    ax = axes[ax_idx]
    date_idx = dates.index(date_str)

    lats_plot = [p["lat"] for p in points_data]
    lons_plot = [p["lon"] for p in points_data]
    vals = [p["saturation_index"][date_idx] for p in points_data]

    # Plot basin outlines
    basins_gdf.boundary.plot(ax=ax, color="gray", linewidth=0.5, alpha=0.7)

    # Scatter plot of saturation
    sc = ax.scatter(
        lons_plot, lats_plot, c=vals, cmap="YlOrRd", vmin=0, vmax=1,
        s=60, edgecolors="none", alpha=0.85
    )

    ax.set_xlim(-9.7, -5.9)
    ax.set_ylim(36.8, 42.3)
    ax.set_title(label, fontsize=11, fontweight="bold")
    ax.set_aspect("equal")
    ax.tick_params(labelsize=8)

fig.colorbar(sc, ax=axes, orientation="horizontal", fraction=0.04, pad=0.08,
             label="Normalized Saturation Index (0=dry, 1=peak)")
fig.suptitle("Soil Moisture Saturation -- Portugal Dec 2025 - Feb 2026", fontsize=14, fontweight="bold", y=0.98)
plt.tight_layout(rect=[0, 0.05, 1, 0.95])
fig.savefig(FIGURES_DIR / "soil-moisture-4dates.png", bbox_inches="tight")
plt.close()
print(f"Saved: {FIGURES_DIR / 'soil-moisture-4dates.png'}")

# %% [markdown]
# ## 5. Per-Basin Average Timeseries

# %%
# Spatial join: assign grid points to basins
points_gdf = gpd.GeoDataFrame(
    [{"id": p["id"], "lat": p["lat"], "lon": p["lon"]} for p in points_data],
    geometry=[Point(p["lon"], p["lat"]) for p in points_data],
    crs="EPSG:4326",
)

# Join points to basins
joined = gpd.sjoin(points_gdf, basins_gdf, how="left", predicate="within")

basin_averages = {}
for _, row in joined.iterrows():
    basin_name = row.get("river")
    if pd.isna(basin_name):
        continue
    if basin_name not in basin_averages:
        basin_averages[basin_name] = {"point_ids": [], "name_pt": row.get("name_pt", basin_name)}
    basin_averages[basin_name]["point_ids"].append(row["id"])

print("Points per basin:")
for name, info in sorted(basin_averages.items()):
    print(f"  {name}: {len(info['point_ids'])} points")

# Compute averages
points_lookup = {p["id"]: p for p in points_data}
basin_timeseries = {}

for basin_name, info in basin_averages.items():
    pts = [points_lookup[pid] for pid in info["point_ids"] if pid in points_lookup]
    if not pts:
        continue
    sat_arrays = np.array([p["saturation_index"] for p in pts])
    avg_sat = np.nanmean(sat_arrays, axis=0)
    basin_timeseries[basin_name] = {
        "avg_saturation": avg_sat,
        "point_count": len(pts),
        "name_pt": info["name_pt"],
    }

# %% Plot timeseries for key basins
HIGHLIGHT_BASINS = ["Tejo", "Mondego", "Sado", "Douro"]
STORM_DATES = {
    "Kristin": "2026-01-27",
    "Leonardo": "2026-02-01",
    "Marta": "2026-02-06",
}

date_range = pd.to_datetime(dates)

fig, ax = plt.subplots(figsize=(14, 6), dpi=100)

colors = {"Tejo": "#e41a1c", "Mondego": "#377eb8", "Sado": "#4daf4a", "Douro": "#984ea3"}

for basin_name in HIGHLIGHT_BASINS:
    if basin_name in basin_timeseries:
        bt = basin_timeseries[basin_name]
        ax.plot(date_range, bt["avg_saturation"], linewidth=2, label=f"{basin_name} ({bt['point_count']} pts)",
                color=colors.get(basin_name, None))

# Storm date markers
for storm_name, storm_date in STORM_DATES.items():
    sd = pd.to_datetime(storm_date)
    ax.axvline(sd, color="red", linestyle="--", alpha=0.5, linewidth=1)
    ax.text(sd, 1.02, storm_name, transform=ax.get_xaxis_transform(),
            ha="center", fontsize=9, color="red", fontweight="bold")

ax.set_ylabel("Normalized Saturation Index")
ax.set_xlabel("Date")
ax.set_title("Basin-Average Soil Saturation -- Key Basins", fontsize=13, fontweight="bold")
ax.legend(loc="lower right")
ax.set_ylim(-0.05, 1.05)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
plt.xticks(rotation=45)
ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig(FIGURES_DIR / "soil-moisture-basin-timeseries.png", bbox_inches="tight")
plt.close()
print(f"Saved: {FIGURES_DIR / 'soil-moisture-basin-timeseries.png'}")

# Also plot ALL basins for completeness
fig, ax = plt.subplots(figsize=(14, 6), dpi=100)
for basin_name, bt in sorted(basin_timeseries.items()):
    ax.plot(date_range, bt["avg_saturation"], linewidth=1.5 if basin_name in HIGHLIGHT_BASINS else 0.8,
            alpha=1.0 if basin_name in HIGHLIGHT_BASINS else 0.5,
            label=f"{basin_name} ({bt['point_count']})")

for storm_name, storm_date in STORM_DATES.items():
    sd = pd.to_datetime(storm_date)
    ax.axvline(sd, color="red", linestyle="--", alpha=0.5, linewidth=1)
    ax.text(sd, 1.02, storm_name, transform=ax.get_xaxis_transform(),
            ha="center", fontsize=9, color="red", fontweight="bold")

ax.set_ylabel("Normalized Saturation Index")
ax.set_title("Basin-Average Soil Saturation -- All Basins", fontsize=13, fontweight="bold")
ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9)
ax.set_ylim(-0.05, 1.05)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
plt.xticks(rotation=45)
ax.grid(True, alpha=0.3)
plt.tight_layout()
fig.savefig(FIGURES_DIR / "soil-moisture-all-basins.png", bbox_inches="tight")
plt.close()
print(f"Saved: {FIGURES_DIR / 'soil-moisture-all-basins.png'}")

# %% [markdown]
# ## 6. Export JSON Files

# %%
# 6a. grid-points.json
grid_export = {
    "grid": [{"id": p["id"], "lat": p["lat"], "lon": p["lon"]} for p in points_data],
    "metadata": {
        "bbox": [BBOX["lat_min"], BBOX["lon_min"], BBOX["lat_max"], BBOX["lon_max"]],
        "spacing_deg": SPACING,
        "total_points": len(points_data),
        "crs": "EPSG:4326",
        "source": "Open-Meteo Historical Weather API (ERA5-Land)",
        "period": f"{START_DATE} to {END_DATE}",
    },
}

with open(DATA_DIR / "grid-points.json", "w") as f:
    json.dump(grid_export, f, indent=2)
print(f"Saved: {DATA_DIR / 'grid-points.json'} ({len(points_data)} points)")

# 6b. timeseries.json
timeseries_export = {
    "dates": dates,
    "points": [
        {
            "id": p["id"],
            "lat": p["lat"],
            "lon": p["lon"],
            "soil_moisture_0_7cm": p["soil_moisture_0_7cm"],
            "soil_moisture_7_28cm": p["soil_moisture_7_28cm"],
            "saturation_index": p["saturation_index"],
        }
        for p in points_data
    ],
}

with open(DATA_DIR / "timeseries.json", "w") as f:
    json.dump(timeseries_export, f)
print(f"Saved: {DATA_DIR / 'timeseries.json'}")

# 6c. basin-averages.json
basin_export = {
    "dates": dates,
    "basins": [
        {
            "name": name,
            "river": name,
            "name_pt": bt["name_pt"],
            "avg_saturation": [round(float(v), 4) for v in bt["avg_saturation"]],
            "point_count": bt["point_count"],
        }
        for name, bt in sorted(basin_timeseries.items())
    ],
}

with open(DATA_DIR / "basin-averages.json", "w") as f:
    json.dump(basin_export, f, indent=2)
print(f"Saved: {DATA_DIR / 'basin-averages.json'} ({len(basin_timeseries)} basins)")

# %% [markdown]
# ## 7. Validation Assessment

# %%
print("\n" + "=" * 70)
print("VALIDATION ASSESSMENT")
print("=" * 70)

# Check progressive saturation
dec01_idx = dates.index("2025-12-01")
jan15_idx = dates.index("2026-01-15")
jan28_idx = dates.index("2026-01-28")
feb05_idx = dates.index("2026-02-05")

print("\n--- National Average Saturation at Key Dates ---")
all_sat = np.array([p["saturation_index"] for p in points_data])
for date_str, idx in [("Dec 01", dec01_idx), ("Jan 15", jan15_idx),
                       ("Jan 28", jan28_idx), ("Feb 05", feb05_idx)]:
    mean_val = np.nanmean(all_sat[:, idx])
    print(f"  {date_str}: {mean_val:.3f}")

mean_dec01 = np.nanmean(all_sat[:, dec01_idx])
mean_jan28 = np.nanmean(all_sat[:, jan28_idx])
progressive = mean_jan28 > mean_dec01

print(f"\n--- Progressive Saturation Test ---")
print(f"  Dec 01 avg: {mean_dec01:.3f} -> Jan 28 avg: {mean_jan28:.3f}")
print(f"  Progressive increase: {'YES' if progressive else 'NO'}")

print(f"\n--- Basin Comparison at Jan 28 (Pre-Kristin) ---")
for basin_name in ["Tejo", "Mondego", "Sado", "Douro", "Guadiana"]:
    if basin_name in basin_timeseries:
        bt = basin_timeseries[basin_name]
        val = bt["avg_saturation"][jan28_idx]
        print(f"  {basin_name:12s}: {val:.3f} (from {bt['point_count']} points)")

print(f"\n--- Peak Saturation Dates per Basin ---")
for basin_name in HIGHLIGHT_BASINS:
    if basin_name in basin_timeseries:
        bt = basin_timeseries[basin_name]
        peak_idx = int(np.argmax(bt["avg_saturation"]))
        print(f"  {basin_name:12s}: peak on {dates[peak_idx]} (index={bt['avg_saturation'][peak_idx]:.3f})")

print(f"\n--- Signal Clarity for Scrollytelling ---")
all_national = np.nanmean(all_sat, axis=0)
dynamic_range = float(np.nanmax(all_national) - np.nanmin(all_national))
print(f"  National dynamic range: {dynamic_range:.3f}")
print(f"  Sufficient for animation: {'YES' if dynamic_range > 0.3 else 'MARGINAL' if dynamic_range > 0.15 else 'NO'}")

print(f"\n--- Data Quality ---")
print(f"  Total valid land points: {len(points_data)}")
print(f"  Ocean/invalid filtered: {ocean_count}")
print(f"  Date range: {dates[0]} to {dates[-1]}")
has_nans = any(any(v is None or (isinstance(v, float) and np.isnan(v)) for v in p["saturation_index"]) for p in points_data)
print(f"  Any NaN in saturation indices: {has_nans}")

print(f"\n--- Summary ---")
if progressive and dynamic_range > 0.3:
    print("  STRONG SUPPORT for saturation hypothesis. The data clearly shows")
    print("  progressive soil wetting from December through late January,")
    print("  with clear spatial and temporal signal for scrollytelling animation.")
elif progressive:
    print("  MODERATE SUPPORT for saturation hypothesis. Progressive increase")
    print("  is visible but dynamic range may limit visual impact.")
else:
    print("  WEAK SUPPORT. Data does not clearly show expected pattern.")
    print("  Consider investigating raw values vs. normalized index.")

print("\n" + "=" * 70)
