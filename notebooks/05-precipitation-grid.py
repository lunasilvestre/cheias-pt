#!/usr/bin/env python3
"""
05 - Precipitation Accumulation Validation
===========================================
Validates the precipitation thesis for Portugal's Jan-Feb 2026 flood crisis.

Data source: Open-Meteo Historical Weather API (ERA5-Land reanalysis)
Period: Dec 1, 2025 - Feb 12, 2026
Grid: ~0.25° spacing across mainland Portugal

Key questions:
- Did >250mm fall across large areas during Jan 25 - Feb 7?
- Are three distinct storm peaks visible (Kristin ~Jan 29, Leonardo ~Feb 5, Marta ~Feb 10)?
- Which basins received the most precipitation?
"""

# %% [markdown]
# ## 1. Setup and Grid Generation

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
from shapely.geometry import Point

warnings.filterwarnings("ignore", category=FutureWarning)

PROJECT_ROOT = Path("/home/nls/Documents/dev/cheias-pt")
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data" / "precipitation"
FIGURES_DIR = PROJECT_ROOT / "notebooks" / "figures"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Date ranges
FULL_START = "2025-12-01"
FULL_END = "2026-02-12"
STORM_START = "2026-01-25"
STORM_END = "2026-02-07"

# Storm dates for annotation
STORMS = {
    "Kristin": "2026-01-29",
    "Leonardo": "2026-02-05",
    "Marta": "2026-02-10",
}

print("Setup complete.")

# %% [markdown]
# ## 2. Generate Point Grid
# Same grid as soil moisture agent: 0.25° spacing, mainland Portugal bbox.

# %%
LAT_MIN, LAT_MAX = 36.9, 42.2
LON_MIN, LON_MAX = -9.6, -6.1
SPACING = 0.25

lats = np.arange(LAT_MIN, LAT_MAX + SPACING / 2, SPACING)
lons = np.arange(LON_MIN, LON_MAX + SPACING / 2, SPACING)

grid_points = []
point_id = 0
for lat in lats:
    for lon in lons:
        grid_points.append({"id": point_id, "lat": round(float(lat), 2), "lon": round(float(lon), 2)})
        point_id += 1

print(f"Grid: {len(lats)} lats x {len(lons)} lons = {len(grid_points)} points")
print(f"Lat range: {lats[0]:.2f} to {lats[-1]:.2f}")
print(f"Lon range: {lons[0]:.2f} to {lons[-1]:.2f}")

# %% [markdown]
# ## 3. Fetch Precipitation from Open-Meteo Historical API
# The API supports comma-separated coordinates for batch requests.
# We'll batch in groups of ~50 to stay within URL length limits.

# %%
API_URL = "https://archive-api.open-meteo.com/v1/archive"
BATCH_SIZE = 50

all_results = {}  # point_id -> {precipitation_mm: [...], weather_code: [...]}
dates_list = None

n_batches = (len(grid_points) + BATCH_SIZE - 1) // BATCH_SIZE
print(f"Fetching {len(grid_points)} points in {n_batches} batches of up to {BATCH_SIZE}...")

