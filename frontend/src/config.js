const API_BASE = typeof window !== 'undefined' && window.__API_BASE__
  ? window.__API_BASE__
  : '/api';

// CARTO's hosted raster basemap prevents the public OSM volunteer tile
// servers from being overloaded or blocking the deployed application.
export const MAP_TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
export const MAP_TILE_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

export default API_BASE;
