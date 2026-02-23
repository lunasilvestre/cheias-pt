# Task: Curate Geocoded Consequence Markers — Portugal Floods Jan-Feb 2026

## What I need

A GeoJSON file with 30-50 geocoded events from Portugal's January-February 2026 flood crisis. These are the human consequences — deaths, evacuations, infrastructure damage, rescues, landslides — that will be plotted as markers on a scrollytelling map at cheias.pt.

Each event must be a GeoJSON Point feature with precise coordinates (not city centroids — actual location where it happened when possible).

## Timeline to cover

- **Jan 26-29:** Storm Kristin — Coimbra, Leiria, Médio Tejo devastated
- **Feb 3-7:** Storm Leonardo — Tejo floods, Sado at 1989 levels, Alcácer do Sal evacuations
- **Feb 8-10:** Storm Marta — continued flooding, Douro overflows into Porto/Gaia
- **Feb 10-15:** Aftermath — state of calamity extended, political fallout, Interior Minister resignation

## Event types to capture

Prioritize diversity of event types and geographic spread across Portugal:

- **Deaths** (at least 13-15 confirmed) — location, date, brief circumstances
- **Evacuations** — Alcácer do Sal (179+ from Sado flooding), others
- **Infrastructure collapse** — A2 highway collapse near Santarém, road cuts, bridge damage
- **River records** — Tejo highest since 1997 (~8,600 m³/s), Sado highest since 1989, Douro at 6.15m in Porto
- **Levee/dam incidents** — Mondego levee concerns, Spanish dam releases into Tejo
- **Landslides** — central Portugal, post-wildfire areas
- **Power/communications cuts** — up to 1 million without power
- **Rescues** — Navy/firefighter boat rescues, isolated villages
- **School/office closures** — Lisbon metro shutdown, train line cuts
- **Military deployment** — 2,000 soldiers deployed

## Required GeoJSON schema

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "title": "Portugal Flood Crisis Jan-Feb 2026 — Consequence Markers",
    "created": "2026-02-15",
    "sources": ["Proteção Civil", "Lusa", "Público", "Expresso", "Bloomberg", "Euronews", "BBC"],
    "total_events": 0
  },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-8.5147, 38.3725]
      },
      "properties": {
        "id": "evt-001",
        "type": "evacuation",
        "date": "2026-02-05",
        "storm": "Leonardo",
        "title_pt": "Evacuação em Alcácer do Sal",
        "description_pt": "179 pessoas evacuadas após Sado transbordar. Água subiu 2 metros em 20 minutos.",
        "title_en": "Alcácer do Sal evacuation",
        "description_en": "179 people evacuated after Sado overflowed. Water rose 2 metres in 20 minutes.",
        "source": "Expresso",
        "source_url": "",
        "river_basin": "Sado",
        "district": "Setúbal",
        "municipality": "Alcácer do Sal",
        "severity": "high",
        "chapter": 6
      }
    }
  ]
}
```

### Property definitions

- **type**: one of `death`, `evacuation`, `infrastructure`, `river_record`, `levee_dam`, `landslide`, `power_cut`, `rescue`, `closure`, `military`, `political`
- **date**: ISO date (YYYY-MM-DD)
- **storm**: `Kristin`, `Leonardo`, `Marta`, or `aftermath`
- **severity**: `extreme` (deaths, major collapse), `high` (mass evacuation, record levels), `medium` (road cuts, power outages), `low` (closures, minor damage)
- **chapter**: which scrollytelling chapter this event anchors (1-9, based on narrative structure below)
- **river_basin**: `Tejo`, `Sado`, `Mondego`, `Douro`, `Lis`, or other
- **source_url**: actual URL if findable, empty string if not

## Narrative chapters for reference (chapter property)

1. The Flood (Tejo satellite view) — chapter 1
2. Three Storms (atmospheric timeline) — chapter 2  
3. The Saturated Ground (soil moisture) — chapter 3
4. The Rivers Rise (discharge data) — chapter 4
5. The Warnings (IPMA) — chapter 5
6. The Consequences (human impact) — chapter 6
7. The Recovery — chapter 7
8. What Could Have Been Different — chapter 8
9. Explore — chapter 9

Most events will be chapter 6, but deaths and major infrastructure might appear in chapters 1 or 7.

## How to work

1. **Search systematically** — go through Portuguese and international sources for each storm period. Key sources:
   - Proteção Civil / ANEPC situation reports
   - Lusa (Portuguese news agency)
   - Público, Expresso, Observador, Diário de Notícias
   - Bloomberg, Euronews, BBC, Reuters international coverage
   - Jorge Branco's Substack (detailed English-language coverage)
   - Local câmara (municipality) social media

2. **Geocode precisely** — don't just use city centroids. If an event happened on a specific road (e.g., A2 collapse), find the approximate coordinates. If villages were isolated, locate those villages specifically.

3. **Ensure geographic coverage** — don't cluster everything in Alcácer do Sal. The floods affected Leiria, Coimbra, Santarém, Setúbal, Porto, Évora, and more. Aim for at least 8 different municipalities.

4. **Ensure temporal coverage** — events across all three storms plus aftermath.

5. **Output the complete GeoJSON** as a code block I can save directly to `data/consequences/events.geojson`.

6. **After the GeoJSON**, provide a summary table: total events by type, by storm, by district, by severity.

## Quality checks

- Every coordinate must be in Portugal (lat ~37-42, lon ~-9.5 to -6.2)
- Every event must have both Portuguese and English text
- No duplicate events
- Dates must be within Jan 25 - Feb 15 2026
- At least 30 events, ideally 40-50
