/**
 * cheias.pt — Map setup
 *
 * Initializes MapLibre GL v5 with CARTO Dark Matter basemap.
 * Handles camera transitions between chapters.
 */

import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Protocol } from 'pmtiles';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { gsap } from 'gsap';
import type { Layer } from '@deck.gl/core';
import type { ChapterCamera, ChapterAnimation } from './types';
import basemapConfig from '../data/basemap/cheias-dark.json';

const BASEMAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

// MapTiler terrain tiles (free tier: 100k tiles/month)
const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY || '';
const TERRAIN_SOURCE_URL = MAPTILER_KEY
  ? `https://api.maptiler.com/tiles/terrain-rgb-v2/{z}/{x}/{y}.webp?key=${MAPTILER_KEY}`
  : 'https://demotiles.maplibre.org/terrain-tiles/{z}/{x}/{y}.png';

let map: maplibregl.Map | null = null;
let deckOverlay: MapboxOverlay | null = null;
let navControl: maplibregl.NavigationControl | null = null;

/**
 * Initialize the MapLibre map instance.
 */
export function initMap(containerId: string): maplibregl.Map {
  // Register PMTiles protocol for vector tile sources
  const protocol = new Protocol();
  maplibregl.addProtocol('pmtiles', protocol.tile);

  map = new maplibregl.Map({
    container: containerId,
    style: BASEMAP_STYLE,
    center: [-15, 35],
    zoom: 3,
    pitch: 0,
    bearing: 0,
    interactive: false,
    attributionControl: false,
    fadeDuration: 0,
  } as maplibregl.MapOptions);

  map.addControl(
    new maplibregl.AttributionControl({ compact: true }),
    'bottom-right'
  );

  // deck.gl overlay — layers added in later phases
  deckOverlay = new MapboxOverlay({ layers: [] });
  map.addControl(deckOverlay as unknown as maplibregl.IControl);

  console.log(`[cheias.pt] MapLibre GL v${map.version}`);
  console.log('[cheias.pt] deck.gl MapboxOverlay attached');

  return map;
}

/**
 * Get the current map instance.
 */
export function getMap(): maplibregl.Map | null {
  return map;
}

/**
 * Get the deck.gl overlay instance.
 */
export function getDeckOverlay(): MapboxOverlay | null {
  return deckOverlay;
}

/**
 * Set deck.gl layers on the overlay directly.
 * Used by weather-layers and temporal player modules.
 */
export function setDeckOverlayLayers(layers: Layer[]): void {
  if (!deckOverlay) return;
  deckOverlay.setProps({ layers });
}

/**
 * Fly or ease the camera to a chapter's position.
 */
export function flyToChapter(camera: ChapterCamera, animation: ChapterAnimation): void {
  if (!map) return;

  const options: maplibregl.FlyToOptions = {
    center: camera.center,
    zoom: camera.zoom,
    pitch: camera.pitch || 0,
    bearing: camera.bearing || 0,
    duration: animation.duration || 1500,
    essential: true,
  };

  if (animation.type === 'easeTo') {
    map.easeTo(options);
  } else {
    map.flyTo({
      ...options,
      curve: 1.2,
      easing: cubicEaseInOut,
    });
  }
}

/**
 * Enable map interactions (for exploration chapter).
 */
export function enableInteraction(): void {
  if (!map) return;
  map.scrollZoom.enable();
  map.dragPan.enable();
  map.dragRotate.enable();
  map.touchZoomRotate.enable();
  map.doubleClickZoom.enable();
  map.keyboard.enable();

  if (!navControl) {
    navControl = new maplibregl.NavigationControl();
    map.addControl(navControl, 'top-right');
  }
}

/**
 * Disable map interactions (for story mode).
 */
export function disableInteraction(): void {
  if (!map) return;
  map.scrollZoom.disable();
  map.dragPan.disable();
  map.dragRotate.disable();
  map.touchZoomRotate.disable();
  map.doubleClickZoom.disable();
  map.keyboard.disable();

  if (navControl) {
    map.removeControl(navControl);
    navControl = null;
  }
}

