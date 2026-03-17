#!/usr/bin/env python3
"""
07 — Historical Rainfall Anomaly + Rich Chart Generation
==========================================================

Fetches multi-year Oct–Feb precipitation for Portugal from Open-Meteo ERA5,
computes anomaly percentages, and generates pre-rendered chart PNGs.

Strategy: Fetch 2000-01-01 → 2026-02-28 at representative points,
then group by winter season and month. Faster than per-season fetching.

Outputs (cheias-pt-veda-ui/stories/):
  - rainfall-anomaly.csv          — anomaly data
  - rainfall-anomaly.png          — rich bar chart (for <Image>)
  - discharge-comparison-story.png — multi-river comparison (for <Image>)

Why pre-rendered PNGs:
  VEDA-UI <Chart> = recharts LineChart only. Cannot do bar charts,
  dual Y-axes, annotations, threshold bands. For complex figures,
  <Image> with matplotlib PNGs is the standard pattern (NASA VEDA does this).
"""

import json
import time
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import requests

# ─── Paths ───────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path("/home/nls/Documents/dev/cheias-pt")
VEDA_STORIES = Path("/home/nls/Documents/dev/cheias-pt-veda-ui/stories")
FIGURES_DIR = PROJECT_ROOT / "notebooks" / "figures"
DISCHARGE_DIR = PROJECT_ROOT / "data" / "discharge"
PRECIP_DIR = PROJECT_ROOT / "data" / "precipitation"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
PRECIP_DIR.mkdir(parents=True, exist_ok=True)

# ─── Representative grid points (12 points, mainland Portugal) ───────────

GRID_POINTS = [
    {"lat": 37.0, "lon": -8.0, "name": "Algarve"},
    {"lat": 38.0, "lon": -8.5, "name": "Alentejo"},
    {"lat": 38.7, "lon": -9.2, "name": "Lisbon"},
    {"lat": 39.2, "lon": -8.7, "name": "Santarém"},
    {"lat": 39.5, "lon": -8.0, "name": "Tejo Basin"},
    {"lat": 39.8, "lon": -8.9, "name": "Leiria"},
    {"lat": 40.0, "lon": -8.3, "name": "Coimbra"},
    {"lat": 40.5, "lon": -8.0, "name": "Viseu"},
    {"lat": 41.0, "lon": -8.5, "name": "Porto"},
    {"lat": 41.2, "lon": -8.0, "name": "Douro"},
    {"lat": 41.7, "lon": -8.5, "name": "Braga"},
    {"lat": 42.0, "lon": -8.2, "name": "Minho"},
]

STORMS = {
    "Kristin": "2026-01-29",
    "Leonardo": "2026-02-05",
    "Marta": "2026-02-10",
}

# ═════════════════════════════════════════════════════════════════════════════
# PART 1: Fetch full historical daily precipitation
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("PART 1: Fetching 2000–2026 daily precipitation (12 representative points)")
print("=" * 70)

API_URL = "https://archive-api.open-meteo.com/v1/archive"

# Fetch in yearly chunks to avoid too-large responses
all_daily = []  # list of {date, lat, lon, precip_mm}

# Split into 2 periods to keep response sizes manageable
PERIODS = [
    ("2000-01-01", "2013-12-31"),
    ("2014-01-01", "2026-02-28"),
]

