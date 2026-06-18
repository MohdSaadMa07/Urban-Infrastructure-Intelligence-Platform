import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Hexagon, LogOut, Filter, AlertCircle, CheckCircle, Clock,
  MapPin, BarChart3, TrendingUp, RefreshCw
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

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

  const fetchDashboard = async (status) => {
    setLoading(true);
    let url = '/api/councillor/dashboard/';
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
      const res = await fetch(`/api/complaints/${complaintId}/status/`, {
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

            {/* --- Complaint List --- */}
            <div style={{
              background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(99,102,241,0.12)',
              borderRadius: 16, overflow: 'hidden',
            }}>
              {/* Filter bar */}
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '1rem 1.5rem', borderBottom: '1px solid rgba(99,102,241,0.08)',
                background: 'rgba(5,10,24,0.3)',
              }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
                  Ward Complaints
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
                          <td style={{ padding: '0.85rem 1.25rem', verticalAlign: 'top', color: '#cbd5e1' }}>{c.category}</td>
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
          </>
        ) : error ? (
          <div style={{ textAlign: 'center', color: '#f87171', padding: '3rem' }}>{error}</div>
        ) : null}
      </main>
    </div>
  );
};

export default CouncillorPortal;
