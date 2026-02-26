# Video Motion Analysis — WeatherWatcher14 Storm Kristin

## Goal

Download the WeatherWatcher14 YouTube video about Storm Kristin / Portugal floods and extract frames that capture the **motion and animation techniques** used. The purpose is to create a visual reference catalog that a separate agent can use to replicate these effects in MapLibre GL JS + deck.gl.

Static screenshots already exist but they DON'T capture the motion — that's the whole point of this task.

## Video

**URL:** https://youtu.be/MypYdH8vPHQ
**Channel:** @WeatherWatcher14
**Content:** European storm analysis covering Storm Kristin hitting Portugal (Jan 28, 2026)

## Step 1: Download the video

```bash
cd ~/Documents/dev/cheias-pt/data
mkdir -p video-analysis/frames
yt-dlp -f "bestvideo[height<=720]+bestaudio/best[height<=720]" \
  -o "video-analysis/source.mp4" \
  "https://youtu.be/MypYdH8vPHQ"
```

If yt-dlp is not installed: `pip install yt-dlp`

## Step 2: Get video duration and create overview strip

```bash
# Get duration
ffprobe -v error -show_entries format=duration -of csv=p=0 data/video-analysis/source.mp4

# Extract 1 frame every 10 seconds for quick overview
ffmpeg -i data/video-analysis/source.mp4 \
  -vf "fps=1/10,scale=640:-1" \
  data/video-analysis/frames/overview_%04d.png
```

## Step 3: Identify animation segments

Review the overview frames and identify timestamps where these specific effects appear:

### Target Effects (from discovery/16-weather-video-data-sources.md)

1. **Wind particle streamlines** — Windy.com animated particles showing cyclonic flow
   - Look for: flowing white/colored particles on dark background, vortex patterns
   - Screenshots 07 (220659) show this static — we need the MOTION

2. **Precipitation temporal sweep** — rain bands moving across map over time
   - Look for: color ramp (white→blue→pink) shifting position frame to frame
   - Screenshots 01 (220341), 09 (220857) show this static

3. **MSLP isobar animation** — pressure systems moving, isobars shifting
   - Look for: contour lines moving, L/H markers translating
   - Screenshot 04 (220620) shows this static

4. **Satellite cloud motion** — cloud masses flowing, storm structure evolving
   - Look for: IR/VIS satellite imagery with temporal progression
   - Screenshots 05-06 (220641, 220644) show this static

5. **Timeline scrubber interaction** — how the presenter uses Windy's time slider
   - Look for: bottom bar with time markers, data changing as time advances

6. **Layer transitions** — how the presenter switches between data overlays
   - Look for: fade/dissolve between different map layers

## Step 4: Extract dense frames from animation segments

For each identified animation segment, extract at HIGH frame rate (2-4 fps) to capture the motion:

```bash
# Template — adjust -ss (start) and -t (duration) per segment
ffmpeg -i data/video-analysis/source.mp4 \
  -ss MM:SS -t 10 \
  -vf "fps=3,scale=640:-1" \
  data/video-analysis/frames/wind-particles_%04d.png

ffmpeg -i data/video-analysis/source.mp4 \
  -ss MM:SS -t 10 \
  -vf "fps=3,scale=640:-1" \
  data/video-analysis/frames/precip-sweep_%04d.png

ffmpeg -i data/video-analysis/source.mp4 \
  -ss MM:SS -t 10 \
  -vf "fps=3,scale=640:-1" \
  data/video-analysis/frames/mslp-animation_%04d.png

ffmpeg -i data/video-analysis/source.mp4 \
  -ss MM:SS -t 10 \
  -vf "fps=3,scale=640:-1" \
  data/video-analysis/frames/satellite-motion_%04d.png
```

## Step 5: Write the motion analysis

Create `data/video-analysis/MOTION-ANALYSIS.md` with:

For EACH animation effect identified:

### Effect: [Name]
- **Timestamp:** MM:SS–MM:SS
- **Platform:** (Windy.com / WXCharts / EUMETSAT / etc.)
- **Frames:** [list of extracted frame filenames]
- **Motion description:**
  - What moves? (particles, color fields, contour lines, markers)
  - Speed/tempo (fast sweep vs slow evolution)
  - Direction (west→east, circular, pulsing)
  - Easing (linear, accelerating, smooth)
- **Visual properties:**
  - Color ramp used
  - Opacity/blending of animated layer vs basemap
  - Trail/fade effect (do particles leave trails?)
  - Density of animated elements
- **Replication approach for deck.gl/MapLibre:**
  - Suggested layer type (deck.gl TripsLayer, ParticleLayer, MapLibre image source animation, etc.)
  - Data format needed (GeoJSON lines, raster frames, vector field grid)
  - Key parameters to tune
  - Available data in cheias-pt that maps to this effect:
    - Wind U/V COGs: `data/cog/wind-u/*.tif` and `data/cog/wind-v/*.tif` (409 files each, 6-hourly)
    - IVT COGs: `data/cog/ivt/*.tif` (78 daily)
    - MSLP contours: `data/qgis/mslp-contours-v2.geojson` (28 isobars)
    - MSLP L/H markers: `data/qgis/mslp-lh-markers.geojson` (7 centers)
    - Precipitation PNGs: `data/raster-frames/precipitation/*.png` (77 daily)
    - Soil moisture PNGs: `data/raster-frames/soil-moisture/*.png` (77 daily)
    - Satellite IR COGs: `data/cog/satellite-ir/*.tif` (49 hourly)
    - Wind barbs GeoJSON: `data/qgis/wind-barbs-kristin.geojson` (6,419 points)
    - Lightning GeoJSON: `data/qgis/lightning-kristin.geojson` (262 points)

## Step 6: Create a contact sheet

For the most important animation sequences, create a horizontal contact sheet showing 6-8 frames side by side to visualize the motion in a single image:

```bash
# Example: wind particle sequence contact sheet
montage data/video-analysis/frames/wind-particles_*.png \
  -tile 8x1 -geometry 320x180+2+2 \
  data/video-analysis/contact-wind-particles.png
```

Create one contact sheet per effect type.

## Output Files

When complete, the following should exist:
- `data/video-analysis/source.mp4` — downloaded video
- `data/video-analysis/frames/overview_*.png` — every 10s overview
- `data/video-analysis/frames/[effect]_*.png` — dense frame extracts per effect
- `data/video-analysis/contact-*.png` — contact sheets per effect
- `data/video-analysis/MOTION-ANALYSIS.md` — the analysis document

## Important Notes

- Do NOT read CLAUDE.md — it describes the story map, not this task
- This is a RESEARCH/ANALYSIS task, not a coding task
- Focus on MOTION — what changes between frames, not what's in a single frame
- The existing screenshots in `discovery/16-weather-video-data-sources.md` cover the static content
- We specifically need to understand: particle speed, sweep direction, temporal cadence, layer blending, easing curves
- If montage (ImageMagick) is not installed: `sudo apt install imagemagick`