// ── Projection switching (globe ↔ mercator) ──

let currentProjection: 'globe' | 'mercator' = 'mercator';

/**
 * Switch between globe and mercator projections.
 * MapLibre v5 handles the animated transition natively.
 */
export function setProjection(proj: 'globe' | 'mercator'): void {
  if (!map || proj === currentProjection) return;
  currentProjection = proj;
  map.setProjection({ type: proj });
  console.log(`[cheias.pt] Projection → ${proj}`);
}

export function getProjection(): 'globe' | 'mercator' {
  return currentProjection;
}

// ── Terrain ──

let terrainEnabled = false;

/**
 * Enable 3D terrain with configurable vertical exaggeration.
 */
export function enableTerrain(exaggeration = 1.5): void {
  if (!map || terrainEnabled) return;

  if (!map.getSource('terrain-rgb')) {
    map.addSource('terrain-rgb', {
      type: 'raster-dem',
      tiles: [TERRAIN_SOURCE_URL],
      tileSize: 256,
      maxzoom: 14,
    });
  }

  map.setTerrain({ source: 'terrain-rgb', exaggeration });
  terrainEnabled = true;
  console.log(`[cheias.pt] Terrain enabled (${exaggeration}×)`);
}

/**
 * Disable 3D terrain.
 */
export function disableTerrain(): void {
  if (!map || !terrainEnabled) return;
  map.setTerrain(null);
  terrainEnabled = false;
}

// ── Basemap mood switching ──

type ChapterGroup = {
  name: string;
  ocean: string;
  land: string;
  labels: boolean | string;
  terrain: boolean | string;
  basemap_opacity: number;
};

/** Map from mood key (e.g. 'ultra-dark') to chapter group key (e.g. 'ch0-ch1') */
const MOOD_MAP: Record<string, string> = {
  'ultra-dark': 'ch0-ch1',
  'dark-ocean': 'ch2',
  'muted-terrain': 'ch3',
  'dark-synoptic': 'ch4',
  'terrain-hydro': 'ch5',
  'aerial-hybrid': 'ch6',
};

let currentMood: string | null = null;

/**
 * Switch basemap mood. Applies background color, label visibility,
 * and opacity from cheias-dark.json.
 */
export function switchBasemapMood(mood: string): void {
  if (!map || mood === currentMood) return;

  const groupKey = MOOD_MAP[mood];
  if (!groupKey) {
    console.warn(`[cheias.pt] Unknown basemap mood: ${mood}`);
    return;
  }

  const group = (basemapConfig.chapter_groups as Record<string, ChapterGroup>)[groupKey];
  if (!group) return;

  currentMood = mood;

  // Animate background color transition
  const canvas = map.getCanvas();
  gsap.to(canvas, {
    backgroundColor: group.ocean,
    duration: 0.3,
    ease: 'power2.inOut',
  });

  // Toggle label visibility on basemap style layers
  const style = map.getStyle();
  if (style?.layers) {
    for (const layer of style.layers) {
      if (layer.type === 'symbol' && layer.id.includes('label')) {
        const visible = group.labels !== false;
        map.setLayoutProperty(layer.id, 'visibility', visible ? 'visible' : 'none');
      }
    }
  }

  // Adjust basemap raster opacity for CARTO layers
  if (style?.layers) {
    for (const layer of style.layers) {
      if (layer.type === 'background') {
        map.setPaintProperty(layer.id, 'background-color', group.ocean);
      }
    }
  }

  console.log(`[cheias.pt] Basemap mood → ${mood} (${group.name})`);
}

/**
 * Cubic ease-in-out for camera transitions.
 */
function cubicEaseInOut(t: number): number {
  return t < 0.5
    ? 4 * t * t * t
    : 1 - Math.pow(-2 * t + 2, 3) / 2;
}
