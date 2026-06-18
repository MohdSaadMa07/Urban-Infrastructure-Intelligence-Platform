import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { Map, BarChart2, Activity, ShieldCheck, Megaphone, Hexagon, ArrowDown, LogIn, UserPlus, User as UserIcon, LogOut } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import MumbaiMap from './components/MumbaiMap';
import WardDetailPanel from './components/WardDetailPanel';
import ComplaintModal from './components/ComplaintModal';
import CouncillorTable from './components/CouncillorTable';
import Dashboard from './pages/Dashboard';
import TrackComplaint from './pages/TrackComplaint';
import AdminPortal from './pages/AdminPortal';
import Login from './pages/Login';
import Signup from './pages/Signup';
import CouncillorPortal from './pages/CouncillorPortal';
import './App.css';

/* --- Navbar Auth Actions --- */
function NavAuthActions() {
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
        <button className="nav-auth-logout" onClick={() => { logout(); navigate('/'); }} title="Logout">
          <LogOut size={16} />
        </button>
      </div>
    );
  }

  return (
    <div className="nav-auth">
      <Link to="/login" className="nav-auth-btn">
        <LogIn size={15} /> Sign In
      </Link>
      <Link to="/signup" className="nav-auth-btn nav-auth-btn-primary">
        <UserPlus size={15} /> Sign Up
      </Link>
    </div>
  );
}

