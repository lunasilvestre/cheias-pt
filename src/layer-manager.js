/**
 * cheias.pt — Layer manager
 *
 * Manages MapLibre layers: add, remove, show/hide, opacity transitions.
 * Gracefully stubs layers whose data files don't exist yet.
 */

const FADE_DURATION = 400;
const registeredLayers = new Set();
const activeLayers = new Set();

/**
 * Layer definitions — maps layer IDs to their source config.
 * Layers whose data doesn't exist yet will log a stub message.
 */
const LAYER_DEFS = {
  'portugal-outline': {
    type: 'line',
    source: { type: 'geojson', data: 'assets/districts.geojson' },
    paint: { 'line-color': '#ffffff', 'line-width': 1, 'line-opacity': 0 },
  },
  'basins-outline': {
    type: 'line',
    source: { type: 'geojson', data: 'assets/basins.geojson' },
    paint: { 'line-color': '#3498db', 'line-width': 1.5, 'line-opacity': 0 },
  },
  'basins-fill': {
    type: 'fill',
    source: { type: 'geojson', data: 'assets/basins.geojson' },
    paint: { 'fill-color': '#2166ac', 'fill-opacity': 0 },
  },
  // Dynamic layers — source data set programmatically after fetch
  'soil-moisture-animation': {
    type: 'heatmap',
    source: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
    paint: {
      'heatmap-weight': ['get', 'value'],
      'heatmap-intensity': 1,
      'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 5, 35, 7, 60, 9, 90],
      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0,    'rgba(0,0,0,0)',
        0.1,  '#a6611a',
        0.3,  '#dfc27d',
        0.5,  '#f5f5f5',
        0.7,  '#80cdc1',
        0.9,  '#018571',
        1.0,  '#003c30',
      ],
      'heatmap-opacity': 0,
    },
  },
  'precipitation-accumulation': {
    type: 'heatmap',
    source: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
    paint: {
      'heatmap-weight': [
        'interpolate', ['linear'], ['get', 'value'],
        0, 0,
        10, 0.3,
        25, 0.6,
        50, 0.9,
        65, 1.0,
      ],
      'heatmap-intensity': 1.2,
      'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 5, 35, 7, 60, 9, 90],
      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0,    'rgba(0,0,0,0)',
        0.15, '#ffffb2',
        0.3,  '#fecc5c',
        0.5,  '#fd8d3c',
        0.7,  '#f03b20',
        0.9,  '#bd0026',
        1.0,  '#800026',
      ],
      'heatmap-opacity': 0,
    },
  },
  'glofas-discharge': {
    type: 'circle',
    source: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['get', 'discharge_ratio'],
        1, 10, 5, 22, 10, 34,
      ],
      'circle-color': [
        'step', ['get', 'discharge_ratio'],
        '#2166ac', 2,
        '#F7991F', 5,
        '#e74c3c',
      ],
      'circle-opacity': 0,
      'circle-stroke-width': 2,
      'circle-stroke-color': 'rgba(255,255,255,0.3)',
    },
  },
  'soil-moisture-snapshot': {
    type: 'heatmap',
    source: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
    paint: {
      'heatmap-weight': ['get', 'value'],
      'heatmap-intensity': 1,
      'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 5, 35, 7, 60, 9, 90],
      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0,    'rgba(0,0,0,0)',
        0.1,  '#a6611a',
        0.3,  '#dfc27d',
        0.5,  '#f5f5f5',
        0.7,  '#80cdc1',
        0.9,  '#018571',
        1.0,  '#003c30',
      ],
      'heatmap-opacity': 0,
    },
  },
  'river-labels': {
    type: 'symbol',
    source: { type: 'geojson', data: { type: 'FeatureCollection', features: [] } },
    layout: {
      'text-field': ['get', 'basin'],
      'text-size': 14,
      'text-font': ['Open Sans Regular'],
      'text-offset': [0, 1.5],
      'text-anchor': 'top',
      'text-allow-overlap': true,
    },
    paint: {
      'text-color': '#ffffff',
      'text-opacity': 0,
      'text-halo-color': 'rgba(10, 33, 46, 0.8)',
      'text-halo-width': 1.5,
    },
  },
  // --- PMTiles flood extent layers ---
  'sentinel1-flood-extent': {
    type: 'fill',
    source: { type: 'vector', url: 'pmtiles://data/flood-extent/combined.pmtiles' },
    'source-layer': 'flood-extent',
    paint: { 'fill-color': '#e74c3c', 'fill-opacity': 0 },
  },
  'flood-extent-polygons': {
    type: 'fill',
    sourceRef: 'sentinel1-flood-extent',
    'source-layer': 'flood-extent',
    paint: { 'fill-color': '#e74c3c', 'fill-opacity': 0 },
  },

  // --- Consequence markers ---
  'consequence-markers': {
    type: 'circle',
    source: { type: 'geojson', data: 'data/consequences/events.geojson' },
    paint: {
      'circle-radius': 7,
      'circle-color': [
        'match', ['get', 'type'],
        'death', '#e74c3c',
        'evacuation', '#F7991F',
        'infrastructure', '#8e44ad',
        'river_record', '#2166ac',
        'levee_dam', '#e74c3c',
        'landslide', '#795548',
        'rescue', '#27ae60',
        'closure', '#607080',
        'power_cut', '#f39c12',
        'military', '#34495e',
        'political', '#95a5a6',
        /* default */ '#607080'
      ],
      'circle-opacity': 0,
      'circle-stroke-width': 1.5,
      'circle-stroke-color': 'rgba(255,255,255,0.7)',
      'circle-stroke-opacity': 0,
    },
  },

  // --- Pre-rendered raster image sources (scroll-driven narrative chapters) ---
  'soil-moisture-raster': {
    type: 'raster',
    imageSource: true,
    bounds: [-9.6, 36.9, -6.1, 42.2],
    initialUrl: 'data/raster-frames/soil-moisture/2025-12-01.png',
    paint: { 'raster-opacity': 0, 'raster-fade-duration': 0 },
  },
  'precipitation-raster': {
    type: 'raster',
    imageSource: true,
    bounds: [-9.6, 36.9, -6.1, 42.2],
    initialUrl: 'data/raster-frames/precipitation/2025-12-01.png',
    paint: { 'raster-opacity': 0, 'raster-fade-duration': 0 },
  },

  // --- titiler dynamic tile sources (explore mode) ---
  'soil-moisture-tiles': {
    type: 'raster',
    tileSource: true,
    tiles: [
      'https://titiler.cheias.pt/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png'
      + '?url=https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/soil-moisture/2026-01-28.tif'
      + '&colormap_name=ylgnbu&rescale=0.05,0.50&return_mask=true'
    ],
    tileSize: 256,
    attribution: 'Soil moisture: Open-Meteo / ERA5-Land',
    paint: { 'raster-opacity': 0 },
  },
  'precipitation-tiles': {
    type: 'raster',
    tileSource: true,
    tiles: [
      'https://titiler.cheias.pt/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png'
      + '?url=https://pub-abad2527698d4bbab82318691c9b07a1.r2.dev/cog/precipitation/2026-02-06.tif'
      + '&colormap_name=ylorrd&rescale=1,80&return_mask=true'
    ],
    tileSize: 256,
    attribution: 'Precipitation: Open-Meteo / ERA5',
    paint: { 'raster-opacity': 0 },
  },

  // Stubbed layers — data not yet available
  'sst-anomaly': { stub: true },
  'atmospheric-river-track': { stub: true },
  'ipma-warnings-timeline': { stub: true },
  'satellite-after': { stub: true },
};

