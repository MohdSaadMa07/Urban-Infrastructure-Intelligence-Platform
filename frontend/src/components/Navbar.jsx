import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Hexagon, LogIn, LogOut, UserPlus, UserIcon, Megaphone, Menu, X } from 'lucide-react';
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

export default function Navbar({ showReportBtn, onReportClick }) {
  const { isAuthenticated, user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const closeMobile = () => setMobileOpen(false);

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
        <a href="/#map-section" onClick={closeMobile}>Live Map</a>
        <Link to="/complaints-map" onClick={closeMobile}>Complaint Map</Link>
        <Link to="/dashboard" onClick={closeMobile}>Dashboard</Link>
        <Link to="/public" onClick={closeMobile}>City Summary</Link>
        <a href="/#features" onClick={closeMobile}>Features</a>

        <div className="nav-mobile-auth">
          <NavAuthActions onAction={closeMobile} />
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
