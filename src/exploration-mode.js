/**
 * cheias.pt — Exploration mode
 *
 * Enables free map navigation after the story ends (chapter 9).
 * Handles geolocation, layer toggles, and URL state.
 */

import { enableInteraction, disableInteraction, getMap } from './map-controller.js';
import { setLayerOpacity } from './layer-manager.js';

let explorationActive = false;
let togglesWired = false;

/**
 * Maps toggle data-layer attributes to actual MapLibre layer IDs and their
 * default explore-mode opacity.
 */
const TOGGLE_LAYER_MAP = {
  'flood-extent': { layers: ['flood-extent-polygons'], opacity: 0.7 },
  'soil-moisture': { layers: ['soil-moisture-tiles'], opacity: 0.6 },
  'precipitation': { layers: ['precipitation-tiles'], opacity: 0.6 },
  'discharge': { layers: ['glofas-discharge'], opacity: 0.9 },
  'precondition': { layers: ['basins-fill'], opacity: 0.7 },
  'basins': { layers: ['basins-outline'], opacity: 0.4 },
};

/**
 * Enter exploration mode — enable map interactions and show controls.
 */
export function enterExplorationMode() {
  if (explorationActive) return;
  explorationActive = true;

  enableInteraction();
  wireToggles();

  const controls = document.getElementById('exploration-controls');
  if (controls) {
    controls.classList.add('visible');
  }

  // Apply initial toggle states
  applyAllToggles();

  console.log('[exploration] Mode enabled');
}

/**
 * Exit exploration mode — disable map interactions.
 */
export function exitExplorationMode() {
  if (!explorationActive) return;
  explorationActive = false;

  disableInteraction();

  const controls = document.getElementById('exploration-controls');
  if (controls) {
    controls.classList.remove('visible');
  }

  console.log('[exploration] Mode disabled');
}

/**
 * Geolocate the user and fly to their position.
 */
export function geolocateUser() {
  const map = getMap();
  if (!map || !navigator.geolocation) return;

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      map.flyTo({
        center: [pos.coords.longitude, pos.coords.latitude],
        zoom: 10,
        duration: 2000,
        essential: true,
      });
    },
    (err) => {
      console.warn('[exploration] Geolocation failed:', err.message);
    },
    { enableHighAccuracy: false, timeout: 5000 }
  );
}

/**
 * Check if exploration mode is active.
 * @returns {boolean}
 */
export function isExplorationActive() {
  return explorationActive;
}

/**
 * Wire checkbox toggles in the exploration panel to layer visibility.
 */
function wireToggles() {
  if (togglesWired) return;
  togglesWired = true;

  const panel = document.getElementById('exploration-controls');
  if (!panel) return;

  panel.addEventListener('change', (e) => {
    const checkbox = e.target.closest('input[data-layer]');
    if (!checkbox) return;

    const layerKey = checkbox.dataset.layer;
    const mapping = TOGGLE_LAYER_MAP[layerKey];
    if (!mapping) return;

    const map = getMap();
    if (!map) return;

    const targetOpacity = checkbox.checked ? mapping.opacity : 0;
    for (const layerId of mapping.layers) {
      setLayerOpacity(map, layerId, targetOpacity);
    }
  });
}

/**
 * Apply all toggle states to map layers (used on mode enter).
 */
function applyAllToggles() {
  const map = getMap();
  if (!map) return;

  const checkboxes = document.querySelectorAll('#exploration-controls input[data-layer]');
  for (const checkbox of checkboxes) {
    const layerKey = checkbox.dataset.layer;
    const mapping = TOGGLE_LAYER_MAP[layerKey];
    if (!mapping) continue;

    const targetOpacity = checkbox.checked ? mapping.opacity : 0;
    for (const layerId of mapping.layers) {
      setLayerOpacity(map, layerId, targetOpacity);
    }
  }
}