/**
 * Register a layer on the map if it hasn't been added yet.
 * @param {maplibregl.Map} map
 * @param {string} layerId
 */
export function ensureLayer(map, layerId) {
  if (registeredLayers.has(layerId)) return;

  const def = LAYER_DEFS[layerId];
  if (!def) {
    console.warn(`[layer-manager] Unknown layer: ${layerId}`);
    return;
  }

  if (def.stub) {
    console.log(`[layer-manager] Stub: ${layerId} (data not yet available)`);
    registeredLayers.add(layerId);
    return;
  }

  // Handle pre-rendered image sources (for scroll-driven narrative chapters)
  if (def.imageSource) {
    const [west, south, east, north] = def.bounds;
    const sourceId = `source-${layerId}`;
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'image',
        url: def.initialUrl,
        coordinates: [
          [west, north],  // top-left
          [east, north],  // top-right
          [east, south],  // bottom-right
          [west, south],  // bottom-left
        ]
      });
    }
    if (!map.getLayer(layerId)) {
      map.addLayer({
        id: layerId,
        type: 'raster',
        source: sourceId,
        paint: { ...def.paint },
      });
    }
    registeredLayers.add(layerId);
    return;
  }

  // Handle titiler tile sources (for explore mode)
  if (def.tileSource) {
    const sourceId = `source-${layerId}`;
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'raster',
        tiles: def.tiles,
        tileSize: def.tileSize || 256,
        attribution: def.attribution || '',
      });
    }
    if (!map.getLayer(layerId)) {
      map.addLayer({
        id: layerId,
        type: 'raster',
        source: sourceId,
        paint: { ...def.paint },
      });
    }
    registeredLayers.add(layerId);
    return;
  }

  // Determine source ID — either own source or reference another layer's source
  let sourceId;
  if (def.sourceRef) {
    sourceId = `source-${def.sourceRef}`;
    // Ensure the referenced layer's source exists
    ensureLayer(map, def.sourceRef);
  } else {
    sourceId = `source-${layerId}`;
  }

  if (!map.getSource(sourceId) && def.source) {
    map.addSource(sourceId, def.source);
  }

  if (!map.getLayer(layerId)) {
    const layerConfig = {
      id: layerId,
      type: def.type,
      source: sourceId,
      paint: { ...def.paint },
    };

    if (def['source-layer']) {
      layerConfig['source-layer'] = def['source-layer'];
    }

    if (def.layout) {
      layerConfig.layout = { ...def.layout };
    }

    if (def.filter) {
      layerConfig.filter = def.filter;
    }

    map.addLayer(layerConfig);
  }

  registeredLayers.add(layerId);
}

