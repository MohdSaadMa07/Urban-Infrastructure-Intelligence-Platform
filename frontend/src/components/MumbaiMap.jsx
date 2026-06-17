import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const MumbaiMap = () => {
  const [geoData, setGeoData] = useState(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/wards-geojson/')
      .then(response => response.json())
      .then(data => setGeoData(data))
      .catch(error => console.error("Error fetching ward data:", error));
  }, []);

  const onEachWard = (feature, layer) => {
    const wardName = feature.properties.ward_name;
    const wardNo = feature.properties.ward_no;
    layer.bindTooltip(`<strong>Ward ${wardName}</strong><br/>Number: ${wardNo}`, {
      sticky: true,
      className: 'ward-tooltip'
    });
    layer.on({
      mouseover: (e) => {
        const layer = e.target;
        layer.setStyle({
          weight: 3,
          color: '#ffffff',
          fillOpacity: 0.7
        });
        layer.bringToFront();
      },
      mouseout: (e) => {
        const layer = e.target;
        layer.setStyle({
          weight: 2,
          color: '#2a9df4',
          fillOpacity: 0.3
        });
      }
    });
  };

  const mapStyle = {
    color: '#2a9df4',
    weight: 2,
    fillOpacity: 0.3
  };

  return (
    <div className="map-wrapper">
      <MapContainer 
        center={[19.0760, 72.8777]} 
        zoom={11} 
        style={{ height: '100%', width: '100%', minHeight: '600px' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {geoData && (
          <GeoJSON 
            data={geoData} 
            style={mapStyle} 
            onEachFeature={onEachWard} 
          />
        )}
      </MapContainer>
    </div>
  );
};

export default MumbaiMap;
