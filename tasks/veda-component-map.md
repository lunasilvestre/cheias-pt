# VEDA-UI Component Map for cheias.pt Portuguese Flood Monitoring Platform

Complete reference for VEDA-UI's component library, covering syntax, configuration, nesting rules, and real-world examples from the eoviz-esip2025 and veda-config-template repositories.

---

## Table of Contents

1. [Block Components](#block-components)
2. [Content Components](#content-components)
3. [Map & Data Visualization](#map--data-visualization)
4. [Scrollytelling & Interactive Blocks](#scrollytelling--interactive-blocks)
5. [Dataset & Layer Configuration](#dataset--layer-configuration)
6. [Mobile & Responsive Behavior](#mobile--responsive-behavior)
7. [Limitations & Workarounds](#limitations--workarounds)

---

## Block Components

### Overview

Blocks are fundamental layout containers that define how content is arranged on a page. Only `Prose` and `Figure` can be direct children of Block. The order of children determines their position.

### Block Types

#### Default Prose Block

Centered single-column text layout.

```jsx
<Block>
  <Prose>
    ### Your markdown header

    Your markdown contents comes here.
  </Prose>
</Block>
```

**Properties:**
- No type attribute (default)
- Single column, centered
- Full width on desktop, responsive on mobile

#### Wide Prose Block

Wider single-column text (more padding reduction).

```jsx
<Block type='wide'>
  <Prose>
    ### Your markdown header

    Your markdown contents comes here.
  </Prose>
</Block>
```

**Properties:**
- `type: 'wide'`
- Increased width compared to default
- Responsive on smaller screens

#### Wide Figure Block

Figure with increased width.

```jsx
<Block type='wide'>
  <Figure>
    <Image ... />
    <Caption ...>caption</Caption>
  </Figure>
</Block>
```

**Properties:**
- `type: 'wide'`
- Full-width media container
- Caption displayed below

#### Full Figure Block

Full-width, full-height figure.

```jsx
<Block type='full'>
  <Figure>
    <Image ... />
    <Caption ...>caption</Caption>
  </Figure>
</Block>
```

**Properties:**
- `type: 'full'`
- Spans entire viewport width
- Useful for hero/banner images
- Maps take full viewport

#### Prose Figure Block

Text on left, figure on right (two-column).

```jsx
<Block>
  <Prose>
    My markdown contents
  </Prose>
  <Figure>
    <Image ... />
    <Caption> ... </Caption>
  </Figure>
</Block>
```

**Properties:**
- Prose comes first (displays on left on desktop)
- Figure comes second (displays on right)
- Single column on mobile

#### Figure Prose Block

Figure on left, text on right (reversed two-column).

```jsx
<Block>
  <Figure>
    <Image ... />
    <Caption> ... </Caption>
  </Figure>
  <Prose>
    My markdown contents
  </Prose>
</Block>
```

**Properties:**
- Figure comes first (displays on left)
- Prose comes second (displays on right)
- Single column on mobile

#### Prose Full Figure Block

Text on left, full-width figure on right.

```jsx
<Block type='full'>
  <Prose>
    My markdown contents
  </Prose>
  <Figure>
    <Image ... />
    <Caption> ... </Caption>
  </Figure>
</Block>
```

**Properties:**
- Prose in first position
- Figure spans full width
- Two-column layout on desktop

#### Full Figure Prose Block

Full-width figure on left, text on right.

```jsx
<Block type='full'>
  <Figure>
    <Image ... />
    <Caption> ... </Caption>
  </Figure>
  <Prose>
    My markdown contents
  </Prose>
</Block>
```

**Properties:**
- Figure comes first and is full-width
- Prose on right side
- Two-column layout on desktop

---

## Content Components

### Image

Displays images with optional alignment, captions, and attribution.

#### Inline Image (in Prose)

```jsx
<Image
  src="http://via.placeholder.com/256x128?text=align-left"
  alt="Media example"
  align="left"
  caption="example caption"
  attrAuthor="example author"
  attrUrl="https://example.com"
  width="256"
/>
```

**Properties:**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `src` | string | '' | Image URL or local file path |
| `alt` | string | '' | Alt text for accessibility |
| `align` | enum | 'center' | Alignment: `left`, `right`, `center` |
| `caption` | string | '' | Caption text (inline images only) |
| `attrAuthor` | string | '' | Image author name |
| `attrUrl` | string | '' | Link to author profile |
| `width` | string/number | | Image width (can use CSS units) |
| `height` | string/number | | Image height |

**Local File Usage:**

```jsx
<Image
  src={new URL('./img.jpg', import.meta.url).href}
  align="center"
  alt="local image"
  attrAuthor="penguin"
  attrUrl="https://linux.org"
  width="256"
/>
```

#### Figure Image (in Figure)

```jsx
<Block type="full">
  <Figure>
    <Image
      src="http://via.placeholder.com/1200x800?text=figure"
      alt='description for image'
    />
    <Caption
      attrAuthor='Development Seed'
      attrUrl='https://developmentseed.org'
    >
      This is an image. This is <a href="link">a link</a>.
    </Caption>
  </Figure>
</Block>
```

**Properties:**
- Same as inline, but used within `<Figure>`
- Caption component replaces `caption` prop (allows HTML)
- Attribution moved to `<Caption>` component

### Caption

Rich caption component for figures.

```jsx
<Caption
  attrAuthor='Attribution Name'
  attrUrl='https://example.com'
>
  This is a caption. It can contain <strong>HTML</strong> and <a href="#">links</a>.
</Caption>
```

**Properties:**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `attrAuthor` | string | '' | Author/source name |
| `attrUrl` | string | '' | Attribution link URL |
| `children` | HTML | | Caption content (supports HTML) |

### Chart

Line chart component for displaying time-series data.

```jsx
<Block type='wide'>
  <Figure>
    <Chart
      dataPath={new URL('./example.csv', import.meta.url).href}
      dateFormat="%m/%d/%Y"
      idKey='County'
      xKey='Test Date'
      yKey='New Positives'
      xAxisLabel='Date'
      yAxisLabel='Cases (%)'
      altTitle='COVID Cases by County'
      altDesc='Daily new positive COVID cases for US counties throughout 2021-2022'
      highlightStart='12/10/2021'
      highlightEnd='01/20/2022'
      highlightLabel='Omicron'
      colors={['#FF0000', '#00FF00']}
    />
    <Caption attrAuthor='Data Source' attrUrl='https://example.com' />
  </Figure>
</Block>
```

**Properties:**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `dataPath` | string | '' | Path to CSV or JSON data file |
| `xKey` | string | '' | Column name for X-axis |
| `yKey` | string | '' | Column name for Y-axis |
| `idKey` | string | '' | Column for grouping data (e.g., region names) |
| `dateFormat` | string | '' | d3 date format string (e.g., '%Y-%m-%d') |
| `xAxisLabel` | string | '' | X-axis label |
| `yAxisLabel` | string | '' | Y-axis label with units |
| `altTitle` | string | '' | Title for accessibility |
| `altDesc` | string | '' | Detailed description for accessibility |
| `colors` | array | undefined | HTML color names matching idKey order |
| `colorScheme` | string | 'viridis' | d3 chromatic scheme name (lowercase) |
| `highlightStart` | string | '' | Highlight region start date |
| `highlightEnd` | string | '' | Highlight region end date |
| `highlightLabel` | string | '' | Label for highlighted region |

**Data Format (CSV):**
```
County,Test Date,New Positives
New York,01/01/2021,150
New York,01/02/2021,155
California,01/01/2021,200
California,01/02/2021,210
```

**Data Format (JSON):**
```json
[
  {"County": "New York", "Test Date": "01/01/2021", "New Positives": 150},
  {"County": "New York", "Test Date": "01/02/2021", "New Positives": 155}
]
```

**Color Schemes (d3 chromatic):**
- Diverging: `purOr`, `rdBu`, `rdYlBu`, `rdYlGn`, `spectral`, `piYG`, `pRGn`, `brBG`
- Sequential: `blues`, `greens`, `greys`, `oranges`, `purples`, `reds`, `viridis`, `plasma`, `inferno`, `magma`, `cividis`

### Table

Displays data in an interactive sortable table.

```jsx
<Block type='wide'>
  <Figure>
    <Table
      dataPath='/path/to/data.csv'
      columnsToSort={['Name', 'Population']}
      excelOption={{ sheetNumber: 0, parseOption: { range: 3 } }}
    />
    <Caption>Wide block Table example</Caption>
  </Figure>
</Block>
```

**Properties:**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `dataPath` | string | '' | Path to CSV, JSON, or Excel file |
| `columnsToSort` | string[] | [] | Column names that enable sorting |
| `excelOption` | object | null | Excel-specific options (sheet number, parse) |
| `excelOption.sheetNumber` | number | 0 | Sheet index (0-based) |
| `excelOption.parseOption` | object | null | xlsx parse options (e.g., `{range: 3}` skips first 3 rows) |

**Supported Formats:**
- CSV
- JSON
- Excel (.xlsx, .xls, .xlsm)

**Features:**
- Fixed header (sticky on scroll)
- Virtual scrolling (renders 400px height)
- Click column header to sort ascending/descending
- Max height: 400px with scrollbar

### CompareImage

Side-by-side image comparison with slider.

```jsx
<Block type="full">
  <Figure>
    <CompareImage
      leftImageSrc='/images/dataset/east_coast_mar_avg.jpg'
      leftImageAlt='NO2 over Northeast U.S. with wider area with higher NO2 level'
      leftImageLabel='March 2015-2019 Avg.'
      rightImageSrc='/images/dataset/east_coast_mar_20.jpg'
      rightImageAlt='NO2 over Northeast U.S. with smaller area with lower NO2 level'
      rightImageLabel='March 2020'
    />
    <Caption
      attrAuthor='NASA Scientific Visualization Studio'
      attrUrl='https://svs.gsfc.nasa.gov/'
    >
      NO2 levels fell by as much as 30% over much of the Northeast U.S.
    </Caption>
  </Figure>
</Block>
```

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `leftImageSrc` | string | URL for left image |
| `leftImageAlt` | string | Alt text for left image |
| `leftImageLabel` | string | Label displayed on left side |
| `rightImageSrc` | string | URL for right image |
| `rightImageAlt` | string | Alt text for right image |
| `rightImageLabel` | string | Label displayed on right side |

**Features:**
- Interactive slider (click and drag or click to move)
- Labels overlay on each side
- Responsive to viewport size
- Fully accessible with keyboard controls

**Limitations:**
- Cannot compare different datasets (only static images)
- Cannot apply different colormaps dynamically
- Limited to 2-image comparison (no multiple images)

### Embed

Embeds external webpages, notebooks, or interactive content.

```jsx
<Block type="wide">
  <Figure>
    <Embed
      height="1200"
      src="https://jsignell.github.io/voici/voici/render/fires.html"
    />
  </Figure>
</Block>
```

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `src` | string | URL of page to embed |
| `height` | number | Height of iframe in pixels |

**Use Cases:**
- Jupyter notebooks (Voici, JupyterHub)
- Interactive dashboards
- External content portals
- Live data feeds (if embedded service supports iframe)

**Limitations:**
- Must be embeddable (no X-Frame-Options restrictions)
- Cross-origin restrictions may apply
- Some external services block iframe embedding

**IPMA & SNIRH Integration:**
If IPMA or SNIRH provide public dashboards with iframe support:
```jsx
<Block type="full">
  <Figure>
    <Embed
      height="800"
      src="https://www.ipma.pt/weather-dashboard"
    />
    <Caption attrAuthor="IPMA" attrUrl="https://www.ipma.pt/">
      Portuguese weather monitoring dashboard
    </Caption>
  </Figure>
</Block>
```

---

## Map & Data Visualization

### Map Component

Displays geospatial data from VEDA datasets.

```jsx
<Block type='full'>
  <Figure>
    <Map
      datasetId='sandbox'
      layerId='nightlights-hd-monthly'
      dateTime='2020-03-01'
      zoom={4}
      center={[117.22, 35.66]}
      compareDateTime='2021-03-01'
      compareLabel='2020 VS 2021'
      projectionId='mercator'
      projectionCenter={[0, 0]}
      projectionParallels={[45, 55]}
    />
    <Caption>
      The caption displays below the map.
    </Caption>
  </Figure>
</Block>
```

**Properties:**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `datasetId` | string | '' | Dataset ID (deprecated, kept for compatibility) |
| `layerId` | string | '' | Layer ID to display (required) |
| `dateTime` | string | '' | Date in YYYY-MM-DD format |
| `compareDateTime` | string | '' | Comparison date for slider (enables compare mode) |
| `compareLabel` | string | | Text overlay during comparison |
| `zoom` | number | | Zoom level (0-20) |
| `center` | [number, number] | | Map center [longitude, latitude] |
| `projectionId` | string | 'mercator' | Projection type |
| `projectionCenter` | [int, int] | | Center for Conic projections |
| `projectionParallels` | [int, int] | | Parallels for Conic projections |

**Available Projections:**
- `mercator` - Web Mercator (default)
- `albers` - Albers Equal-Area Conic
- `equalEarth` - Equal Earth
- `equirectangular` - Equirectangular
- `lambertConformalConic` - Lambert Conformal Conic
- `naturalEarth` - Natural Earth 1
- `winkelTripel` - Winkel Tripel
- `globe` - 3D Globe
- `polarNorth` - North Pole (Lambert Conformal variant)
- `polarSouth` - South Pole (Lambert Conformal variant)

**Real Example (NO2 Comparison):**
```jsx
<Map
  datasetId='no2'
  layerId='no2-monthly'
  center={[-84.39, 33.75]}
  zoom={9.5}
  dateTime='2019-04-01'
  compareDateTime='2020-04-01'
  compareLabel='April 2019 VS April 2020'
/>
```

**Interactive Features:**
- Time slider (if temporal data)
- Comparison slider (if compareDateTime set)
- Layer legend
- Zoom/pan controls
- Basemap toggle (dark, light, satellite, topo)
- Statistics panel on click

### MultiLayer Map

Display multiple layers simultaneously with layer controls.

```jsx
<Block type='full'>
  <Figure>
    <Map
      layerId='layer-1'
      dateTime='2020-03-01'
    />
    <Map
      layerId='layer-2'
      dateTime='2020-03-01'
    />
  </Figure>
</Block>
```

**Note:** Multiple maps in Figure require separate Map components stacked.

---

## Scrollytelling & Interactive Blocks

### ScrollytellingBlock

Map-based narrative where map animates as user scrolls through chapters.

```jsx
<ScrollytellingBlock>
  <Chapter
    center={[0, 0]}
    zoom={2}
    datasetId='no2'
    layerId='no2-monthly-diff'
    datetime='2021-03-01'
  >
    ## Content of chapter 1

    Markdown is supported. This text appears as the user scrolls to this section. The map animates to center [0,0] at zoom 2.
  </Chapter>

  <Chapter
    center={[-83.0059, 34.3382]}
    zoom={4.5}
    datasetId='no2'
    layerId='no2-monthly-diff'
    datetime='2020-03-01'
  >
    With people largely confined to their homes... [text appears here while map transitions to new center/zoom]
  </Chapter>

  <Chapter
    center={[-74.0236, 40.7234]}
    zoom={12}
    showBaseMap={true}
  >
    ## What Makes Air Quality Good or Bad?

    Cities are easy to spot from space. [Map shows basemap without layer]
  </Chapter>
</ScrollytellingBlock>
```

**Chapter Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `center` | [number, number] | Map center [longitude, latitude] |
| `zoom` | number | Zoom level (0-20) |
| `datasetId` | string | Dataset ID for the layer |
| `layerId` | string | Layer to display |
| `datetime` | string | Date in YYYY-MM-DD format |
| `showBaseMap` | boolean | Show basemap without layer (optional) |
| `projectionName` | string | Projection ID (default: 'mercator') |
| `projectionCenter` | [int, int] | Center for Conic projections |
| `projectionParallels` | [int, int] | Parallels for Conic projections |

**Features:**
- Smooth map transitions between chapters
- Automatic scroll-to-map interaction
- Full-width responsive design
- Chapter content overlays map
- Markdown support in chapter text

**Layer Transitions:**
- Layer changes are **instant** (no fade transition)
- Center and zoom animate smoothly
- Different projections persist across chapters once set

**Real Example (COVID-19 Air Quality):**
```jsx
<ScrollytellingBlock>
  <Chapter center={[0, 0]} zoom={2} datasetId='no2' layerId='no2-monthly-diff' datetime='2021-03-01'>
    ## Going through changes
    When governments began implementing shutdowns at the start of the COVID-19 pandemic...
  </Chapter>
  <Chapter center={[-83.0059, 34.3382]} zoom={4.5} datasetId='no2' layerId='no2-monthly-diff' datetime='2020-03-01'>
    With people largely confined to their homes to slow the spread of the novel coronavirus...
  </Chapter>
</ScrollytellingBlock>
```

**Mobile Behavior:**
- Full-width on all devices
- Text overlays map (readable on all sizes)
- Map remains above the fold
- Chapter text scrolls through viewport
- Touch-friendly interaction

---

## Dataset & Layer Configuration

### Dataset Configuration

Datasets are defined in MDX files with frontmatter YAML.

```yaml
---
id: no2
name: 'Nitrogen Dioxide'
description: "Since the outbreak of the novel coronavirus, atmospheric concentrations of nitrogen dioxide have changed by as much as 60% in some regions."
media:
  src: /images/dataset/no2--dataset-cover.jpg
  alt: Power plant shooting steam at the sky.
  author:
    name: Mick Truyts
    url: https://unsplash.com/photos/x6WQeNYJC1w
taxonomy:
  - name: Topics
    values:
      - Covid 19
      - Air Quality
featured: true
disableExplore: false
layers:
  - id: no2-monthly
    stacCol: no2-monthly
    name: No2 Monthly
    description: Levels in 10¹⁵ molecules cm⁻²
    type: raster
    projection:
      id: mercator
    bounds: [-180, -90, 180, 90]
    zoomExtent: [0, 20]
    basemapId: 'dark'
    legend:
      unit:
        label: Molecules cm³
      type: gradient
      min: "Less"
      max: "More"
      stops:
        - "#99c5e0"
        - "#f9eaa9"
        - "#f7765d"
        - "#c13b72"
        - "#461070"
        - "#050308"
    compare:
      datasetId: no2
      layerId: no2-monthly-diff
      mapLabel: |
        ::js ({ dateFns, datetime, compareDatetime }) => {
          return `${dateFns.format(datetime, 'LLL yyyy')} VS ${dateFns.format(compareDatetime, 'LLL yyyy')}`;
        }
    analysis:
      metrics:
        - min
        - max
        - mean
    info:
      source: NASA
      spatialExtent: Global
      temporalResolution: Monthly
      unit: 10¹⁵ molecules cm⁻²
usage:
  - url: 'https://nasa-impact.github.io/veda-documentation/'
    label: Static notebook
    title: 'Time series using STAC API'
infoDescription: |
  ::markdown
    - Temporal Extent: January 2000 - December 2021
    - Temporal Resolution: Monthly
    - Spatial Extent: Global
    - Spatial Resolution: 1 km x 1 km
---

<Block type='full'>
  <Figure>
    <Map
      datasetId='no2'
      layerId='no2-monthly'
      dateTime='2020-03-01'
    />
  </Figure>
</Block>
```

**Dataset Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique dataset identifier |
| `name` | string | Display name |
| `description` | string | Short description (shown on cards) |
| `media` | Media | Cover image (2000x1000px, <500KB) |
| `taxonomy` | Taxonomy[] | Classification tags |
| `featured` | boolean | Featured on homepage |
| `disableExplore` | boolean | Hide explore data section |
| `layers` | Layer[] | Array of layer configurations |
| `usage` | Usage[] | Links to example notebooks |
| `infoDescription` | string | Markdown metadata block |

### Layer Configuration

Detailed layer setup for map display and data access.

```yaml
layers:
  - id: no2-monthly
    stacCol: no2-monthly
    stacApiEndpoint: 'https://stac.openveda.cloud/api/v1'
    tileApiEndpoint: 'https://titiler.openveda.cloud'
    name: 'Nitrogen Dioxide Monthly'
    type: raster
    initialDatetime: 'newest'
    description: 'NO2 column density in molecules/cm²'

    # Projection setup
    projection:
      id: 'mercator'
      center: [0, 0]
      parallels: [45, 55]

    # Map bounds
    bounds: [-180, -90, 180, 90]
    basemapId: 'dark'
    zoomExtent: [0, 20]

    # Tile rendering parameters
    sourceParams:
      rescale: [0, 1000]
      colormap_name: 'viridis'
      resampling: 'bilinear'
      bidx: 1
      minzoom: 0
      maxzoom: 20

    # Legend configuration
    legend:
      type: gradient
      unit:
        label: Molecules cm⁻³
      min: "Low"
      max: "High"
      stops:
        - '#99c5e0'
        - '#f9eaa9'
        - '#f7765d'
        - '#c13b72'
        - '#461070'
        - '#050308'

    # Comparison layer
    compare:
      datasetId: no2
      layerId: no2-monthly-diff
      mapLabel: |
        ::js ({ dateFns, datetime, compareDatetime }) => {
          return `${dateFns.format(datetime, 'LLL yyyy')} VS ${dateFns.format(compareDatetime, 'LLL yyyy')}`;
        }

    # Analysis configuration
    analysis:
      metrics: [min, max, mean, std]
      exclude: false
      sourceParams:
        resampling: 'bilinear'

    # Layer metadata
    info:
      source: NASA
      spatialExtent: Global
      temporalResolution: Monthly
      unit: 10¹⁵ molecules cm⁻²
```

**Layer Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique layer identifier (lowercase, dashes) |
| `stacCol` | string | STAC collection name |
| `stacApiEndpoint` | string | STAC API URL (defaults to env var) |
| `tileApiEndpoint` | string | Tile API URL (defaults to env var) |
| `name` | string | Display name |
| `type` | string | `raster`, `vector`, `wms`, `wmts` |
| `initialDatetime` | string | 'oldest', 'newest', or YYYY-MM-DD |
| `description` | string | Layer description |
| `projection` | Projection | Map projection settings |
| `bounds` | [number, number, number, number] | [minLon, minLat, maxLon, maxLat] |
| `basemapId` | string | 'dark', 'light', 'satellite', 'topo' |
| `zoomExtent` | [number, number] | [minZoom, maxZoom] |
| `sourceParams` | object | Tile rendering parameters |
| `legend` | Legend | Visual legend configuration |
| `compare` | Compare | Comparison layer setup |
| `analysis` | Analysis | Statistical analysis settings |
| `info` | Info | Metadata key-value pairs |

**sourceParams Common Values:**
- `rescale: [min, max]` - Data value range for color mapping
- `colormap_name: 'viridis'` - Color map from rio-tiler
- `resampling: 'bilinear'` - Resampling method
- `bidx: 1` - Band index for multi-band rasters
- `minzoom`, `maxzoom` - Tile zoom level constraints

**Available Colormaps:**
From rio-tiler defaults: viridis, plasma, inferno, magma, cividis, twilight, turbo, Blues, Greens, Greys, Oranges, Purples, Reds, summer, autumn, winter, spring, cool, warm, hsv, Spectral, coolwarm, RdYlBu, RdYlGn, RdBu, PuOr, BrBG, PRGn, PiYG, Set1, Set2, Set3, Pastel1, Pastel2, Paired, Accent

**Function Values in Layer Config:**

Certain properties support JavaScript functions for dynamic values:

```yaml
sourceParams:
  rescale: ::js (bag) => {
    return [0, bag.datetime.getFullYear() === 2020 ? 100 : 500];
  }

compare:
  mapLabel: ::js ({ dateFns, datetime, compareDatetime }) => {
    return `${dateFns.format(datetime, 'MMM yyyy')} vs ${dateFns.format(compareDatetime, 'MMM yyyy')}`;
  }
```

**Bag Parameter Properties:**
```js
{
  datetime: Date,           // Currently selected date
  compareDatetime: Date,    // Comparison date (null if not set)
  dateFns: Object,          // date-fns library
  raw: Object               // Raw layer configuration
}
```

### Categorical Legend

```yaml
legend:
  type: categorical
  stops:
    - color: '#FF0000'
      label: Corn
    - color: '#00FF00'
      label: Wheat
    - color: '#0000FF'
      label: Barley
```

### Media Configuration

```yaml
media:
  src: /images/dataset/no2--dataset-cover.jpg
  # OR for local files:
  # src: ::file ./img-placeholder-4.jpg
  alt: "Description of image"
  author:
    name: Attribution Name
    url: https://unsplash.com/
```

**Image Requirements:**
- Ratio: 2:1
- Minimum size: 2000x1000px
- Maximum size: 500KB
- Supported formats: JPG, PNG

---

## Mobile & Responsive Behavior

### Breakpoints

VEDA uses responsive design with these approximate breakpoints:

- **Small (mobile):** < 768px
- **Medium (tablet):** 768px - 991px
- **Large (desktop):** > 991px

### Block Layouts on Mobile

| Block Type | Desktop | Mobile |
|-----------|---------|--------|
| Default Prose | Single column, centered | Full width |
| Wide Prose | Wider column | Full width |
| Wide Figure | Wide figure | Full width |
| Full Figure | Full-width figure | Full-width figure |
| Prose Figure | 2 columns (text, figure) | Single column (text on top) |
| Figure Prose | 2 columns (figure, text) | Single column (figure on top) |
| Prose Full Figure | 2 columns | Single column |
| Full Figure Prose | 2 columns | Single column |

### ScrollytellingBlock Mobile Behavior

- **Full width** on all screen sizes
- **Sticky map** stays visible as content scrolls
- **Overlay text** adapts font size for mobile readability
- **Touch-friendly** chapter interaction
- **No horizontal scroll** (maintains viewport)

### Chart Mobile Behavior

- **Responsive width:** Uses full container width
- **Dynamic height:** Adjusts aspect ratio based on `useMediaQuery` hook
- **Brush disabled:** Brush/timeline control hidden on very small screens (< 400px width)
- **Legend repositioning:** May move below chart on narrow screens
- **Axis labels:** Font size reduces on mobile (0.8rem baseline)

### Map Mobile Behavior

- **Full-width container** with responsive height
- **Zoom controls:** Touch-friendly on mobile
- **Click for info:** Replaces hover tooltips
- **Comparison slider:** Full-width on mobile
- **Legend:** Scrollable if multiple layers

### Table Mobile Behavior

- **Horizontal scrolling:** Tables scroll horizontally on small screens
- **Fixed width:** 400px height with scrollbar
- **Column visibility:** All columns visible (horizontal scroll required)
- **Sticky header:** Always visible while scrolling

---

## Limitations & Workarounds

### CompareImage Limitations

**Limitation:** Cannot compare different datasets or apply different colormaps.

**Current Capability:** Static image comparison only (two PNG/JPG images).

**Workaround for Dataset Comparison:** Use Map with compareDateTime:

```jsx
<Map
  datasetId='no2'
  layerId='no2-monthly'
  dateTime='2019-04-01'
  compareDateTime='2020-04-01'
  compareLabel='April 2019 vs April 2020'
/>
```

**Workaround for Colormap Comparison:** Generate two separate Map components without comparison:

```jsx
<Block>
  <Figure>
    <Map
      datasetId='so2'
      layerId='OMSO2PCA-COG'
      dateTime='2006-01-01'
      zoom={4}
      center={[117.22, 35.66]}
    />
    <Caption>2006 - Red-Yellow-Blue colormap</Caption>
  </Figure>
</Block>

<Block>
  <Figure>
    <Map
      datasetId='so2'
      layerId='OMSO2PCA-COG-alt'
      dateTime='2006-01-01'
      zoom={4}
      center={[117.22, 35.66]}
    />
    <Caption>2006 - Viridis colormap</Caption>
  </Figure>
</Block>
```

### Chart Data Format Limitations

**Limitation:** Charts require specific CSV/JSON structure.

**Requirement:** Data must have consistent column names matching `idKey`, `xKey`, `yKey`.

**Issue:** Missing dates cause gaps in line continuity.

**Workaround:** Pre-process data to ensure continuous date ranges:

```csv
County,Test Date,New Positives
Alabama,01/01/2021,100
Alabama,01/02/2021,105
Alabama,01/03/2021,108
California,01/01/2021,500
California,01/02/2021,510
California,01/03/2021,520
```

### Embed CORS Restrictions

**Limitation:** Cannot embed external content with X-Frame-Options restrictions.

**Error:** "Refused to display in a frame" or blank iframe.

**Workaround Options:**

1. **Use direct links instead:**
```jsx
<Prose>
  View the weather data at <Link to="https://www.ipma.pt">IPMA's website</Link>
</Prose>
```

2. **Host your own wrapper page:**
```jsx
<Embed
  height="800"
  src="https://your-domain.com/ipma-wrapper.html"
/>
```

3. **Check service documentation** for official embed options

### Layer Type Limitations

**Vector Layers:** Style customization not available - uses default vector styling.

**WMS/WMTS Layers:** Limited control over rendering parameters.

**Workaround:** Use raster COG format (Cloud Optimized GeoTIFF) for maximum control:

```yaml
type: raster
sourceParams:
  rescale: [0, 1000]
  colormap_name: 'viridis'
  resampling: 'bilinear'
```

### Table Performance

**Limitation:** Tables with > 10,000 rows may slow down sorting.

**Workaround:** Pre-sort data and use `columnsToSort` for only necessary columns:

```jsx
<Table
  dataPath='/path/to/data.csv'
  columnsToSort={['Date', 'Status']}
/>
```

### Analysis Metrics Exclusion

**Limitation:** Some layers have `analysis.exclude: true` and cannot be analyzed.

**Workaround:** Create comparison layer that allows analysis:

```yaml
analysis:
  exclude: false
  metrics: [min, max, mean]
```

---

## Real-World Examples from eoviz-esip2025

### Example 1: Air Quality & COVID-19 Story

**File:** `/tmp/eoviz-esip2025/app/content/stories/air-quality-and-covid-19.mdx`

**Components Used:**
- ScrollytellingBlock with 15 chapters
- Map with temporal comparison
- Chapter transitions showing NO2 changes
- showBaseMap for basemap-only chapters

### Example 2: NO2 & SO2 Comparison Story

**File:** `/tmp/eoviz-esip2025/app/content/stories/no2-and-so2.mdx`

**Components Used:**
- Chart component (3 instances, one per region)
- Map with compareDateTime
- Prose blocks with descriptions
- Image components with captions

### Example 3: Agriculture Dataset

**File:** `/tmp/eoviz-esip2025/app/content/stories/sat-data-agriculture.mdx`

**Components Used:**
- Multiple Image components (inline)
- Image with Caption in Figure blocks
- Prose-heavy narrative
- Local image references

---

## Quick Reference: Component Nesting Rules

```
<Block>
  ├── <Prose>
  │   ├── Markdown text
  │   ├── <Image> (inline)
  │   ├── <Link>
  │   └── <NotebookConnectCallout>
  │
  └── <Figure>
      ├── <Map>
      ├── <Chart>
      ├── <Table>
      ├── <Image>
      ├── <CompareImage>
      ├── <Embed>
      └── <Caption>
```

---

## Configuration File Precedence for TiTiler

When rendering tiles, VEDA applies sourceParams in this order:

1. Layer `sourceParams` in dataset config (highest priority)
2. Dashboard render config from STAC endpoint
3. Asset-specific renders in STAC metadata
4. Default: `{colormap_name: 'viridis'}`

Example resolution:

```yaml
# This takes priority
sourceParams:
  rescale: [0, 500]
  colormap_name: 'turbo'

# Over STAC metadata values
# Over TiTiler defaults
```

---

## Key Takeaways for cheias.pt

1. **Scrollytelling** is ideal for flood event narratives (before/after chapters)
2. **Map with compareDateTime** enables temporal analysis of water level changes
3. **Charts** work well for rainfall/discharge time series data
4. **Embed** can link to IPMA/SNIRH dashboards if they support iframes
5. **CompareImage** useful for satellite before/after flood imagery
6. **Tables** perfect for daily flood alerts and river discharge data
7. **All layouts** are fully responsive and mobile-friendly
8. Layer projections can be customized per dataset (e.g., Azimuthal Equidistant for Portugal)
9. Dynamic legends using functions can show temporal metadata
10. Categorical legends work well for flood risk levels (low/medium/high/extreme)

