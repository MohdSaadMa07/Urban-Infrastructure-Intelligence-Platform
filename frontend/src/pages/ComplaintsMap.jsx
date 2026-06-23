import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Hexagon, Filter, MapPin, X } from 'lucide-react';

const CATEGORY_COLORS = {
  'Garbage': '#f59e0b',
  'Potholes': '#ef4444',
  'Roads': '#ef4444',
  'Water Supply': '#3b82f6',
  'Drainage': '#06b6d4',
  'Street Lights': '#eab308',
  'Other': '#64748b',
};

const LABEL_COLORS = {
  'Good': { fill: 'rgba(34, 197, 94, 0.25)', border: '#22c55e' },
  'Moderate': { fill: 'rgba(245, 158, 11, 0.25)', border: '#f59e0b' },
  'Poor': { fill: 'rgba(239, 68, 68, 0.25)', border: '#ef4444' },
};

function createPinIcon(category) {
  const fill = CATEGORY_COLORS[category] || '#64748b';
  return L.divIcon({
    className: '',
    html: `<svg width="20" height="30" viewBox="0 0 24 36"><path d="M12 0C5.373 0 0 5.373 0 12c0 9 12 24 12 24s12-15 12-24C24 5.373 18.627 0 12 0z" fill="${fill}" stroke="#fff" stroke-width="1.5"/><circle cx="12" cy="12" r="5" fill="#fff"/><circle cx="12" cy="12" r="2" fill="${fill}"/></svg>`,
    iconSize: [20, 30],
    iconAnchor: [10, 30],
    popupAnchor: [0, -30],
  });
}

