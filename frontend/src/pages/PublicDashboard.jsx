import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { Hexagon, MapPin, Search, Smartphone, AlertCircle, CheckCircle, TrendingUp, ShieldCheck, MessageSquare, ExternalLink } from 'lucide-react';
import API_BASE from '../config';

const LABEL_COLORS = {
  'Good': { bg: 'rgba(34,197,94,0.15)', text: '#4ade80' },
  'Moderate': { bg: 'rgba(245,158,11,0.15)', text: '#fbbf24' },
  'Poor': { bg: 'rgba(239,68,68,0.15)', text: '#f87171' },
  'No Data': { bg: 'rgba(100,116,139,0.15)', text: '#94a3b8' },
};

const PublicDashboard = () => {
  const [wards, setWards] = useState([]);
  const [summary, setSummary] = useState(null);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [trackId, setTrackId] = useState('');
  const [trackResult, setTrackResult] = useState(null);
  const [trackError, setTrackError] = useState('');

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/public/wards/`).then(r => r.json()),
      fetch(`${API_BASE}/public/summary/`).then(r => r.json()),
      fetch(`${API_BASE}/public/config/`).then(r => r.json()),
    ]).then(([w, s, c]) => {
      setWards(w);
      setSummary(s);
      setConfig(c);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleTrack = async () => {
    if (!trackId.trim()) return;
    setTrackError('');
    setTrackResult(null);
    try {
      const res = await fetch(`${API_BASE}/complaints/${trackId.trim()}/`);
      if (!res.ok) { setTrackError('Complaint not found. Check the ID and try again.'); return; }
      setTrackResult(await res.json());
    } catch {
      setTrackError('Could not fetch complaint. Please try again.');
    }
  };

  const statusBadge = (status) => {
    const colors = {
      open: { bg: 'rgba(239,68,68,0.2)', text: '#f87171' },
      in_progress: { bg: 'rgba(245,158,11,0.2)', text: '#fbbf24' },
      resolved: { bg: 'rgba(34,197,94,0.2)', text: '#4ade80' },
    };
    const c = colors[status] || { bg: 'rgba(100,116,139,0.2)', text: '#94a3b8' };
    return <span style={{ padding: '0.15rem 0.5rem', borderRadius: 100, fontSize: '0.72rem', fontWeight: 700, background: c.bg, color: c.text }}>{status.replace('_', ' ')}</span>;
  };

  return (
    <div style={{ minHeight: '100vh', background: '#050a18', color: '#f8fafc' }}>
      {/* Navbar */}
      <nav className="navbar" style={{ background: 'rgba(5,10,24,0.9)' }}>
        <Link to="/" className="nav-brand" style={{ textDecoration: 'none' }}>
          <Hexagon className="nav-icon" size={24} />
          <span className="nav-title">UrbanIQ</span>
        </Link>
        <div className="nav-links">
          <Link to="/" style={{ color: '#94a3b8' }}>Home</Link>
          <span style={{ color: '#818cf8', fontWeight: 700 }}>Public Dashboard</span>
          <Link to="/complaints-map" style={{ color: '#94a3b8' }}>Complaint Map</Link>
        </div>
      </nav>

      <main style={{ maxWidth: 1000, margin: '0 auto', padding: 'calc(2rem + 60px) 1rem 2rem' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: '#94a3b8' }}>Loading...</div>
        ) : (
          <>
            {/* City Summary */}
            {summary && (
              <div style={{
                background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)',
                borderRadius: 16, padding: '1.5rem 2rem', marginBottom: '2rem',
              }}>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <TrendingUp size={18} color="#818cf8" /> Mumbai City Overview
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Total Complaints</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 900, color: '#818cf8' }}>{summary.total_complaints?.toLocaleString()}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Avg Health Score</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 900, color: summary.average_health_score >= 70 ? '#4ade80' : '#fbbf24' }}>{summary.average_health_score ?? '—'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Best Ward</div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: '#4ade80' }}>{summary.best_ward?.ward || '—'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Needs Attention</div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f87171' }}>{summary.worst_ward?.ward || '—'}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Complaint Map CTA */}
            <Link to="/complaints-map" style={{ textDecoration: 'none', display: 'block', marginBottom: '1.5rem' }}>
              <div style={{
                background: 'linear-gradient(135deg, rgba(129,140,248,0.12), rgba(6,182,212,0.08))',
                border: '1px solid rgba(129,140,248,0.2)', borderRadius: 16, padding: '1.25rem 1.5rem',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              }}>
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: '#f1f5f9' }}>
                    <MapPin size={18} color="#818cf8" style={{ verticalAlign: 'middle', marginRight: 6 }} />
                    Explore Complaint Map
                  </h3>
                  <p style={{ color: '#94a3b8', fontSize: '0.82rem', margin: '0.3rem 0 0' }}>
                    See all civic complaints across Mumbai wards on an interactive map with filters
                  </p>
                </div>
                <span style={{
                  padding: '0.4rem 1rem', borderRadius: 8, background: '#818cf8', color: '#fff',
                  fontSize: '0.82rem', fontWeight: 600, whiteSpace: 'nowrap',
                }}>View Map →</span>
              </div>
            </Link>

            {/* Ward Health Grid */}
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <ShieldCheck size={18} color="#818cf8" /> Ward Health
            </h2>
            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.75rem', marginBottom: '2rem',
            }}>
              {wards.map(w => {
                const lc = LABEL_COLORS[w.health_label] || LABEL_COLORS['No Data'];
                return (
                  <div key={w.ward_name} style={{
                    background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(99,102,241,0.08)',
                    borderRadius: 12, padding: '1rem',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{w.ward_name}</span>
                      <span style={{ fontSize: '0.72rem', padding: '0.15rem 0.5rem', borderRadius: 100, fontWeight: 700, background: lc.bg, color: lc.text }}>{w.health_label}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: '#94a3b8' }}>
                      <span>{w.total_complaints?.toLocaleString()} complaints</span>
                      <span>{w.avg_resolution_days ? `${w.avg_resolution_days}d avg` : '—'}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Track Complaint */}
            <div style={{
              background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)',
              borderRadius: 16, padding: '1.5rem 2rem', marginBottom: '2rem',
            }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Search size={18} color="#818cf8" /> Track a Complaint
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1rem' }}>
                Enter your complaint ID to check its current status.
              </p>
              <div style={{ display: 'flex', gap: '0.5rem', maxWidth: 400 }}>
                <input
                  type="text"
                  placeholder="Complaint ID (e.g. 42)"
                  value={trackId}
                  onChange={e => setTrackId(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleTrack()}
                  style={{
                    flex: 1, padding: '0.6rem 0.75rem', borderRadius: 8, border: '1px solid #334155',
                    background: '#0f172a', color: '#f8fafc', fontSize: '0.9rem', outline: 'none',
                  }}
                />
                <button onClick={handleTrack} style={{
                  padding: '0.6rem 1.25rem', borderRadius: 8, border: 'none',
                  background: '#818cf8', color: '#fff', fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem',
                }}>Track</button>
              </div>
              {trackError && <p style={{ color: '#f87171', fontSize: '0.82rem', marginTop: '0.5rem' }}><AlertCircle size={14} style={{ verticalAlign: 'middle', marginRight: '0.3rem' }} />{trackError}</p>}
              {trackResult && (
                <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(5,10,24,0.5)', borderRadius: 10, fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700 }}>#{trackResult.id} — {trackResult.category}</span>
                    {statusBadge(trackResult.status)}
                  </div>
                  <p style={{ color: '#94a3b8', margin: '0 0 0.3rem' }}>{trackResult.description}</p>
                  <p style={{ color: '#64748b', fontSize: '0.78rem', margin: 0 }}>
                    <MapPin size={12} style={{ verticalAlign: 'middle' }} /> {trackResult.ward_name} · {new Date(trackResult.created_at).toLocaleDateString()}
                  </p>
                </div>
              )}
            </div>

            {/* File via WhatsApp */}
            <div style={{
              background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)',
              borderRadius: 16, padding: '1.5rem 2rem',
            }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <MessageSquare size={18} color="#25D366" /> File a Complaint via WhatsApp
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1rem' }}>
                Scan the QR code or save our number to file a complaint in minutes.
              </p>
              <div style={{
                display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap',
                padding: '1rem', background: 'rgba(37,211,102,0.05)', borderRadius: 10,
                border: '1px solid rgba(37,211,102,0.15)',
              }}>
                {config?.whatsapp_link && (
                  <a href={config.whatsapp_link} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', flexShrink: 0 }}>
                    <QRCodeSVG
                      value={config.whatsapp_link}
                      size={110}
                      bgColor="#ffffff"
                      fgColor="#075e54"
                      level="M"
                      style={{ borderRadius: 8 }}
                    />
                  </a>
                )}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Smartphone size={22} color="#25D366" />
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#25D366' }}>
                        {config?.whatsapp_number || 'Loading...'}
                      </div>
                      <div style={{ color: '#94a3b8', fontSize: '0.8rem' }}>
                        Tap the QR code or save this number to start.
                      </div>
                    </div>
                  </div>
                  {config?.whatsapp_link && (
                    <a
                      href={config.whatsapp_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
                        marginTop: '0.6rem', padding: '0.4rem 0.9rem', borderRadius: 8,
                        background: '#25D366', color: '#fff', fontWeight: 700,
                        fontSize: '0.8rem', textDecoration: 'none',
                      }}
                    >
                      <ExternalLink size={14} /> Open WhatsApp
                    </a>
                  )}
                </div>
              </div>
              <div style={{ marginTop: '1rem', fontSize: '0.82rem', color: '#64748b' }}>
                <strong style={{ color: '#94a3b8' }}>How it works:</strong>
                <ol style={{ margin: '0.3rem 0 0', paddingLeft: '1.2rem', lineHeight: 1.8 }}>
                  <li>Send the category of your issue (e.g. "Pothole")</li>
                  <li>Describe the problem briefly</li>
                  <li>Send a photo (optional)</li>
                  <li>Share your location — done!</li>
                </ol>
                <p style={{ marginTop: '0.5rem', color: '#64748b' }}>You'll receive a complaint ID to track progress.</p>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default PublicDashboard;
