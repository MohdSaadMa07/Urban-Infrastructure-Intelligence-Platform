import React, { useState, useEffect } from 'react';
import { Hexagon, Filter, LogOut, AlertCircle, Lock } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE from '../config';

const WARDS = [
  'A', 'B', 'C', 'D', 'E', 'F/N', 'F/S', 'G/N', 'G/S',
  'H/E', 'H/W', 'K/E', 'K/W', 'L', 'M/E', 'M/W', 'N',
  'P/N', 'P/S', 'R/C', 'R/N', 'R/S', 'S', 'T'
];

const AdminPortal = () => {
  const { isAuthenticated, isAdmin, user, logout, getAccessToken, loading } = useAuth();
  const navigate = useNavigate();

  const [complaints, setComplaints] = useState([]);
  const [fetchLoading, setFetchLoading] = useState(true);
  const [wardFilter, setWardFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [error, setError] = useState('');

  const fetchComplaints = async () => {
    setFetchLoading(true);
    let url = `${API_BASE}/complaints/`;
    if (wardFilter) url += `?ward=${wardFilter}`;

    try {
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${getAccessToken()}` },
      });
      const data = await res.json();
      setComplaints(data);
    } catch (err) {
      console.error(err);
    }
    setFetchLoading(false);
  };

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated) {
        navigate('/login', { state: { from: '/admin-portal' } });
        return;
      }
      if (!isAdmin) {
        setError('Access denied. Admin privileges required.');
        setFetchLoading(false);
        return;
      }
      fetchComplaints();
    }
  }, [isAuthenticated, isAdmin, loading, wardFilter]);

  const handleStatusChange = async (id, newStatus) => {
    try {
      const res = await fetch(`${API_BASE}/complaints/${id}/status/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        setComplaints(prev => prev.map(c => c.id === id ? { ...c, status: newStatus } : c));
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

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a' }}>
        <div className="dash-spinner" />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#0f172a', gap: '1rem' }}>
        <AlertCircle size={48} color="#ef4444" />
        <h2 style={{ color: '#f8fafc' }}>Access Denied</h2>
        <p style={{ color: '#94a3b8' }}>{error}</p>
        <Link to="/" style={{ color: '#818cf8' }}>Back to Home</Link>
      </div>
    );
  }

  const filteredComplaints = complaints.filter(c => statusFilter === 'all' || c.status === statusFilter);

  return (
    <div className="admin-page" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#0f172a' }}>
      <nav className="navbar" style={{ position: 'sticky', top: 0, zIndex: 10, background: 'rgba(15, 23, 42, 0.9)' }}>
        <Link to="/" className="nav-brand" style={{ textDecoration: 'none' }}>
          <Hexagon className="nav-icon" size={24} />
          <span className="nav-title">UrbanIQ Admin</span>
        </Link>
        <div className="nav-links">
          <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>{user?.username}</span>
          <Link to="/">Back to Public Site</Link>
          <button onClick={handleLogout} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <LogOut size={14} /> Logout
          </button>
        </div>
      </nav>

      <main style={{ padding: '2rem', flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1 style={{ color: '#f8fafc', margin: 0 }}>Complaint Management</h1>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#1e293b', padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <Filter size={16} color="#94a3b8" />
              <select
                value={wardFilter}
                onChange={e => setWardFilter(e.target.value)}
                style={{ background: 'transparent', border: 'none', color: '#f8fafc', outline: 'none' }}
              >
                <option value="">All Wards</option>
                {WARDS.map(w => <option key={w} value={w}>Ward {w}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#1e293b', padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <Filter size={16} color="#94a3b8" />
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                style={{ background: 'transparent', border: 'none', color: '#f8fafc', outline: 'none' }}
              >
                <option value="all">All Statuses</option>
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>
          </div>
        </div>

        {fetchLoading ? (
          <div style={{ textAlign: 'center', color: '#94a3b8', padding: '3rem' }}>Loading complaints...</div>
        ) : filteredComplaints.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#94a3b8', padding: '3rem', background: '#1e293b', borderRadius: '16px' }}>No complaints found matching your criteria.</div>
        ) : (
          <div style={{ background: '#1e293b', borderRadius: '16px', border: '1px solid #334155', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', color: '#e2e8f0' }}>
              <thead>
                <tr style={{ background: '#0f172a', borderBottom: '1px solid #334155' }}>
                  <th style={{ padding: '1rem' }}>ID & Date</th>
                  <th style={{ padding: '1rem' }}>Photo</th>
                  <th style={{ padding: '1rem' }}>Category</th>
                  <th style={{ padding: '1rem' }}>Ward</th>
                  <th style={{ padding: '1rem' }}>Description</th>
                  <th style={{ padding: '1rem' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredComplaints.map(c => (
                  <tr key={c.id} style={{ borderBottom: '1px solid #334155' }}>
                    <td style={{ padding: '1rem', verticalAlign: 'top' }}>
                      <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>#{c.id}</div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{new Date(c.created_at).toLocaleDateString()}</div>
                    </td>
                    <td style={{ padding: '1rem', verticalAlign: 'top' }}>
                      {c.image ? (
                        <img
                          src={c.image}
                          alt=""
                          style={{ width: 56, height: 56, objectFit: 'cover', borderRadius: 8, border: '1px solid #334155', cursor: 'pointer' }}
                          onClick={() => window.open(c.image, '_blank')}
                          onError={(e) => { e.target.style.display = 'none'; }}
                        />
                      ) : (
                        <span style={{ color: '#334155' }}>--</span>
                      )}
                    </td>
                    <td style={{ padding: '1rem', verticalAlign: 'top' }}>{c.category}</td>
                    <td style={{ padding: '1rem', verticalAlign: 'top' }}>{c.ward_name} ({c.ward_no})</td>
                    <td style={{ padding: '1rem', verticalAlign: 'top', maxWidth: '300px' }}>
                      <div style={{ fontSize: '0.875rem', lineHeight: '1.4' }}>{c.description}</div>
                      {(c.latitude && c.longitude) && (
                        <div style={{ fontSize: '0.75rem', color: '#818cf8', marginTop: '0.5rem' }}>
                          Lat: {c.latitude}, Lng: {c.longitude}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '1rem', verticalAlign: 'top' }}>
                      <select
                        value={c.status}
                        onChange={(e) => handleStatusChange(c.id, e.target.value)}
                        style={{
                          background: c.status === 'resolved' ? 'rgba(34, 197, 94, 0.2)' : c.status === 'in_progress' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                          color: c.status === 'resolved' ? '#4ade80' : c.status === 'in_progress' ? '#fbbf24' : '#f87171',
                          border: `1px solid ${c.status === 'resolved' ? '#22c55e' : c.status === 'in_progress' ? '#f59e0b' : '#ef4444'}`,
                          padding: '0.5rem',
                          borderRadius: '8px',
                          outline: 'none',
                          cursor: 'pointer',
                          fontWeight: 'bold'
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
      </main>
    </div>
  );
};

export default AdminPortal;