export default function ComplaintsMap() {
  const [complaints, setComplaints] = useState([]);
  const [geoData, setGeoData] = useState(null);
  const [healthMap, setHealthMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [stats, setStats] = useState({ total: 0, byCategory: {}, byWard: {} });

  const categories = Object.keys(CATEGORY_COLORS);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch('/api/complaints/').then(r => r.json()),
      fetch('/api/wards-geojson/').then(r => r.json()),
      fetch('/api/health-scores/').then(r => r.json()),
    ])
      .then(([complaintsData, geo, scores]) => {
        const map = {};
        scores.forEach(s => { map[s.ward_name] = s; });
        setHealthMap(map);
        setGeoData(geo);
        setComplaints(complaintsData);

        const byCat = {};
        const byWard = {};
        complaintsData.forEach(c => {
          byCat[c.category] = (byCat[c.category] || 0) + 1;
          byWard[c.ward_name] = (byWard[c.ward_name] || 0) + 1;
        });
        setStats({
          total: complaintsData.length,
          byCategory: byCat,
          byWard,
        });
      })
      .catch(err => console.error('Error fetching data:', err))
      .finally(() => setLoading(false));
  }, []);

  const visibleComplaints = selectedCategory
    ? complaints.filter(c => c.category === selectedCategory)
    : complaints;

  const wardStyle = (feature) => {
    const wardName = feature.properties.ward_name;
    const health = healthMap[wardName];
    if (!health) return { color: '#94a3b8', weight: 1, fillColor: 'rgba(148,163,184,0.15)', fillOpacity: 1 };
    const colors = LABEL_COLORS[health.label] || LABEL_COLORS['Poor'];
    return { color: colors.border, weight: 1.5, fillColor: colors.fill, fillOpacity: 1 };
  };

  const onEachWard = (feature, layer) => {
    const wn = feature.properties.ward_name;
    const h = healthMap[wn];
    const count = stats.byWard[wn] || 0;
    layer.bindTooltip(
      `<strong>Ward ${wn}</strong><br/>Complaints: ${count}<br/>Score: ${h ? h.health_score + ' (' + h.label + ')' : 'No Data'}`,
      { sticky: true }
    );
    layer.on({
      mouseover: (e) => {
        const target = e.target;
        target.setStyle({ weight: 3, color: '#ffffff', fillOpacity: 0.55 });
        target.bringToFront();
      },
      mouseout: (e) => {
        e.target.setStyle(wardStyle(feature));
      },
    });
  };

  const complaintCount = visibleComplaints.filter(c => c.latitude && c.longitude).length;

  if (loading) {
    return (
      <div className="auth-page">
        <div className="dash-spinner" />
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#050a18', color: '#f1f5f9', fontFamily: 'Inter, sans-serif' }}>
      <nav className="navbar">
        <div className="nav-brand">
          <Hexagon className="nav-icon" size={24} />
          <span className="nav-title">UrbanIQ</span>
        </div>
        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/public">Public Dashboard</Link>
          <span style={{ color: '#818cf8', borderBottom: '2px solid #818cf8', paddingBottom: 2 }}>Complaint Map</span>
        </div>
        <div className="nav-right">
          <Link to="/login" className="nav-auth-btn nav-auth-btn-primary">
            Sign In
          </Link>
        </div>
      </nav>

      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '2rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 600, margin: 0 }}>Mumbai Complaint Map</h1>
            <p style={{ color: '#94a3b8', margin: '0.25rem 0 0' }}>
              {stats.total} total complaints across all wards
            </p>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            <button
              onClick={() => setSelectedCategory(null)}
              style={{
                padding: '0.35rem 0.75rem', borderRadius: 8, border: '1px solid #334155',
                background: selectedCategory === null ? '#1e293b' : 'transparent',
                color: selectedCategory === null ? '#f1f5f9' : '#64748b',
                cursor: 'pointer', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 4,
              }}
            >
              <Filter size={14} /> All
            </button>
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(selectedCategory === cat ? null : cat)}
                style={{
                  padding: '0.35rem 0.75rem', borderRadius: 8, border: '1px solid #334155',
                  background: selectedCategory === cat ? '#1e293b' : 'transparent',
                  color: selectedCategory === cat ? '#f1f5f9' : '#64748b',
                  cursor: 'pointer', fontSize: '0.8rem',
                  borderLeft: `3px solid ${CATEGORY_COLORS[cat]}`,
                }}
              >
                {cat} ({stats.byCategory[cat] || 0})
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: '1.5rem' }}>
          <div style={{ borderRadius: 12, overflow: 'hidden', border: '1px solid #1e293b', height: '75vh', minHeight: 500 }}>
            <MapContainer center={[19.076, 72.877]} zoom={11} style={{ height: '100%', width: '100%' }}>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              />
              {geoData && (
                <GeoJSON data={geoData} style={wardStyle} onEachFeature={onEachWard} />
              )}
              {visibleComplaints.filter(c => c.latitude && c.longitude).map(c => (
                <Marker key={c.id} position={[Number(c.latitude), Number(c.longitude)]} icon={createPinIcon(c.category)}>
                  <Popup>
                    <div style={{ fontFamily: 'Inter, sans-serif', fontSize: '0.8rem', maxWidth: 220, color: '#0f172a' }}>
                      <strong style={{ color: CATEGORY_COLORS[c.category] || '#64748b' }}>{c.category}</strong>
                      <br />
                      {c.description.slice(0, 100)}{c.description.length > 100 ? '...' : ''}
                      <br />
                      <span style={{ color: '#64748b', fontSize: '0.7rem' }}>
                        Ward {c.ward_name} · {new Date(c.created_at).toLocaleDateString('en-IN')}
                      </span>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="dash-card" style={{ padding: '1rem' }}>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                <MapPin size={16} color="#818cf8" /> Legend
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#94a3b8' }}>
                  <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#ef4444' }} /> Potholes
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#94a3b8' }}>
                  <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#3b82f6' }} /> Water Supply
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#94a3b8' }}>
                  <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#06b6d4' }} /> Drainage
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#94a3b8' }}>
                  <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#f59e0b' }} /> Garbage
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#94a3b8' }}>
                  <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#eab308' }} /> Street Lights
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#94a3b8' }}>
                  <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#64748b' }} /> Other
                </div>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid #1e293b', margin: '0.75rem 0' }} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#94a3b8' }}>
                  <div style={{ width: 16, height: 8, borderRadius: 2, background: 'rgba(34,197,94,0.4)', border: '1px solid #22c55e' }} /> Good
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#94a3b8' }}>
                  <div style={{ width: 16, height: 8, borderRadius: 2, background: 'rgba(245,158,11,0.4)', border: '1px solid #f59e0b' }} /> Moderate
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#94a3b8' }}>
                  <div style={{ width: 16, height: 8, borderRadius: 2, background: 'rgba(239,68,68,0.4)', border: '1px solid #ef4444' }} /> Poor
                </div>
              </div>
            </div>

            <div className="dash-card" style={{ padding: '1rem' }}>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.5rem' }}>Summary</h3>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', lineHeight: 1.8 }}>
                <div><strong style={{ color: '#f1f5f9' }}>{stats.total}</strong> Total Complaints</div>
                <div><strong style={{ color: '#f1f5f9' }}>{complaintCount}</strong> Mapped on Map</div>
                <div><strong style={{ color: '#f1f5f9' }}>{Object.keys(stats.byWard).length}</strong> Wards with Data</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
