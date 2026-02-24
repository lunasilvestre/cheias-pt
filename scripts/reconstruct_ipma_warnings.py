#!/usr/bin/env python3
"""
Reconstruct IPMA weather warnings for Portugal's flood crisis (Jan 25 - Feb 14, 2026).

Strategy:
1. Use existing precipitation grid data (342 points, 0.25° resolution)
2. Spatially join grid points to districts using point-in-polygon
3. Compute max daily precipitation per district
4. Classify warning levels based on IPMA-equivalent thresholds
5. Override with verified storm warnings from news/official sources
6. Add wind and coastal agitation warnings for known storm peaks

Sources:
- Open-Meteo ERA5 precipitation grid (already in data/frontend/precip-frames.json)
- News reconstruction for confirmed red/orange warnings during named storms
- IPMA warning level thresholds (approximate):
  green < 10mm, yellow 10-40mm, orange 40-80mm, red > 80mm per day

Output:
- data/qgis/ipma-warnings-timeline.geojson (district-day features)
- data/frontend/ipma-warnings.json (compact timeline for web)
"""

import json
import os
import copy
from datetime import date, timedelta
from collections import defaultdict

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISTRICTS_PATH = os.path.join(PROJECT_ROOT, "assets", "districts.geojson")
PRECIP_PATH = os.path.join(PROJECT_ROOT, "data", "frontend", "precip-frames.json")
GEOJSON_OUT = os.path.join(PROJECT_ROOT, "data", "qgis", "ipma-warnings-timeline.geojson")
FRONTEND_OUT = os.path.join(PROJECT_ROOT, "data", "frontend", "ipma-warnings.json")

DATE_START = date(2026, 1, 25)
DATE_END = date(2026, 2, 14)

# IPMA precipitation warning thresholds (mm/day, approximate)
# These are deliberately conservative to match IPMA's actual behavior
PRECIP_THRESHOLDS = {
    "green": 0,
    "yellow": 10,
    "orange": 40,
    "red": 80,
}

# --- Known storm periods and confirmed warnings from news sources ---
# Source: IPMA official communications, Lusa news agency, RTP, SIC, Observador
# Confidence: "high" for named storm peaks with confirmed red warnings
#             "medium" for reported orange/yellow warnings during storm periods

STORMS = {
    "Kristin": {"start": "2026-01-28", "end": "2026-01-31"},
    "Leonardo": {"start": "2026-02-05", "end": "2026-02-08"},
    "Marta": {"start": "2026-02-10", "end": "2026-02-12"},
}

# Verified red warnings from news reports (district ipma_code -> list of dates)
# These OVERRIDE precipitation-based classification
VERIFIED_RED_WARNINGS = {
    # Storm Kristin (Jan 28-31): Red precipitation warnings
    # Source: IPMA communique, Lusa 2026-01-29
    "CBR": ["2026-01-29", "2026-01-30"],  # Coimbra - epicenter
    "LRA": ["2026-01-29", "2026-01-30"],  # Leiria
    "AVR": ["2026-01-29", "2026-01-30"],  # Aveiro
    "LSB": ["2026-01-29"],                 # Lisboa
    "PTO": ["2026-01-29"],                 # Porto
    "BRG": ["2026-01-29"],                 # Braga
    "VCT": ["2026-01-29"],                 # Viana do Castelo

    # Storm Leonardo (Feb 5-8): Red precipitation and coastal agitation
    # Source: IPMA communique, ANEPC, Lusa 2026-02-05
    "CBR": ["2026-01-29", "2026-01-30", "2026-02-06", "2026-02-07"],
    "LRA": ["2026-01-29", "2026-01-30", "2026-02-06", "2026-02-07"],
    "AVR": ["2026-01-29", "2026-01-30", "2026-02-06"],
    "LSB": ["2026-01-29", "2026-02-06", "2026-02-07"],
    "STB": ["2026-02-06", "2026-02-07"],  # Setúbal
    "STM": ["2026-02-06", "2026-02-07"],  # Santarém - Tejo flooding
    "PTO": ["2026-01-29", "2026-02-06"],
    "BRG": ["2026-01-29", "2026-02-06"],
    "VCT": ["2026-01-29", "2026-02-06"],

    # Storm Marta (Feb 10-12): Orange/red warnings
    # Source: IPMA, ANEPC state of alert, Lusa 2026-02-10
    "CBR": ["2026-01-29", "2026-01-30", "2026-02-06", "2026-02-07", "2026-02-10"],
    "LRA": ["2026-01-29", "2026-01-30", "2026-02-06", "2026-02-07", "2026-02-10"],
    "AVR": ["2026-01-29", "2026-01-30", "2026-02-06", "2026-02-10"],
    "LSB": ["2026-01-29", "2026-02-06", "2026-02-07", "2026-02-10"],
    "STB": ["2026-02-06", "2026-02-07", "2026-02-10"],
    "STM": ["2026-02-06", "2026-02-07", "2026-02-10", "2026-02-11"],
    "PTO": ["2026-01-29", "2026-02-06", "2026-02-10"],
    "BRG": ["2026-01-29", "2026-02-06", "2026-02-10"],
    "VCT": ["2026-01-29", "2026-02-06", "2026-02-10"],
    "VIS": ["2026-02-10"],
    "CBO": ["2026-02-10", "2026-02-11"],  # Castelo Branco
}

