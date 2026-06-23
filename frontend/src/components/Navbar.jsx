import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Hexagon, LogIn, LogOut, UserPlus, UserIcon, Megaphone, ChevronDown, Menu, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

function NavAuthActions({ onAction }) {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  if (isAuthenticated) {
    const roleLabel = user?.profile?.role === 'councillor' ? 'Councillor'
      : user?.profile?.role === 'admin' ? 'Admin' : 'Citizen';
    return (
      <div className="nav-auth">
        <Link to={user?.profile?.role === 'admin' ? '/admin-portal' : user?.profile?.role === 'councillor' ? '/councillor-portal' : '/dashboard'} className="nav-auth-user">
          <UserIcon size={16} />
          <span className="nav-auth-name">{user.username}</span>
          <span className="nav-auth-role">{roleLabel}</span>
        </Link>
        <button className="nav-auth-logout" onClick={() => { logout(); navigate('/'); if (onAction) onAction(); }} title="Logout">
          <LogOut size={16} />
        </button>
      </div>
    );
  }

  return (
    <div className="nav-auth">
      <Link to="/login" className="nav-auth-btn" onClick={onAction}>
        <LogIn size={15} /> Sign In
      </Link>
      <Link to="/signup" className="nav-auth-btn nav-auth-btn-primary" onClick={onAction}>
        <UserPlus size={15} /> Sign Up
      </Link>
    </div>
  );
}

function MoreDropdown({ open, onToggle, onClose }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) onClose(); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open, onClose]);

  return (
    <div className="nav-more" ref={ref}>
      <button className="nav-more-btn" onClick={onToggle}>
        More <ChevronDown size={14} style={{ marginLeft: 2 }} />
      </button>
      {open && (
        <div className="nav-more-dropdown">
          <Link to="/complaints-map" onClick={onClose}><span className="nav-more-icon">🗺️</span> Complaint Map</Link>
          <Link to="/dashboard" onClick={onClose}><span className="nav-more-icon">📊</span> Dashboard</Link>
          <Link to="/track" onClick={onClose}><span className="nav-more-icon">🔍</span> Track Issue</Link>
          <Link to="/public" onClick={onClose}><span className="nav-more-icon">📈</span> Public Dashboard</Link>
          <a href="#accountability" onClick={onClose}><span className="nav-more-icon">📋</span> Accountability</a>
        </div>
      )}
    </div>
  );
}

export default function Navbar({ showReportBtn, onReportClick, onNavAction }) {
  const { isAuthenticated, user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);

  const roleDashboard = user?.profile?.role === 'councillor' ? '/councillor-portal'
    : user?.profile?.role === 'admin' ? '/admin-portal' : '/dashboard';

  return (
    <nav className="navbar" id="navbar">
      <Link to="/" className="nav-brand" style={{ textDecoration: 'none' }}>
        <Hexagon className="nav-icon" size={24} />
        <span className="nav-title">UrbanIQ</span>
        <span className="nav-tagline">Mumbai Civic Intelligence</span>
      </Link>

      <div className={`nav-links ${mobileOpen ? 'nav-links-open' : ''}`}>
        <a href="#problem" onClick={() => setMobileOpen(false)}>The Problem</a>
        <a href="#how-it-works" onClick={() => setMobileOpen(false)}>How It Works</a>
        <a href="#features" onClick={() => setMobileOpen(false)}>Features</a>
        <a href="#map-section" onClick={() => setMobileOpen(false)}>Live Map</a>

        <MoreDropdown
          open={moreOpen}
          onToggle={() => setMoreOpen(v => !v)}
          onClose={() => setMoreOpen(false)}
        />

        {isAuthenticated && (
          <Link to={roleDashboard} className={`nav-link-emphasis ${mobileOpen ? '' : 'nav-link-desktop-hide'}`} onClick={() => setMobileOpen(false)}>
            Dashboard
          </Link>
        )}

        <div className="nav-mobile-auth">
          <NavAuthActions onAction={() => setMobileOpen(false)} />
        </div>
      </div>

      <div className="nav-right">
        <NavAuthActions />
        {showReportBtn && (
          <button
            id="report-issue-btn"
            className="btn-report"
            onClick={onReportClick}
          >
            <Megaphone size={15} /> Report
          </button>
        )}
        <button className="nav-mobile-toggle" onClick={() => setMobileOpen(v => !v)} aria-label="Toggle menu">
          {mobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>
    </nav>
  );
}

export { NavAuthActions };