for period_start, period_end in PERIODS:
    print(f"\n  Period: {period_start} → {period_end}")

    lat_str = ",".join(str(p["lat"]) for p in GRID_POINTS)
    lon_str = ",".join(str(p["lon"]) for p in GRID_POINTS)

    params = {
        "latitude": lat_str,
        "longitude": lon_str,
        "start_date": period_start,
        "end_date": period_end,
        "daily": "precipitation_sum",
        "timezone": "Europe/Lisbon",
    }

    for attempt in range(3):
        try:
            resp = requests.get(API_URL, params=params, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            print(f"    Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(3)
            else:
                data = None

    if data is None:
        print(f"    FAILED for period {period_start}–{period_end}")
        continue

    entries = data if isinstance(data, list) else [data]

    for i, entry in enumerate(entries):
        daily = entry.get("daily", {})
        dates = daily.get("time", [])
        precip = daily.get("precipitation_sum", [])
        pt = GRID_POINTS[i]

        for d, p in zip(dates, precip):
            all_daily.append({
                "date": d,
                "lat": pt["lat"],
                "lon": pt["lon"],
                "precip_mm": p if p is not None else 0.0,
            })

    print(f"    Got {len(entries)} points × {len(entries[0].get('daily',{}).get('time',[]))} days")
    time.sleep(1)

df = pd.DataFrame(all_daily)
df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

print(f"\nTotal records: {len(df)}")
print(f"Date range: {df['date'].min()} → {df['date'].max()}")

# Save raw data
raw_path = PRECIP_DIR / "historical-monthly-grid.parquet"
df.to_parquet(raw_path, index=False)
print(f"Saved raw data: {raw_path}")

# ─── Compute monthly totals per point, then grid average ──────────────────

monthly = df.groupby(["year", "month", "lat", "lon"])["precip_mm"].sum().reset_index()
monthly.columns = ["year", "month", "lat", "lon", "total_mm"]

# Grid-averaged monthly totals
grid_avg = monthly.groupby(["year", "month"])["total_mm"].mean().reset_index()
grid_avg.columns = ["year", "month", "avg_mm"]

print("\nGrid-averaged monthly precipitation (sample):")
print(grid_avg[grid_avg["month"] == 1].sort_values("year").to_string(index=False))

# ─── Assign winter seasons ───────────────────────────────────────────────

def get_season(year, month):
    """Oct-Dec → season starts this year; Jan-Feb → season started last year."""
    if month >= 10:
        return f"{year}-{str(year+1)[-2:]}"
    elif month <= 2:
        return f"{year-1}-{str(year)[-2:]}"
    return None

grid_avg["season"] = grid_avg.apply(lambda r: get_season(int(r["year"]), int(r["month"])), axis=1)
grid_avg = grid_avg[grid_avg["season"].notna()]

# ─── Compute baseline (2000-01 through 2019-20) ──────────────────────────

baseline_seasons = [f"{y}-{str(y+1)[-2:]}" for y in range(2000, 2020)]
baseline_df = grid_avg[grid_avg["season"].isin(baseline_seasons)]

baseline = {}
for month in [10, 11, 12, 1, 2]:
    vals = baseline_df[baseline_df["month"] == month]["avg_mm"]
    baseline[month] = round(vals.mean(), 1) if len(vals) > 0 else 0.0

month_names = {10: "Oct", 11: "Nov", 12: "Dec", 1: "Jan", 2: "Feb"}
print("\n2000–2020 Baseline (grid average):")
for m in [10, 11, 12, 1, 2]:
    print(f"  {month_names[m]}: {baseline[m]:.1f} mm")

# ─── Compute anomaly percentages ─────────────────────────────────────────

all_seasons = sorted(grid_avg["season"].unique())
anomaly_rows = []

# Baseline row
for m in [10, 11, 12, 1, 2]:
    anomaly_rows.append({"Year": "2000-2020 Average", "Month": month_names[m], "Anomaly_Percent": 100})

# Per-season anomaly
for season in all_seasons:
    season_df = grid_avg[grid_avg["season"] == season]
    for m in [10, 11, 12, 1, 2]:
        actual = season_df[season_df["month"] == m]["avg_mm"]
        if len(actual) > 0 and baseline[m] > 0:
            pct = round(actual.values[0] / baseline[m] * 100)
        else:
            pct = 0
        anomaly_rows.append({"Year": season, "Month": month_names[m], "Anomaly_Percent": pct})

anomaly_df = pd.DataFrame(anomaly_rows)

print("\nKey January anomalies:")
for season in all_seasons:
    jan = anomaly_df[(anomaly_df["Year"] == season) & (anomaly_df["Month"] == "Jan")]
    if not jan.empty:
        pct = jan["Anomaly_Percent"].values[0]
        marker = " ← CURRENT" if "2025" in season else ""
        if pct >= 180 or "2025" in season or "2009" in season:
            print(f"  {season}: {pct}%{marker}")

# Save CSV
csv_path = VEDA_STORIES / "rainfall-anomaly.csv"
anomaly_df.to_csv(csv_path, index=False)
print(f"\nSaved: {csv_path}")

# ═════════════════════════════════════════════════════════════════════════════
# PART 2: Rich Rainfall Anomaly Chart (PNG)
# ═════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PART 2: Generating rainfall anomaly bar chart")
print("=" * 70)

fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor("#1a1a2e")
ax.set_facecolor("#16213e")

jan_data = anomaly_df[(anomaly_df["Month"] == "Jan") & (anomaly_df["Year"] != "2000-2020 Average")]
years = jan_data["Year"].values
pcts = jan_data["Anomaly_Percent"].values

colors = []
for p in pcts:
    if p >= 200:
        colors.append("#e74c3c")
    elif p >= 150:
        colors.append("#f39c12")
    elif p >= 120:
        colors.append("#3498db")
    elif p >= 80:
        colors.append("#2ecc71")
    else:
        colors.append("#95a5a6")

bars = ax.bar(range(len(years)), pcts, color=colors, alpha=0.85, edgecolor="none")

# Baseline
ax.axhline(100, color="#ffffff", linewidth=1, linestyle="--", alpha=0.4)

# Annotate top 3 and current year
sorted_idx = np.argsort(pcts)[::-1]
for rank, idx in enumerate(sorted_idx[:3]):
    bars[idx].set_edgecolor("#ffffff")
    bars[idx].set_linewidth(2 if rank == 0 else 1.2)
    ax.annotate(f'{pcts[idx]}%',
                xy=(idx, pcts[idx]),
                xytext=(0, 8), textcoords="offset points",
                fontsize=10 if rank == 0 else 8,
                fontweight="bold" if rank == 0 else "normal",
                color=colors[idx], ha="center", va="bottom")

# Always annotate 2025-26
if "2025-26" in list(years):
    idx_2526 = list(years).index("2025-26")
    if idx_2526 not in sorted_idx[:3]:
        bars[idx_2526].set_edgecolor("#ffffff")
        bars[idx_2526].set_linewidth(2)
        ax.annotate(f'{pcts[idx_2526]}%',
                    xy=(idx_2526, pcts[idx_2526]),
                    xytext=(0, 8), textcoords="offset points",
                    fontsize=10, fontweight="bold",
                    color=colors[idx_2526], ha="center", va="bottom")

ax.set_xticks(range(len(years)))
ax.set_xticklabels([y.split("-")[0][-2:] + "/" + y.split("-")[1] for y in years],
                    rotation=45, ha="right", fontsize=8, color="#cccccc")
ax.set_ylabel("% of 2000–2020 Average", color="#cccccc", fontsize=11)
ax.set_title("January Rainfall Anomaly — Mainland Portugal (ERA5-Land)\n"
             "Grid average across 12 representative stations",
             color="white", fontsize=13, fontweight="bold", pad=15)

ax.tick_params(colors="#cccccc")
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["bottom", "left"]:
    ax.spines[spine].set_color("#444")

legend_elements = [
    mpatches.Patch(color="#e74c3c", label="≥200% (extreme wet)"),
    mpatches.Patch(color="#f39c12", label="150–200%"),
    mpatches.Patch(color="#3498db", label="120–150%"),
    mpatches.Patch(color="#2ecc71", label="80–120% (normal)"),
    mpatches.Patch(color="#95a5a6", label="<80% (dry)"),
]
ax.legend(handles=legend_elements, loc="upper left", fontsize=8,
          facecolor="#1a1a2e", edgecolor="#444", labelcolor="#cccccc")

plt.tight_layout()
for path in [FIGURES_DIR / "07-rainfall-anomaly.png",
             VEDA_STORIES / "rainfall-anomaly.png"]:
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved: {path}")
plt.close(fig)

# ═════════════════════════════════════════════════════════════════════════════
# PART 3: Rich Discharge Comparison (from existing JSON data)
# ═════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PART 3: Generating discharge comparison chart")
print("=" * 70)

STORM_COLORS = {"Kristin": "#9b59b6", "Leonardo": "#2ecc71", "Marta": "#e67e22"}

rivers_data = {}
for json_file in sorted(DISCHARGE_DIR.glob("*.json")):
    if json_file.stem == "summary":
        continue
    with open(json_file) as f:
        data = json.load(f)
    rivers_data[data["river"]] = data

if rivers_data:
    sorted_rivers = sorted(
        rivers_data.items(),
        key=lambda x: (x[1].get("summary_stats", {}).get("storm_amplification") or 0),
        reverse=True,
    )

    TOP_N = min(6, len(sorted_rivers))
    fig, axes = plt.subplots(TOP_N, 1, figsize=(14, 3 * TOP_N), sharex=True)
    fig.patch.set_facecolor("#1a1a2e")
    if TOP_N == 1:
        axes = [axes]

    for ax, (river, result) in zip(axes, sorted_rivers[:TOP_N]):
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="#cccccc", labelsize=8)
        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)
        for s in ["bottom", "left"]:
            ax.spines[s].set_color("#444")

        dates = [datetime.strptime(d, "%Y-%m-%d") for d in result["dates"]]
        discharge = result["discharge_m3s"]
        mean_vals = result["discharge_mean"]
        max_vals = result.get("discharge_max", [])
        p25 = result.get("discharge_p25", [])
        p75 = result.get("discharge_p75", [])

        if p25 and p75:
            ax.fill_between(dates, p25, p75, alpha=0.2, color="#3498db")
        if max_vals:
            ax.plot(dates, max_vals, color="#95a5a6", linewidth=0.8, linestyle=":", alpha=0.5)

        ax.plot(dates, mean_vals, color="#3498db", linewidth=1.2, linestyle="--", alpha=0.7)
        ax.plot(dates, discharge, color="#e74c3c", linewidth=2.5, zorder=5)

        for storm_name, storm_date in STORMS.items():
            sd = datetime.strptime(storm_date, "%Y-%m-%d")
            if dates[0] <= sd <= dates[-1]:
                ax.axvline(sd, color=STORM_COLORS[storm_name], linewidth=1.5, linestyle="--", alpha=0.6)
                ymax = ax.get_ylim()[1]
                ax.text(sd, ymax * 0.92, f" {storm_name}",
                        color=STORM_COLORS[storm_name], fontsize=8, fontweight="bold", va="top")

        peak = result.get("peak", {})
        if peak.get("date"):
            peak_dt = datetime.strptime(peak["date"], "%Y-%m-%d")
            ax.scatter([peak_dt], [peak["discharge_m3s"]], color="#e74c3c", s=60, zorder=6,
                       edgecolors="white", linewidths=1.5)

        stats = result.get("summary_stats", {})
        amp = stats.get("storm_amplification", "?")
        ax.set_ylabel(f"{river}", color="white", fontsize=10, fontweight="bold",
                       rotation=0, labelpad=60)
        ax.text(0.98, 0.85,
                f'Peak: {peak.get("discharge_m3s", "?")} m³/s | {amp}× storm amplification',
                transform=ax.transAxes, fontsize=8, color="#cccccc",
                ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a1a2e", edgecolor="#444", alpha=0.9))

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    axes[-1].xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    axes[-1].set_xlabel("Date (2026)", color="#cccccc", fontsize=11)

    fig.suptitle("River Discharge vs Climatology — Jan–Feb 2026\n"
                 "Red = actual | Blue dashed = clim. mean | Shaded = IQR | Grey = hist. max",
                 color="white", fontsize=13, fontweight="bold", y=1.01)

    storm_patches = [mpatches.Patch(color=c, label=f"Storm {n}", alpha=0.7) for n, c in STORM_COLORS.items()]
    fig.legend(handles=storm_patches, loc="upper right", fontsize=9,
               facecolor="#1a1a2e", edgecolor="#444", labelcolor="#cccccc")

    plt.tight_layout()
    for path in [FIGURES_DIR / "07-discharge-comparison-story.png",
                 VEDA_STORIES / "discharge-comparison-story.png"]:
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        print(f"Saved: {path}")
    plt.close(fig)
else:
    print("  No discharge data — skipping")

# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("CONTENT PIVOT RATIONALE (for reviewers)")
print("=" * 70)
print("""
VEDA-UI component capabilities vs story needs:

  <Chart>   = recharts LineChart only → line plots, time axis, brush zoom
  <Table>   = sortable data table from CSV → good for storm comparison
  <Image>   = static figure → complex multi-variable charts
  <CompareImage> = before/after slider → satellite imagery

v0 story content mapping:

  Component        | Asset                          | Why this type
  -----------------+--------------------------------+-------------------------
  <Chart>          | discharge-timeseries.csv       | Simple hydrograph, interactive zoom useful
  <Chart>          | fatality-timeline.csv          | Cumulative line, simple
  <Image>          | rainfall-anomaly.png           | Bar chart (Chart can't do bars)
  <Image>          | discharge-comparison-story.png | Multi-river, dual context, annotations
  <Table>          | storm-comparison.csv           | Sortable properties, natural table
  <Image>          | (notebook figures as needed)    | Any complex visualization

This preserves narrative flow: readers see rich, publication-quality figures
inline, with interactive elements where interactivity genuinely helps.
""")
print("Done.")
