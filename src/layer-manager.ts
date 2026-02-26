/**
 * cheias.pt — Layer manager
 *
 * Manages MapLibre layers: add, remove, show/hide, opacity transitions.
 * Gracefully stubs layers whose data files don't exist yet.
 */

import maplibregl from 'maplibre-gl';
import type { Map as MLMap } from 'maplibre-gl';
import type { LayerDef, ResolvedChapter } from './types';

const registeredLayers = new Set<string>();
const activeLayers = new Set<string>();

/**
 * Layer definitions — maps layer IDs to their source config.
 */
const LAYER_DEFS: Record<string, LayerDef> = {
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
        '#607080'
      ],
      'circle-opacity': 0,
      'circle-stroke-width': 1.5,
      'circle-stroke-color': 'rgba(255,255,255,0.7)',
      'circle-stroke-opacity': 0,
    },
  },
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
  'sst-anomaly': { stub: true, type: 'raster', paint: {} },
  'atmospheric-river-track': { stub: true, type: 'line', paint: {} },
  'ipma-warnings-timeline': { stub: true, type: 'line', paint: {} },
  'satellite-after': { stub: true, type: 'raster', paint: {} },
};

/**
 * Register a layer on the map if it hasn't been added yet.
 */
export function ensureLayer(map: MLMap, layerId: string): void {
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

  // Handle pre-rendered image sources
  if (def.imageSource) {
    const [west, south, east, north] = def.bounds!;
    const sourceId = `source-${layerId}`;
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'image',
        url: def.initialUrl!,
        coordinates: [
          [west, north],
          [east, north],
          [east, south],
          [west, south],
        ]
      });
    }
    if (!map.getLayer(layerId)) {
      map.addLayer({
        id: layerId,
        type: 'raster',
        source: sourceId,
        paint: { ...def.paint } as maplibregl.RasterLayerSpecification['paint'],
      });
    }
    registeredLayers.add(layerId);
    return;
  }

  // Handle titiler tile sources
  if (def.tileSource) {
    const sourceId = `source-${layerId}`;
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'raster',
        tiles: def.tiles!,
        tileSize: def.tileSize || 256,
        attribution: def.attribution || '',
      });
    }
    if (!map.getLayer(layerId)) {
      map.addLayer({
        id: layerId,
        type: 'raster',
        source: sourceId,
        paint: { ...def.paint } as maplibregl.RasterLayerSpecification['paint'],
      });
    }
    registeredLayers.add(layerId);
    return;
  }

  // Determine source ID
  let sourceId: string;
  if (def.sourceRef) {
    sourceId = `source-${def.sourceRef}`;
    ensureLayer(map, def.sourceRef);
  } else {
    sourceId = `source-${layerId}`;
  }

  if (!map.getSource(sourceId) && def.source) {
    map.addSource(sourceId, def.source as maplibregl.SourceSpecification);
  }

  if (!map.getLayer(layerId)) {
    const layerConfig: Record<string, unknown> = {
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

    map.addLayer(layerConfig as maplibregl.LayerSpecification);
  }

  registeredLayers.add(layerId);
}

/**
 * Set a layer's opacity with an animated transition.
 */
export function setLayerOpacity(map: MLMap, layerId: string, opacity: number): void {
  const def = LAYER_DEFS[layerId];
  if (!def || def.stub) return;
  if (!map.getLayer(layerId)) return;

  const opacityProp = getOpacityProperty(def.type);
  if (opacityProp) {
    map.setPaintProperty(layerId, opacityProp, opacity);
  }

  if (def.type === 'circle' && map.getLayer(layerId)) {
    map.setPaintProperty(layerId, 'circle-stroke-opacity', opacity);
  }
}

/**
 * Show layers for a specific chapter, hiding all others.
 */
