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
import type { Layer } from '@deck.gl/core';
import type { ChapterCamera, ChapterAnimation } from './types';

const BASEMAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

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

/**
 * Cubic ease-in-out for camera transitions.
 */
function cubicEaseInOut(t: number): number {
  return t < 0.5
    ? 4 * t * t * t
    : 1 - Math.pow(-2 * t + 2, 3) / 2;
}
