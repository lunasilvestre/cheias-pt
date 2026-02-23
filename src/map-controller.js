/**
 * cheias.pt — Map controller
 *
 * Initializes MapLibre GL with CARTO Dark Matter basemap.
 * Handles camera transitions between chapters.
 */

const BASEMAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

let map = null;
let navControl = null;

/**
 * Initialize the MapLibre map instance.
 * @param {string} containerId - DOM element ID for the map
 * @returns {maplibregl.Map}
 */
export function initMap(containerId) {
  // Register PMTiles protocol for vector tile sources
  const protocol = new pmtiles.Protocol();
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
  });

  map.addControl(
    new maplibregl.AttributionControl({ compact: true }),
    'bottom-right'
  );

  return map;
}

/**
 * Get the current map instance.
 * @returns {maplibregl.Map|null}
 */
export function getMap() {
  return map;
}

/**
 * Fly or ease the camera to a chapter's position.
 * @param {Object} camera - { center, zoom, pitch, bearing }
 * @param {Object} animation - { type: 'flyTo'|'easeTo', duration }
 */
export function flyToChapter(camera, animation) {
  if (!map) return;

  const options = {
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
export function enableInteraction() {
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
export function disableInteraction() {
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
 * Approximates cubic-bezier(0.445, 0.05, 0.55, 0.95)
 */
function cubicEaseInOut(t) {
  return t < 0.5
    ? 4 * t * t * t
    : 1 - Math.pow(-2 * t + 2, 3) / 2;
}
