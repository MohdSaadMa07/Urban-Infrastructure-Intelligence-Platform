import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import API_BASE from '../config';

// Health score color mapping -- transparent fills
const getHealthColor = (label) => {
  switch (label) {
    case 'Good':     return { fill: 'rgba(34, 197, 94, 0.35)',  border: '#22c55e' }; // green
    case 'Moderate': return { fill: 'rgba(245, 158, 11, 0.35)', border: '#f59e0b' }; // amber
    case 'Poor':     return { fill: 'rgba(239, 68, 68, 0.35)',  border: '#ef4444' }; // red
    default:         return { fill: 'rgba(148, 163, 184, 0.2)', border: '#94a3b8' }; // gray
  }
};

const MumbaiMap = ({ onWardClick }) => {
  const [geoData, setGeoData] = useState(null);
  const [healthData, setHealthData] = useState([]);
  const [healthMap, setHealthMap] = useState({});

  useEffect(() => {
    // Fetch GeoJSON and health scores in parallel
    Promise.all([
      fetch(`${API_BASE}/wards-geojson/`).then(r => r.json()),
      fetch(`${API_BASE}/health-scores/`).then(r => r.json()),
    ])
      .then(([geo, scores]) => {
        // Build a lookup: ward_name -> full score data
        const map = {};
        scores.forEach(s => {
          map[s.ward_name] = s;
        });
        setHealthMap(map);
        setHealthData(scores);
        setGeoData(geo);
      })
      .catch(error => console.error("Error fetching ward data:", error));
  }, []);

  const wardStyle = (feature) => {
    const wardName = feature.properties.ward_name;
    const health = healthMap[wardName];
    const colors = getHealthColor(health?.label);
    return {
      color: colors.border,
      weight: 1.5,
      fillColor: colors.fill,
      fillOpacity: 1,
    };
  };

  const onEachWard = (feature, layer) => {
    const wardName = feature.properties.ward_name;
    const wardNo = feature.properties.ward_no;
    const health = healthMap[wardName];

    const scoreText = health?.health_score != null
      ? `${health.health_score}`
      : '--';
    const labelText = health?.label || 'No Data';
    const labelClass = (health?.label || 'nodata').toLowerCase();

    layer.bindTooltip(
      `<strong>Ward ${wardName}</strong>` +
      `<br/>Number: ${wardNo}` +
      `<br/><span class="health-label health-${labelClass}">${labelText}</span>` +
      `<span class="health-score">${scoreText}</span>`,
      { sticky: true, className: 'ward-tooltip' }
    );

    const defaultStyle = wardStyle(feature);

    layer.on({
      mouseover: (e) => {
        const target = e.target;
        const colors = getHealthColor(health?.label);
        target.setStyle({
          weight: 3,
          color: '#ffffff',
          fillColor: colors.fill.replace(/[\d.]+\)$/, '0.55)'),
          fillOpacity: 1,
        });
        target.bringToFront();
      },
      mouseout: (e) => {
        e.target.setStyle(defaultStyle);
      },
      click: () => {
        if (onWardClick && health) {
          onWardClick(health);
        }
      }
    });
  };

  return (
    <div className="map-wrapper">
      {/* Legend */}
      <div className="health-legend">
        <div className="legend-title">Health Score</div>
        <div className="legend-item">
          <span className="legend-swatch" style={{ background: 'rgba(34, 197, 94, 0.5)' }}></span>
          Good ({'>='} 70)
        </div>
        <div className="legend-item">
          <span className="legend-swatch" style={{ background: 'rgba(245, 158, 11, 0.5)' }}></span>
          Moderate (45-69)
        </div>
        <div className="legend-item">
          <span className="legend-swatch" style={{ background: 'rgba(239, 68, 68, 0.5)' }}></span>
          Poor (&lt; 45)
        </div>
        <div className="legend-item">
          <span className="legend-swatch" style={{ background: 'rgba(148, 163, 184, 0.3)' }}></span>
          No Data
        </div>
      </div>

      <MapContainer 
        center={[19.0760, 72.8777]} 
        zoom={11} 
        style={{ height: '100%', width: '100%', minHeight: '600px' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {geoData && (
          <GeoJSON 
            data={geoData} 
            style={wardStyle} 
            onEachFeature={onEachWard} 
          />
        )}
      </MapContainer>
    </div>
  );
};

export default MumbaiMap;