/* --- Landing Page --- */
function LandingPage() {
  const [selectedWard, setSelectedWard] = useState(null);
  const [showComplaintModal, setShowComplaintModal] = useState(false);
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="landing-page">
      {/* --- Navbar --- */}
      <nav className="navbar" id="navbar">
        <div className="nav-brand">
          <Hexagon className="nav-icon" size={24} />
          <span className="nav-title">UrbanIQ</span>
        </div>
        <div className="nav-links">
          <a href="#hero">Home</a>
          <a href="#problem">The Problem</a>
          <a href="#map-section">Live Map</a>
          <a href="#features">Features</a>
          <a href="#accountability">Accountability</a>
          <Link to="/track">Track Issue</Link>
          <Link to="/dashboard" id="nav-dashboard-link" className="nav-link-dashboard">
            Dashboard &gt;
          </Link>
        </div>
        <div className="nav-right">
          <NavAuthActions />
          <button
            id="report-issue-btn"
            className="btn-report"
            onClick={() => setShowComplaintModal(true)}
          >
            <Megaphone size={15} /> Report
          </button>
        </div>
      </nav>

      {/* --- Hero Section --- */}
      <section className="hero-section" id="hero">
        <div className="hero-glow hero-glow-1"></div>
        <div className="hero-glow hero-glow-2"></div>
        <div className="hero-content">
          <div className="hero-badge">Mumbai Urban Intelligence Platform</div>
          <h1 className="hero-title">
            Civic infrastructure is <span className="hero-highlight">failing silently.</span>
            <br />We make it visible.
          </h1>
          <p className="hero-subtitle">
            Every year, Mumbai's 24 wards generate over <strong>900,000 civic complaints</strong> -- 
            potholes, water leaks, garbage overflow, drainage failures. Most go unresolved for weeks.
            Our platform turns this chaos into actionable, ward-level intelligence.
          </p>
          <div className="hero-actions">
            <a href="#map-section" className="btn btn-primary">Explore the Map</a>
            <Link to="/dashboard" className="btn btn-ghost" id="hero-dashboard-btn">
              View Dashboard
            </Link>
          </div>
        </div>
        <div className="hero-scroll-hint">
          <span>Scroll to explore</span>
          <div className="scroll-arrow"><ArrowDown size={20} /></div>
        </div>
      </section>

      {/* --- Problem / Stats Section --- */}
      <section className="stats-section" id="problem">
        <div className="section-header">
          <span className="section-tag">The Problem</span>
          <h2 className="section-title">Mumbai's civic complaint crisis in numbers</h2>
          <p className="section-desc">
            Data from the Praja Foundation's annual report reveals a staggering scale of unresolved 
            infrastructure issues across the city. These numbers represent real people waiting for basic services.
          </p>
        </div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">9,44,000+</div>
            <div className="stat-label">Total complaints filed</div>
            <div className="stat-sub">across all 24 wards annually</div>
          </div>
          <div className="stat-card stat-card-warn">
            <div className="stat-number">42 days</div>
            <div className="stat-label">Average resolution time</div>
            <div className="stat-sub">some wards take over 68 days</div>
          </div>
          <div className="stat-card stat-card-danger">
            <div className="stat-number">13%</div>
            <div className="stat-label">Complaints escalated</div>
            <div className="stat-sub">unresolved at the first level</div>
          </div>
          <div className="stat-card stat-card-info">
            <div className="stat-number">24</div>
            <div className="stat-label">Administrative wards</div>
            <div className="stat-sub">with vastly different performance</div>
          </div>
        </div>
      </section>

      {/* --- Map Section --- */}
      <section className="map-section" id="map-section">
        <div className="section-header">
          <span className="section-tag">Live Intelligence</span>
          <h2 className="section-title">Ward-level infrastructure health, visualized</h2>
          <p className="section-desc">
            Each ward is color-coded by its infrastructure health score -- combining complaint burden, 
            resolution speed, and civic engagement. Hover over any ward to see detailed metrics.
            <strong> Red zones need urgent attention.</strong>
          </p>
        </div>
        <div className="map-container" id="interactive-map">
          <MumbaiMap onWardClick={setSelectedWard} />
        </div>
      </section>

      {/* --- Features / How It Helps Section --- */}
      <section className="features-section" id="features">
        <div className="section-header">
          <span className="section-tag">Why UrbanIQ</span>
          <h2 className="section-title">From raw complaints to urban intelligence</h2>
          <p className="section-desc">
            Our platform transforms scattered civic data into a unified decision-support system 
            for administrators, councillors, and citizens.
          </p>
        </div>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon"><Map size={32} color="#818cf8" /></div>
            <h3>Geospatial Analytics</h3>
            <p>
              Pinpoint infrastructure failures at the ward level. See which neighborhoods 
              are underserved and where resources should be redirected.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><BarChart2 size={32} color="#818cf8" /></div>
            <h3>Health Scoring</h3>
            <p>
              A composite score for each ward based on complaint volume, resolution speed, 
              and civic participation -- making performance comparison instant.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><Activity size={32} color="#818cf8" /></div>
            <h3>Real-time Monitoring</h3>
            <p>
              Track complaint trends as they evolve. Identify emerging hotspots before 
              they become crises with early-warning indicators.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><ShieldCheck size={32} color="#818cf8" /></div>
            <h3>Accountability Engine</h3>
            <p>
              Compare ward-level councillor activity, deliberation counts, and response 
              rates. Hold elected representatives accountable with data.
            </p>
          </div>
        </div>
      </section>

      {/* --- Councillor Accountability Section --- */}
      <section className="accountability-section" id="accountability">
        <div className="section-header">
          <span className="section-tag">Councillor Accountability</span>
          <h2 className="section-title">Who is representing Mumbai's wards?</h2>
          <p className="section-desc">
            Civic deliberations are a key measure of a councillor's engagement with their ward.
            Wards with higher per-capita deliberations have more active political representation.
            <strong> Sort by any column to find your ward.</strong>
          </p>
        </div>
        <CouncillorTable />
      </section>

      {/* --- Footer --- */}
      <footer className="site-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <Hexagon className="nav-icon" size={20} />
            <span>UrbanIQ</span>
          </div>
          <p className="footer-text">
            Built for Mumbai. Powered by open civic data from the Praja Foundation.
          </p>
          <div className="footer-links">
            <a href="#hero">Home</a>
            <a href="#problem">The Problem</a>
            <a href="#map-section">Live Map</a>
            <a href="#features">Features</a>
            <Link to="/dashboard">Dashboard</Link>
          </div>
          <div style={{ marginTop: '1rem' }}>
            <Link to="/admin-portal" style={{ color: '#818cf8', textDecoration: 'none', fontSize: '0.875rem' }}>
              Admin Portal
            </Link>
          </div>
        </div>
      </footer>

      {/* --- Ward Detail Panel --- */}
      <WardDetailPanel ward={selectedWard} onClose={() => setSelectedWard(null)} />

      {/* --- Complaint Modal --- */}
      {showComplaintModal && (
        <ComplaintModal onClose={() => setShowComplaintModal(false)} />
      )}
    </div>
  );
}

/* --- App with Router --- */
function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/track" element={<TrackComplaint />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/admin-portal" element={<AdminPortal />} />
          <Route path="/councillor-portal" element={<CouncillorPortal />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
