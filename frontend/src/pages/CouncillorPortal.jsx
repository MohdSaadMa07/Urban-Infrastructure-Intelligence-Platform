import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Hexagon, LogOut, Filter, AlertCircle, CheckCircle, Clock,
  MapPin, BarChart3, TrendingUp, RefreshCw, Sparkles, ListTodo, FileText
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
  const [checkedActions, setCheckedActions] = useState({});
  const [hoveredAction, setHoveredAction] = useState(null);
  const [hoveredBriefCard, setHoveredBriefCard] = useState(null);

  const toggleAction = (idx) => {
    setCheckedActions(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

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

            {/* --- ML Insights / Forecast Card --- */}
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
                    AI Infrastructure Forecast & Insights
                  </h3>
                  <span style={{ fontSize: '0.72rem', color: '#64748b', marginLeft: 'auto', fontFamily: 'monospace' }}>
                    Model: {d.predictions.model_version}
                  </span>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 0.7fr', gap: '1.5rem', flexWrap: 'wrap' }}>
                  {/* Left column: Metrics */}
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
                        For next year (2027)
                      </div>
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

                  {/* Right column: AI Recommendation */}
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

            {/* --- AI Ward Briefing & Action Plan --- */}
            {d.briefing && !d.briefing.error && (
              <div style={{
                background: 'linear-gradient(135deg, rgba(10, 15, 30, 0.9) 0%, rgba(20, 25, 45, 0.8) 100%)',
                border: '1px solid rgba(129, 140, 248, 0.25)',
                borderRadius: 20,
                padding: '2.2rem',
                marginBottom: '2rem',
                boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
                position: 'relative',
                overflow: 'hidden'
              }}>
                {/* Glow effects */}
                <div style={{
                  position: 'absolute',
                  top: '-80px',
                  right: '-80px',
                  width: '200px',
                  height: '200px',
                  background: 'rgba(99, 102, 241, 0.18)',
                  filter: 'blur(60px)',
                  borderRadius: '50%',
                  pointerEvents: 'none'
                }} />
                <div style={{
                  position: 'absolute',
                  bottom: '-80px',
                  left: '-80px',
                  width: '200px',
                  height: '200px',
                  background: 'rgba(168, 85, 247, 0.1)',
                  filter: 'blur(60px)',
                  borderRadius: '50%',
                  pointerEvents: 'none'
                }} />

                {/* Header */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '1rem',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                  paddingBottom: '1.25rem',
                  marginBottom: '1.75rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                    <div style={{
                      background: 'linear-gradient(135deg, #818cf8 0%, #4f46e5 100%)',
                      borderRadius: 12,
                      padding: '0.6rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 0 20px rgba(99, 102, 241, 0.45)'
                    }}>
                      <Sparkles size={20} color="#ffffff" style={{ animation: 'pulse 2s infinite' }} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1.35rem', fontWeight: 900, color: '#f8fafc', margin: 0, letterSpacing: '0.02em', background: 'linear-gradient(90deg, #f8fafc 0%, #cbd5e1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                        AI Ward Briefing & Action Plan
                      </h3>
                      <p style={{ color: '#64748b', fontSize: '0.8rem', margin: '0.2rem 0 0 0', fontWeight: 500 }}>
                        Synthesized on {new Date(d.briefing.generated_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
                      </p>
                    </div>
                  </div>

                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.45rem',
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.25)',
                    padding: '0.35rem 0.75rem',
                    borderRadius: 100
                  }}>
                    <span style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: '#10b981',
                      boxShadow: '0 0 8px #10b981',
                      display: 'inline-block'
                    }} />
                    <span style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#34d399' }}>
                      Live ML Analysis
                    </span>
                  </div>
                </div>

                {/* Executive Summary Banner */}
                <div style={{
                  background: 'rgba(99, 102, 241, 0.05)',
                  borderLeft: '4px solid #818cf8',
                  padding: '1rem 1.25rem',
                  borderRadius: '0 12px 12px 0',
                  marginBottom: '1.75rem',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                }}>
                  <div style={{ fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', color: '#818cf8', letterSpacing: '0.08em', marginBottom: '0.25rem' }}>
                    Executive Summary
                  </div>
                  <div style={{ color: '#e2e8f0', fontSize: '0.92rem', fontWeight: 600, lineHeight: '1.45' }}>
                    {d.briefing.summary}
                  </div>
                </div>

                {/* Grid Layout */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1.2fr 0.8fr',
                  gap: '2.2rem',
                  alignItems: 'start'
                }}>
                  
                  {/* Left Column: Briefing Sections */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {[
                      {
                        id: 'overview',
                        icon: <FileText size={16} color="#818cf8" />,
                        title: 'Ward Overview & Health',
                        content: d.briefing.sections.header,
                        borderLeftColor: '#818cf8',
                        glowColor: 'rgba(99, 102, 241, 0.08)',
                      },
                      {
                        id: 'happening',
                        icon: <TrendingUp size={16} color="#a78bfa" />,
                        title: "What's Happening (Trends & Anomalies)",
                        content: d.briefing.sections.whats_happening,
                        borderLeftColor: '#a78bfa',
                        glowColor: 'rgba(167, 139, 250, 0.08)',
                      },
                      {
                        id: 'forecast',
                        icon: <AlertCircle size={16} color="#fb7185" />,
                        title: 'Infrastructure Risk Forecast',
                        content: d.briefing.sections.forecast,
                        borderLeftColor: '#fb7185',
                        glowColor: 'rgba(251, 113, 133, 0.08)',
                      }
                    ].map(card => {
                      const isHovered = hoveredBriefCard === card.id;
                      return (
                        <div
                          key={card.id}
                          onMouseEnter={() => setHoveredBriefCard(card.id)}
                          onMouseLeave={() => setHoveredBriefCard(null)}
                          style={{
                            background: 'rgba(15, 23, 42, 0.45)',
                            border: '1px solid rgba(255, 255, 255, 0.05)',
                            borderLeft: `5px solid ${card.borderLeftColor}`,
                            borderRadius: 14,
                            padding: '1.35rem',
                            transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
                            transform: isHovered ? 'translateY(-2px)' : 'none',
                            boxShadow: isHovered ? `0 10px 20px ${card.glowColor}` : 'none',
                            backdropFilter: 'blur(10px)'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' }}>
                            <div style={{
                              background: 'rgba(255, 255, 255, 0.03)',
                              borderRadius: 8,
                              padding: '0.35rem',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}>
                              {card.icon}
                            </div>
                            <h4 style={{ fontSize: '0.85rem', fontWeight: 800, color: isHovered ? '#f8fafc' : '#e2e8f0', margin: 0, textTransform: 'uppercase', letterSpacing: '0.06em', transition: 'color 0.2s' }}>
                              {card.title}
                            </h4>
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                            {card.content && card.content.split('\n').map((line, lineIdx) => (
                              <div key={lineIdx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                                <span style={{ color: card.borderLeftColor, fontSize: '1rem', lineHeight: '1.3', userSelect: 'none' }}>•</span>
                                <span style={{ color: '#94a3b8', fontSize: '0.86rem', lineHeight: '1.5', fontWeight: 400 }}>
                                  {line}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Right Column: AI Action Plan */}
                  <div style={{
                    background: 'rgba(15, 23, 42, 0.35)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    borderRadius: 18,
                    padding: '1.6rem',
                    boxShadow: 'inset 0 4px 15px rgba(0, 0, 0, 0.35)',
                    backdropFilter: 'blur(12px)',
                    position: 'relative'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                        <ListTodo size={18} color="#818cf8" style={{ filter: 'drop-shadow(0 0 5px rgba(129, 140, 248, 0.4))' }} />
                        <h4 style={{ fontSize: '0.98rem', fontWeight: 900, color: '#f8fafc', margin: 0, letterSpacing: '0.01em' }}>
                          Action Items
                        </h4>
                      </div>
                      <span style={{
                        fontSize: '0.72rem',
                        background: 'rgba(99, 102, 241, 0.15)',
                        border: '1px solid rgba(99, 102, 241, 0.2)',
                        color: '#a5b4fc',
                        padding: '0.2rem 0.6rem',
                        borderRadius: 100,
                        fontWeight: 700,
                        letterSpacing: '0.02em'
                      }}>
                        {d.briefing.sections.action_items ? (
                          `${d.briefing.sections.action_items.filter((_, i) => checkedActions[i]).length} / ${d.briefing.sections.action_items.length}`
                        ) : '0 / 0'}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    {d.briefing.sections.action_items && d.briefing.sections.action_items.length > 0 && (
                      <div style={{
                        width: '100%',
                        height: 7,
                        background: 'rgba(255, 255, 255, 0.04)',
                        borderRadius: 4,
                        marginBottom: '1.5rem',
                        overflow: 'hidden',
                        border: '1px solid rgba(255, 255, 255, 0.02)'
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${(d.briefing.sections.action_items.filter((_, i) => checkedActions[i]).length / d.briefing.sections.action_items.length) * 100}%`,
                          background: 'linear-gradient(90deg, #818cf8 0%, #c084fc 100%)',
                          borderRadius: 4,
                          boxShadow: '0 0 10px rgba(129, 140, 248, 0.5)',
                          transition: 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
                        }} />
                      </div>
                    )}

                    {/* Tasks List */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                      {d.briefing.sections.action_items && d.briefing.sections.action_items.map((item, idx) => {
                        const isChecked = !!checkedActions[idx];
                        const isHovered = hoveredAction === idx;
                        
                        // Parse critical severity (e.g. Health is critical)
                        const isCritical = item.toLowerCase().includes('critical') || item.toLowerCase().includes('spike');
                        const cardBorder = isChecked 
                          ? '1px solid rgba(255, 255, 255, 0.05)' 
                          : isHovered
                            ? '1px solid rgba(99, 102, 241, 0.35)'
                            : isCritical
                              ? '1px solid rgba(239, 68, 68, 0.2)'
                              : '1px solid rgba(255, 255, 255, 0.06)';
                              
                        const cardBg = isChecked
                          ? 'rgba(255, 255, 255, 0.01)'
                          : isHovered
                            ? 'rgba(99, 102, 241, 0.06)'
                            : isCritical
                              ? 'rgba(239, 68, 68, 0.03)'
                              : 'rgba(255, 255, 255, 0.02)';

                        return (
                          <div
                            key={idx}
                            onClick={() => toggleAction(idx)}
                            onMouseEnter={() => setHoveredAction(idx)}
                            onMouseLeave={() => setHoveredAction(null)}
                            style={{
                              display: 'flex',
                              alignItems: 'flex-start',
                              gap: '0.85rem',
                              background: cardBg,
                              border: cardBorder,
                              borderRadius: 12,
                              padding: '0.85rem 1rem',
                              cursor: 'pointer',
                              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                              opacity: isChecked ? 0.45 : 1,
                              transform: (isHovered && !isChecked) ? 'scale(1.01)' : 'none',
                              boxShadow: (isHovered && !isChecked) ? '0 4px 15px rgba(0,0,0,0.15)' : 'none',
                              borderLeft: isCritical && !isChecked ? '3px solid #ef4444' : cardBorder
                            }}
                          >
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              width: 18,
                              height: 18,
                              borderRadius: 5,
                              border: isChecked ? '1px solid #10b981' : '1px solid #4b5563',
                              background: isChecked ? '#10b981' : 'transparent',
                              marginTop: '0.1rem',
                              transition: 'all 0.15s ease',
                              flexShrink: 0
                            }}>
                              {isChecked && (
                                <svg width="10" height="8" viewBox="0 0 10 8" fill="none" xmlns="http://www.w3.org/2000/svg">
                                  <path d="M1.5 4L3.8 6.3L8.5 1.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                </svg>
                              )}
                            </div>
                            <span style={{
                              color: isChecked ? '#64748b' : isCritical ? '#fda4af' : '#e2e8f0',
                              fontSize: '0.84rem',
                              lineHeight: '1.45',
                              textDecoration: isChecked ? 'line-through' : 'none',
                              userSelect: 'none',
                              fontWeight: isCritical ? 600 : 500,
                            }}>
                              {item}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                </div>
              </div>
            )}

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