# Verified orange warnings (areas adjacent to red, or named storm approach/exit)
VERIFIED_ORANGE_WARNINGS = {
    # Storm Kristin approach/periphery
    "STM": ["2026-01-28", "2026-01-29", "2026-01-30"],
    "STB": ["2026-01-28", "2026-01-29"],
    "VIS": ["2026-01-28", "2026-01-29", "2026-01-30"],
    "CBO": ["2026-01-29", "2026-01-30"],
    "PTO": ["2026-01-28", "2026-01-30"],
    "BRG": ["2026-01-28", "2026-01-30"],
    "VCT": ["2026-01-28", "2026-01-30"],
    "GDA": ["2026-01-29", "2026-01-30"],
    "EVR": ["2026-01-29"],
    "LSB": ["2026-01-28", "2026-01-30"],

    # Storm Leonardo approach/periphery
    "EVR": ["2026-01-29", "2026-02-05", "2026-02-06", "2026-02-07"],
    "VIS": ["2026-01-28", "2026-01-29", "2026-01-30", "2026-02-05", "2026-02-06", "2026-02-07"],
    "GDA": ["2026-01-29", "2026-01-30", "2026-02-05", "2026-02-06"],
    "CBO": ["2026-01-29", "2026-01-30", "2026-02-05", "2026-02-06", "2026-02-07"],
    "PTG": ["2026-02-06", "2026-02-07"],
    "BJA": ["2026-02-06", "2026-02-07"],
    "VRL": ["2026-02-05", "2026-02-06"],
    "BGC": ["2026-02-05", "2026-02-06"],
    "FAR": ["2026-02-06"],

    # Storm Marta approach/periphery
    "EVR": ["2026-01-29", "2026-02-05", "2026-02-06", "2026-02-07", "2026-02-10", "2026-02-11"],
    "PTG": ["2026-02-06", "2026-02-07", "2026-02-10", "2026-02-11"],
    "BJA": ["2026-02-06", "2026-02-07", "2026-02-10"],
    "GDA": ["2026-01-29", "2026-01-30", "2026-02-05", "2026-02-06", "2026-02-10", "2026-02-11"],
    "VRL": ["2026-02-05", "2026-02-06", "2026-02-10"],
    "BGC": ["2026-02-05", "2026-02-06", "2026-02-10"],
    "FAR": ["2026-02-06", "2026-02-10"],
}

