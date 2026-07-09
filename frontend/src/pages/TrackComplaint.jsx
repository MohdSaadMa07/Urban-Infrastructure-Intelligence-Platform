import React, { useState } from 'react';
import { Search, Hexagon, CheckCircle, Clock, AlertCircle, LogIn, UserPlus, User as UserIcon, LogOut } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE from '../config';

const TrackComplaint = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [complaintId, setComplaintId] = useState('');
  const [status, setStatus] = useState('idle'); // idle | loading | found | error
  const [data, setData] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!complaintId.trim()) return;

    setStatus('loading');
    setErrorMsg('');

    try {
      const res = await fetch(`${API_BASE}/complaints/${complaintId.trim()}/`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
        setStatus('found');
      } else if (res.status === 404) {
        setStatus('error');
        setErrorMsg(`We couldn't find a complaint with ID #${complaintId}`);
      } else {
        setStatus('error');
        setErrorMsg('An error occurred. Please try again later.');
      }
    } catch {
      setStatus('error');
      setErrorMsg('Network error. Please check your connection.');
    }
  };

  const getStatusIcon = (st) => {
    switch (st) {
      case 'resolved': return <CheckCircle size={32} color="#22c55e" />;
      case 'in_progress': return <Clock size={32} color="#f59e0b" />;
      case 'open': return <AlertCircle size={32} color="#ef4444" />;
      default: return <AlertCircle size={32} color="#64748b" />;
    }
  };

  const getStatusLabel = (st) => {
    switch (st) {
      case 'resolved': return 'Resolved';
      case 'in_progress': return 'In Progress';
      case 'open': return 'Open';
      default: return 'Unknown';
    }
  };

  return (
    <div className="track-page" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <nav className="navbar" id="navbar">
        <Link to="/" className="nav-brand" style={{ textDecoration: 'none' }}>
          <Hexagon className="nav-icon" size={24} />
          <span className="nav-title">UrbanIQ</span>
        </Link>
        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/dashboard">Dashboard</Link>
        </div>
        <div className="nav-auth">
          {isAuthenticated ? (
            <>
              <Link to="/dashboard" className="nav-auth-user">
                <UserIcon size={16} />
                <span className="nav-auth-name">{user.username}</span>
              </Link>
              <button className="nav-auth-logout" onClick={() => { logout(); navigate('/'); }} title="Logout">
                <LogOut size={16} />
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-auth-btn"><LogIn size={15} /> Sign In</Link>
              <Link to="/signup" className="nav-auth-btn nav-auth-btn-primary"><UserPlus size={15} /> Sign Up</Link>
            </>
          )}
        </div>
      </nav>

      <main style={{ flex: 1, padding: '6rem 2rem 4rem', display: 'flex', justifyContent: 'center' }}>
        <div style={{ maxWidth: '600px', width: '100%' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h1 style={{ fontSize: '2.5rem', fontWeight: '700', marginBottom: '1rem', color: '#f8fafc' }}>
              Track Your Complaint
            </h1>
            <p style={{ color: '#94a3b8', fontSize: '1.125rem' }}>
              Enter your complaint reference ID to check its current status.
            </p>
          </div>

          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '1rem', marginBottom: '3rem' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <Search size={20} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
              <input
                type="text"
                placeholder="e.g. 124"
                value={complaintId}
                onChange={(e) => setComplaintId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '1rem 1rem 1rem 3rem',
                  borderRadius: '12px',
                  border: '1px solid #334155',
                  background: '#1e293b',
                  color: '#f8fafc',
                  fontSize: '1.125rem',
                  outline: 'none'
                }}
              />
            </div>
            <button
              type="submit"
              disabled={status === 'loading'}
              style={{
                background: '#4f46e5',
                color: 'white',
                border: 'none',
                padding: '0 2rem',
                borderRadius: '12px',
                fontSize: '1.125rem',
                fontWeight: '600',
                cursor: status === 'loading' ? 'not-allowed' : 'pointer',
                opacity: status === 'loading' ? 0.7 : 1,
              }}
            >
              {status === 'loading' ? 'Searching...' : 'Track'}
            </button>
          </form>

          {status === 'error' && (
            <div style={{ background: '#451a1a', border: '1px solid #ef4444', padding: '1rem', borderRadius: '12px', color: '#fecaca', textAlign: 'center' }}>
              {errorMsg}
            </div>
          )}

          {status === 'found' && data && (
            <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '16px', padding: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#f8fafc', margin: '0 0 0.5rem 0' }}>
                    Complaint #{data.id}
                  </h2>
                  <p style={{ color: '#94a3b8', margin: 0 }}>
                    Filed on {new Date(data.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#0f172a', padding: '0.75rem 1rem', borderRadius: '12px' }}>
                  {getStatusIcon(data.status)}
                  <span style={{ fontWeight: '600', color: '#f8fafc' }}>
                    {getStatusLabel(data.status)}
                  </span>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                <div>
                  <div style={{ color: '#64748b', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Category</div>
                  <div style={{ color: '#f8fafc', fontWeight: '500' }}>{data.category}</div>
                </div>
                <div>
                  <div style={{ color: '#64748b', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Ward</div>
                  <div style={{ color: '#f8fafc', fontWeight: '500' }}>Ward {data.ward_name} (No. {data.ward_no})</div>
                </div>
              </div>

              {data.image && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <div style={{ color: '#64748b', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Photo</div>
                  <img
                    src={data.image}
                    alt=""
                    style={{ width: '100%', maxHeight: 300, objectFit: 'cover', borderRadius: 12, border: '1px solid #334155' }}
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                </div>
              )}
              <div>
                <div style={{ color: '#64748b', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Description</div>
                <div style={{ color: '#e2e8f0', lineHeight: '1.6', background: '#0f172a', padding: '1rem', borderRadius: '8px' }}>
                  {data.description}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default TrackComplaint;
