# T5 — Story Swap: Fix Extended Story + Drop into VEDA-UI

## Mission

Transform `cheias-pt/tasks/cheias-extended-story.mdx` into a VEDA-UI–compatible
story and deploy it to `cheias-pt-veda-ui/stories/winter-2025-26-floods.stories.mdx`.

This is mechanical surgery — no content changes, just path/prop fixes and
a content type pivot for two chart components.

## Working copies

- Source: `~/Documents/dev/cheias-pt/tasks/cheias-extended-story.mdx` (755 lines)
- Target: `~/Documents/dev/cheias-pt-veda-ui/stories/winter-2025-26-floods.stories.mdx`
- Assets: `~/Documents/dev/cheias-pt-veda-ui/stories/media/floods/` (7 files)

Work on the **source** first, verify, then copy to target.

## Step 1: Fix frontmatter

Replace the extended story's frontmatter (lines 1–35) with VEDA-UI–compatible frontmatter.
Keep the richer metadata but fix the structure:

```yaml
---
id: 'winter-2025-26-floods'
name: 'Winter 2025-26 Portuguese Flood Events: A Compound Disaster'
description: 'How sequential storms on saturated soils created an unprecedented flood catastrophe across central and southern Portugal.'
media:
  src: ::file ./media/floods/hero-sentinel1-tejo.jpg
  alt: 'Sentinel-1 SAR image showing Tejo river floodplain inundation (Feb 7, 2026) compared to December 2025 baseline'
  author:
    name: 'Copernicus Sentinel-1 SAR'
    url: 'https://sentinels.copernicus.eu/'
pubDate: 2026-03-05T00:00
taxonomy:
  - name: Topics
    values:
      - Flood Monitoring
      - Climate Change
      - Emergency Response
  - name: Subtopics
    values:
      - Hydrological Extremes
      - Portugal
---
```