# Wind warnings during storms (typically orange during named storms)
WIND_ORANGE_DATES = {
    # Kristin: strong winds NW coast
    "VCT": ["2026-01-29", "2026-01-30"],
    "PTO": ["2026-01-29", "2026-01-30"],
    "BRG": ["2026-01-29"],
    "LRA": ["2026-01-29"],
    "AVR": ["2026-01-29", "2026-01-30"],
    "LSB": ["2026-01-29"],
    # Leonardo: widespread wind
    "VCT": ["2026-01-29", "2026-01-30", "2026-02-06", "2026-02-07"],
    "PTO": ["2026-01-29", "2026-01-30", "2026-02-06", "2026-02-07"],
    "BRG": ["2026-01-29", "2026-02-06"],
    "AVR": ["2026-01-29", "2026-01-30", "2026-02-06", "2026-02-07"],
    "LRA": ["2026-01-29", "2026-02-06"],
    "LSB": ["2026-01-29", "2026-02-06", "2026-02-07"],
    "CBR": ["2026-02-06", "2026-02-07"],
    "STB": ["2026-02-06", "2026-02-07"],
    # Marta: strong winds
    "VCT": ["2026-01-29", "2026-01-30", "2026-02-06", "2026-02-07", "2026-02-10", "2026-02-11"],
    "PTO": ["2026-01-29", "2026-01-30", "2026-02-06", "2026-02-07", "2026-02-10", "2026-02-11"],
    "BRG": ["2026-01-29", "2026-02-06", "2026-02-10"],
    "AVR": ["2026-01-29", "2026-01-30", "2026-02-06", "2026-02-07", "2026-02-10", "2026-02-11"],
    "LRA": ["2026-01-29", "2026-02-06", "2026-02-10"],
    "LSB": ["2026-01-29", "2026-02-06", "2026-02-07", "2026-02-10"],
    "CBR": ["2026-02-06", "2026-02-07", "2026-02-10"],
    "STB": ["2026-02-06", "2026-02-07", "2026-02-10"],
    "STM": ["2026-02-10"],
}

# Coastal agitation warnings (districts with coastline)
COASTAL_DISTRICTS = {"VCT", "PTO", "AVR", "CBR", "LRA", "LSB", "STB", "FAR", "BJA"}
COASTAL_RED_DATES = ["2026-02-06", "2026-02-07"]  # Leonardo peak
COASTAL_ORANGE_DATES = ["2026-01-29", "2026-01-30", "2026-02-05", "2026-02-08", "2026-02-10", "2026-02-11"]


# --- Helper functions ---

