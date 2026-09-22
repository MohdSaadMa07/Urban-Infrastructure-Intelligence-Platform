const API_BASE = typeof window !== 'undefined' && window.__API_BASE__
  ? window.__API_BASE__
  : '/api';

// Esri's World Street Map endpoint works with Leaflet without exposing an API
// key in the browser. The y/x order is required by the ArcGIS tile service.
export const MAP_TILE_URL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}';
export const MAP_TILE_ATTRIBUTION = 'Tiles &copy; <a href="https://www.esri.com/">Esri</a> — Sources: Esri, TomTom, Garmin, FAO, NOAA, USGS, &copy; OpenStreetMap contributors';

export default API_BASE;