Key changes from original:
- `media.src`: was `/images/floods/salvaterra-hero...jpg` (never existed) → use `::file ./media/floods/hero-sentinel1-tejo.jpg` — real ESA Sentinel-1 SAR image (1920×1920, CC BY-SA 3.0 IGO)
- Add `pubDate` (VEDA-UI requires it)
- Remove `featured`, `geography`, `datasets`, `temporalExtent` (VEDA-UI story frontmatter doesn't use these; dataset binding happens via `<Chapter datasetId=...>`)

## Step 2: Fix longitude signs

Every `center={[X, Y]}` in the story where X is positive and greater than 1
needs to be negated. Portugal's longitude is negative (~-9.5 to -6.1).

Pattern: `center={[9.5, 39]}` → `center={[-9.5, 39]}`

**Affected values** (apply to ALL occurrences):
- `9.5` → `-9.5`
- `9.2` → `-9.2`
- `9.0` → `-9.0`
- `8.9` → `-8.9`
- `8.5` → `-8.5`

**Do NOT change** `center={[-5, 38]}` — that's already correct (wide Atlantic view).

Use a regex or sed: inside `center={[`, negate any bare positive number > 1
before the comma. There are ~19 occurrences.

Verify after: `grep "center=" <file>` should show ALL longitudes negative.

## Step 3: Rewrite dataPath references

All `./data/*.csv` → `./media/floods/*`:

```
./data/discharge-timeseries.csv  →  ./media/floods/discharge-timeseries.csv
./data/storm-comparison.csv      →  ./media/floods/storm-comparison.csv
./data/fatality-timeline.csv     →  ./media/floods/fatality-timeline.csv
./data/rainfall-anomaly.csv      →  ./media/floods/rainfall-anomaly.csv
```

## Step 4: Content type pivot — Chart → Image for complex figures

VEDA-UI's `<Chart>` is recharts LineChart-only. Two charts in the extended story
need to become `<Image>` components using pre-rendered PNGs.

### 4a. Rainfall anomaly (~line 519-535)

Replace this:
```jsx
<Chart
  dataPath={new URL('./data/rainfall-anomaly.csv', import.meta.url).href}
  idKey='Year'
  xKey='Month'
  yKey='Anomaly_Percent'
  xAxisLabel='Month'
  yAxisLabel='Percent of 1991-2020 Average'
  altTitle='January Rainfall: 2026 vs Historical (1991-2020)'
  altDesc='Bar chart showing January 2026 at 222% of normal...'
  colors={['#1f77b4', '#ff7f0e']}
  colorScheme='blues'
/>
```

With this:
```jsx
<Image
  src={new URL('./media/floods/rainfall-anomaly.png', import.meta.url).href}
  alt='Bar chart showing January 2026 at 252% of 2000-2020 average rainfall — 2nd wettest January in 26-year ERA5 dataset'
/>
```

Also update the `<Caption>` below it — change "222%" to "252%" and
"1991-2020" to "2000-2020" to match the actual ERA5 computation:
```
January 2026: 252% of 2000-2020 average rainfall. 2nd wettest January
in 26-year ERA5 dataset. Only winter 2000-01 was wetter (253%).
```

### 4b. Discharge comparison — ADD new figure

The extended story doesn't currently have a standalone discharge comparison
chart (it shows the hydrograph inline via `<Chart>`). The `<Chart>` for
`discharge-timeseries.csv` can stay — it's a simple line chart that works
in recharts. But ALSO add the multi-river comparison figure in Chapter 7
(Climate Attribution), right before the rainfall anomaly chart. Add:

```jsx
<Block type='wide'>
  <Figure>
    <Image
      src={new URL('./media/floods/discharge-comparison-story.png', import.meta.url).href}
      alt='Six Portuguese rivers showing 3–11× discharge amplification during the Jan 29 – Feb 12 storm cluster, with peaks aligning to Storms Leonardo and Marta'
    />
    <Caption
      attrAuthor='GloFAS via Open-Meteo Flood API'
      attrUrl='https://flood-api.open-meteo.com/'
    >
      All eight monitored rivers showed extreme storm amplification. Guadiana
      and Lis experienced the most dramatic response (8–11× pre-storm baseline).
      Blue shading shows historical IQR; grey dotted line is the historical maximum.
    </Caption>
  </Figure>
</Block>
```

## Step 5: Fix Table component prop name

The extended story uses `columnsToSort` (line ~235) but VEDA-UI's `<Table>`
component expects `columnToSort` (no 's'). Fix:

```
columnsToSort={['Max_Wind_kmh', 'Deaths_Direct', 'Evacuations']}
→
columnToSort={['Max_Wind_kmh', 'Deaths_Direct', 'Evacuations']}
```

Also fix the Table dataPath:
```
dataPath={new URL('./data/storm-comparison.csv', import.meta.url).href}
→
dataPath={new URL('./media/floods/storm-comparison.csv', import.meta.url).href}
```

## Step 6: Remove image references we don't have

The extended story references images that don't exist yet:
- `src='/images/floods/salvaterra-hero-02086-20260208.jpg'` (frontmatter — already fixed in step 1)
- `src='/images/floods/a1-motorway-collapse-20260212.jpg'` (~line 325)

For the A1 motorway image: comment it out or replace with a placeholder `<Prose>`
block that preserves the caption text. We don't have the image yet. Use:

```jsx
<Block>
  <Prose>
    *[Image: A1 motorway bridge pillar failure near Coimbra, Feb 12, 2026.
    Source: Portuguese Government / Estradas de Portugal]*
  </Prose>
</Block>
```

## Step 7: Copy to VEDA-UI

Copy the fixed file to the target:
```bash
cp ~/Documents/dev/cheias-pt/tasks/cheias-extended-story.mdx \
   ~/Documents/dev/cheias-pt-veda-ui/stories/winter-2025-26-floods.stories.mdx
```

## Step 8: Verification

Run these checks:

```bash
# 1. No positive longitudes in center props (except the [-5, 38] Atlantic view)
grep "center=" ~/Documents/dev/cheias-pt-veda-ui/stories/winter-2025-26-floods.stories.mdx

# 2. No references to ./data/ (all should be ./media/floods/)
grep "'/data/" ~/Documents/dev/cheias-pt-veda-ui/stories/winter-2025-26-floods.stories.mdx
grep "./data/" ~/Documents/dev/cheias-pt-veda-ui/stories/winter-2025-26-floods.stories.mdx

# 3. No references to /images/ (all image paths should use new URL or ::file)
grep "'/images/" ~/Documents/dev/cheias-pt-veda-ui/stories/winter-2025-26-floods.stories.mdx

# 4. All media/floods/ assets referenced actually exist
ls -la ~/Documents/dev/cheias-pt-veda-ui/stories/media/floods/

# 5. No columnsToSort (should be columnToSort)
grep "columnsToSort" ~/Documents/dev/cheias-pt-veda-ui/stories/winter-2025-26-floods.stories.mdx
```

All 5 checks should return empty (no matches) except check 1 (should show
all negative longitudes) and check 4 (should list 7 files).

## Step 9: Commit

```bash
cd ~/Documents/dev/cheias-pt-veda-ui
git add stories/winter-2025-26-floods.stories.mdx
git commit -m "feat(T5): swap extended story — fix coords, paths, content types

- Fix 19 positive longitude values → negative (Portugal is west of Greenwich)
- Rewrite all dataPath refs: ./data/ → ./media/floods/ (VEDA convention)
- Pivot rainfall-anomaly from <Chart> to <Image> (recharts can't do bar charts)
- Add multi-river discharge comparison <Image> in climate chapter
- Fix <Table> prop: columnsToSort → columnToSort (VEDA-UI API)
- Replace missing image refs with placeholder prose
- Update frontmatter to VEDA-UI format (::file hero, pubDate)"
```

Do NOT push — Nelson will review and push.
