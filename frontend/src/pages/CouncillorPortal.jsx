import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Hexagon, LogOut, Filter, AlertCircle, CheckCircle,
  MapPin, BarChart3, TrendingUp, RefreshCw, Sparkles, ListTodo, FileText,
  ArrowUp, ArrowDown, Minus, Award, ChartPie, Calendar
} from 'lucide-react';
import {
  RadialBarChart, RadialBar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, LineChart, Line, PieChart, Pie, Legend,
} from 'recharts';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useAuth } from '../context/AuthContext';
import API_BASE from '../config';

// DivIcon-based markers (no image path issues with bundlers)
import L from 'leaflet';

const CATEGORY_PIN_COLORS = {
  'Garbage': '#f59e0b', 'Potholes': '#ef4444', 'Roads': '#ef4444',
  'Water Supply': '#3b82f6', 'Drainage': '#06b6d4',
  'Street Lights': '#eab308', 'Other': '#64748b',
};
function createPinIcon(category) {
  const fill = CATEGORY_PIN_COLORS[category] || '#64748b';
  return L.divIcon({
    className: 'complaint-pin',
    html: `<svg width="24" height="36" viewBox="0 0 24 36" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0C5.373 0 0 5.373 0 12c0 9 12 24 12 24s12-15 12-24C24 5.373 18.627 0 12 0z" fill="${fill}" stroke="#fff" stroke-width="1.5"/>
      <circle cx="12" cy="12" r="5" fill="#fff"/>
      <circle cx="12" cy="12" r="2" fill="${fill}"/>
    </svg>`,
    iconSize: [24, 36],
    iconAnchor: [12, 36],
    popupAnchor: [0, -36],
  });
}

const ESCALATION_COLORS = {
  high: { bg: 'rgba(239,68,68,0.2)', color: '#ef4444', border: '#ef4444' },
  medium: { bg: 'rgba(245,158,11,0.2)', color: '#f59e0b', border: '#f59e0b' },
  low: { bg: 'rgba(34,197,94,0.2)', color: '#22c55e', border: '#22c55e' },
};

const CATEGORY_DISPLAY_TO_KEY = {
  'Potholes': 'Roads', 'Water Supply': 'Water Supply', 'Drainage': 'Drainage',
  'Garbage': 'Solid Waste Management', 'Street Lights': 'Roads', 'Roads': 'Roads',
};

const STATUS_COLORS = {
  open: { bg: 'rgba(239,68,68,0.2)', color: '#f87171', border: '#ef4444' },
  in_progress: { bg: 'rgba(245,158,11,0.2)', color: '#fbbf24', border: '#f59e0b' },
  resolved: { bg: 'rgba(34,197,94,0.2)', color: '#4ade80', border: '#22c55e' },
};

const STATUS_LABELS = { open: 'Open', in_progress: 'In Progress', resolved: 'Resolved' };