/**
 * Set a layer's opacity with an animated transition.
 * @param {maplibregl.Map} map
 * @param {string} layerId
 * @param {number} opacity - Target opacity (0-1)
 */
export function setLayerOpacity(map, layerId, opacity) {
  const def = LAYER_DEFS[layerId];
  if (!def || def.stub) return;
  if (!map.getLayer(layerId)) return;

  const opacityProp = getOpacityProperty(def.type);
  if (opacityProp) {
    map.setPaintProperty(layerId, opacityProp, opacity);
  }

  // For circle layers, also set stroke opacity
  if (def.type === 'circle' && map.getLayer(layerId)) {
    map.setPaintProperty(layerId, 'circle-stroke-opacity', opacity);
  }
}

/**
 * Show layers for a specific chapter, hiding all others.
 * @param {maplibregl.Map} map
 * @param {Object} chapterConfig - Chapter config with layers array
 */
export function showChapterLayers(map, chapterConfig) {
  const targetLayers = chapterConfig.layers || [];
  const targetIds = new Set(targetLayers.map(l => l.id));

  // Fade out layers not in the current chapter
  for (const layerId of activeLayers) {
    if (!targetIds.has(layerId)) {
      setLayerOpacity(map, layerId, 0);
      activeLayers.delete(layerId);
    }
  }

  // Fade in target layers
  for (const layer of targetLayers) {
    ensureLayer(map, layer.id);
    setLayerOpacity(map, layer.id, layer.opacity);
    activeLayers.add(layer.id);
  }
}

/**
 * Hide all active layers.
 * @param {maplibregl.Map} map
 */
export function hideAllLayers(map) {
  for (const layerId of activeLayers) {
    setLayerOpacity(map, layerId, 0);
  }
  activeLayers.clear();
}

/**
 * Add a layer from config (for dynamic layer additions).
 * @param {maplibregl.Map} map
 * @param {Object} config - { id, type, source, paint }
 */
export function addLayer(map, config) {
  LAYER_DEFS[config.id] = config;
  ensureLayer(map, config.id);
}

/**
 * Remove a layer from the map.
 * @param {maplibregl.Map} map
 * @param {string} layerId
 */
export function removeLayer(map, layerId) {
  if (map.getLayer(layerId)) {
    map.removeLayer(layerId);
  }
  const sourceId = `source-${layerId}`;
  if (map.getSource(sourceId)) {
    map.removeSource(sourceId);
  }
  registeredLayers.delete(layerId);
  activeLayers.delete(layerId);
}

/**
 * Update the URL of an image source (for raster frame animation).
 * @param {maplibregl.Map} map
 * @param {string} layerId
 * @param {string} url - New image URL
 */
export function updateImageSource(map, layerId, url) {
  const sourceId = `source-${layerId}`;
  const source = map.getSource(sourceId);
  if (source && typeof source.updateImage === 'function') {
    source.updateImage({ url });
  }
}

/**
 * Update the GeoJSON data for a dynamic layer's source.
 * @param {maplibregl.Map} map
 * @param {string} layerId
 * @param {Object} geojson - GeoJSON FeatureCollection
 */
export function updateSourceData(map, layerId, geojson) {
  const sourceId = `source-${layerId}`;
  const source = map.getSource(sourceId);
  if (source) {
    source.setData(geojson);
  }
}

/** Active popup reference for cleanup */
let activePopup = null;