export function showChapterLayers(map: MLMap, chapterConfig: ResolvedChapter): void {
  const targetLayers = chapterConfig.layers || [];
  const targetIds = new Set(targetLayers.map(l => l.id));

  for (const layerId of activeLayers) {
    if (!targetIds.has(layerId)) {
      setLayerOpacity(map, layerId, 0);
      activeLayers.delete(layerId);
    }
  }

  for (const layer of targetLayers) {
    ensureLayer(map, layer.id);
    setLayerOpacity(map, layer.id, layer.opacity);
    activeLayers.add(layer.id);
  }
}

/**
 * Hide all active layers.
 */
export function hideAllLayers(map: MLMap): void {
  for (const layerId of activeLayers) {
    setLayerOpacity(map, layerId, 0);
  }
  activeLayers.clear();
}

/**
 * Update the URL of an image source (for raster frame animation).
 */
export function updateImageSource(map: MLMap, layerId: string, url: string): void {
  const sourceId = `source-${layerId}`;
  const source = map.getSource(sourceId);
  if (source && 'updateImage' in source && typeof (source as Record<string, unknown>).updateImage === 'function') {
    (source as { updateImage: (opts: { url: string }) => void }).updateImage({ url });
  }
}

/**
 * Update the GeoJSON data for a dynamic layer's source.
 */
export function updateSourceData(map: MLMap, layerId: string, geojson: GeoJSON.FeatureCollection): void {
  const sourceId = `source-${layerId}`;
  const source = map.getSource(sourceId);
  if (source && 'setData' in source) {
    (source as maplibregl.GeoJSONSource).setData(geojson);
  }
}

/** Active popup reference for cleanup */
let activePopup: maplibregl.Popup | null = null;

/**
 * Set up click handlers for consequence markers popups.
 */
export function initConsequencePopups(map: MLMap): void {
  map.on('click', 'consequence-markers', (e) => {
    if (!e.features || e.features.length === 0) return;

    const props = e.features[0].properties;
    const coords = (e.features[0].geometry as GeoJSON.Point).coordinates.slice() as [number, number];

    if (activePopup) {
      activePopup.remove();
      activePopup = null;
    }

    const dateStr = (props.date as string) || '';
    const sourceUrl = (props.source_url as string) || '';
    const sourceLabel = (props.source as string) || 'Fonte';

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
 */
export function filterConsequencesByChapter(map: MLMap, chapter: number | null): void {
  if (!map.getLayer('consequence-markers')) return;
  if (chapter === null) {
    map.setFilter('consequence-markers', null);
  } else {
    map.setFilter('consequence-markers', ['==', ['get', 'chapter'], chapter]);
  }
}

/** Cached precondition basin data */
let preconditionBasinData: Record<string, { basins: Record<string, number> }> | null = null;

/**
 * Color basins-fill layer by precondition index.
 */
export async function colorBasinsByPrecondition(map: MLMap, mode: 'peak' | 'pre_storm' | null): Promise<void> {
  if (!map.getLayer('basins-fill')) return;

  if (mode === null) {
    map.setPaintProperty('basins-fill', 'fill-color', '#2166ac');
    return;
  }

  if (!preconditionBasinData) {
    try {
      const resp = await fetch('data/frontend/precondition-basins.json');
      preconditionBasinData = await resp.json();
    } catch (err) {
      console.error('[layer-manager] Failed to load precondition basins:', err);
      return;
    }
  }

  const snapshot = preconditionBasinData![mode];
  if (!snapshot) return;

  const basinValues = snapshot.basins;
  const matchExpr: unknown[] = ['match', ['get', 'river']];
  for (const [river, value] of Object.entries(basinValues)) {
    let color: string;
    if (value < 0.2) color = '#2166ac';
    else if (value < 0.4) color = '#67a9cf';
    else if (value < 0.6) color = '#f7f7f7';
    else if (value < 0.8) color = '#ef8a62';
    else color = '#b2182b';
    matchExpr.push(river, color);
  }
  matchExpr.push('#2166ac');

  map.setPaintProperty('basins-fill', 'fill-color', matchExpr as maplibregl.ExpressionSpecification);
}

/**
 * Format a date string (YYYY-MM-DD) to Portuguese format.
 */
function formatDatePT(dateStr: string): string {
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
function getOpacityProperty(type: string): string | null {
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