const CouncillorPortal = () => {
  const { isAuthenticated, isCouncillor, user, logout, getAccessToken, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [checkedActions, setCheckedActions] = useState({});
  const [hotspots, setHotspots] = useState([]);

  const toggleAction = (idx) => {
    setCheckedActions(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const fetchDashboard = async (status) => {
    setLoading(true);
    let url = `${API_BASE}/councillor/dashboard/`;
    if (status && status !== 'all') url += `?status=${status}`;
    try {
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${getAccessToken()}` },
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Failed to load dashboard');
      }
      const data = await res.json();
      setDashboard(data);
      // Fetch hotspots
      try {
        const hres = await fetch(`${API_BASE}/hotspots/?ward=${data.ward.ward_name}`, {
          headers: { Authorization: `Bearer ${getAccessToken()}` },
        });
        if (hres.ok) setHotspots(await hres.json());
      } catch (e) { console.warn('Hotspots fetch failed:', e); }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (!authLoading) {
      if (!isAuthenticated) {
        navigate('/login', { state: { from: '/councillor-portal' } });
        return;
      }
      if (!isCouncillor) {
        setError('Access denied. Only ward councillors can access this page.');
        setLoading(false);
        return;
      }
      fetchDashboard(statusFilter);
    }
  }, [isAuthenticated, isCouncillor, authLoading]);

  const handleFilterChange = (status) => {
    setStatusFilter(status);
    fetchDashboard(status);
  };

  const handleStatusChange = async (complaintId, newStatus) => {
    try {
      const res = await fetch(`${API_BASE}/complaints/${complaintId}/status/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        setDashboard(prev => ({
          ...prev,
          complaints: prev.complaints.map(c =>
            c.id === complaintId ? { ...c, status: newStatus } : c
          ),
          open_complaints: newStatus === 'open' ? prev.open_complaints + 1 : prev.open_complaints - (prev.complaints.find(c => c.id === complaintId)?.status === 'open' ? 1 : 0),
          in_progress_complaints: newStatus === 'in_progress' ? prev.in_progress_complaints + 1 : prev.in_progress_complaints - (prev.complaints.find(c => c.id === complaintId)?.status === 'in_progress' ? 1 : 0),
          resolved_complaints: newStatus === 'resolved' ? prev.resolved_complaints + 1 : prev.resolved_complaints - (prev.complaints.find(c => c.id === complaintId)?.status === 'resolved' ? 1 : 0),
        }));
      }
    } catch (err) {
      console.error(err);
      alert('Failed to update status');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // Auth guard
  if (authLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#050a18' }}>
        <div className="dash-spinner" />
      </div>
    );
  }

  if (error && !dashboard) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#050a18', gap: '1rem' }}>
        <AlertCircle size={48} color="#ef4444" />
        <h2 style={{ color: '#f8fafc' }}>{error.includes('denied') ? 'Access Denied' : 'Error'}</h2>
        <p style={{ color: '#94a3b8' }}>{error}</p>
        <Link to="/" style={{ color: '#818cf8' }}>Back to Home</Link>
      </div>
    );
  }

  const d = dashboard;

  /* Chart tooltips */
  const ChartTooltip = ({ active, payload, label, unit }) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, padding: '0.5rem 0.75rem', boxShadow: '0 4px 12px rgba(0,0,0,0.3)' }}>
        <p style={{ color: '#94a3b8', fontSize: '0.72rem', margin: 0 }}>{label}</p>
        {payload.map((entry, idx) => (
          entry.value != null && (
            <p key={idx} style={{ color: entry.color, fontSize: '0.85rem', fontWeight: 700, margin: '0.2rem 0 0' }}>
              {entry.name}: {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}{unit || ''}
            </p>
          )
        ))}
      </div>
    );
  };

  const TrendArrow = ({ value }) => {
    if (value == null) return <Minus size={14} color="#64748b" />;
    if (value > 0) return <ArrowUp size={14} color="#ef4444" />;
    if (value < 0) return <ArrowDown size={14} color="#22c55e" />;
    return <Minus size={14} color="#64748b" />;
  };

  const scoreColor = (score) => {
    if (score >= 70) return '#22c55e';
    if (score >= 45) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#050a18' }}>
      {/* --- Navbar --- */}
      <nav className="navbar" style={{ position: 'sticky', top: 0, zIndex: 10, background: 'rgba(5,10,24,0.9)' }}>
        <Link to="/" className="nav-brand" style={{ textDecoration: 'none' }}>
          <Hexagon className="nav-icon" size={24} />
          <span className="nav-title">UrbanIQ</span>
        </Link>
        <div className="nav-links">
          <Link to="/" style={{ color: '#94a3b8' }}>Home</Link>
          <Link to="/dashboard" style={{ color: '#94a3b8' }}>Dashboard</Link>
          <span style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            padding: '0.2rem 0.6rem',
            borderRadius: '4px',
            background: 'rgba(99,102,241,0.15)',
            color: '#818cf8',
          }}>
            {d ? `Ward ${d.ward.ward_name}` : 'Councillor'}
          </span>
        </div>
        <div className="nav-auth">
          <span style={{ color: '#94a3b8', fontSize: '0.82rem', marginRight: '0.5rem' }}>{user?.username}</span>
          <button className="nav-auth-logout" onClick={handleLogout} title="Logout">
            <LogOut size={16} />
          </button>
        </div>
      </nav>

      <main style={{ flex: 1, padding: '2rem', maxWidth: 1100, margin: '0 auto', width: '100%' }}>
        {loading && !d ? (
          <div style={{ textAlign: 'center', color: '#94a3b8', padding: '4rem' }}>
            <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 1rem' }} />
            Loading your ward dashboard...
          </div>
        ) : d ? (
          <>
            {/* --- Ward Header --- */}
            <div style={{
              background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)',
              borderRadius: 16, padding: '1.5rem 2rem', marginBottom: '1.5rem',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem',
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
                  <MapPin size={18} color="#818cf8" />
                  <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                    Ward {d.ward.ward_name}
                  </h1>
                  <span style={{ fontSize: '0.8rem', color: '#64748b' }}>No. {d.ward.ward_no}</span>
                </div>
                <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: 0 }}>
                  {d.metrics_year ? `Data from ${d.metrics_year}` : 'No metric data available'}
                </p>
              </div>
              {d.health_score != null && (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '1rem',
                  background: 'rgba(5,10,24,0.5)', padding: '0.75rem 1.25rem', borderRadius: 12,
                  border: '1px solid rgba(99,102,241,0.1)',
                }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#64748b', marginBottom: '0.2rem' }}>Health Score</div>
                    <div style={{ fontSize: '1.8rem', fontWeight: 900, color: d.health_score >= 70 ? '#22c55e' : d.health_score >= 45 ? '#f59e0b' : '#ef4444' }}>
                      {Math.round(d.health_score)}
                    </div>
                  </div>
                  <span style={{
                    padding: '0.25rem 0.75rem', borderRadius: 100, fontSize: '0.72rem', fontWeight: 700,
                    textTransform: 'uppercase', letterSpacing: '0.04em',
                    background: d.health_label === 'Good' ? 'rgba(34,197,94,0.15)' : d.health_label === 'Moderate' ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)',
                    color: d.health_label === 'Good' ? '#4ade80' : d.health_label === 'Moderate' ? '#fbbf24' : '#f87171',
                  }}>
                    {d.health_label}
                  </span>
                  <button
                    onClick={async () => {
                      try {
                        const wardName = d.ward?.ward_name;
                        if (!wardName) return;
                        const res = await fetch(`${API_BASE}/reports/download/?ward=${encodeURIComponent(wardName)}`, {
                          headers: { Authorization: `Bearer ${getAccessToken()}` },
                        });
                        if (!res.ok) { alert('Report generation failed'); return; }
                        const blob = await res.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url; a.download = `ward_${wardName}_report.pdf`; a.click();
                        URL.revokeObjectURL(url);
                      } catch (e) { alert('Could not download report'); }
                    }}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '0.4rem',
                      padding: '0.5rem 1rem', borderRadius: 8, border: '1px solid rgba(99,102,241,0.3)',
                      background: 'rgba(99,102,241,0.1)', color: '#818cf8',
                      fontSize: '0.78rem', fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap',
                    }}
                    title="Download PDF Report"
                  >
                    <FileText size={14} /> PDF Report
                  </button>
                </div>
              )}
            </div>

            {/* --- Stats Row --- */}
            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem',
            }}>
              {[
                { label: 'Total Complaints', value: d.total_complaints, color: '#818cf8' },
                { label: 'Open', value: d.open_complaints, color: '#ef4444' },
                { label: 'In Progress', value: d.in_progress_complaints, color: '#f59e0b' },
                { label: 'Resolved', value: d.resolved_complaints, color: '#22c55e' },
              ].map(stat => (
                <div key={stat.label} style={{
                  background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(99,102,241,0.08)',
                  borderRadius: 12, padding: '1.25rem', textAlign: 'center',
                }}>
                  <div style={{ fontSize: '1.8rem', fontWeight: 900, color: stat.color, fontVariantNumeric: 'tabular-nums' }}>
                    {stat.value}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: '0.2rem' }}>
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>

            {/* ── Complaint Categories ── */}
            {d.major_categories && d.major_categories.length > 0 && (
              <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)', borderRadius: 16, padding: '1.25rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                  <ChartPie size={16} color="#a78bfa" />
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    What Issues Are Being Reported
                  </h3>
                  <span style={{ fontSize: '0.7rem', color: '#64748b', marginLeft: 'auto' }}>
                    {d.complaints.length} total complaints
                  </span>
                </div>
                {(() => {
                  const CATEGORY_COLORS = {
                    'Potholes': '#ef4444', 'Water Supply': '#3b82f6', 'Drainage': '#f59e0b',
                    'Garbage': '#22c55e', 'Street Lights': '#eab308', 'Roads': '#64748b', 'Other': '#8b5cf6',
                    'Solid Waste Management': '#22c55e',
                  };
                  const pieData = d.major_categories.map(c => ({
                    name: c.category_display,
                    value: c.count,
                    fill: CATEGORY_COLORS[c.category_display] || '#818cf8',
                  }));
                  return (
                    <ResponsiveContainer width="100%" height={260}>
                      <PieChart>
                        <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100}
                          paddingAngle={3} dataKey="value" nameKey="name">
                          {pieData.map(entry => (
                            <Cell key={entry.name} fill={entry.fill} stroke="rgba(5,10,24,0.6)" strokeWidth={2} />
                          ))}
                        </Pie>
                        <Tooltip content={<ChartTooltip unit="" />} />
                        <Legend
                          wrapperStyle={{ fontSize: '0.75rem', color: '#94a3b8' }}
                          iconType="circle"
                          formatter={(value) => <span style={{ color: '#cbd5e1' }}>{value}</span>}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  );
                })()}
              </div>
            )}

            {/* ── Complaint Map with Hotspots ── */}
              <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)', borderRadius: 16, padding: '1.25rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <MapPin size={16} color="#22c55e" />
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Where Complaints Are Located
                  </h3>
                  {(() => {
                    const marked = d.complaints.filter(c => c.latitude != null && c.longitude != null);
                    return marked.length > 0 ? (
                      <span style={{ fontSize: '0.72rem', color: '#22c55e', marginLeft: 'auto' }}>
                        {marked.length} pin{marked.length > 1 ? 's' : ''} on map
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.72rem', color: '#64748b', marginLeft: 'auto' }}>
                        No location data — complaints lack coordinates
                      </span>
                    );
                  })()}
                  {hotspots.length > 0 && (
                    <span style={{ fontSize: '0.72rem', color: '#f59e0b', marginLeft: '0.5rem' }}>
                      · {hotspots.length} hotspot{hotspots.length > 1 ? 's' : ''} detected
                    </span>
                  )}
                </div>
                <MapContainer center={[19.076, 72.877]} zoom={12} style={{ height: 380, borderRadius: 12, zIndex: 1 }}
                  key={d.ward.ward_name}>
                  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                  {d.complaints.filter(c => c.latitude != null && c.longitude != null).map(c => (
                    <Marker key={c.id} position={[Number(c.latitude), Number(c.longitude)]} icon={createPinIcon(c.category)}>
                      <Popup>
                        <div style={{ fontFamily: 'Inter, sans-serif', fontSize: '0.8rem', maxWidth: 220 }}>
                          <strong>{c.category}</strong><br />
                          {c.description.slice(0, 80)}{c.description.length > 80 ? '...' : ''}<br />
                          <span style={{ color: '#64748b', fontSize: '0.7rem' }}>
                            {new Date(c.created_at).toLocaleDateString('en-IN')} · {c.status}
                          </span>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                  {hotspots.filter(h => h.count >= 2).map(h => (
                    <Circle key={h.cluster_id} center={[h.center_lat, h.center_lng]}
                      radius={100} pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.15, weight: 2 }} />
                  ))}
                </MapContainer>
                {d.complaints.filter(c => c.latitude != null && c.longitude != null).length === 0 && (
                  <div style={{ textAlign: 'center', padding: '1rem', color: '#64748b', fontSize: '0.85rem' }}>
                    <MapPin size={24} style={{ opacity: 0.3, margin: '0 auto 0.4rem' }} />
                    Complaints need location data to appear as pins on this map.<br />
                    Use the <strong>Detect My Location</strong> option when submitting complaints.
                  </div>
                )}
                {hotspots.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
                    {hotspots.map(h => (
                      <span key={h.cluster_id} style={{ fontSize: '0.72rem', background: 'rgba(239,68,68,0.1)', color: '#f87171', padding: '0.25rem 0.6rem', borderRadius: 100 }}>
                        {h.count} complaints near {h.center_lat.toFixed(3)}, {h.center_lng.toFixed(3)}
                      </span>
                    ))}
                  </div>
                )}
              </div>

            {/* ── Complaint List ── */}
            <div style={{
              background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)',
              borderRadius: 16, overflow: 'hidden', marginBottom: '1.5rem',
            }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '1rem 1.5rem', borderBottom: '1px solid rgba(99,102,241,0.08)',
                background: 'rgba(5,10,24,0.3)',
              }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
                  All Complaints
                </h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#0f172a', padding: '0.4rem 0.8rem', borderRadius: 8, border: '1px solid #1e293b' }}>
                  <Filter size={14} color="#64748b" />
                  <select
                    value={statusFilter}
                    onChange={e => handleFilterChange(e.target.value)}
                    style={{ background: 'transparent', border: 'none', color: '#e2e8f0', outline: 'none', fontSize: '0.82rem', cursor: 'pointer' }}
                  >
                    <option value="all">All</option>
                    <option value="open">Open</option>
                    <option value="in_progress">In Progress</option>
                    <option value="resolved">Resolved</option>
                  </select>
                </div>
              </div>

              {d.complaints.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#64748b', padding: '3rem' }}>
                  <CheckCircle size={32} style={{ margin: '0 auto 0.75rem', opacity: 0.4 }} />
                  No complaints found{statusFilter !== 'all' ? ` with "${STATUS_LABELS[statusFilter]}" status` : ''}.
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid rgba(99,102,241,0.06)' }}>
                        <th style={{ padding: '0.85rem 1.25rem', textAlign: 'left', color: '#475569', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>ID & Date</th>
                        <th style={{ padding: '0.85rem 1.25rem', textAlign: 'left', color: '#475569', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Photo</th>
                        <th style={{ padding: '0.85rem 1.25rem', textAlign: 'left', color: '#475569', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Category</th>
                        <th style={{ padding: '0.85rem 1.25rem', textAlign: 'left', color: '#475569', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Description</th>
                        <th style={{ padding: '0.85rem 1.25rem', textAlign: 'left', color: '#475569', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {d.complaints.map(c => (
                        <tr key={c.id} style={{ borderBottom: '1px solid rgba(99,102,241,0.04)', transition: 'background 0.15s' }}
                          onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.04)'}
                          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                        >
                          <td style={{ padding: '0.85rem 1.25rem', verticalAlign: 'top' }}>
                            <div style={{ fontWeight: 700, color: '#f8fafc' }}>#{c.id}</div>
                            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.15rem' }}>
                              {new Date(c.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                            </div>
                            {c.resolved_at && (
                              <div style={{ fontSize: '0.68rem', color: '#22c55e', marginTop: '0.1rem' }}>
                                Resolved: {new Date(c.resolved_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                              </div>
                            )}
                          </td>
                          <td style={{ padding: '0.85rem 1.25rem', verticalAlign: 'top' }}>
                            {c.image ? (
                              <img
                                src={c.image}
                                alt=""
                                style={{ width: 56, height: 56, objectFit: 'cover', borderRadius: 8, border: '1px solid #334155', cursor: 'pointer' }}
                                onClick={() => window.open(c.image, '_blank')}
                                onError={(e) => { e.target.style.display = 'none'; }}
                              />
                            ) : (
                              <span style={{ color: '#334155', fontSize: '0.75rem' }}>--</span>
                            )}
                          </td>
                          <td style={{ padding: '0.85rem 1.25rem', verticalAlign: 'top' }}>
                            <div style={{ color: '#cbd5e1' }}>{c.category}</div>
                            {(() => {
                              const escKey = CATEGORY_DISPLAY_TO_KEY[c.category] || c.category;
                              const esc = d.escalation_data?.find(e => e.category === escKey);
                              if (!esc || esc.escalation_rate < 0.1) return null;
                              const level = esc.escalation_rate >= 0.4 ? 'high' : esc.escalation_rate >= 0.2 ? 'medium' : 'low';
                              const ec = ESCALATION_COLORS[level];
                              return (
                                <span style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', background: ec.bg, color: ec.color, padding: '0.1rem 0.45rem', borderRadius: 3, display: 'inline-block', marginTop: '0.2rem' }}>
                                  {Math.round(esc.escalation_rate * 100)}% escalate
                                </span>
                              );
                            })()}
                          </td>
                          <td style={{ padding: '0.85rem 1.25rem', verticalAlign: 'top', maxWidth: '320px' }}>
                            <div style={{ lineHeight: '1.5', color: '#94a3b8' }}>{c.description}</div>
                            {c.latitude && c.longitude && (
                              <div style={{ fontSize: '0.72rem', color: '#475569', marginTop: '0.35rem', fontFamily: 'monospace' }}>
                                {c.latitude.toFixed(4)}, {c.longitude.toFixed(4)}
                              </div>
                            )}
                          </td>
                          <td style={{ padding: '0.85rem 1.25rem', verticalAlign: 'top' }}>
                            <select
                              value={c.status}
                              onChange={e => handleStatusChange(c.id, e.target.value)}
                              style={{
                                background: STATUS_COLORS[c.status]?.bg || 'rgba(148,163,184,0.1)',
                                color: STATUS_COLORS[c.status]?.color || '#94a3b8',
                                border: `1px solid ${STATUS_COLORS[c.status]?.border || '#475569'}`,
                                padding: '0.4rem 0.75rem', borderRadius: 8, outline: 'none',
                                cursor: 'pointer', fontWeight: 700, fontSize: '0.78rem',
                                fontFamily: 'Inter, sans-serif',
                              }}
                            >
                              <option value="open">Open</option>
                              <option value="in_progress">In Progress</option>
                              <option value="resolved">Resolved</option>
                            </select>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* ── Health Score Gauge + Ward Rankings ── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
              <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)', borderRadius: 16, padding: '1.25rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <BarChart3 size={16} color="#818cf8" />
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Ward Health Score
                  </h3>
                </div>
                {d.health_score != null ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ width: 140, height: 140 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="100%" barSize={16}
                          data={[{ name: 'Score', value: Math.round(d.health_score), fill: scoreColor(d.health_score) }]}
                          startAngle={180} endAngle={0}>
                          <RadialBar dataKey="value" cornerRadius={8} background={{ fill: '#1e293b' }} />
                          <text x="70" y="75" textAnchor="middle" dominantBaseline="middle" fill="#f8fafc" fontSize={28} fontWeight={900}>
                            {Math.round(d.health_score)}
                          </text>
                          <text x="70" y="95" textAnchor="middle" dominantBaseline="middle" fill="#64748b" fontSize={11} fontWeight={600}>
                            / 100
                          </text>
                        </RadialBarChart>
                      </ResponsiveContainer>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <span style={{ padding: '0.2rem 0.6rem', borderRadius: 100, fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', background: d.health_label === 'Good' ? 'rgba(34,197,94,0.15)' : d.health_label === 'Moderate' ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)', color: d.health_label === 'Good' ? '#4ade80' : d.health_label === 'Moderate' ? '#fbbf24' : '#f87171' }}>
                          {d.health_label}
                        </span>
                        {d.ward_rankings && (
                          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                            #{d.ward_rankings.health_score_rank} of {d.ward_rankings.total_wards} wards
                          </span>
                        )}
                      </div>
                      {d.health_breakdown && d.health_breakdown.deliberation_score != null && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                          {[
                            { label: 'Complaint Volume', value: Math.round(d.health_breakdown.complaint_score * 100), color: '#818cf8' },
                            { label: 'Resolution Speed', value: Math.round(d.health_breakdown.resolution_score * 100), color: '#a78bfa' },
                            { label: 'Civic Engagement', value: Math.round(d.health_breakdown.deliberation_score * 100), color: '#c084fc' },
                          ].map(s => (
                            <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span style={{ fontSize: '0.7rem', color: '#94a3b8', width: 100, flexShrink: 0 }}>{s.label}</span>
                              <div style={{ flex: 1, height: 6, background: '#1e293b', borderRadius: 3, overflow: 'hidden' }}>
                                <div style={{ width: `${s.value}%`, height: '100%', background: s.color, borderRadius: 3, transition: 'width 0.5s' }} />
                              </div>
                              <span style={{ fontSize: '0.7rem', color: s.color, fontWeight: 700, width: 28, textAlign: 'right' }}>{s.value}%</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <p style={{ color: '#64748b', fontSize: '0.85rem' }}>No health score available</p>
                )}
              </div>

              <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)', borderRadius: 16, padding: '1.25rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <Award size={16} color="#fbbf24" />
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Ward Rankings & Trends
                  </h3>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  {[
                    { label: 'Health Score', rank: d.ward_rankings?.health_score_rank, total: d.ward_rankings?.total_wards, color: '#818cf8', bestIs: 'high' },
                    { label: 'Complaint Volume', rank: d.ward_rankings?.complaints_rank, total: d.ward_rankings?.total_wards, color: '#f87171', bestIs: 'low' },
                    { label: 'Resolution Speed', rank: d.ward_rankings?.resolution_rank, total: d.ward_rankings?.total_wards, color: '#fbbf24', bestIs: 'low' },
                    { label: 'Civic Engagement', rank: d.ward_rankings?.deliberation_rank, total: d.ward_rankings?.total_wards, color: '#4ade80', bestIs: 'high' },
                  ].map(item => (
                    <div key={item.label} style={{ background: 'rgba(5,10,24,0.3)', borderRadius: 10, padding: '0.75rem', border: '1px solid rgba(99,102,241,0.06)' }}>
                      <div style={{ fontSize: '0.65rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.3rem' }}>
                        {item.label}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.3rem' }}>
                        <span style={{ fontSize: '1.2rem', fontWeight: 900, color: item.color }}>
                          {item.rank ? `#${item.rank}` : '--'}
                        </span>
                        {item.total && (
                          <span style={{ fontSize: '0.7rem', color: '#64748b' }}>of {item.total}</span>
                        )}
                      </div>
                      {d.yoy_change && item.label === 'Health Score' && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.2rem' }}>
                          <TrendArrow value={d.yoy_change.health_score_change} />
                          <span style={{ fontSize: '0.68rem', color: d.yoy_change.health_score_change > 0 ? '#22c55e' : '#ef4444', fontWeight: 600 }}>
                            {d.yoy_change.health_score_change > 0 ? '+' : ''}{d.yoy_change.health_score_change} pts
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* ── Your Ward vs City Average ── */}
            {d.ward_metrics_history && d.ward_metrics_history.length > 0 && d.city_averages && (
              <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)', borderRadius: 16, padding: '1.25rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                  <BarChart3 size={16} color="#818cf8" />
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Your Ward vs City Average
                  </h3>
                  <span style={{ fontSize: '0.7rem', color: '#64748b', marginLeft: 'auto' }}>
                    Latest year: {d.metrics_year}
                  </span>
                </div>
                {(() => {
                  const latest = d.ward_metrics_history[d.ward_metrics_history.length - 1];
                  if (!latest) return null;

                  const fmt = (v) => {
                    if (v == null) return '--';
                    return typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 1 }) : v;
                  };

                  const rows = [
                    { label: 'Health Score', ward: latest.health_score, city: d.city_averages.health_score },
                    { label: 'Complaints / Capita', ward: latest.per_capita_complaints, city: d.city_averages.per_capita_complaints },
                    { label: 'Resolution Days', ward: latest.avg_resolution_days, city: d.city_averages.avg_resolution_days },
                    { label: 'Deliberations / Capita', ward: latest.per_capita_deliberations, city: d.city_averages.per_capita_deliberations },
                  ];

                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {rows.map(r => {
                        const wardVal = r.ward;
                        const cityVal = r.city;
                        const belowAvg = wardVal != null && cityVal != null ? wardVal < cityVal : null;
                        const barPct = wardVal != null && cityVal != null && cityVal !== 0
                          ? Math.min(Math.abs(wardVal / cityVal), 3)
                          : 0;
                        return (
                          <div key={r.label} style={{
                            display: 'grid', gridTemplateColumns: '140px 1fr 1fr 40px',
                            gap: '0.75rem', alignItems: 'center',
                            padding: '0.55rem 0.8rem', borderRadius: 10,
                            background: 'rgba(5,10,24,0.3)', border: '1px solid rgba(99,102,241,0.06)',
                          }}>
                            <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>{r.label}</span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f1f5f9', minWidth: 48 }}>
                                {fmt(wardVal)}
                              </span>
                              <div style={{
                                flex: 1, height: 6, background: '#1e293b', borderRadius: 3, overflow: 'hidden',
                              }}>
                                <div style={{
                                  width: `${Math.min(barPct * 100, 100)}%`,
                                  height: '100%', borderRadius: 3,
                                  background: belowAvg === true ? '#22c55e' : belowAvg === false ? '#ef4444' : '#475569',
                                  transition: 'width 0.4s',
                                }} />
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                              <span style={{ fontSize: '0.82rem', color: '#64748b' }}>{fmt(cityVal)}</span>
                              <span style={{ fontSize: '0.65rem', color: '#475569' }}>avg</span>
                            </div>
                            <div style={{ textAlign: 'center' }}>
                              {belowAvg === true ? (
                                <ArrowDown size={14} color="#22c55e" />
                              ) : belowAvg === false ? (
                                <ArrowUp size={14} color="#ef4444" />
                              ) : (
                                <Minus size={14} color="#64748b" />
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}
              </div>
            )}

            {/* ── Multi-Year Trend Chart ── */}
            {(() => {
              if (!d.ward_metrics_history || d.ward_metrics_history.length === 0) return null;
              const chartData = d.ward_metrics_history.map(m => ({
                year: m.year,
                total: m.total_complaints,
                isPredicted: false,
              }));
              if (d.predicted_data) {
                [2025, 2026].forEach(yr => {
                  const p = d.predicted_data[String(yr)];
                  if (p) {
                    const existing = chartData.find(d => d.year === yr);
                    if (existing) {
                      existing.total = p.predicted_complaints;
                      existing.isPredicted = true;
                    } else {
                      chartData.push({ year: yr, total: p.predicted_complaints, isPredicted: true });
                    }
                  }
                });
                chartData.sort((a, b) => a.year - b.year);
              }
              const hasPredicted = chartData.some(d => d.isPredicted);
              return (
              <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)', borderRadius: 16, padding: '1.25rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <TrendingUp size={16} color="#22c55e" />
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Complaint Trend (2019-2026) <span className="ml-badge">ML</span>
                  </h3>
                  {hasPredicted && (
                    <span style={{ fontSize: '0.7rem', color: '#64748b', marginLeft: 'auto' }}>
                      Blue = Actual · Orange = ML Predicted
                    </span>
                  )}
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={chartData} margin={{ top: 8, right: 16, left: 16, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                    <XAxis dataKey="year" tick={{ fill: '#64748b', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                    <Tooltip content={<ChartTooltip unit=" complaints" />} />
                    <Line type="monotone" dataKey="total" name="Complaints" stroke="#818cf8" strokeWidth={3}
                      dot={(props) => {
                        const isPred = (props.payload?.year || 0) >= 2025;
                        return (
                          <circle cx={props.cx} cy={props.cy} r={isPred ? 5 : 4}
                            fill={isPred ? '#f59e0b' : '#818cf8'} stroke="none" />
                        );
                      }}
                      activeDot={{ r: 6, fill: '#818cf8' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )})()}

            {/* ── Seasonal Advisories (Proactive) ── */}
            {d.seasonal_advisories && d.seasonal_advisories.filter(a => a.urgency > 0).length > 0 && (
              <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(56,189,248,0.15)', borderRadius: 16, padding: '1.25rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <Calendar size={16} color="#38bdf8" />
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#38bdf8', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Seasonal Advisory <span className="ml-badge" style={{ background: 'rgba(56,189,248,0.2)', color: '#38bdf8' }}>Forecast</span>
                  </h3>
                  <span style={{ fontSize: '0.72rem', color: '#64748b', marginLeft: 'auto' }}>
                    Upcoming 2 months
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {d.seasonal_advisories.filter(a => a.urgency > 0).slice(0, 4).map(a => (
                    <div key={a.category} style={{
                      display: 'grid', gridTemplateColumns: 'auto 1fr',
                      gap: '0.75rem', alignItems: 'start',
                      padding: '0.7rem 0.8rem', borderRadius: 10,
                      background: 'rgba(5,10,24,0.3)', border: '1px solid rgba(56,189,248,0.08)',
                    }}>
                      <span style={{
                        fontSize: '0.65rem', fontWeight: 700, padding: '2px 8px', borderRadius: 4,
                        textTransform: 'uppercase', whiteSpace: 'nowrap', marginTop: 1,
                        background: a.season_status === 'peak_season' ? 'rgba(239,68,68,0.2)' :
                                     a.season_status === 'pre_season' ? 'rgba(251,146,60,0.2)' :
                                     'rgba(56,189,248,0.2)',
                        color: a.season_status === 'peak_season' ? '#ef4444' :
                               a.season_status === 'pre_season' ? '#fb923c' : '#38bdf8',
                      }}>
                        {a.season_status === 'pre_season' ? 'Prepare' : a.season_status === 'peak_season' ? 'Active' : 'Watch'}
                      </span>
                      <div>
                        <div style={{ fontSize: '0.82rem', color: '#e2e8f0', fontWeight: 600, marginBottom: '0.2rem' }}>{a.display_name}</div>
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8', lineHeight: 1.5 }}>{a.advisory_text}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── City-Wide Trends (Praja CSV data) ── */}
            {d.failing_categories && d.failing_categories.length > 0 && (
              <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(239,68,68,0.15)', borderRadius: 16, padding: '1.25rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <TrendingUp size={16} color="#ef4444" />
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f87171', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    City-Wide Trends <span className="ml-badge">ML</span>
                  </h3>
                  <span style={{ fontSize: '0.72rem', color: '#64748b', marginLeft: 'auto' }}>
                    City-wide · 3-year growth
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {d.failing_categories.filter(c => c.recent_3yr_growth_pct > 5).slice(0, 5).map(c => (
                    <div key={c.issue} style={{
                      display: 'grid', gridTemplateColumns: '1fr auto auto',
                      gap: '0.75rem', alignItems: 'center',
                      padding: '0.55rem 0.8rem', borderRadius: 10,
                      background: 'rgba(5,10,24,0.3)', border: '1px solid rgba(239,68,68,0.08)',
                    }}>
                      <span style={{ fontSize: '0.82rem', color: '#e2e8f0', fontWeight: 600 }}>{c.issue}</span>
                      <span style={{ fontSize: '0.82rem', fontWeight: 700, color: c.recent_3yr_growth_pct > 20 ? '#ef4444' : '#f59e0b' }}>
                        +{c.recent_3yr_growth_pct}%
                      </span>
                      <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                        ~{c.projected_next?.toLocaleString()} next
                      </span>
                    </div>
                  ))}
                  <div style={{ fontSize: '0.65rem', color: '#64748b', textAlign: 'right', paddingRight: '0.2rem' }}>
                    Based on city-wide Praja data · May not reflect your ward specifically
                  </div>
                </div>
              </div>
            )}

            {/* ── ML Insights / Forecast Card ── */}
            {d.predictions && (
              <div style={{
                background: 'linear-gradient(135deg, rgba(30,27,75,0.4) 0%, rgba(15,23,42,0.6) 100%)',
                border: '1px solid rgba(129,140,248,0.2)',
                borderRadius: 16, padding: '1.5rem 2rem', marginBottom: '1.5rem',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.25)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
                  <TrendingUp size={20} color="#818cf8" style={{ filter: 'drop-shadow(0 0 4px rgba(129,140,248,0.4))' }} />
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f8fafc', margin: 0, letterSpacing: '0.02em' }}>
                    AI Infrastructure Forecast & Insights <span className="ml-badge">ML</span>
                  </h3>
                  <span style={{ fontSize: '0.72rem', color: '#64748b', marginLeft: 'auto', fontFamily: 'monospace' }}>
                    v{d.predictions.model_version}
                  </span>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 0.7fr', gap: '1.5rem', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', gap: '0.75rem', width: '100%' }}>
                    <div style={{
                      flex: 1, background: 'rgba(5,10,24,0.3)', border: '1px solid rgba(99,102,241,0.08)',
                      borderRadius: 12, padding: '1rem', display: 'flex', flexDirection: 'column', justifyContent: 'center'
                    }}>
                      <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b', marginBottom: '0.25rem' }}>
                        Forecasted Complaints
                      </div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 900, color: '#f8fafc' }}>
                        {d.predictions.predicted_complaints?.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: '#818cf8', marginTop: '0.2rem' }}>
                        For {d.predicted_data ? Object.keys(d.predicted_data).sort().pop() : '2026'}
                      </div>
                      {(() => {
                        const years = d.predicted_data ? Object.keys(d.predicted_data).sort() : [];
                        const latestYear = years.length ? years[years.length - 1] : null;
                        const pd = latestYear ? d.predicted_data[latestYear] : null;
                        if (!pd || pd.predicted_complaints_lower == null || pd.predicted_complaints_upper == null) return null;
                        return (
                          <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(99,102,241,0.1)' }}>
                            <div style={{ fontSize: '0.62rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b', marginBottom: '0.2rem' }}>
                              ML Confidence Range
                            </div>
                            <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                              {pd.predicted_complaints_lower.toLocaleString()} – {pd.predicted_complaints_upper.toLocaleString()}
                            </div>
                          </div>
                        );
                      })()}
                    </div>

                    <div style={{
                      flex: 1, background: 'rgba(5,10,24,0.3)', border: '1px solid rgba(99,102,241,0.08)',
                      borderRadius: 12, padding: '1rem', display: 'flex', flexDirection: 'column', justifyContent: 'center'
                    }}>
                      <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b', marginBottom: '0.25rem' }}>
                        Predicted Risk Level
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{
                          width: 8, height: 8, borderRadius: '50%',
                          background: d.predictions.predicted_risk?.toLowerCase() === 'high' ? '#ef4444' : d.predictions.predicted_risk?.toLowerCase() === 'medium' ? '#f59e0b' : '#22c55e'
                        }} />
                        <div style={{
                          fontSize: '1.3rem', fontWeight: 900,
                          color: d.predictions.predicted_risk?.toLowerCase() === 'high' ? '#ef4444' : d.predictions.predicted_risk?.toLowerCase() === 'medium' ? '#f59e0b' : '#22c55e',
                          textTransform: 'capitalize'
                        }}>
                          {d.predictions.predicted_risk}
                        </div>
                      </div>
                      <div style={{ fontSize: '0.72rem', color: '#818cf8', marginTop: '0.2rem' }}>
                        Infrastructure Risk
                      </div>
                    </div>

                    {d.focus_facility && (
                      <div style={{
                        flex: 1, background: 'rgba(5,10,24,0.3)', border: '1px solid rgba(239,68,68,0.15)',
                        borderRadius: 12, padding: '1.0rem 0.75rem', display: 'flex', flexDirection: 'column', justifyContent: 'center'
                      }}>
                        <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#f87171', fontWeight: 700, marginBottom: '0.25rem' }}>
                          AI Priority Focus
                        </div>
                        <div style={{ fontSize: '1.15rem', fontWeight: 900, color: '#f87171', lineHeight: '1.2' }}>
                          {d.focus_facility.display_name}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                          {d.focus_facility.escalation_rate}% escalation rate
                        </div>
                      </div>
                    )}
                  </div>

                  <div style={{
                    background: 'rgba(99,102,241,0.04)', border: '1px solid rgba(99,102,241,0.08)',
                    borderRadius: 12, padding: '1rem', display: 'flex', gap: '0.75rem'
                  }}>
                    <AlertCircle size={20} color="#818cf8" style={{ flexShrink: 0, marginTop: '0.1rem' }} />
                    <div>
                      <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#818cf8', fontWeight: 700, marginBottom: '0.25rem' }}>
                        AI Recommendation
                      </div>
                      <p style={{ color: '#cbd5e1', fontSize: '0.82rem', lineHeight: '1.45', margin: 0 }}>
                        {d.predictions.recommendation}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ── AI Ward Briefing & Action Plan ── */}
            {d.briefing && !d.briefing.error && (
              <div style={{
                background: 'linear-gradient(135deg, #0a0f1e 0%, #14192d 100%)',
                border: '1px solid rgba(129, 140, 248, 0.2)',
                borderRadius: 16,
                padding: '1.8rem',
                marginBottom: '1.5rem',
              }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '0.8rem',
                  borderBottom: '1px solid rgba(255,255,255,0.08)',
                  paddingBottom: '1rem', marginBottom: '1.2rem', flexWrap: 'wrap',
                }}>
                  <Sparkles size={24} color="#818cf8" />
                  <div>
                    <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                      AI Ward Briefing <span className="ml-badge">ML</span>
                    </h3>
                    <p style={{ color: '#64748b', fontSize: '0.85rem', margin: 0 }}>
                      {new Date(d.briefing.generated_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
                    </p>
                  </div>
                </div>

                <div style={{
                  background: 'rgba(99, 102, 241, 0.06)',
                  borderLeft: '5px solid #818cf8',
                  padding: '1.2rem 1.4rem',
                  borderRadius: '0 12px 12px 0',
                  marginBottom: '1.5rem',
                }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 800, textTransform: 'uppercase', color: '#818cf8', letterSpacing: '0.06em', marginBottom: '0.3rem' }}>
                    Quick Summary
                  </div>
                  <div style={{ color: '#e2e8f0', fontSize: '1.05rem', fontWeight: 600, lineHeight: '1.5' }}>
                    {d.briefing.summary}
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
                  {[
                    {
                      icon: <FileText size={18} color="#818cf8" />,
                      title: 'Ward Health',
                      content: d.briefing.sections.header,
                      borderColor: '#818cf8',
                    },
                    {
                      icon: <TrendingUp size={18} color="#a78bfa" />,
                      title: "What's Happening",
                      content: d.briefing.sections.whats_happening,
                      borderColor: '#a78bfa',
                    },
                    {
                      icon: <AlertCircle size={18} color="#fb7185" />,
                      title: 'Forecast',
                      content: d.briefing.sections.forecast,
                      borderColor: '#fb7185',
                    },
                  ].map(card => (
                    <div key={card.title} style={{
                      background: 'rgba(15, 23, 42, 0.5)',
                      border: '1px solid rgba(255,255,255,0.04)',
                      borderLeft: `5px solid ${card.borderColor}`,
                      borderRadius: 12,
                      padding: '1.1rem 1.3rem',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.6rem' }}>
                        {card.icon}
                        <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
                          {card.title}
                        </h4>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {card.content && card.content.split('\n').map((line, i) => (
                          <div key={i} style={{ display: 'flex', gap: '0.5rem' }}>
                            <span style={{ color: card.borderColor, fontSize: '1rem', lineHeight: '1.4' }}>•</span>
                            <span style={{ color: '#cbd5e1', fontSize: '0.95rem', lineHeight: '1.5' }}>
                              {line}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                <div style={{
                  background: 'rgba(15, 23, 42, 0.4)',
                  border: '1px solid rgba(255,255,255,0.05)',
                  borderRadius: 14, padding: '1.3rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <ListTodo size={20} color="#818cf8" />
                      <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
                        Action Items
                      </h4>
                    </div>
                    <span style={{
                      fontSize: '0.8rem', background: 'rgba(99,102,241,0.15)', color: '#a5b4fc',
                      padding: '0.25rem 0.75rem', borderRadius: 100, fontWeight: 700,
                    }}>
                      {d.briefing.sections.action_items ? (
                        `${d.briefing.sections.action_items.filter((_, i) => checkedActions[i]).length} / ${d.briefing.sections.action_items.length}`
                      ) : '0 / 0'}
                    </span>
                  </div>

                  {d.briefing.sections.action_items && d.briefing.sections.action_items.length > 0 && (
                    <>
                      <div style={{
                        width: '100%', height: 8, background: 'rgba(255,255,255,0.04)',
                        borderRadius: 4, marginBottom: '1rem', overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%', borderRadius: 4,
                          width: `${(d.briefing.sections.action_items.filter((_, i) => checkedActions[i]).length / d.briefing.sections.action_items.length) * 100}%`,
                          background: 'linear-gradient(90deg, #818cf8, #c084fc)',
                          transition: 'width 0.4s',
                        }} />
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.7rem' }}>
                        {d.briefing.sections.action_items.map((item, idx) => {
                          const isChecked = !!checkedActions[idx];
                          const lower = item.toLowerCase();
                          const isEmergency = lower.includes('immediately') || lower.includes('spike') || (lower.includes('low') && !lower.includes('normal'));
                          const isImportant = lower.includes('rising') || lower.includes('needs') || lower.includes('shift') || lower.includes('risk');
                          const priorityColor = isEmergency ? '#ef4444' : isImportant ? '#f59e0b' : '#3b82f6';
                          const priorityLabel = isEmergency ? 'EMERGENCY' : isImportant ? 'IMPORTANT' : 'KEEP WATCH';
                          return (
                            <div
                              key={idx}
                              onClick={() => toggleAction(idx)}
                              style={{
                                display: 'flex', alignItems: 'flex-start', gap: '0.8rem',
                                background: isChecked ? 'rgba(255,255,255,0.02)' : isEmergency ? 'rgba(239,68,68,0.06)' : 'rgba(255,255,255,0.02)',
                                border: isChecked ? '1px solid rgba(255,255,255,0.04)' : isEmergency ? '1px solid rgba(239,68,68,0.25)' : '1px solid rgba(255,255,255,0.06)',
                                borderLeft: isEmergency && !isChecked ? '4px solid #ef4444' : '4px solid transparent',
                                borderRadius: 10, padding: '0.9rem 1rem',
                                cursor: 'pointer', transition: 'all 0.15s',
                                opacity: isChecked ? 0.4 : 1,
                              }}
                            >
                              <div style={{
                                width: 22, height: 22, borderRadius: 6, flexShrink: 0, marginTop: '0.05rem',
                                border: isChecked ? '1px solid #10b981' : '1px solid #64748b',
                                background: isChecked ? '#10b981' : 'transparent',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                              }}>
                                {isChecked && (
                                  <svg width="12" height="10" viewBox="0 0 10 8" fill="none">
                                    <path d="M1.5 4L3.8 6.3L8.5 1.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                  </svg>
                                )}
                              </div>
                              <div style={{ flex: 1 }}>
                                <div style={{
                                  fontSize: '0.95rem',
                                  color: isChecked ? '#64748b' : '#e2e8f0',
                                  textDecoration: isChecked ? 'line-through' : 'none',
                                  lineHeight: '1.5',
                                  fontWeight: isEmergency ? 600 : 400,
                                }}>
                                  {item}
                                </div>
                                <span style={{
                                  fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase',
                                  padding: '0.1rem 0.45rem', borderRadius: 3,
                                  background: isEmergency ? 'rgba(239,68,68,0.15)' : isImportant ? 'rgba(245,158,11,0.15)' : 'rgba(59,130,246,0.15)',
                                  color: priorityColor,
                                  display: 'inline-block', marginTop: '0.3rem',
                                }}>
                                  {priorityLabel}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
          </>
        ) : error ? (
          <div style={{ textAlign: 'center', color: '#f87171', padding: '3rem' }}>{error}</div>
        ) : null}
      </main>
    </div>
  );
};

export default CouncillorPortal;