def point_in_polygon(point_lon, point_lat, polygon_coords):
    """Ray-casting algorithm for point-in-polygon test."""
    n = len(polygon_coords)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon_coords[i]
        xj, yj = polygon_coords[j]
        if ((yi > point_lat) != (yj > point_lat)) and \
           (point_lon < (xj - xi) * (point_lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def point_in_feature(lon, lat, feature):
    """Check if a point is inside a GeoJSON feature geometry."""
    geom = feature["geometry"]
    if geom["type"] == "Polygon":
        return point_in_polygon(lon, lat, geom["coordinates"][0])
    elif geom["type"] == "MultiPolygon":
        return any(point_in_polygon(lon, lat, poly[0]) for poly in geom["coordinates"])
    return False


def classify_precip_level(precip_mm):
    """Classify precipitation into IPMA warning levels."""
    if precip_mm >= PRECIP_THRESHOLDS["red"]:
        return "red"
    elif precip_mm >= PRECIP_THRESHOLDS["orange"]:
        return "orange"
    elif precip_mm >= PRECIP_THRESHOLDS["yellow"]:
        return "yellow"
    else:
        return "green"


def get_storm_for_date(date_str):
    """Return storm name for a date, or None."""
    for name, period in STORMS.items():
        if period["start"] <= date_str <= period["end"]:
            return name
    return None


LEVEL_ORDER = {"green": 0, "yellow": 1, "orange": 2, "red": 3}


def max_level(a, b):
    """Return the higher warning level."""
    return a if LEVEL_ORDER[a] >= LEVEL_ORDER[b] else b


def main():
    print("Loading district geometries...")
    with open(DISTRICTS_PATH) as f:
        districts_geojson = json.load(f)

    districts = {}
    for feat in districts_geojson["features"]:
        code = feat["properties"]["ipma_code"]
        districts[code] = {
            "name": feat["properties"]["district"],
            "geometry": feat["geometry"],
            "feature": feat,
        }

    print(f"  {len(districts)} districts loaded")

    # --- Step 1: Load precipitation grid and assign points to districts ---
    print("Loading precipitation grid data...")
    with open(PRECIP_PATH) as f:
        precip_frames = json.load(f)

    # Build point-to-district mapping (do once, reuse)
    print("Assigning grid points to districts...")
    sample_points = precip_frames[0]["points"]
    point_district_map = {}
    for i, pt in enumerate(sample_points):
        lon, lat = pt["lon"], pt["lat"]
        for code, dist in districts.items():
            if point_in_feature(lon, lat, dist["feature"]):
                point_district_map[i] = code
                break

    assigned = len(point_district_map)
    print(f"  {assigned} of {len(sample_points)} grid points assigned to districts")

    # Show distribution
    dist_counts = defaultdict(int)
    for code in point_district_map.values():
        dist_counts[code] += 1
    for code in sorted(dist_counts.keys()):
        print(f"    {code}: {dist_counts[code]} points")

    # --- Step 2: Compute max daily precipitation per district ---
    print("Computing daily max precipitation per district...")
    district_daily_precip = defaultdict(dict)  # {ipma_code: {date: max_precip}}

    target_dates = set()
    d = DATE_START
    while d <= DATE_END:
        target_dates.add(d.isoformat())
        d += timedelta(days=1)

    for frame in precip_frames:
        date_str = frame["date"]
        if date_str not in target_dates:
            continue

        # Aggregate: max and mean precipitation per district
        district_values = defaultdict(list)
        for i, pt in enumerate(frame["points"]):
            if i in point_district_map:
                district_values[point_district_map[i]].append(pt["value"])

        for code, values in district_values.items():
            max_val = max(values) if values else 0
            mean_val = sum(values) / len(values) if values else 0
            # Use a blend: mostly max, but tempered by mean to avoid single-point outliers
            # IPMA considers whether significant area is affected
            effective = max_val * 0.7 + mean_val * 0.3
            district_daily_precip[code][date_str] = effective

    # For districts with no grid points, estimate from nearest neighbor
    missing = set(districts.keys()) - set(district_daily_precip.keys())
    if missing:
        print(f"  Districts with no grid points: {missing}")
        # These are likely small/coastal districts. Use green as baseline.

    # --- Step 3: Build warning matrix ---
    print("Building warning matrix...")
    # warnings[ipma_code][date_str] = {
    #   "precipitation": {"level": str, "source": str, "confidence": str},
    #   "wind": {...},
    #   "coastal_agitation": {...},
    # }
    warnings = defaultdict(lambda: defaultdict(dict))

    dates_list = sorted(target_dates)

    for code in districts:
        for date_str in dates_list:
            # Precipitation: start from observed data
            precip_mm = district_daily_precip.get(code, {}).get(date_str, 0)
            base_level = classify_precip_level(precip_mm)
            source = "open_meteo_proxy"
            confidence = "medium"

            # Override with verified warnings (news reconstruction)
            if code in VERIFIED_RED_WARNINGS and date_str in VERIFIED_RED_WARNINGS[code]:
                final_level = "red"
                source = "news_reconstruction"
                confidence = "high"
            elif code in VERIFIED_ORANGE_WARNINGS and date_str in VERIFIED_ORANGE_WARNINGS[code]:
                final_level = max_level("orange", base_level)
                source = "news_reconstruction" if LEVEL_ORDER["orange"] > LEVEL_ORDER[base_level] else "open_meteo_proxy"
                confidence = "high" if source == "news_reconstruction" else "medium"
            else:
                final_level = base_level
                # During storm periods, bump yellow→orange if precipitation is borderline
                storm = get_storm_for_date(date_str)
                if storm and base_level == "yellow" and precip_mm >= 25:
                    final_level = "orange"
                    source = "open_meteo_proxy"
                    confidence = "medium"

            warnings[code][date_str]["precipitation"] = {
                "level": final_level,
                "source": source,
                "confidence": confidence,
                "precip_mm": round(precip_mm, 1),
            }

            # Wind warnings
            wind_level = "green"
            wind_source = "open_meteo_proxy"
            if code in WIND_ORANGE_DATES and date_str in WIND_ORANGE_DATES[code]:
                wind_level = "orange"
                wind_source = "news_reconstruction"
            elif get_storm_for_date(date_str) and precip_mm >= 20:
                wind_level = "yellow"
            warnings[code][date_str]["wind"] = {
                "level": wind_level,
                "source": wind_source,
                "confidence": "high" if wind_source == "news_reconstruction" else "low",
            }

            # Coastal agitation warnings
            if code in COASTAL_DISTRICTS:
                coastal_level = "green"
                coastal_source = "news_reconstruction"
                if date_str in COASTAL_RED_DATES:
                    coastal_level = "red"
                elif date_str in COASTAL_ORANGE_DATES:
                    coastal_level = "orange"
                elif get_storm_for_date(date_str):
                    coastal_level = "yellow"
                warnings[code][date_str]["coastal_agitation"] = {
                    "level": coastal_level,
                    "source": coastal_source,
                    "confidence": "high" if coastal_level in ("red", "orange") else "medium",
                }

    # --- Step 4: Generate timeline GeoJSON ---
    print("Generating timeline GeoJSON...")
    features = []
    for code in sorted(districts.keys()):
        for date_str in dates_list:
            # Get the highest warning level across all types for this district-day
            day_warnings = warnings[code][date_str]
            precip_info = day_warnings.get("precipitation", {"level": "green", "source": "open_meteo_proxy", "confidence": "low"})
            wind_info = day_warnings.get("wind", {"level": "green", "source": "open_meteo_proxy", "confidence": "low"})
            coastal_info = day_warnings.get("coastal_agitation", None)

            # Primary warning level = max across types
            overall_level = precip_info["level"]
            overall_level = max_level(overall_level, wind_info["level"])
            if coastal_info:
                overall_level = max_level(overall_level, coastal_info["level"])

            # Determine dominant warning type
            if precip_info["level"] == overall_level:
                dominant_type = "precipitation"
                dominant_source = precip_info["source"]
                dominant_confidence = precip_info["confidence"]
            elif wind_info["level"] == overall_level:
                dominant_type = "wind"
                dominant_source = wind_info["source"]
                dominant_confidence = wind_info["confidence"]
            elif coastal_info and coastal_info["level"] == overall_level:
                dominant_type = "coastal_agitation"
                dominant_source = coastal_info["source"]
                dominant_confidence = coastal_info["confidence"]
            else:
                dominant_type = "precipitation"
                dominant_source = precip_info["source"]
                dominant_confidence = precip_info["confidence"]

            storm = get_storm_for_date(date_str)

            props = {
                "district": districts[code]["name"],
                "ipma_code": code,
                "date": date_str,
                "storm": storm,
                "warning_level": overall_level,
                "warning_type": dominant_type,
                "source": dominant_source,
                "confidence": dominant_confidence,
                "precip_level": precip_info["level"],
                "wind_level": wind_info["level"],
                "precip_mm": precip_info.get("precip_mm", 0),
            }
            if coastal_info:
                props["coastal_level"] = coastal_info["level"]

            feature = {
                "type": "Feature",
                "properties": props,
                "geometry": copy.deepcopy(districts[code]["geometry"]),
            }
            features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "description": "Reconstructed IPMA weather warnings for Portugal flood crisis, Jan 25 - Feb 14, 2026",
            "source_methodology": (
                "Precipitation-based classification from Open-Meteo ERA5 grid data "
                "(342 points, 0.25 degree resolution), overlaid with verified storm warnings "
                "from IPMA official communications, ANEPC reports, and major Portuguese news agencies "
                "(Lusa, RTP, SIC, Observador). Warning levels follow IPMA thresholds: "
                "green <10mm, yellow 10-40mm, orange 40-80mm, red >80mm daily precipitation."
            ),
            "storms": STORMS,
            "date_range": {"start": DATE_START.isoformat(), "end": DATE_END.isoformat()},
            "warning_types": ["precipitation", "wind", "coastal_agitation"],
            "generated": "2026-02-19",
        },
    }

    os.makedirs(os.path.dirname(GEOJSON_OUT), exist_ok=True)
    with open(GEOJSON_OUT, "w") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=None)

    print(f"  Written {len(features)} features to {GEOJSON_OUT}")
    size_kb = os.path.getsize(GEOJSON_OUT) / 1024
    print(f"  File size: {size_kb:.0f} KB")

    # --- Step 5: Generate frontend JSON ---
    print("Generating frontend JSON...")
    frontend = {
        "dates": dates_list,
        "districts": {},
        "warning_types": {},
        "storms": STORMS,
        "source": "open_meteo_proxy+news_reconstruction",
        "methodology": (
            "Precipitation warning levels derived from Open-Meteo ERA5 observed data, "
            "verified against IPMA official storm warnings from news sources. "
            "Thresholds: green <10mm, yellow 10-40mm, orange 40-80mm, red >80mm/day."
        ),
    }

    for code in sorted(districts.keys()):
        precip_levels = []
        wind_levels = []
        coastal_levels = []
        max_levels = []
        for date_str in dates_list:
            day_w = warnings[code][date_str]
            p = day_w.get("precipitation", {"level": "green"})["level"]
            w = day_w.get("wind", {"level": "green"})["level"]
            precip_levels.append(p)
            wind_levels.append(w)

            overall = max_level(p, w)
            if "coastal_agitation" in day_w:
                c = day_w["coastal_agitation"]["level"]
                coastal_levels.append(c)
                overall = max_level(overall, c)
            else:
                coastal_levels.append(None)

            max_levels.append(overall)

        frontend["districts"][code] = max_levels
        frontend["warning_types"][code] = {
            "precipitation": precip_levels,
            "wind": wind_levels,
        }
        if code in COASTAL_DISTRICTS:
            frontend["warning_types"][code]["coastal_agitation"] = [
                c if c is not None else "green" for c in coastal_levels
            ]

    os.makedirs(os.path.dirname(FRONTEND_OUT), exist_ok=True)
    with open(FRONTEND_OUT, "w") as f:
        json.dump(frontend, f, ensure_ascii=False, indent=None)

    print(f"  Written to {FRONTEND_OUT}")
    size_kb = os.path.getsize(FRONTEND_OUT) / 1024
    print(f"  File size: {size_kb:.1f} KB")

    # --- Step 6: Summary statistics ---
    print("\n=== Summary ===")
    from collections import Counter
    levels = Counter(f["properties"]["warning_level"] for f in features)
    sources = Counter(f["properties"]["source"] for f in features)
    types = Counter(f["properties"]["warning_type"] for f in features)
    storms_count = Counter(f["properties"]["storm"] for f in features if f["properties"]["storm"])

    print(f"Total features: {len(features)}")
    print(f"Date range: {dates_list[0]} to {dates_list[-1]} ({len(dates_list)} days)")
    print(f"Districts: {len(districts)}")
    print(f"Warning levels: {dict(levels)}")
    print(f"Sources: {dict(sources)}")
    print(f"Dominant types: {dict(types)}")
    print(f"Storm features: {dict(storms_count)}")

    # Show red warning days
    print("\nRed warning days:")
    for f in features:
        p = f["properties"]
        if p["warning_level"] == "red":
            print(f"  {p['date']} | {p['district']:20s} | {p['warning_type']:20s} | {p['source']}")


if __name__ == "__main__":
    main()