/**
 * Set up click handlers for consequence markers popups.
 * Call once after map load.
 * @param {maplibregl.Map} map
 */
export function initConsequencePopups(map) {
  map.on('click', 'consequence-markers', (e) => {
    if (!e.features || e.features.length === 0) return;

    const props = e.features[0].properties;
    const coords = e.features[0].geometry.coordinates.slice();

    if (activePopup) {
      activePopup.remove();
      activePopup = null;
    }

    const dateStr = props.date || '';
    const sourceUrl = props.source_url || '';
    const sourceLabel = props.source || 'Fonte';

    const html = `
      <div class="popup-consequence">
        <h3 class="popup-consequence__title">${props.title_pt || ''}</h3>
        <p class="popup-consequence__date">${formatDatePT(dateStr)} · ${props.storm || ''}</p>
        <p class="popup-consequence__desc">${props.description_pt || ''}</p>
        ${sourceUrl ? `<a class="popup-consequence__source" href="${sourceUrl}" target="_blank" rel="noopener">${sourceLabel}</a>` : ''}
      </div>
    `;

    activePopup = new maplibregl.Popup({ maxWidth: '320px', closeButton: true })
      .setLngLat(coords)
      .setHTML(html)
      .addTo(map);
  });

  map.on('mouseenter', 'consequence-markers', () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'consequence-markers', () => {
    map.getCanvas().style.cursor = '';
  });
}

/**
 * Filter consequence markers to only show events for a given chapter number.
 * @param {maplibregl.Map} map
 * @param {number|null} chapter - Chapter number to filter by, or null to show all
 */
export function filterConsequencesByChapter(map, chapter) {
  if (!map.getLayer('consequence-markers')) return;
  if (chapter === null) {
    map.setFilter('consequence-markers', null);
  } else {
    map.setFilter('consequence-markers', ['==', ['get', 'chapter'], chapter]);
  }
}

/** Cached precondition basin data */
let preconditionBasinData = null;

/**
 * Color basins-fill layer by precondition index.
 * @param {maplibregl.Map} map
 * @param {'peak'|'pre_storm'|null} mode - Which snapshot to use, or null to reset to flat blue
 */
export async function colorBasinsByPrecondition(map, mode) {
  if (!map.getLayer('basins-fill')) return;

  if (mode === null) {
    // Reset to flat blue
    map.setPaintProperty('basins-fill', 'fill-color', '#2166ac');
    return;
  }

  // Fetch precondition data if not cached
  if (!preconditionBasinData) {
    try {
      const resp = await fetch('data/frontend/precondition-basins.json');
      preconditionBasinData = await resp.json();
    } catch (err) {
      console.error('[layer-manager] Failed to load precondition basins:', err);
      return;
    }
  }

  const snapshot = preconditionBasinData[mode];
  if (!snapshot) return;

  const basinValues = snapshot.basins;

  // Build a match expression: ['match', ['get', 'river'], 'Tejo', '#color', ... , default]
  // Color ramp: 0.0-0.2 #2166ac, 0.2-0.4 #67a9cf, 0.4-0.6 #f7f7f7, 0.6-0.8 #ef8a62, 0.8-1.0 #b2182b
  const matchExpr = ['match', ['get', 'river']];
  for (const [river, value] of Object.entries(basinValues)) {
    let color;
    if (value < 0.2) color = '#2166ac';
    else if (value < 0.4) color = '#67a9cf';
    else if (value < 0.6) color = '#f7f7f7';
    else if (value < 0.8) color = '#ef8a62';
    else color = '#b2182b';
    matchExpr.push(river, color);
  }
  matchExpr.push('#2166ac'); // default fallback

  map.setPaintProperty('basins-fill', 'fill-color', matchExpr);
}

/**
 * Format a date string (YYYY-MM-DD) to Portuguese format.
 */
function formatDatePT(dateStr) {
  if (!dateStr) return '';
  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];
  const parts = dateStr.split('-');
  if (parts.length !== 3) return dateStr;
  const day = parseInt(parts[2], 10);
  const month = months[parseInt(parts[1], 10) - 1] || '';
  return `${day} de ${month} de ${parts[0]}`;
}

/**
 * Get the appropriate opacity paint property for a layer type.
 */
function getOpacityProperty(type) {
  switch (type) {
    case 'fill': return 'fill-opacity';
    case 'line': return 'line-opacity';
    case 'circle': return 'circle-opacity';
    case 'heatmap': return 'heatmap-opacity';
    case 'symbol': return 'text-opacity';
    case 'raster': return 'raster-opacity';
    default: return null;
  }
}