for batch_idx in range(n_batches):
    start = batch_idx * BATCH_SIZE
    end = min(start + BATCH_SIZE, len(grid_points))
    batch = grid_points[start:end]

    lat_str = ",".join(str(p["lat"]) for p in batch)
    lon_str = ",".join(str(p["lon"]) for p in batch)

    params = {
        "latitude": lat_str,
        "longitude": lon_str,
        "start_date": FULL_START,
        "end_date": FULL_END,
        "daily": "precipitation_sum,weather_code",
        "timezone": "Europe/Lisbon",
    }

    for attempt in range(3):
        try:
            resp = requests.get(API_URL, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            break
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"  Batch {batch_idx + 1}: attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
            else:
                print(f"  Batch {batch_idx + 1}: FAILED after 3 attempts, skipping")
                data = None

    if data is None:
        continue

    # Single-point response is a dict, multi-point is a list
    if isinstance(data, list):
        entries = data
    else:
        entries = [data]

    for i, entry in enumerate(entries):
        pid = batch[i]["id"]
        daily = entry.get("daily", {})
        precip = daily.get("precipitation_sum", [])
        wcode = daily.get("weather_code", [])
        dates_raw = daily.get("time", [])

        if dates_list is None and dates_raw:
            dates_list = dates_raw

        # Replace None with 0.0 for precipitation
        precip = [v if v is not None else 0.0 for v in precip]
        wcode = [v if v is not None else 0 for v in wcode]

        all_results[pid] = {
            "precipitation_mm": precip,
            "weather_code": wcode,
        }

    pct = (batch_idx + 1) / n_batches * 100
    print(f"  Batch {batch_idx + 1}/{n_batches} done ({pct:.0f}%) - got {len(entries)} points")
    time.sleep(0.8)  # Rate limiting

print(f"\nFetched data for {len(all_results)} / {len(grid_points)} points")
print(f"Date range: {dates_list[0]} to {dates_list[-1]} ({len(dates_list)} days)")

# %% [markdown]
# ## 4. Calculate Storm Window Totals

# %%
dates_pd = pd.to_datetime(dates_list)
storm_mask = (dates_pd >= STORM_START) & (dates_pd <= STORM_END)
storm_indices = np.where(storm_mask)[0]

print(f"Storm window: {STORM_START} to {STORM_END}")
print(f"Storm window indices: {storm_indices[0]} to {storm_indices[-1]} ({len(storm_indices)} days)")

# Calculate totals
storm_totals = []
full_totals = []
for pt in grid_points:
    pid = pt["id"]
    if pid not in all_results:
        storm_totals.append(None)
        full_totals.append(None)
        continue
    precip = all_results[pid]["precipitation_mm"]
    storm_total = sum(precip[i] for i in storm_indices)
    full_total = sum(precip)
    storm_totals.append(round(storm_total, 1))
    full_totals.append(round(full_total, 1))

# Summary stats
valid_storm = [v for v in storm_totals if v is not None]
print(f"\nStorm window totals (Jan 25 - Feb 7):")
print(f"  Points with data: {len(valid_storm)}")
print(f"  Max: {max(valid_storm):.1f} mm")
print(f"  Mean: {np.mean(valid_storm):.1f} mm")
print(f"  Median: {np.median(valid_storm):.1f} mm")
print(f"  Points > 100mm: {sum(1 for v in valid_storm if v > 100)}")
print(f"  Points > 150mm: {sum(1 for v in valid_storm if v > 150)}")
print(f"  Points > 200mm: {sum(1 for v in valid_storm if v > 200)}")
print(f"  Points > 250mm: {sum(1 for v in valid_storm if v > 250)}")
print(f"  Points > 300mm: {sum(1 for v in valid_storm if v > 300)}")

valid_full = [v for v in full_totals if v is not None]
print(f"\nFull period totals (Dec 1 - Feb 12):")
print(f"  Max: {max(valid_full):.1f} mm")
print(f"  Mean: {np.mean(valid_full):.1f} mm")

# %% [markdown]
# ## 5. Map: Cumulative Precipitation (Storm Window)

# %%
fig, axes = plt.subplots(1, 2, figsize=(16, 10))

# Load basins for outline
basins = gpd.read_file(ASSETS_DIR / "basins.geojson")

for ax, (totals, title, vmax_hint) in zip(axes, [
    (storm_totals, f"Precipitation: Storm Window\n{STORM_START} to {STORM_END}", None),
    (full_totals, f"Precipitation: Full Period\n{FULL_START} to {FULL_END}", None),
]):
    valid_lats = [pt["lat"] for pt, v in zip(grid_points, totals) if v is not None]
    valid_lons = [pt["lon"] for pt, v in zip(grid_points, totals) if v is not None]
    valid_vals = [v for v in totals if v is not None]

    # Basin outlines
    basins.boundary.plot(ax=ax, color="#666", linewidth=0.5, alpha=0.5)

    sc = ax.scatter(
        valid_lons, valid_lats, c=valid_vals,
        cmap="YlOrRd", s=40, edgecolors="none", alpha=0.85,
        vmin=0, vmax=max(valid_vals) if vmax_hint is None else vmax_hint,
    )
    plt.colorbar(sc, ax=ax, label="Precipitation (mm)", shrink=0.7)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(LON_MIN - 0.3, LON_MAX + 0.3)
    ax.set_ylim(LAT_MIN - 0.3, LAT_MAX + 0.3)
    ax.set_aspect("equal")

plt.tight_layout()
plt.savefig(FIGURES_DIR / "05-precip-accumulation-maps.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: notebooks/figures/05-precip-accumulation-maps.png")

# %% [markdown]
# ## 6. Timeseries: Daily Precipitation at Representative Locations

# %%
# Representative locations (nearest grid point will be found)
LOCATIONS = {
    "Lisbon": (38.72, -9.14),
    "Leiria/Coimbra": (40.0, -8.5),
    "Santarém/Tejo": (39.2, -8.7),
    "Setúbal/Sado": (38.52, -8.89),
}

def find_nearest_point(target_lat, target_lon, points):
    """Find the nearest grid point to target coordinates."""
    min_dist = float("inf")
    best = None
    for pt in points:
        d = (pt["lat"] - target_lat) ** 2 + (pt["lon"] - target_lon) ** 2
        if d < min_dist:
            min_dist = d
            best = pt
    return best

fig, axes = plt.subplots(len(LOCATIONS), 1, figsize=(14, 3.5 * len(LOCATIONS)), sharex=True)

for ax, (name, (tlat, tlon)) in zip(axes, LOCATIONS.items()):
    nearest = find_nearest_point(tlat, tlon, grid_points)
    pid = nearest["id"]
    if pid not in all_results:
        ax.set_title(f"{name} — NO DATA")
        continue

    precip = all_results[pid]["precipitation_mm"]
    ax.bar(dates_pd, precip, width=0.8, color="#4a90d9", alpha=0.8, label="Daily precip")

    # Cumulative on secondary axis
    ax2 = ax.twinx()
    cumulative = np.cumsum(precip)
    ax2.plot(dates_pd, cumulative, color="#e74c3c", linewidth=2, label="Cumulative")
    ax2.set_ylabel("Cumulative (mm)", color="#e74c3c")

    # Mark storms
    for storm_name, storm_date in STORMS.items():
        sd = pd.Timestamp(storm_date)
        ax.axvline(sd, color="#ff6b35", linestyle="--", alpha=0.7, linewidth=1.2)
        ax.text(sd, ax.get_ylim()[1] * 0.95, f" {storm_name}", fontsize=8,
                color="#ff6b35", va="top", ha="left")

    # Mark storm window
    ax.axvspan(pd.Timestamp(STORM_START), pd.Timestamp(STORM_END),
               alpha=0.08, color="red", label="Storm window")

    storm_total = sum(precip[i] for i in storm_indices)
    full_total = sum(precip)
    ax.set_title(f"{name} (grid {nearest['lat']:.2f}°N, {nearest['lon']:.2f}°W) — "
                 f"Storm: {storm_total:.0f}mm, Total: {full_total:.0f}mm",
                 fontsize=11, fontweight="bold")
    ax.set_ylabel("Daily (mm)")
    ax.legend(loc="upper left", fontsize=8)
    ax2.legend(loc="upper right", fontsize=8)

axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
axes[-1].xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(FIGURES_DIR / "05-precip-timeseries-locations.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: notebooks/figures/05-precip-timeseries-locations.png")

# %% [markdown]
# ## 7. Per-Basin Averages

# %%
# Create GeoDataFrame from grid points
grid_gdf = gpd.GeoDataFrame(
    grid_points,
    geometry=[Point(pt["lon"], pt["lat"]) for pt in grid_points],
    crs="EPSG:4326",
)

# Add precipitation data
grid_gdf["storm_total"] = storm_totals
grid_gdf["full_total"] = full_totals

# Spatial join: which points fall in which basin
basins_proj = basins.to_crs("EPSG:4326")
joined = gpd.sjoin(grid_gdf, basins_proj, how="inner", predicate="within")

print("Points per basin:")
basin_counts = joined.groupby("name_pt").size().sort_values(ascending=False)
for name, count in basin_counts.items():
    print(f"  {name}: {count} points")

# Points not in any basin (ocean or outside boundary)
n_outside = len(grid_gdf) - len(joined)
print(f"\n  Outside all basins: {n_outside} points")

# %%
# Calculate per-basin daily averages
basin_daily = {}

for basin_name in basins_proj["name_pt"].values:
    basin_points = joined[joined["name_pt"] == basin_name]
    if len(basin_points) == 0:
        continue

    pids = basin_points["id"].tolist()
    daily_sums = np.zeros(len(dates_list))
    valid_count = 0

    for pid in pids:
        if pid in all_results:
            daily_sums += np.array(all_results[pid]["precipitation_mm"])
            valid_count += 1

    if valid_count > 0:
        daily_avg = daily_sums / valid_count
    else:
        daily_avg = daily_sums

    storm_total = sum(daily_avg[i] for i in storm_indices)
    river_name = basins_proj[basins_proj["name_pt"] == basin_name]["river"].iloc[0]

    basin_daily[basin_name] = {
        "name": basin_name,
        "river": river_name,
        "daily_avg_mm": [round(float(v), 1) for v in daily_avg],
        "storm_window_total_mm": round(float(storm_total), 1),
        "full_period_total_mm": round(float(sum(daily_avg)), 1),
        "point_count": valid_count,
    }

# Sort by storm window total
ranked = sorted(basin_daily.values(), key=lambda b: b["storm_window_total_mm"], reverse=True)
print("\nBasin ranking by storm window total:")
for i, b in enumerate(ranked):
    print(f"  {i+1}. {b['name']:25s} — {b['storm_window_total_mm']:6.1f} mm "
          f"(full: {b['full_period_total_mm']:.1f} mm, {b['point_count']} pts)")

# %% [markdown]
# ## 8. Plot: Top Basins Daily Precipitation

# %%
TOP_N = 6
top_basins = ranked[:TOP_N]

fig, axes = plt.subplots(TOP_N, 1, figsize=(14, 3.5 * TOP_N), sharex=True)

for ax, b in zip(axes, top_basins):
    daily = b["daily_avg_mm"]
    ax.bar(dates_pd, daily, width=0.8, color="#2ecc71", alpha=0.8, label="Basin avg daily")

    # Cumulative
    ax2 = ax.twinx()
    cum = np.cumsum(daily)
    ax2.plot(dates_pd, cum, color="#e74c3c", linewidth=2, label="Cumulative")
    ax2.set_ylabel("Cumulative (mm)", color="#e74c3c")

    # Storm markers
    for storm_name, storm_date in STORMS.items():
        sd = pd.Timestamp(storm_date)
        ax.axvline(sd, color="#ff6b35", linestyle="--", alpha=0.7, linewidth=1.2)
        ax.text(sd, ax.get_ylim()[1] * 0.95, f" {storm_name}", fontsize=8,
                color="#ff6b35", va="top", ha="left")

    ax.axvspan(pd.Timestamp(STORM_START), pd.Timestamp(STORM_END),
               alpha=0.08, color="red")

    ax.set_title(f"{b['name']} ({b['river']}) — Storm: {b['storm_window_total_mm']:.0f}mm, "
                 f"Full: {b['full_period_total_mm']:.0f}mm ({b['point_count']} pts)",
                 fontsize=11, fontweight="bold")
    ax.set_ylabel("Daily avg (mm)")
    ax.legend(loc="upper left", fontsize=8)
    ax2.legend(loc="upper right", fontsize=8)

axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
axes[-1].xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(FIGURES_DIR / "05-precip-basin-timeseries.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: notebooks/figures/05-precip-basin-timeseries.png")

# %% [markdown]
# ## 9. Weather Code Analysis

# %%
# Analyze weather codes during storm window
wmo_labels = {
    0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm + slight hail", 99: "Thunderstorm + heavy hail",
}

# Count weather codes across all points during storm window
code_counts = {}
for pid, result in all_results.items():
    wcodes = result["weather_code"]
    for i in storm_indices:
        if i < len(wcodes):
            code = wcodes[i]
            code_counts[code] = code_counts.get(code, 0) + 1

print("Weather codes during storm window (Jan 25 - Feb 7):")
print(f"{'Code':>5} | {'Label':30s} | {'Count':>8} | {'Pct':>6}")
print("-" * 60)
total_obs = sum(code_counts.values())
for code in sorted(code_counts.keys()):
    label = wmo_labels.get(code, f"Unknown ({code})")
    count = code_counts[code]
    pct = count / total_obs * 100
    print(f"{code:>5} | {label:30s} | {count:>8} | {pct:>5.1f}%")

# Heavy rain days (codes 65, 82, 95-99)
heavy_codes = {65, 67, 82, 95, 96, 99}
heavy_count = sum(code_counts.get(c, 0) for c in heavy_codes)
rain_codes = {61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
rain_count = sum(code_counts.get(c, 0) for c in rain_codes)
print(f"\nRain observations (any intensity): {rain_count}/{total_obs} ({rain_count/total_obs*100:.1f}%)")
print(f"Heavy rain observations (65,67,82,95+): {heavy_count}/{total_obs} ({heavy_count/total_obs*100:.1f}%)")

# %% [markdown]
# ## 10. Output JSON Files

# %%
# 10a. daily-grid.json
daily_grid = {
    "dates": dates_list,
    "points": [],
}
for pt in grid_points:
    pid = pt["id"]
    if pid in all_results:
        daily_grid["points"].append({
            "id": pid,
            "lat": pt["lat"],
            "lon": pt["lon"],
            "precipitation_mm": [round(v, 1) for v in all_results[pid]["precipitation_mm"]],
            "weather_code": all_results[pid]["weather_code"],
        })

with open(DATA_DIR / "daily-grid.json", "w") as f:
    json.dump(daily_grid, f)

print(f"Wrote daily-grid.json: {len(daily_grid['points'])} points x {len(dates_list)} days")
print(f"  File size: {(DATA_DIR / 'daily-grid.json').stat().st_size / 1024:.0f} KB")

# %%
# 10b. accumulation-jan25-feb07.json
accum_points = []
for pt in grid_points:
    pid = pt["id"]
    if pid in all_results and storm_totals[pid] is not None:
        accum_points.append({
            "id": pid,
            "lat": pt["lat"],
            "lon": pt["lon"],
            "total_mm": storm_totals[pid],
        })

valid_totals = [p["total_mm"] for p in accum_points]
accumulation = {
    "storm_window": {"start": STORM_START, "end": STORM_END},
    "points": accum_points,
    "metadata": {
        "max_total_mm": round(max(valid_totals), 1),
        "mean_total_mm": round(float(np.mean(valid_totals)), 1),
        "median_total_mm": round(float(np.median(valid_totals)), 1),
        "points_above_100mm": sum(1 for v in valid_totals if v > 100),
        "points_above_150mm": sum(1 for v in valid_totals if v > 150),
        "points_above_200mm": sum(1 for v in valid_totals if v > 200),
        "points_above_250mm": sum(1 for v in valid_totals if v > 250),
        "points_above_300mm": sum(1 for v in valid_totals if v > 300),
        "total_points": len(accum_points),
    },
}

with open(DATA_DIR / "accumulation-jan25-feb07.json", "w") as f:
    json.dump(accumulation, f, indent=2)

print(f"Wrote accumulation-jan25-feb07.json: {len(accum_points)} points")
print(f"  Max: {accumulation['metadata']['max_total_mm']} mm")
print(f"  Mean: {accumulation['metadata']['mean_total_mm']} mm")
print(f"  Points > 200mm: {accumulation['metadata']['points_above_200mm']}")
print(f"  Points > 250mm: {accumulation['metadata']['points_above_250mm']}")

# %%
# 10c. basin-averages.json
basin_avg_output = {
    "dates": dates_list,
    "basins": [],
}
for b in ranked:
    basin_avg_output["basins"].append({
        "name": b["name"],
        "river": b["river"],
        "daily_avg_mm": b["daily_avg_mm"],
        "storm_window_total_mm": b["storm_window_total_mm"],
        "full_period_total_mm": b["full_period_total_mm"],
        "point_count": b["point_count"],
    })

with open(DATA_DIR / "basin-averages.json", "w") as f:
    json.dump(basin_avg_output, f, indent=2)

print(f"Wrote basin-averages.json: {len(basin_avg_output['basins'])} basins")

# %% [markdown]
# ## 11. Validation Assessment

# %%
print("=" * 70)
print("PRECIPITATION VALIDATION ASSESSMENT")
print("=" * 70)

print(f"\n1. STORM WINDOW TOTALS ({STORM_START} to {STORM_END}):")
print(f"   Max point total: {accumulation['metadata']['max_total_mm']} mm")
print(f"   Mean point total: {accumulation['metadata']['mean_total_mm']} mm")
print(f"   Points > 200mm: {accumulation['metadata']['points_above_200mm']} / {accumulation['metadata']['total_points']}")
print(f"   Points > 250mm: {accumulation['metadata']['points_above_250mm']} / {accumulation['metadata']['total_points']}")

# Check against reported values
if accumulation['metadata']['max_total_mm'] > 250:
    print("   CONFIRMED: >250mm totals match reports of extreme precipitation")
elif accumulation['metadata']['max_total_mm'] > 150:
    print("   PARTIAL: Significant precipitation but below some reports")
    print("   NOTE: ERA5-Land may underestimate peak orographic rainfall")
else:
    print("   WARNING: Totals seem low — check data source or grid resolution")

print(f"\n2. TOP BASINS BY STORM WINDOW PRECIPITATION:")
for i, b in enumerate(ranked[:5]):
    print(f"   {i+1}. {b['name']:25s} — {b['storm_window_total_mm']:.1f} mm avg "
          f"({b['point_count']} grid points)")

print(f"\n3. STORM PEAKS ANALYSIS:")
# Check for peaks near storm dates
for storm_name, storm_date in STORMS.items():
    sd = pd.Timestamp(storm_date)
    # Find the day index
    day_idx = None
    for i, d in enumerate(dates_list):
        if d == storm_date:
            day_idx = i
            break

    if day_idx is None:
        print(f"   {storm_name} ({storm_date}): date not in range")
        continue

    # Average precipitation across all points for that day and surrounding days
    window = range(max(0, day_idx - 2), min(len(dates_list), day_idx + 3))
    daily_avgs = []
    for di in window:
        vals = [all_results[pid]["precipitation_mm"][di]
                for pid in all_results if di < len(all_results[pid]["precipitation_mm"])]
        daily_avgs.append((dates_list[di], round(np.mean(vals), 1)))

    peak_day = max(daily_avgs, key=lambda x: x[1])
    print(f"   {storm_name} ({storm_date}):")
    for date, avg in daily_avgs:
        marker = " <-- PEAK" if date == peak_day[0] else ""
        print(f"     {date}: {avg:6.1f} mm avg{marker}")

print(f"\n4. WEATHER CODE HIGHLIGHTS:")
print(f"   Rain observations during storm window: {rain_count}/{total_obs} "
      f"({rain_count/total_obs*100:.1f}%)")
print(f"   Heavy rain (code 65,67,82,95+): {heavy_count}/{total_obs} "
      f"({heavy_count/total_obs*100:.1f}%)")

print(f"\n5. DATA QUALITY NOTES:")
print(f"   Source: Open-Meteo Historical API (ERA5-Land reanalysis)")
print(f"   Grid: {len(grid_points)} points, {SPACING}° spacing")
print(f"   Points with data: {len(all_results)} / {len(grid_points)}")
n_missing = len(grid_points) - len(all_results)
if n_missing > 0:
    print(f"   Missing: {n_missing} points (likely ocean/outside domain)")
print(f"   ERA5-Land is 0.1° (~9km) native resolution, may smooth peaks")
print(f"   Station-based records likely show higher local maxima")

print(f"\n6. OUTPUT FILES:")
for fname in ["daily-grid.json", "accumulation-jan25-feb07.json", "basin-averages.json"]:
    fpath = DATA_DIR / fname
    if fpath.exists():
        size_kb = fpath.stat().st_size / 1024
        print(f"   {fname}: {size_kb:.0f} KB")
    else:
        print(f"   {fname}: NOT WRITTEN")

print("\n" + "=" * 70)
print("Assessment complete.")
